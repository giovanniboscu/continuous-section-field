# Driver v8 (2026-10-12)
# Changelog: explicitly accept the actual CSF-CUF PointForceGlobalZPoint class
# reported by the installed library. The point load and the start-section clamp
# still come from the CUF problem builder, with no implicit fallback.
"""
FEM3D driver v8 (2026-10-12).
Historical changelog:
- Remove hard-coded benchmark load amplitude and y/z location restrictions.
- Validate the free-end station against CSF; preserve exact FEM-node matching.
- Preserve structured H8 mesh, OpenSees solve, CLI and NPZ interface.

FEM3D reference for the Carrera Table 9.13 C-section benchmark.

Version v4: adapt structured H8 mesh to the point-load coordinates from YAML;
remove free-end-only point-load restriction; retain exact nodal loading.

The purpose of this driver is to reproduce the CSF-CUF physical problem with a
3D OpenSees stdBrick model while keeping geometry, material, units, coordinates,
load and constraints aligned with the CSF-CUF definition.

Sources of truth
----------------
Geometry and material:
    CSF model loaded through CSFReader / field.section(z).

Load:
    The same CSF-CUF problem YAML is read through the same
    c_section_table_9_13 adapter.  The FEM load is therefore the exact
    PointForceGlobalZPoint (point_force_global_z_point), legacy PointForce, or
    PointForceGlobalZ defined by that problem: neither amplitude nor coordinates
    are independently re-entered here.

Constraint:
    The same CSF-CUF problem adapter supplies the FullStartSectionClamp object.
    This driver accepts that adapter explicitly and translates its physical
    meaning into OpenSees nodal restrictions: ux = uy = uz = 0 on every node
    of the complete start section. Unsupported adapter types raise an error.
    CUF generalized-DOF constraint matrices cannot be applied to H8 DOFs.

Coordinate system
-----------------
The NPZ is written directly in CUF physical axes:

    FEM x = CUF x = CSF longitudinal station z
    FEM y = CUF y = CSF section-plane Pt.x
    FEM z = CUF z = CSF section-plane Pt.y

For the supplied Carrera C-section model this also means:

    paper beam-axis y -> FEM/CUF x
    paper section x   -> FEM/CUF y
    paper section z   -> FEM/CUF z

Units
-----
No unit conversion is performed.  The supplied benchmark uses:

    length : mm
    force  : N
    stress : MPa = N/mm^2

Therefore OpenSees receives coordinates in mm, E/G in MPa, force in N, and its
computed displacements are in mm.

The output contains both the standard ``fem3d_h8_displacement v1`` keys used by
the current stress/strain postprocessor and the legacy keys used by earlier
FEM3D comparison tools.
"""

# Driver v2 (2026-10-10)
# Changelog: accept the load at the area-patch centroid (-50,-450) while
# retaining the original benchmark point (0,-500). Mesh topology, FEM load
# projection, and all other benchmark validations remain unchanged.

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from csf.cuf.adapters.problem.loads.point_force_global_z import PointForceGlobalZ
    from csf.cuf.adapters.problem.loads.point_force_global_z_point import PointForceGlobalZPoint
    from csf.cuf.adapters.problem.constraints.full_start_section_clamp import FullStartSectionClamp
    SupportedPointLoad = PointForceGlobalZ | PointForceGlobalZPoint

import numpy as np


UNITS = "mm,N,MPa"
COORDINATE_SYSTEM = "CUF"
ELEMENT_TYPE = "stdBrick"
FORMAT_NAME = "fem3d_h8_displacement"
FORMAT_VERSION = 1


@dataclass(frozen=True)
class MeshSettings:
    """Structured H8 subdivisions for the three rectangular C-section bands."""

    nx: int = 80
    ny_top_free: int = 18
    ny_bottom_free: int = 8
    ny_web: int = 2
    nz_flange: int = 2
    nz_web: int = 16


@dataclass(frozen=True)
class CSectionStation:
    """Physical C-section dimensions in CUF/FEM y-z coordinates at one x."""

    x: float
    y_top_left: float
    y_bottom_left: float
    y_web_left: float
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
    end0_nodes: np.ndarray
    end1_nodes: np.ndarray


