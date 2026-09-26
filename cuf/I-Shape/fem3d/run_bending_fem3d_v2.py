#!/usr/bin/env python3
# version: 2026-09-24-v3-real-surface-load
"""
Physical geometry and material data are obtained exclusively through the CSF
Python API.  This driver does not parse the CSF YAML itself and does not
interpolate geometry or material laws independently of CSF.

The FEM layer provides only:
- numerical mesh subdivisions;
- 3D stdBrick discretisation;
- bending load and boundary conditions matching the CUF problem;
- OpenSees solution and NPZ output.

Coordinate mapping:
- CSF longitudinal coordinate z -> FEM x;
- CSF section-plane Pt.x      -> FEM y;
- CSF section-plane Pt.y      -> FEM z.
"""
from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class MeshSettings:
    nx: int = 40
    ny_left: int = 2
    ny_web: int = 4
    ny_right: int = 2
    nz_flange: int = 3
    nz_web: int = 12


@dataclass(frozen=True)
class ISectionTopology:
    top_flange: int
    web: int
    bottom_flange: int


@dataclass(frozen=True)
class ISectionStation:
    x: float
    y_left: float
    y_web_left: float
    y_web_right: float
    y_right: float
    z_bottom: float
    z_web_bottom: float
    z_web_top: float
    z_top: float


@dataclass
class StructuredMesh:
    nodes: np.ndarray
    elements: np.ndarray
    element_region: np.ndarray
    element_xmid: np.ndarray
    bottom_faces: np.ndarray
    end0_nodes: np.ndarray
    end1_nodes: np.ndarray


def load_csf_field(path: Path):
    """Load and build the ContinuousSectionField through the public CSF reader."""
    try:
        from csf.io.csf_reader import CSFReader
        from csf.io.csf_issues import CSFIssues
    except ImportError as exc:
        raise SystemExit(
            "CSF is required. Install the project/library in the active environment "
            "(for example: pip install csfpy)."
        ) from exc

    result = CSFReader().read_file(str(path))
    if not result.ok or result.field is None:
        try:
            report = CSFIssues.format_report(result.issues)
        except Exception:
            report = "\n".join(str(issue) for issue in result.issues)
        raise ValueError(f"CSF model could not be built from {path}:\n{report}")

    field = result.field
    if not float(field.s1.z) > float(field.s0.z):
        raise ValueError("CSF field requires s1.z > s0.z for this FEM3D driver")
    return field


def _i_section_topology(field) -> ISectionTopology:
    """Resolve the three physical I-section regions once from the CSF API objects."""
    names = [str(poly.name) for poly in field.s0.polygons]
    required = ("top_flange", "web", "bottom_flange")
    missing = [name for name in required if name not in names]
    if missing:
        raise ValueError(
            "I-shaped FEM3D requires CSF polygon labels "
            f"{required}; missing {missing}; available labels are {names}"
        )
    if len(names) != 3:
        raise ValueError(
            "I-shaped FEM3D expects exactly three CSF polygons "
            f"(top_flange, web, bottom_flange); got {names}"
        )
    return ISectionTopology(
        top_flange=names.index("top_flange"),
        web=names.index("web"),
        bottom_flange=names.index("bottom_flange"),
    )


def _polygon_bounds(poly) -> tuple[float, float, float, float]:
    """Bounds of one CSF Polygon in its native section-plane coordinates."""
    pts = np.asarray([(float(v.x), float(v.y)) for v in poly.vertices], dtype=float)
    if pts.ndim != 2 or pts.shape[1] != 2:
        raise ValueError("CSF Polygon.vertices must define 2D Pt objects")
    return (
        float(np.min(pts[:, 0])),
        float(np.max(pts[:, 0])),
        float(np.min(pts[:, 1])),
        float(np.max(pts[:, 1])),
    )