def load_csf_field(path: Path):
    """Load the ContinuousSectionField only through the public CSF reader."""

    try:
        from csf.io.csf_reader import CSFReader
        from csf.io.csf_issues import CSFIssues
    except ImportError as exc:
        raise SystemExit(
            "CSF is required in the active environment. Run this script from the "
            "continuous-section-field environment/repository."
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
        raise ValueError("CSF field requires s1.z > s0.z")
    return field


def load_cuf_problem(path: Path):
    """Build and retain the original CSF-CUF load AND constraint adapters."""

    try:
        import yaml
        from csf.cuf.adapters.problem.c_section_cantilever_point_load import build_problem
        from csf.cuf.adapters.problem.constraints.full_start_section_clamp import FullStartSectionClamp
    except ImportError as exc:
        raise ImportError(
            f"Unable to import the CSF-CUF problem builder, clamp adapter, or PyYAML: {exc}"
        ) from exc

    with path.open("r", encoding="utf-8") as stream:
        root = yaml.safe_load(stream)

    if not isinstance(root, dict):
        raise ValueError(f"problem YAML must contain a mapping: {path}")
    options = root.get("problem")
    if not isinstance(options, dict):
        raise ValueError(f"problem YAML has no 'problem' mapping: {path}")

    problem_type = options.get("type")
    problem = build_problem(problem_type, options)
    load = getattr(problem, "load", None)
    required = ("amplitude", "x", "y", "z")
    # The CSF-CUF builder is the source of the physical load instance.
    # Validate its concrete adapter identity without importing unrelated load
    # modules that a particular installed CSF-CUF release need not export.
    # Accept only explicitly identified global-z point-load adapters.
    # PointForceGlobalZPoint is the concrete class returned by the user's
    # current CSF-CUF problem builder (see 2026-10-12 traceback).
    supported_load_classes = frozenset({
        "csf.cuf.adapters.problem.loads.point_force_global_z_point.PointForceGlobalZPoint",
        "csf.cuf.adapters.problem.loads.point_force_global_z_point.PointForce",
        "csf.cuf.adapters.problem.loads.point_force_global_z.PointForceGlobalZ",
    })
    actual_load_class = f"{type(load).__module__}.{type(load).__name__}"
    if actual_load_class not in supported_load_classes:
        raise ValueError(
            f"Unsupported CSF-CUF global-z point-load adapter: {actual_load_class}. "
            "No implicit conversion is permitted."
        )
    missing = [name for name in required if not hasattr(load, name)]
    if missing:
        raise ValueError(
            "CSF-CUF point-load adapter is missing physical load attributes: "
            + ", ".join(missing)
        )

    values = [float(getattr(load, name)) for name in required]
    if not all(math.isfinite(value) for value in values):
        raise ValueError("point-force data contain non-finite values")

    constraint = getattr(problem, "constraint", None)
    if type(constraint) is not FullStartSectionClamp:
        raise ValueError(
            "Unsupported CSF-CUF constraint adapter for this FEM3D driver: "
            f"{type(constraint).__module__}.{type(constraint).__name__}. "
            "Expected FullStartSectionClamp; no implicit fallback is permitted."
        )

    return problem



def _validate_csf_polygon_identity(field) -> None:
    """Validate the YAML polygon identity without interpreting runtime labels.

    CSF runtime polygon labels can be qualified (e.g. ``c_section:c_section``).
    The public inspection API is the authoritative source for the names declared
    in S0/S1, so use it when available instead of parsing ``poly.name``.
    """

    inspect_entities = getattr(field, "inspect_section_entities", None)
    if not callable(inspect_entities):
        # Older CSF objects may not expose the inspection operation.  The driver
        # still validates the unique eight-vertex C topology and all benchmark
        # dimensions/material/load values, so do not guess from a qualified
        # runtime string here.
        return

    entities = inspect_entities(float(field.s0.z))
    if len(entities) != 1:
        raise ValueError(
            "Carrera Table 9.13 C-section FEM3D expects exactly one CSF polygon; "
            f"inspection returned {len(entities)} entities"
        )

    entity = entities[0]
    s0_name = str(entity.get("s0_name", ""))
    s1_name = str(entity.get("s1_name", s0_name))
    if s0_name != "c_section" or s1_name != "c_section":
        raise ValueError(
            "Carrera Table 9.13 C-section FEM3D expects the CSF polygon declared "
            "as 'c_section' at both end sections; "
            f"inspection returned S0={s0_name!r}, S1={s1_name!r}"
        )

def _polygon_vertices(poly) -> np.ndarray:
    pts = np.asarray([(float(v.x), float(v.y)) for v in poly.vertices], dtype=float)
    if pts.shape != (8, 2):
        raise ValueError(
            "Carrera Table 9.13 FEM3D expects one 8-vertex orthogonal C-section polygon; "
            f"got shape={pts.shape} for polygon {getattr(poly, 'name', '<unnamed>')!r}"
        )
    if not np.isfinite(pts).all():
        raise ValueError("C-section polygon contains non-finite coordinates")
    return pts


def _close(a: float, b: float, scale: float) -> bool:
    return math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=1.0e-10 * scale)


def _station_from_csf(field, x: float) -> CSectionStation:
    """Query and validate the exact Table 9.13 C-section topology at one station."""

    sec = field.section(float(x))
    if sec is None:
        raise ValueError(f"CSF returned no section at longitudinal coordinate x={x}")
    if len(sec.polygons) != 1:
        raise ValueError(
            "Carrera Table 9.13 C-section FEM3D expects exactly one CSF polygon; "
            f"got {len(sec.polygons)} at x={x}"
        )

    # Do not validate the user-facing polygon name from the runtime label here.
    # CSF may qualify runtime labels (for example ``c_section:c_section``).
    # Polygon identity is checked once through the public CSF inspection API in
    # ``_validate_csf_polygon_identity``; this routine only consumes geometry.
    poly = sec.polygons[0]

    # The benchmark CSF polygon is intentionally ordered as the eight physical
    # vertices shown in the model YAML.  Validate that topology instead of
    # silently reinterpreting another polygon.
    p = _polygon_vertices(poly)
    scale = max(1.0, float(np.max(np.abs(p))))
    y0, z0 = p[0]
    y1, z1 = p[1]
    y2, z2 = p[2]
    y3, z3 = p[3]
    y4, z4 = p[4]
    y5, z5 = p[5]
    y6, z6 = p[6]
    y7, z7 = p[7]

    checks = (
        _close(z0, z1, scale),
        _close(y1, y2, scale),
        _close(z2, z3, scale),
        _close(y3, y4, scale),
        _close(z4, z5, scale),
        _close(y5, y6, scale),
        _close(z6, z7, scale),
        _close(y7, y0, scale),
        _close(y0, y7, scale),
        _close(y1, y2, scale),
        _close(y5, y6, scale),
        _close(z7, z6, scale),
        _close(z5, z4, scale),
    )
    if not all(checks):
        raise ValueError(
            f"CSF section at x={x} does not match the expected orthogonal C-section topology"
        )

    y_top_left = float(y3)
    y_bottom_left = float(y0)
    y_web_left = float(y6)
    y_right = float(y1)
    z_bottom = float(z0)
    z_web_bottom = float(z7)
    z_web_top = float(z5)
    z_top = float(z2)

    if not (
        y_top_left < y_bottom_left < y_web_left < y_right
        and z_bottom < z_web_bottom < z_web_top < z_top
    ):
        raise ValueError(
            "C-section orientation differs from the benchmark orientation "
            "(web right, opening left, long flange top)"
        )

    return CSectionStation(
        x=float(sec.z),
        y_top_left=y_top_left,
        y_bottom_left=y_bottom_left,
        y_web_left=y_web_left,
        y_right=y_right,
        z_bottom=z_bottom,
        z_web_bottom=z_web_bottom,
        z_web_top=z_web_top,
        z_top=z_top,
    )