def _station_from_csf(field, topology: ISectionTopology, x: float) -> ISectionStation:
    """Query CSF for the complete physical section at one FEM longitudinal station."""
    sec = field.section(float(x))
    if sec is None:
        raise ValueError(f"CSF returned no section at z={x}")

    tf = _polygon_bounds(sec.polygons[topology.top_flange])
    wb = _polygon_bounds(sec.polygons[topology.web])
    bf = _polygon_bounds(sec.polygons[topology.bottom_flange])

    tol = 1.0e-10
    if not (
        math.isclose(tf[0], bf[0], abs_tol=tol)
        and math.isclose(tf[1], bf[1], abs_tol=tol)
        and math.isclose(wb[2], bf[3], abs_tol=tol)
        and math.isclose(wb[3], tf[2], abs_tol=tol)
    ):
        raise ValueError(
            f"CSF section at z={x} does not form the expected three-block I-section topology"
        )

    return ISectionStation(
        x=float(sec.z),
        y_left=bf[0],
        y_web_left=wb[0],
        y_web_right=wb[1],
        y_right=bf[1],
        z_bottom=bf[2],
        z_web_bottom=wb[2],
        z_web_top=wb[3],
        z_top=tf[3],
    )


def _material_from_csf(field, region_idx: int, x: float) -> tuple[float, float, float]:
    """Return (E, G, nu) directly from the CSF Polygon evaluated at z=x."""
    sec = field.section(float(x))
    poly = sec.polygons[int(region_idx)]

    if poly.weight is None:
        raise ValueError(f"CSF polygon '{poly.name}' has no weight at z={x}")
    if poly.shear_weight is None:
        raise ValueError(f"CSF polygon '{poly.name}' has no shear_weight at z={x}")
    if poly.poisson is None:
        raise ValueError(f"CSF polygon '{poly.name}' has no poisson value at z={x}")

    E = float(poly.weight)
    G = float(poly.shear_weight)
    nu = float(poly.poisson)
    if not (math.isfinite(E) and E > 0.0):
        raise ValueError(f"invalid CSF weight/E={E} for polygon '{poly.name}' at z={x}")
    if not (math.isfinite(G) and G > 0.0):
        raise ValueError(f"invalid CSF shear_weight/G={G} for polygon '{poly.name}' at z={x}")
    if not math.isfinite(nu):
        raise ValueError(f"invalid CSF poisson={nu} for polygon '{poly.name}' at z={x}")

    # OpenSees ElasticIsotropic accepts E and nu.  G is retained in the output as
    # the CSF shear carrier and checked against the isotropic relation because this
    # FEM3D bending driver uses an isotropic 3D constitutive model.
    G_iso = E / (2.0 * (1.0 + nu))
    if not math.isclose(G, G_iso, rel_tol=1.0e-10, abs_tol=1.0e-12 * max(1.0, abs(G))):
        raise ValueError(
            f"CSF material for polygon '{poly.name}' at z={x} is not compatible with "
            "OpenSees ElasticIsotropic: shear_weight != E/[2(1+nu)]"
        )
    return E, G, nu


def _piecewise_grid(a: float, b: float, n: int) -> np.ndarray:
    if n < 1:
        raise ValueError("mesh subdivision counts must be >= 1")
    return np.linspace(float(a), float(b), int(n) + 1)