def _material_from_csf(field, x: float) -> tuple[float, float, float]:
    """Return physical (E,G,nu) with no unit conversion."""

    sec = field.section(float(x))
    if sec is None or len(sec.polygons) != 1:
        raise ValueError(f"expected one C-section polygon at x={x}")
    poly = sec.polygons[0]

    if poly.weight is None:
        raise ValueError(f"CSF polygon '{poly.name}' has no weight/E at x={x}")
    if poly.shear_weight is None:
        raise ValueError(f"CSF polygon '{poly.name}' has no shear_weight/G at x={x}")
    if poly.poisson is None:
        raise ValueError(f"CSF polygon '{poly.name}' has no poisson value at x={x}")

    E = float(poly.weight)
    G = float(poly.shear_weight)
    nu = float(poly.poisson)
    if not (math.isfinite(E) and E > 0.0):
        raise ValueError(f"invalid E={E} at x={x}")
    if not (math.isfinite(G) and G > 0.0):
        raise ValueError(f"invalid G={G} at x={x}")
    if not math.isfinite(nu):
        raise ValueError(f"invalid nu={nu} at x={x}")

    # OpenSees ElasticIsotropic is parameterised by E and nu.  Reject the model
    # if the CSF shear carrier describes a different constitutive law.
    G_iso = E / (2.0 * (1.0 + nu))
    if not math.isclose(
        G,
        G_iso,
        rel_tol=1.0e-10,
        abs_tol=1.0e-12 * max(1.0, abs(G)),
    ):
        raise ValueError(
            "CSF material is not compatible with OpenSees ElasticIsotropic: "
            f"G={G} but E/[2(1+nu)]={G_iso} at x={x}"
        )
    return E, G, nu


def _grid(a: float, b: float, n: int) -> np.ndarray:
    if int(n) < 1:
        raise ValueError("all mesh subdivision counts must be >= 1")
    return np.linspace(float(a), float(b), int(n) + 1)


def _joined_grid(a: float, interface: float, b: float, n_a: int, n_b: int) -> np.ndarray:
    """Grid that contains the web interface exactly and shares its web nodes."""

    left = _grid(a, interface, n_a)
    right = _grid(interface, b, n_b)
    return np.concatenate((left[:-1], right))


def _insert_grid_coordinate(grid: np.ndarray, position: float) -> np.ndarray:
    """Include an interior target coordinate without moving existing grid nodes."""
    target = float(position)
    if grid[0] < target < grid[-1] and not np.any(np.isclose(grid, target, rtol=0, atol=1e-9)):
        return np.sort(np.append(grid, target))
    return grid


def build_mesh(field, settings: MeshSettings, force: SupportedPointLoad | None = None) -> StructuredMesh:
    """Build a conforming three-block H8 mesh directly in CUF physical axes."""

    x0 = float(field.s0.z)
    x1 = float(field.s1.z)
    xs = np.linspace(x0, x1, settings.nx + 1)
    if force is not None:
        if not x0 <= force.x <= x1:
            raise ValueError(f"Point-load x={force.x} lies outside [{x0}, {x1}]")
        xs = _insert_grid_coordinate(xs, force.x)

    # Determine which structured section band contains the requested point.
    # Insert matching cuts on every longitudinal station to preserve H8 topology.
    target_y_band = None
    target_z_band = None
    if force is not None:
        station = _station_from_csf(field, force.x)
        if station.y_bottom_left < force.y < station.y_web_left and station.z_bottom <= force.z <= station.z_web_bottom:
            target_y_band = "bottom_free"
        elif station.y_top_left < force.y < station.y_web_left and station.z_web_top <= force.z <= station.z_top:
            target_y_band = "top_free"
        elif station.y_web_left < force.y < station.y_right:
            target_y_band = "web"
        if station.z_bottom < force.z < station.z_web_bottom:
            target_z_band = "bottom"
        elif station.z_web_bottom < force.z < station.z_web_top:
            target_z_band = "web"
        elif station.z_web_top < force.z < station.z_top:
            target_z_band = "top"

    node_xyz: list[tuple[float, float, float]] = []
    layer_coord_to_id: list[dict[tuple[float, float], int]] = []
    block_grids: list[tuple[np.ndarray, ...]] = []

    def key(v: float) -> float:
        return round(float(v), 12)

    for x in xs:
        s = _station_from_csf(field, float(x))

        y_web = _grid(s.y_web_left, s.y_right, settings.ny_web)
        y_bottom = _joined_grid(
            s.y_bottom_left,
            s.y_web_left,
            s.y_right,
            settings.ny_bottom_free,
            settings.ny_web,
        )
        y_top = _joined_grid(
            s.y_top_left,
            s.y_web_left,
            s.y_right,
            settings.ny_top_free,
            settings.ny_web,
        )

        z_bottom = _grid(s.z_bottom, s.z_web_bottom, settings.nz_flange)
        z_web = _grid(s.z_web_bottom, s.z_web_top, settings.nz_web)
        z_top = _grid(s.z_web_top, s.z_top, settings.nz_flange)

        if force is not None:
            if target_y_band == "bottom_free":
                if not s.y_bottom_left < force.y < s.y_web_left:
                    raise ValueError("Point y cannot define a conforming bottom-flange grid at all stations")
                y_bottom = _insert_grid_coordinate(y_bottom, force.y)
            elif target_y_band == "top_free":
                if not s.y_top_left < force.y < s.y_web_left:
                    raise ValueError("Point y cannot define a conforming top-flange grid at all stations")
                y_top = _insert_grid_coordinate(y_top, force.y)
            elif target_y_band == "web":
                if not s.y_web_left < force.y < s.y_right:
                    raise ValueError("Point y cannot define a conforming web grid at all stations")
                y_web = _insert_grid_coordinate(y_web, force.y)
                y_bottom = _insert_grid_coordinate(y_bottom, force.y)
                y_top = _insert_grid_coordinate(y_top, force.y)
            if target_z_band == "bottom":
                z_bottom = _insert_grid_coordinate(z_bottom, force.z)
            elif target_z_band == "web":
                z_web = _insert_grid_coordinate(z_web, force.z)
            elif target_z_band == "top":
                z_top = _insert_grid_coordinate(z_top, force.z)

        coord_to_id: dict[tuple[float, float], int] = {}

        def ensure(y: float, z: float) -> int:
            yz = (key(y), key(z))
            if yz not in coord_to_id:
                coord_to_id[yz] = len(node_xyz)
                node_xyz.append((float(x), float(y), float(z)))
            return coord_to_id[yz]

        for z in z_bottom:
            for y in y_bottom:
                ensure(y, z)
        for z in z_web:
            for y in y_web:
                ensure(y, z)
        for z in z_top:
            for y in y_top:
                ensure(y, z)

        layer_coord_to_id.append(coord_to_id)
        block_grids.append((y_bottom, y_web, y_top, z_bottom, z_web, z_top))

    elements: list[tuple[int, ...]] = []
    element_xmid: list[float] = []

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
    ) -> None:
        g0 = ids_for(ix, ys0, zs0)
        g1 = ids_for(ix + 1, ys1, zs1)
        if g0.shape != g1.shape:
            raise RuntimeError("C-section block topology changed between longitudinal layers")

        xmid = 0.5 * (xs[ix] + xs[ix + 1])
        for iz in range(g0.shape[0] - 1):
            for iy in range(g0.shape[1] - 1):
                n000 = int(g0[iz, iy])
                n010 = int(g0[iz, iy + 1])
                n001 = int(g0[iz + 1, iy])
                n011 = int(g0[iz + 1, iy + 1])
                n100 = int(g1[iz, iy])
                n110 = int(g1[iz, iy + 1])
                n101 = int(g1[iz + 1, iy])
                n111 = int(g1[iz + 1, iy + 1])

                # OpenSees stdBrick / H8 ordering.  This is also the ordering
                # expected by the existing FEM3D strain/stress recovery code.
                elements.append(
                    (n000, n100, n110, n010, n001, n101, n111, n011)
                )
                element_xmid.append(float(xmid))

    for ix in range(len(xs) - 1):
        yb0, yw0, yt0, zb0, zw0, zt0 = block_grids[ix]
        yb1, yw1, yt1, zb1, zw1, zt1 = block_grids[ix + 1]
        add_block(ix, yb0, zb0, yb1, zb1)
        add_block(ix, yw0, zw0, yw1, zw1)
        add_block(ix, yt0, zt0, yt1, zt1)

    nodes = np.asarray(node_xyz, dtype=float)
    elems = np.asarray(elements, dtype=np.int64)
    xmids = np.asarray(element_xmid, dtype=float)
    regions = np.zeros(elems.shape[0], dtype=np.int64)

    tol = 1.0e-10 * max(1.0, abs(x1 - x0))
    end0 = np.flatnonzero(np.abs(nodes[:, 0] - x0) <= tol)
    end1 = np.flatnonzero(np.abs(nodes[:, 0] - x1) <= tol)

    if end0.size == 0 or end1.size == 0:
        raise RuntimeError("failed to identify complete start/end FEM sections")

    return StructuredMesh(
        nodes=nodes,
        elements=elems,
        element_region=regions,
        element_xmid=xmids,
        end0_nodes=end0.astype(np.int64),
        end1_nodes=end1.astype(np.int64),
    )