def build_mesh(field, topology: ISectionTopology, m: MeshSettings) -> StructuredMesh:
    x0 = float(field.s0.z)
    x1 = float(field.s1.z)
    xs = np.linspace(x0, x1, m.nx + 1)

    node_xyz: list[tuple[float, float, float]] = []
    layer_coord_to_id: list[dict[tuple[float, float], int]] = []
    block_grids = []

    def key(v: float) -> float:
        return round(float(v), 12)

    for x in xs:
        # Geometry comes from CSF at every mesh layer.  There is no FEM-side
        # interpolation between S0 and S1.
        s = _station_from_csf(field, topology, float(x))
        ys_left = _piecewise_grid(s.y_left, s.y_web_left, m.ny_left)
        ys_web = _piecewise_grid(s.y_web_left, s.y_web_right, m.ny_web)
        ys_right = _piecewise_grid(s.y_web_right, s.y_right, m.ny_right)
        ys_full = np.concatenate((ys_left[:-1], ys_web[:-1], ys_right))

        z_bot = _piecewise_grid(s.z_bottom, s.z_web_bottom, m.nz_flange)
        z_web = _piecewise_grid(s.z_web_bottom, s.z_web_top, m.nz_web)
        z_top = _piecewise_grid(s.z_web_top, s.z_top, m.nz_flange)

        coord_to_id: dict[tuple[float, float], int] = {}

        def ensure(y: float, z: float) -> int:
            yz = (key(y), key(z))
            if yz not in coord_to_id:
                coord_to_id[yz] = len(node_xyz)
                node_xyz.append((float(x), float(y), float(z)))
            return coord_to_id[yz]

        for z in z_bot:
            for y in ys_full:
                ensure(y, z)
        for z in z_web:
            for y in ys_web:
                ensure(y, z)
        for z in z_top:
            for y in ys_full:
                ensure(y, z)

        layer_coord_to_id.append(coord_to_id)
        block_grids.append((ys_full, ys_web, z_bot, z_web, z_top))

    elements: list[tuple[int, ...]] = []
    element_region: list[int] = []
    element_xmid: list[float] = []
    bottom_faces: list[tuple[int, ...]] = []

    def ids_for(ix: int, ys: np.ndarray, zs: np.ndarray) -> np.ndarray:
        cmap = layer_coord_to_id[ix]
        out = np.empty((len(zs), len(ys)), dtype=int)
        for iz, z in enumerate(zs):
            for iy, y in enumerate(ys):
                out[iz, iy] = cmap[(key(y), key(z))]
        return out

    def add_block(
        ix: int,
        ys0: np.ndarray,
        zs0: np.ndarray,
        ys1: np.ndarray,
        zs1: np.ndarray,
        region_idx: int,
        *,
        mark_bottom: bool = False,
    ) -> None:
        g0 = ids_for(ix, ys0, zs0)
        g1 = ids_for(ix + 1, ys1, zs1)
        if g0.shape != g1.shape:
            raise RuntimeError("block topology changed between longitudinal layers")
        xmid = 0.5 * (xs[ix] + xs[ix + 1])
        for iz in range(g0.shape[0] - 1):
            for iy in range(g0.shape[1] - 1):
                n000 = g0[iz, iy]
                n010 = g0[iz, iy + 1]
                n001 = g0[iz + 1, iy]
                n011 = g0[iz + 1, iy + 1]
                n100 = g1[iz, iy]
                n110 = g1[iz, iy + 1]
                n101 = g1[iz + 1, iy]
                n111 = g1[iz + 1, iy + 1]
                elements.append((n000, n100, n110, n010, n001, n101, n111, n011))
                element_region.append(int(region_idx))
                element_xmid.append(float(xmid))
                if mark_bottom and iz == 0:
                    bottom_faces.append((n000, n100, n110, n010))

    for ix in range(m.nx):
        yf0, yw0, zb0, zw0, zt0 = block_grids[ix]
        yf1, yw1, zb1, zw1, zt1 = block_grids[ix + 1]
        add_block(
            ix, yf0, zb0, yf1, zb1, topology.bottom_flange, mark_bottom=True
        )
        add_block(ix, yw0, zw0, yw1, zw1, topology.web)
        add_block(ix, yf0, zt0, yf1, zt1, topology.top_flange)

    nodes = np.asarray(node_xyz, dtype=float)
    elems = np.asarray(elements, dtype=int)
    regions = np.asarray(element_region, dtype=int)
    xmids = np.asarray(element_xmid, dtype=float)
    faces = np.asarray(bottom_faces, dtype=int)
    tol = 1.0e-10 * max(1.0, abs(x1 - x0))
    end0 = np.flatnonzero(np.abs(nodes[:, 0] - x0) <= tol)
    end1 = np.flatnonzero(np.abs(nodes[:, 0] - x1) <= tol)

    return StructuredMesh(nodes, elems, regions, xmids, faces, end0, end1)