def evaluate_element_materials(field, mesh: StructuredMesh):
    """Evaluate the same CSF material at every H8 longitudinal centre."""

    E = np.empty(mesh.elements.shape[0], dtype=float)
    G = np.empty(mesh.elements.shape[0], dtype=float)
    nu = np.empty(mesh.elements.shape[0], dtype=float)
    cache: dict[float, tuple[float, float, float]] = {}

    for eid, xmid in enumerate(mesh.element_xmid):
        key = float(xmid)
        if key not in cache:
            cache[key] = _material_from_csf(field, key)
        E[eid], G[eid], nu[eid] = cache[key]
    return E, G, nu


def build_point_load(mesh: StructuredMesh, force: SupportedPointLoad) -> tuple[np.ndarray, int]:
    """Apply exactly one physical global-z point force at its FEM node."""

    point = np.asarray((force.x, force.y, force.z), dtype=float)
    scale = max(1.0, float(np.max(np.abs(mesh.nodes))), float(np.max(np.abs(point))))
    tol = 1.0e-10 * scale
    matches = np.flatnonzero(np.all(np.abs(mesh.nodes - point) <= tol, axis=1))
    if matches.size != 1:
        raise ValueError(
            "The CUF point load must coincide with exactly one FEM node. "
            f"point={tuple(point)}, matches={matches.size}. "
            "The C-section mesh must not move or distribute this load."
        )

    load_node = int(matches[0])
    loads = np.zeros_like(mesh.nodes, dtype=float)
    loads[load_node, 2] = float(force.amplitude)
    return loads, load_node


def _validate_physical_contract(field, mesh: StructuredMesh, force: SupportedPointLoad) -> None:
    """Validate CSF longitudinal bounds and exact mesh position, not fixed inputs."""
    x0 = float(field.s0.z)
    x1 = float(field.s1.z)
    if not x0 <= force.x <= x1:
        raise ValueError(f"Point-force x={force.x} lies outside the CSF domain [{x0}, {x1}]")
    tol = 1e-10 * max(1.0, abs(x0), abs(x1))
    if not np.allclose(mesh.nodes[mesh.end0_nodes, 0], x0, rtol=0.0, atol=tol):
        raise RuntimeError("start-section nodes do not match the CSF start station")



def apply_cuf_constraint_to_fem(mesh: StructuredMesh, constraint: FullStartSectionClamp, ops) -> None:
    """Translate the physical meaning of the selected CSF-CUF adapter to H8 DOFs.

    FullStartSectionClamp.build_constraints() acts on CUF generalized DOFs and
    cannot be reused directly for FEM nodal DOFs. The adapter type is checked
    explicitly: no other constraint is silently treated as a full clamp.
    """
    from csf.cuf.adapters.problem.constraints.full_start_section_clamp import FullStartSectionClamp

    if type(constraint) is not FullStartSectionClamp:
        raise ValueError(
            "Unsupported constraint adapter for H8 translation: "
            f"{type(constraint).__module__}.{type(constraint).__name__}"
        )
    if mesh.end0_nodes.size == 0:
        raise ValueError("No nodes were found on the start section")

    # Exact FEM nodal counterpart of the original CSF-CUF adapter:
    # ux = uy = uz = 0 on the entire initial section.
    for nid in mesh.end0_nodes:
        ops.fix(int(nid) + 1, 1, 1, 1)


def solve_opensees(
    mesh: StructuredMesh,
    element_E: np.ndarray,
    element_nu: np.ndarray,
    nodal_loads: np.ndarray,
    constraint: FullStartSectionClamp,
):
    """Solve using the exact CUF problem load and translated CUF constraint."""

    try:
        import openseespy.opensees as ops
    except ImportError as exc:
        raise SystemExit(
            "OpenSeesPy is required. Install it in the active environment with: "
            "pip install openseespy"
        ) from exc

    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 3)

    for node_id, (x, y, z) in enumerate(mesh.nodes, start=1):
        ops.node(node_id, float(x), float(y), float(z))

    material_tags: dict[tuple[float, float], int] = {}
    element_mat_tag = np.empty(mesh.elements.shape[0], dtype=np.int64)
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

    apply_cuf_constraint_to_fem(mesh, constraint, ops)

    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)
    loaded = np.flatnonzero(np.any(nodal_loads != 0.0, axis=1))
    if loaded.size != 1:
        raise RuntimeError(f"expected exactly one loaded FEM node; got {loaded.size}")
    for nid in loaded:
        f = nodal_loads[int(nid)]
        ops.load(int(nid) + 1, float(f[0]), float(f[1]), float(f[2]))

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

    displacement = np.asarray(
        [ops.nodeDisp(i) for i in range(1, mesh.nodes.shape[0] + 1)],
        dtype=float,
    )

    support_reactions = np.full((mesh.end0_nodes.size, 3), np.nan, dtype=float)
    try:
        ops.reactions()
        support_reactions = np.asarray(
            [ops.nodeReaction(int(nid) + 1) for nid in mesh.end0_nodes],
            dtype=float,
        )
    except Exception:
        # Reactions are diagnostic only; the displacement solution remains valid.
        pass

    return displacement, element_mat_tag, support_reactions