def evaluate_element_materials(field, mesh: StructuredMesh) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Evaluate CSF material carriers at every element longitudinal centre."""
    E = np.empty(mesh.elements.shape[0], dtype=float)
    G = np.empty(mesh.elements.shape[0], dtype=float)
    nu = np.empty(mesh.elements.shape[0], dtype=float)

    # Query once for each (xmid, region) pair; all bricks in that block slice share it.
    cache: dict[tuple[float, int], tuple[float, float, float]] = {}
    for eid, (xmid, region) in enumerate(zip(mesh.element_xmid, mesh.element_region)):
        k = (float(xmid), int(region))
        if k not in cache:
            cache[k] = _material_from_csf(field, int(region), float(xmid))
        E[eid], G[eid], nu[eid] = cache[k]
    return E, G, nu


def _face_consistent_loads(mesh: StructuredMesh, amplitude: float, x0: float, x1: float):
    """Consistent nodal loads for the Carrera bottom-surface half-wave.

    This is the direct 3D-FE counterpart of BendingSurfaceProjector:

        p_z(x) = -amplitude * sin(pi * (x-x0) / L)

    integrated on the minimum-z physical surface using the real 3D surface
    measure.  The traction direction remains global z; it is not rotated with
    the inclined surface.  This matches surface_halfwave.py exactly.
    """
    L = float(x1 - x0)
    if not L > 0.0:
        raise ValueError("bending load requires x1 > x0")

    # The load is sinusoidal in x.  Eight longitudinal Gauss points make the
    # consistent nodal integration effectively exact for the present linear
    # brick faces, while two points are exact for the transverse linear shape.
    xi_points, xi_weights = np.polynomial.legendre.leggauss(8)
    eta_points, eta_weights = np.polynomial.legendre.leggauss(2)
    loads = np.zeros((mesh.nodes.shape[0], 3), dtype=float)

    for face in mesh.bottom_faces:
        xyz = mesh.nodes[face]

        for xi, wx in zip(xi_points, xi_weights):
            for eta, wy in zip(eta_points, eta_weights):
                N = np.asarray(
                    [
                        0.25 * (1.0 - xi) * (1.0 - eta),
                        0.25 * (1.0 + xi) * (1.0 - eta),
                        0.25 * (1.0 + xi) * (1.0 + eta),
                        0.25 * (1.0 - xi) * (1.0 + eta),
                    ],
                    dtype=float,
                )
                dN_dxi = np.asarray(
                    [
                        -0.25 * (1.0 - eta),
                         0.25 * (1.0 - eta),
                         0.25 * (1.0 + eta),
                        -0.25 * (1.0 + eta),
                    ],
                    dtype=float,
                )
                dN_deta = np.asarray(
                    [
                        -0.25 * (1.0 - xi),
                        -0.25 * (1.0 + xi),
                         0.25 * (1.0 + xi),
                         0.25 * (1.0 - xi),
                    ],
                    dtype=float,
                )

                x = float(np.dot(N, xyz[:, 0]))

                # Real 3D surface Jacobian of the inclined Q4 face.
                tangent_xi = np.asarray(
                    [float(np.dot(dN_dxi, xyz[:, j])) for j in range(3)],
                    dtype=float,
                )
                tangent_eta = np.asarray(
                    [float(np.dot(dN_deta, xyz[:, j])) for j in range(3)],
                    dtype=float,
                )
                jac_surface = float(np.linalg.norm(np.cross(tangent_xi, tangent_eta)))

                # Same sign convention as surface_halfwave.py:
                # t_global,z = amplitude * sin(pi*(x-x0)/L).
                q = float(amplitude) * math.sin(math.pi * (x - x0) / L)
                scale = float(wx) * float(wy) * jac_surface
                for a, nid in enumerate(face):
                    loads[nid, 2] += q * N[a] * scale

    return loads


def _centerline_nodes(mesh: StructuredMesh) -> np.ndarray:
    """Return one (y,z)=(0,0) node for every longitudinal mesh layer.

    carrera_problem.py defines the axial rigid-body gauge at the physical
    section point (0,0).  This FEM mesh must therefore contain that same point;
    no fallback to a different point is allowed.
    """
    scale = max(1.0, float(np.max(np.abs(mesh.nodes))))
    tol = 1.0e-10 * scale
    xs = np.unique(mesh.nodes[:, 0])
    ids = []

    for x in xs:
        candidates = np.flatnonzero(
            (np.abs(mesh.nodes[:, 0] - x) <= tol)
            & (np.abs(mesh.nodes[:, 1]) <= tol)
            & (np.abs(mesh.nodes[:, 2]) <= tol)
        )
        if candidates.size != 1:
            raise ValueError(
                "Carrera axial gauge requires exactly one FEM node at "
                f"(x,y,z)=({x},0,0); found {candidates.size}"
            )
        ids.append(int(candidates[0]))

    return np.asarray(ids, dtype=int)


def _axial_gauge_mean(mesh: StructuredMesh, displacement: np.ndarray, centerline: np.ndarray) -> float:
    """FE analogue of (1/L) integral u_x(x,0,0) dx used by carrera_problem.py."""
    x = np.asarray(mesh.nodes[centerline, 0], dtype=float)
    ux = np.asarray(displacement[centerline, 0], dtype=float)
    order = np.argsort(x)
    x = x[order]
    ux = ux[order]
    length = float(x[-1] - x[0])
    if not length > 0.0:
        raise ValueError("axial gauge requires a non-zero beam length")
    integral = float(np.sum(0.5 * np.diff(x) * (ux[:-1] + ux[1:])))
    return integral / length


def solve_opensees(
    mesh: StructuredMesh,
    element_E: np.ndarray,
    element_nu: np.ndarray,
    amplitude: float,
    x0: float,
    x1: float,
):
    try:
        import openseespy.opensees as ops
    except ImportError as exc:
        raise SystemExit(
            "OpenSeesPy is required. Install it in the active environment with: pip install openseespy"
        ) from exc

    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 3)

    for i, (x, y, z) in enumerate(mesh.nodes, start=1):
        ops.node(i, float(x), float(y), float(z))

    # Reuse a material tag only when CSF returns exactly the same isotropic pair.
    material_tags: dict[tuple[float, float], int] = {}
    element_mat_tag = np.empty(mesh.elements.shape[0], dtype=int)
    for eid, (E, nu) in enumerate(zip(element_E, element_nu)):
        key = (float(E), float(nu))
        tag = material_tags.get(key)
        if tag is None:
            tag = len(material_tags) + 1
            material_tags[key] = tag
            ops.nDMaterial("ElasticIsotropic", tag, float(E), float(nu))
        element_mat_tag[eid] = tag

    for eid, (conn, mat_tag) in enumerate(zip(mesh.elements, element_mat_tag), start=1):
        tags = [int(n) + 1 for n in conn]
        ops.element("stdBrick", eid, *tags, int(mat_tag))

    # Carrera constraints: both end sections have only the two transverse
    # displacement components fixed.  The longitudinal component remains free.
    # A single temporary ux anchor is used only to remove the rigid axial null
    # mode from the OpenSees solve.  After the solve, the displacement field is
    # shifted to satisfy the same integral axial gauge as carrera_problem.py.
    centerline = _centerline_nodes(mesh)
    x_mid = 0.5 * (float(x0) + float(x1))
    gauge = int(centerline[np.argmin(np.abs(mesh.nodes[centerline, 0] - x_mid))])

    fixity: dict[int, list[int]] = {}
    for nid in np.concatenate((mesh.end0_nodes, mesh.end1_nodes)):
        fixity[int(nid)] = [0, 1, 1]
    fixity.setdefault(gauge, [0, 0, 0])[0] = 1

    for nid, flags in fixity.items():
        ops.fix(int(nid) + 1, *flags)

    nodal_loads = _face_consistent_loads(mesh, amplitude, x0, x1)
    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)
    for nid, f in enumerate(nodal_loads, start=1):
        if np.any(f != 0.0):
            ops.load(nid, float(f[0]), float(f[1]), float(f[2]))

    ops.system("UmfPack")
    ops.numberer("RCM")
    ops.constraints("Plain")
    ops.integrator("LoadControl", 1.0)
    ops.algorithm("Linear")
    ops.analysis("Static")
    ok = ops.analyze(1)
    if ok != 0:
        ops.wipeAnalysis()
        ops.system("SparseGeneral", "-piv")
        ops.numberer("RCM")
        ops.constraints("Plain")
        ops.integrator("LoadControl", 1.0)
        ops.algorithm("Linear")
        ops.analysis("Static")
        ok = ops.analyze(1)
    if ok != 0:
        raise RuntimeError(f"OpenSees static analysis failed with code {ok}")

    u = np.asarray(
        [ops.nodeDisp(i) for i in range(1, mesh.nodes.shape[0] + 1)], dtype=float
    )

    # The temporary OpenSees anchor selected one representative of the rigid
    # axial-translation equivalence class.  Re-centre that solution so that
    # (1/L) integral u_x(x,0,0) dx = 0, exactly matching the CUF gauge.
    axial_gauge_shift = _axial_gauge_mean(mesh, u, centerline)
    u[:, 0] -= axial_gauge_shift
    axial_gauge_residual = _axial_gauge_mean(mesh, u, centerline)

    return (
        u,
        nodal_loads,
        gauge,
        element_mat_tag,
        centerline,
        axial_gauge_shift,
        axial_gauge_residual,
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        description="3D solid FEM bending model driven entirely by the CSF API"
    )
    ap.add_argument("model", type=Path, help="CSF YAML model (loaded only through CSFReader)")
    ap.add_argument("output", type=Path, help="output .npz file")
    ap.add_argument("--amplitude", type=float, default=1.0)
    ap.add_argument("--nx", type=int, default=40)
    ap.add_argument("--ny-left", type=int, default=2)
    ap.add_argument("--ny-web", type=int, default=4)
    ap.add_argument("--ny-right", type=int, default=2)
    ap.add_argument("--nz-flange", type=int, default=3)
    ap.add_argument("--nz-web", type=int, default=12)
    ap.add_argument(
        "--mesh-only",
        action="store_true",
        help="write CSF-generated mesh/material/load data without running OpenSees",
    )
    args = ap.parse_args()

    field = load_csf_field(args.model.resolve())
    topology = _i_section_topology(field)
    x0 = float(field.s0.z)
    x1 = float(field.s1.z)

    settings = MeshSettings(
        nx=args.nx,
        ny_left=args.ny_left,
        ny_web=args.ny_web,
        ny_right=args.ny_right,
        nz_flange=args.nz_flange,
        nz_web=args.nz_web,
    )
    mesh = build_mesh(field, topology, settings)
    element_E, element_G, element_nu = evaluate_element_materials(field, mesh)
    loads = _face_consistent_loads(mesh, args.amplitude, x0, x1)

    if args.mesh_only:
        u = np.empty((0, 3), dtype=float)
        gauge = -1
        element_mat_tag = np.full(mesh.elements.shape[0], -1, dtype=int)
        centerline = _centerline_nodes(mesh)
        axial_gauge_shift = math.nan
        axial_gauge_residual = math.nan
    else:
        (
            u,
            loads,
            gauge,
            element_mat_tag,
            centerline,
            axial_gauge_shift,
            axial_gauge_residual,
        ) = solve_opensees(
            mesh, element_E, element_nu, args.amplitude, x0, x1
        )

    region_names = np.asarray(
        [str(poly.name) for poly in field.s0.polygons], dtype="U64"
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.output,
        nodes=mesh.nodes,
        elements=mesh.elements,
        element_region=mesh.element_region,
        element_region_names=region_names,
        element_xmid=mesh.element_xmid,
        element_E=element_E,
        element_G=element_G,
        element_nu=element_nu,
        element_material_tag=element_mat_tag,
        bottom_faces=mesh.bottom_faces,
        displacement=u,
        nodal_loads=loads,
        end0_nodes=mesh.end0_nodes,
        end1_nodes=mesh.end1_nodes,
        gauge_node=np.asarray(gauge, dtype=int),
        axial_gauge_centerline_nodes=centerline,
        axial_gauge_shift=np.asarray(axial_gauge_shift),
        axial_gauge_residual=np.asarray(axial_gauge_residual),
        amplitude=np.asarray(args.amplitude),
        x0=np.asarray(x0),
        x1=np.asarray(x1),
    )

    print(f"model       : {args.model}")
    print("CSF source  : geometry + material via CSFReader / field.section(z)")
    print(f"nodes       : {mesh.nodes.shape[0]}")
    print(f"stdBrick    : {mesh.elements.shape[0]}")
    print(f"bottom faces: {mesh.bottom_faces.shape[0]}")
    print(f"E range     : {element_E.min():.12e} .. {element_E.max():.12e}")
    print(f"G range     : {element_G.min():.12e} .. {element_G.max():.12e}")
    print(f"nu range    : {element_nu.min():.12e} .. {element_nu.max():.12e}")
    print(f"sum Fz      : {loads[:, 2].sum():.12e}")
    if u.size:
        print(f"axial gauge : mean={axial_gauge_residual:.12e} shift={axial_gauge_shift:.12e}")
        i = int(np.argmin(u[:, 2]))
        print(f"min uz      : {u[i, 2]:.12e} at {mesh.nodes[i]}")
    print(f"saved       : {args.output}")


if __name__ == "__main__":
    main()