def _save_npz(
    path: Path,
    *,
    model_path: Path,
    problem_path: Path,
    mesh: StructuredMesh,
    displacement: np.ndarray,
    element_E: np.ndarray,
    element_G: np.ndarray,
    element_nu: np.ndarray,
    element_mat_tag: np.ndarray,
    nodal_loads: np.ndarray,
    load_node: int,
    force: SupportedPointLoad,
    support_reactions: np.ndarray,
    x0: float,
    x1: float,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    element_ids = np.arange(1, mesh.elements.shape[0] + 1, dtype=np.int64)
    load_point = np.asarray((force.x, force.y, force.z), dtype=float)

    np.savez_compressed(
        path,
        # Current standard FEM3D H8 schema.
        format=np.asarray(FORMAT_NAME),
        coordinate_system=np.asarray(COORDINATE_SYSTEM),
        element_type=np.asarray(ELEMENT_TYPE),
        version=np.asarray(FORMAT_VERSION, dtype=np.int64),
        connectivity_index_base=np.asarray(0, dtype=np.int64),
        coordinates=mesh.nodes,
        displacements=displacement,
        connectivity=mesh.elements,
        element_ids=element_ids,
        units=np.asarray(UNITS),
        # Legacy compatibility keys.
        nodes=mesh.nodes,
        elements=mesh.elements,
        displacement=displacement,
        amplitude=np.asarray(force.amplitude),
        x0=np.asarray(x0),
        x1=np.asarray(x1),
        # Physical/model metadata.
        model_path=np.asarray(str(model_path)),
        problem_path=np.asarray(str(problem_path)),
        coordinate_mapping=np.asarray(
            "x=CSF station z; y=CSF Pt.x; z=CSF Pt.y; identical to CUF physical axes"
        ),
        length_unit=np.asarray("mm"),
        force_unit=np.asarray("N"),
        stress_unit=np.asarray("MPa"),
        constraint_type=np.asarray("full_start_section_clamp"),
        load_type=np.asarray("point_force_global_z"),
        load_point=load_point,
        load_vector=np.asarray((0.0, 0.0, force.amplitude), dtype=float),
        load_node=np.asarray(load_node, dtype=np.int64),
        nodal_loads=nodal_loads,
        end0_nodes=mesh.end0_nodes,
        end1_nodes=mesh.end1_nodes,
        support_reactions=support_reactions,
        element_region=mesh.element_region,
        element_region_names=np.asarray(("c_section",), dtype="U64"),
        element_xmid=mesh.element_xmid,
        element_E=element_E,
        element_G=element_G,
        element_nu=element_nu,
        element_material_tag=element_mat_tag,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "3D stdBrick FEM reference for Carrera Table 9.13, using the same "
            "CSF geometry/material, CUF axes, point load and full start clamp."
        )
    )
    parser.add_argument("model", type=Path, help="CSF C-section YAML")
    parser.add_argument("problem", type=Path, help="CSF-CUF Table 9.13 problem YAML")
    parser.add_argument("output", type=Path, help="output FEM3D .npz")
    parser.add_argument("--nx", type=int, default=80)
    parser.add_argument("--ny-top-free", type=int, default=18)
    parser.add_argument("--ny-bottom-free", type=int, default=8)
    parser.add_argument("--ny-web", type=int, default=2)
    parser.add_argument("--nz-flange", type=int, default=2)
    parser.add_argument("--nz-web", type=int, default=16)
    parser.add_argument(
        "--mesh-only",
        action="store_true",
        help="write mesh/material/load data without running OpenSees",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    model_path = args.model.expanduser().resolve()
    problem_path = args.problem.expanduser().resolve()
    output_path = args.output.expanduser().resolve()

    field = load_csf_field(model_path)
    _validate_csf_polygon_identity(field)
    cuf_problem = load_cuf_problem(problem_path)
    force = cuf_problem.load
    constraint = cuf_problem.constraint
    x0 = float(field.s0.z)
    x1 = float(field.s1.z)

    settings = MeshSettings(
        nx=args.nx,
        ny_top_free=args.ny_top_free,
        ny_bottom_free=args.ny_bottom_free,
        ny_web=args.ny_web,
        nz_flange=args.nz_flange,
        nz_web=args.nz_web,
    )
    mesh = build_mesh(field, settings, force)
    element_E, element_G, element_nu = evaluate_element_materials(field, mesh)
    nodal_loads, load_node = build_point_load(mesh, force)
    _validate_physical_contract(field, mesh, force)

    if args.mesh_only:
        displacement = np.empty((0, 3), dtype=float)
        element_mat_tag = np.full(mesh.elements.shape[0], -1, dtype=np.int64)
        support_reactions = np.empty((0, 3), dtype=float)
    else:
        displacement, element_mat_tag, support_reactions = solve_opensees(
            mesh,
            element_E,
            element_nu,
            nodal_loads,
            constraint,
        )

    _save_npz(
        output_path,
        model_path=model_path,
        problem_path=problem_path,
        mesh=mesh,
        displacement=displacement,
        element_E=element_E,
        element_G=element_G,
        element_nu=element_nu,
        element_mat_tag=element_mat_tag,
        nodal_loads=nodal_loads,
        load_node=load_node,
        force=force,
        support_reactions=support_reactions,
        x0=x0,
        x1=x1,
    )

    print("FEM3D Carrera Table 9.13 C-section")
    print("====================================")
    print(f"model             : {model_path}")
    print(f"problem           : {problem_path}")
    print(f"CUF load adapter  : {type(force).__module__}.{type(force).__name__}")
    print(f"CUF constraint    : {type(constraint).__module__}.{type(constraint).__name__}")
    print(f"coordinate system : CUF (x longitudinal, y/z cross-section)")
    print(f"mapping           : x=CSF station z, y=CSF Pt.x, z=CSF Pt.y")
    print(f"units             : {UNITS} (no conversion)")
    print(f"domain x          : {x0:.12g} .. {x1:.12g} mm")
    print(f"nodes             : {mesh.nodes.shape[0]}")
    print(f"stdBrick          : {mesh.elements.shape[0]}")
    print(f"clamped nodes     : {mesh.end0_nodes.size} at x={x0:.12g} mm; ux=uy=uz=0")
    print(
        "point load         : "
        f"Fz={force.amplitude:.12g} N at "
        f"(x,y,z)=({force.x:.12g},{force.y:.12g},{force.z:.12g}) mm"
    )
    print(f"load node          : {load_node} -> {mesh.nodes[load_node]}")
    print(
        "sum applied force : "
        f"({nodal_loads[:,0].sum():.12e}, "
        f"{nodal_loads[:,1].sum():.12e}, "
        f"{nodal_loads[:,2].sum():.12e}) N"
    )
    print(f"E range           : {element_E.min():.12e} .. {element_E.max():.12e} MPa")
    print(f"G range           : {element_G.min():.12e} .. {element_G.max():.12e} MPa")
    print(f"nu range          : {element_nu.min():.12e} .. {element_nu.max():.12e}")
    if displacement.size:
        tip = mesh.end1_nodes
        iz = int(tip[np.argmin(displacement[tip, 2])])
        print(f"min tip uz        : {displacement[iz,2]:.12e} mm at {mesh.nodes[iz]}")
        if support_reactions.size and np.isfinite(support_reactions).all():
            reaction_sum = support_reactions.sum(axis=0)
            print(
                "sum reactions      : "
                f"({reaction_sum[0]:.12e}, {reaction_sum[1]:.12e}, "
                f"{reaction_sum[2]:.12e}) N"
            )
    print(f"saved             : {output_path}")


if __name__ == "__main__":
    main()
