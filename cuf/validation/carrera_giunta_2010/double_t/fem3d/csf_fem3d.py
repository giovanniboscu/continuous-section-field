from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np

from csf.io.csf_issues import CSFIssues
from csf.io.csf_reader import CSFReader


# ---------------------------------------------------------------------------
# Small data objects
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MaterialState:
    E: float
    G: float
    nu: float


@dataclass(frozen=True)
class RectDomain:
    domain_id: int
    y0: float
    y1: float
    z0: float
    z1: float
    material: MaterialState

    @property
    def width(self) -> float:
        return self.y1 - self.y0

    @property
    def height(self) -> float:
        return self.z1 - self.z0

    @property
    def z_mid(self) -> float:
        return 0.5 * (self.z0 + self.z1)


@dataclass(frozen=True)
class ISectionFrame:
    bottom: RectDomain
    web: RectDomain
    top: RectDomain

    def domain_for_role(self, role: str) -> RectDomain:
        return {
            "bottom": self.bottom,
            "web": self.web,
            "top": self.top,
        }[role]


@dataclass(frozen=True)
class Cell2D:
    role: str
    corners: Tuple[Tuple[float, float], ...]  # (y,z): 00,10,11,01


@dataclass
class StationMesh:
    x: float
    nodes: Dict[Tuple[float, float], int]
    cells: List[Cell2D]
    plus_load_node: int
    minus_load_node: int


@dataclass(frozen=True)
class Brick:
    tag: int
    node_tags: Tuple[int, int, int, int, int, int, int, int]
    role: str
    domain_id: int
    material: MaterialState


@dataclass
class FEMMesh:
    nodes: Dict[int, Tuple[float, float, float]]
    bricks: List[Brick]
    stations: List[StationMesh]
    x0: float
    x1: float
    end0_nodes: List[int]
    end1_nodes: List[int]
    axial_anchor_node: int


# ---------------------------------------------------------------------------
# CSF model
# ---------------------------------------------------------------------------

def read_csf_field(path: str | Path):
    """Read one CSF YAML model. Geometry and material come only from this file."""
    result = CSFReader().read_file(str(Path(path)))
    if not result.ok or result.field is None:
        raise RuntimeError(CSFIssues.format_report(result.issues))
    return result.field


def longitudinal_domain(field) -> Tuple[float, float]:
    x0 = float(field.z0)
    x1 = float(field.z1)
    if x1 <= x0:
        raise ValueError(f"CSF longitudinal coordinates must increase: {x0}, {x1}")
    return x0, x1


def _polygon_area(vertices: Iterable[Tuple[float, float]]) -> float:
    pts = list(vertices)
    area2 = 0.0
    for i, (y0, z0) in enumerate(pts):
        y1, z1 = pts[(i + 1) % len(pts)]
        area2 += y0 * z1 - y1 * z0
    return 0.5 * abs(area2)


def _material_from_polygon(poly) -> MaterialState:
    """
    Resolve the physical isotropic state carried by one sampled CSF polygon.

    CSF post-resolution absolute carriers are preferred:
        weightabs        -> E
        shear_weightabs  -> G

    OpenSees ElasticIsotropic accepts E and nu.  nu is therefore reconstructed
    from the two CSF carriers so that the OpenSees material has the same E-G
    isotropic constitutive state used by the CSF-CUF path.

    If CSF also exposes poisson, it is used only as a consistency check.
    """
    E_raw = getattr(poly, "weightabs", None)
    if E_raw is None:
        E_raw = getattr(poly, "weight", None)

    G_raw = getattr(poly, "shear_weightabs", None)
    if G_raw is None:
        G_raw = getattr(poly, "shear_weight", None)

    if E_raw is None or G_raw is None:
        raise ValueError("CSF polygon does not provide both E and G carriers")

    E = float(E_raw)
    G = float(G_raw)

    if not (math.isfinite(E) and E > 0.0):
        raise ValueError(f"invalid CSF E carrier: {E!r}")
    if not (math.isfinite(G) and G > 0.0):
        raise ValueError(f"invalid CSF G carrier: {G!r}")

    nu = E / (2.0 * G) - 1.0
    if not (-1.0 < nu < 0.5):
        raise ValueError(
            f"invalid isotropic E-G state: E={E}, G={G}, derived nu={nu}"
        )

    poisson_raw = getattr(poly, "poisson", None)
    if poisson_raw is not None:
        poisson = float(poisson_raw)
        if math.isfinite(poisson):
            tol = 1.0e-9 * max(1.0, abs(poisson), abs(nu))
            if abs(poisson - nu) > tol:
                raise ValueError(
                    "CSF material inconsistency: "
                    f"poisson={poisson} but E/G imply nu={nu}"
                )

    return MaterialState(E=E, G=G, nu=nu)


def _rect_domain_from_polygon(poly, domain_id: int) -> RectDomain:
    vertices = [(float(v.x), float(v.y)) for v in poly.vertices]
    ys = [p[0] for p in vertices]
    zs = [p[1] for p in vertices]

    y0, y1 = min(ys), max(ys)
    z0, z1 = min(zs), max(zs)

    if not (y1 > y0 and z1 > z0):
        raise ValueError(f"domain {domain_id} has zero rectangular extent")

    polygon_area = _polygon_area(vertices)
    box_area = (y1 - y0) * (z1 - z0)
    tol = 1.0e-9 * max(1.0, box_area)

    # Extra collinear vertices are accepted; this is useful for the I-section
    # flange polygons used by the CSF model.
    if abs(polygon_area - box_area) > tol:
        raise ValueError(
            "The first FEM3D mesher supports an I-section built from three "
            f"axis-aligned rectangular CSF domains. Domain {domain_id} is not rectangular."
        )

    return RectDomain(
        domain_id=domain_id,
        y0=y0,
        y1=y1,
        z0=z0,
        z1=z1,
        material=_material_from_polygon(poly),
    )


def i_section_frame(field, x: float) -> ISectionFrame:
    """
    Infer the first supported topology: three rectangular domains forming an I.

    No domain name is used.  No dimension is prescribed.
    """
    section = field.section(float(x))
    if section is None or not hasattr(section, "polygons"):
        raise RuntimeError(f"CSF returned no polygonal section at x={x}")

    if len(section.polygons) != 3:
        raise ValueError(
            "The first FEM3D mesher requires exactly three CSF domains "
            "forming an I-section."
        )

    rects = [
        _rect_domain_from_polygon(poly, domain_id=i)
        for i, poly in enumerate(section.polygons)
    ]
    bottom, web, top = sorted(rects, key=lambda r: r.z_mid)

    scale = max(
        1.0,
        abs(bottom.y0), abs(bottom.y1), abs(bottom.z0), abs(bottom.z1),
        abs(web.y0), abs(web.y1), abs(web.z0), abs(web.z1),
        abs(top.y0), abs(top.y1), abs(top.z0), abs(top.z1),
    )
    tol = 1.0e-9 * scale

    if abs(bottom.z1 - web.z0) > tol:
        raise ValueError("I-section topology error: bottom flange does not meet the web")
    if abs(web.z1 - top.z0) > tol:
        raise ValueError("I-section topology error: web does not meet the top flange")

    if bottom.y0 > web.y0 + tol or bottom.y1 < web.y1 - tol:
        raise ValueError("I-section topology error: web lies outside bottom flange width")
    if top.y0 > web.y0 + tol or top.y1 < web.y1 - tol:
        raise ValueError("I-section topology error: web lies outside top flange width")

    return ISectionFrame(bottom=bottom, web=web, top=top)


# ---------------------------------------------------------------------------
# Structured I-section mesh
# ---------------------------------------------------------------------------

def _linspace(a: float, b: float, divisions: int) -> List[float]:
    if divisions < 1:
        raise ValueError("all mesh division counts must be >= 1")
    return [float(v) for v in np.linspace(float(a), float(b), int(divisions) + 1)]


def _join_piecewise(parts: List[List[float]]) -> List[float]:
    values: List[float] = []
    for part in parts:
        if not values:
            values.extend(part)
        else:
            values.extend(part[1:])
    return values


def _flange_y_grid(
    flange: RectDomain,
    web: RectDomain,
    overhang_divisions: int,
    web_width_divisions: int,
) -> List[float]:
    parts: List[List[float]] = []

    if web.y0 > flange.y0:
        parts.append(_linspace(flange.y0, web.y0, overhang_divisions))

    parts.append(_linspace(web.y0, web.y1, web_width_divisions))

    if flange.y1 > web.y1:
        parts.append(_linspace(web.y1, flange.y1, overhang_divisions))

    return _join_piecewise(parts)


def _coord_key(y: float, z: float) -> Tuple[float, float]:
    # Coordinates in CSF are deterministic interpolations.  Rounding is used
    # only to merge nodes shared by adjacent rectangular sub-domains.
    return (round(float(y), 12), round(float(z), 12))


def _add_rect_cells(
    cells: List[Cell2D],
    *,
    role: str,
    ys: List[float],
    zs: List[float],
) -> None:
    for iz in range(len(zs) - 1):
        for iy in range(len(ys) - 1):
            y0, y1 = ys[iy], ys[iy + 1]
            z0, z1 = zs[iz], zs[iz + 1]
            cells.append(
                Cell2D(
                    role=role,
                    corners=(
                        _coord_key(y0, z0),
                        _coord_key(y1, z0),
                        _coord_key(y1, z1),
                        _coord_key(y0, z1),
                    ),
                )
            )


def _section_cells(frame: ISectionFrame, mesh_cfg: dict) -> List[Cell2D]:
    no = int(mesh_cfg["flange_overhang_divisions"])
    nw = int(mesh_cfg["web_width_divisions"])
    nt = int(mesh_cfg["flange_thickness_divisions"])
    nh = int(mesh_cfg["web_height_divisions"])

    bottom_ys = _flange_y_grid(frame.bottom, frame.web, no, nw)
    web_ys = _linspace(frame.web.y0, frame.web.y1, nw)
    top_ys = _flange_y_grid(frame.top, frame.web, no, nw)

    bottom_zs = _linspace(frame.bottom.z0, frame.bottom.z1, nt)
    web_zs = _linspace(frame.web.z0, frame.web.z1, nh)
    top_zs = _linspace(frame.top.z0, frame.top.z1, nt)

    cells: List[Cell2D] = []
    _add_rect_cells(cells, role="bottom", ys=bottom_ys, zs=bottom_zs)
    _add_rect_cells(cells, role="web", ys=web_ys, zs=web_zs)
    _add_rect_cells(cells, role="top", ys=top_ys, zs=top_zs)
    return cells


def _find_corner_node(
    node_map: Dict[Tuple[float, float], int],
    *,
    y: float,
    z: float,
    label: str,
) -> int:
    key = _coord_key(y, z)
    if key not in node_map:
        raise ValueError(
            f"{label} torsion load point is not a mesh vertex: y={y}, z={z}"
        )
    return node_map[key]


def build_mesh(field, mesh_cfg: dict) -> FEMMesh:
    """
    Build a conforming stdBrick-ready mesh from the sampled CSF I-section.

    The geometry is re-evaluated from CSF at every longitudinal station.
    """
    x0, x1 = longitudinal_domain(field)
    nx = int(mesh_cfg["longitudinal_divisions"])
    if nx < 1:
        raise ValueError("mesh.longitudinal_divisions must be >= 1")

    xs = [float(v) for v in np.linspace(x0, x1, nx + 1)]

    nodes: Dict[int, Tuple[float, float, float]] = {}
    stations: List[StationMesh] = []
    next_node = 1

    for x in xs:
        frame = i_section_frame(field, x)
        cells = _section_cells(frame, mesh_cfg)

        local_coords = sorted(
            {corner for cell in cells for corner in cell.corners},
            key=lambda p: (p[1], p[0]),
        )

        node_map: Dict[Tuple[float, float], int] = {}
        for y, z in local_coords:
            tag = next_node
            next_node += 1
            node_map[(y, z)] = tag
            nodes[tag] = (x, y, z)

        y_min = min(frame.bottom.y0, frame.top.y0)
        y_max = max(frame.bottom.y1, frame.top.y1)
        z_min = frame.bottom.z0
        z_max = frame.top.z1

        plus = _find_corner_node(
            node_map, y=y_min, z=z_max, label="positive"
        )
        minus = _find_corner_node(
            node_map, y=y_max, z=z_min, label="negative"
        )

        stations.append(
            StationMesh(
                x=x,
                nodes=node_map,
                cells=cells,
                plus_load_node=plus,
                minus_load_node=minus,
            )
        )

    # All stations must retain the same topology.
    reference_roles = [c.role for c in stations[0].cells]
    for station in stations[1:]:
        roles = [c.role for c in station.cells]
        if roles != reference_roles:
            raise ValueError("section mesh topology changes along the member")

    bricks: List[Brick] = []
    next_element = 1

    for ix in range(nx):
        s0 = stations[ix]
        s1 = stations[ix + 1]
        x_mid = 0.5 * (s0.x + s1.x)
        mid_frame = i_section_frame(field, x_mid)

        for c0, c1 in zip(s0.cells, s1.cells):
            if c0.role != c1.role:
                raise RuntimeError("internal cell topology mismatch")

            # Cell corner order in each transverse section:
            # 0=(y0,z0), 1=(y1,z0), 2=(y1,z1), 3=(y0,z1)
            a0, b0, c0k, d0 = c0.corners
            a1, b1, c1k, d1 = c1.corners

            # Standard 8-node brick orientation:
            # local axis 1 -> global longitudinal x
            # local axis 2 -> global transverse y
            # local axis 3 -> global transverse z
            node_tags = (
                s0.nodes[a0],
                s1.nodes[a1],
                s1.nodes[b1],
                s0.nodes[b0],
                s0.nodes[d0],
                s1.nodes[d1],
                s1.nodes[c1k],
                s0.nodes[c0k],
            )

            domain = mid_frame.domain_for_role(c0.role)
            bricks.append(
                Brick(
                    tag=next_element,
                    node_tags=node_tags,
                    role=c0.role,
                    domain_id=domain.domain_id,
                    material=domain.material,
                )
            )
            next_element += 1

    end0_nodes = list(stations[0].nodes.values())
    end1_nodes = list(stations[-1].nodes.values())

    # One axial DOF is fixed only to remove the rigid translation.
    # Choose the end node nearest the transverse center of the first section.
    first_frame = i_section_frame(field, x0)
    y_center = 0.5 * (first_frame.web.y0 + first_frame.web.y1)
    z_center = 0.5 * (first_frame.web.z0 + first_frame.web.z1)
    axial_anchor_node = min(
        end0_nodes,
        key=lambda tag: (
            (nodes[tag][1] - y_center) ** 2
            + (nodes[tag][2] - z_center) ** 2
        ),
    )

    return FEMMesh(
        nodes=nodes,
        bricks=bricks,
        stations=stations,
        x0=x0,
        x1=x1,
        end0_nodes=end0_nodes,
        end1_nodes=end1_nodes,
        axial_anchor_node=axial_anchor_node,
    )


# ---------------------------------------------------------------------------
# Loads
# ---------------------------------------------------------------------------

def _consistent_line_segment_loads(
    xa: float,
    xb: float,
    *,
    amplitude: float,
    x0: float,
    x1: float,
    gauss_order: int,
) -> Tuple[float, float]:
    """
    Equivalent nodal forces for q(x)=amplitude*sin(pi*(x-x0)/L)
    on one two-node longitudinal line segment.
    """
    points, weights = np.polynomial.legendre.leggauss(int(gauss_order))
    jac = 0.5 * (xb - xa)
    mid = 0.5 * (xa + xb)
    length = x1 - x0

    fa = 0.0
    fb = 0.0

    for r, w in zip(points, weights):
        x = mid + jac * float(r)
        n0 = 0.5 * (1.0 - float(r))
        n1 = 0.5 * (1.0 + float(r))
        q = float(amplitude) * math.sin(math.pi * (x - x0) / length)
        fa += float(w) * jac * n0 * q
        fb += float(w) * jac * n1 * q

    return fa, fb


def torsion_line_pair_nodal_loads(
    mesh: FEMMesh,
    problem_cfg: dict,
    mesh_cfg: dict,
) -> Dict[int, np.ndarray]:
    """
    Build the current Carrera-Giunta torsional line pair.

    The load geometry is obtained from the current CSF mesh:
      positive line -> (y_min, z_max)
      negative line -> (y_max, z_min)

    The forces act in global transverse Z and vary as a half sine wave.
    """
    amplitude = float(problem_cfg.get("amplitude", 1.0))
    gauss_order = int(mesh_cfg.get("load_gauss_order", 6))

    loads: Dict[int, np.ndarray] = {}

    def add(node: int, fz: float) -> None:
        loads.setdefault(node, np.zeros(3, dtype=float))
        loads[node][2] += float(fz)

    for s0, s1 in zip(mesh.stations[:-1], mesh.stations[1:]):
        f0, f1 = _consistent_line_segment_loads(
            s0.x,
            s1.x,
            amplitude=amplitude,
            x0=mesh.x0,
            x1=mesh.x1,
            gauss_order=gauss_order,
        )

        add(s0.plus_load_node, +f0)
        add(s1.plus_load_node, +f1)

        add(s0.minus_load_node, -f0)
        add(s1.minus_load_node, -f1)

    return loads


def _quad_shape(r: float, s: float) -> Tuple[float, float, float, float]:
    """Bilinear shape functions in node order 00,10,11,01."""
    return (
        0.25 * (1.0 - r) * (1.0 - s),
        0.25 * (1.0 + r) * (1.0 - s),
        0.25 * (1.0 + r) * (1.0 + s),
        0.25 * (1.0 - r) * (1.0 + s),
    )


def _quad_shape_derivatives(
    r: float,
    s: float,
) -> Tuple[Tuple[float, float, float, float], Tuple[float, float, float, float]]:
    """Derivatives dN/dr and dN/ds in node order 00,10,11,01."""
    dndr = (
        -0.25 * (1.0 - s),
        +0.25 * (1.0 - s),
        +0.25 * (1.0 + s),
        -0.25 * (1.0 + s),
    )
    dnds = (
        -0.25 * (1.0 - r),
        -0.25 * (1.0 + r),
        +0.25 * (1.0 + r),
        +0.25 * (1.0 - r),
    )
    return dndr, dnds


def bending_bottom_surface_nodal_loads(
    mesh: FEMMesh,
    problem_cfg: dict,
    mesh_cfg: dict,
) -> Dict[int, np.ndarray]:
    """
    Consistent nodal forces for the Carrera-Giunta bending surface loading.

    The loaded surface is discovered from the CSF-driven mesh: it is the
    outer face of the lower flange.  The traction acts in global -Z, which is
    paper +x under the adopted coordinate mapping, and varies longitudinally
    as sin(pi*(x-x0)/L).

    ``amplitude`` is a surface traction (force / area).  No section dimension
    or benchmark displacement value is embedded here.
    """
    amplitude = float(problem_cfg.get("amplitude", 1.0))
    gauss_order = int(mesh_cfg.get("load_gauss_order", 6))
    points, weights = np.polynomial.legendre.leggauss(gauss_order)
    length = mesh.x1 - mesh.x0

    loads: Dict[int, np.ndarray] = {}

    def add(node: int, fz: float) -> None:
        loads.setdefault(node, np.zeros(3, dtype=float))
        loads[node][2] += float(fz)

    for s0, s1 in zip(mesh.stations[:-1], mesh.stations[1:]):
        for c0, c1 in zip(s0.cells, s1.cells):
            if c0.role != "bottom":
                continue
            if c1.role != "bottom":
                raise RuntimeError("bottom-surface topology mismatch")

            # Only the outer lower edge of each bottom-flange cell is loaded.
            z0_values = [corner[1] for corner in c0.corners]
            z1_values = [corner[1] for corner in c1.corners]
            station0_min_z = min(p[1] for p in s0.nodes)
            station1_min_z = min(p[1] for p in s1.nodes)
            tol = 1.0e-9 * max(
                1.0,
                abs(station0_min_z),
                abs(station1_min_z),
            )
            if abs(min(z0_values) - station0_min_z) > tol:
                continue
            if abs(min(z1_values) - station1_min_z) > tol:
                continue

            k00 = c0.corners[0]
            k01 = c0.corners[1]
            k10 = c1.corners[0]
            k11 = c1.corners[1]

            tags = (
                s0.nodes[k00],
                s1.nodes[k10],
                s1.nodes[k11],
                s0.nodes[k01],
            )
            xyz = [np.asarray(mesh.nodes[tag], dtype=float) for tag in tags]

            local = np.zeros(4, dtype=float)

            for r, wr in zip(points, weights):
                for s, ws in zip(points, weights):
                    r = float(r)
                    s = float(s)
                    N = _quad_shape(r, s)
                    dndr, dnds = _quad_shape_derivatives(r, s)

                    position = sum(N[i] * xyz[i] for i in range(4))
                    tangent_r = sum(dndr[i] * xyz[i] for i in range(4))
                    tangent_s = sum(dnds[i] * xyz[i] for i in range(4))
                    jacobian = float(np.linalg.norm(np.cross(tangent_r, tangent_s)))

                    q = amplitude * math.sin(
                        math.pi * (float(position[0]) - mesh.x0) / length
                    )

                    for i in range(4):
                        local[i] += float(wr) * float(ws) * N[i] * q * jacobian

            for tag, force in zip(tags, local):
                add(tag, -force)

    if not loads:
        raise RuntimeError("no lower-flange surface patches were found for bending load")

    return loads


# ---------------------------------------------------------------------------
# OpenSees model and solve
# ---------------------------------------------------------------------------

def _material_key(material: MaterialState) -> Tuple[float, float]:
    return (round(material.E, 12), round(material.G, 12))


def solve_opensees(
    mesh: FEMMesh,
    loads: Dict[int, np.ndarray],
    analysis_cfg: dict,
):
    """
    Build and solve the 3D OpenSees model.

    OpenSees is imported here so that --mesh-only can be used without it.
    """
    try:
        import openseespy.opensees as ops
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "OpenSeesPy is not installed. Install it with:\n"
            "  python -m pip install openseespy"
        ) from exc

    ops.wipe()
    ops.model("Basic", "-ndm", 3, "-ndf", 3)

    for tag, (x, y, z) in mesh.nodes.items():
        ops.node(tag, x, y, z)

    material_tags: Dict[Tuple[float, float], int] = {}
    next_material = 1

    for brick in mesh.bricks:
        key = _material_key(brick.material)
        if key not in material_tags:
            tag = next_material
            next_material += 1
            material_tags[key] = tag
            ops.nDMaterial(
                "ElasticIsotropic",
                tag,
                brick.material.E,
                brick.material.nu,
            )

    for brick in mesh.bricks:
        mat_tag = material_tags[_material_key(brick.material)]
        ops.element("stdBrick", brick.tag, *brick.node_tags, mat_tag)

    # Navier-compatible end supports:
    # transverse Y and Z fixed on both end faces; axial X remains free.
    # One node on the first end also fixes X only to remove rigid translation.
    for tag in mesh.end0_nodes:
        if tag == mesh.axial_anchor_node:
            ops.fix(tag, 1, 1, 1)
        else:
            ops.fix(tag, 0, 1, 1)

    for tag in mesh.end1_nodes:
        ops.fix(tag, 0, 1, 1)

    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)

    for node_tag, force in loads.items():
        ops.load(node_tag, float(force[0]), float(force[1]), float(force[2]))

    system_name = str(analysis_cfg.get("system", "UmfPack"))
    ops.constraints("Plain")
    ops.numberer("RCM")
    ops.system(system_name)
    ops.integrator("LoadControl", 1.0)
    ops.algorithm("Linear")
    ops.analysis("Static")

    status = int(ops.analyze(1))
    if status != 0:
        raise RuntimeError(f"OpenSees analysis failed with code {status}")

    displacements = {
        tag: np.asarray(ops.nodeDisp(tag), dtype=float)
        for tag in mesh.nodes
    }

    # Reactions are needed only at constrained nodes.
    ops.reactions()
    constrained_nodes = set(mesh.end0_nodes) | set(mesh.end1_nodes)
    reactions = {
        tag: np.asarray(ops.nodeReaction(tag), dtype=float)
        for tag in constrained_nodes
    }

    return {
        "ops": ops,
        "displacements": displacements,
        "reactions": reactions,
        "material_count": len(material_tags),
    }



# ---------------------------------------------------------------------------
# Paper-style reporting
# ---------------------------------------------------------------------------

def _carrera_table9_reference_data(
    field,
    mesh: FEMMesh,
    problem_cfg: dict,
):
    """
    Return the current-model normalization data used by the Table-9 report.

    No published displacement/result value enters this calculation.
    """
    frame = i_section_frame(field, mesh.x0)
    a = frame.web.height

    E_values = [
        frame.bottom.material.E,
        frame.web.material.E,
        frame.top.material.E,
    ]
    tol_E = 1.0e-9 * max(1.0, *(abs(v) for v in E_values))
    if max(E_values) - min(E_values) > tol_E:
        raise ValueError(
            "Table-9-style normalization requires one reference Young's "
            "modulus at the start section. The FEM solve itself remains valid."
        )
    E_ref = sum(E_values) / len(E_values)

    L = mesh.x1 - mesh.x0
    pressure_amplitude = float(problem_cfg.get("amplitude", 1.0))
    if pressure_amplitude == 0.0:
        raise ValueError(
            "Table-9-style normalization requires non-zero load amplitude"
        )

    factor = (
        (math.pi ** 4) / 12.0
        * (a ** 3) / (L ** 4)
        * E_ref / pressure_amplitude
    )

    l_over_a = L / a
    if math.isclose(l_over_a, 10.0, rel_tol=1.0e-9, abs_tol=1.0e-9):
        scales = (10.0, 1.0e3, 1.0e2)
        value_fields = ("10_ux_star", "1e3_abs_uy_star", "1e2_uz_star")
    elif math.isclose(l_over_a, 100.0, rel_tol=1.0e-9, abs_tol=1.0e-9):
        scales = (10.0, 1.0e5, 1.0e3)
        value_fields = ("10_ux_star", "1e5_abs_uy_star", "1e3_uz_star")
    else:
        raise ValueError(
            f"Table-9-style display is defined here for L/a=10 or 100; got {l_over_a:g}"
        )

    return factor, l_over_a, scales, value_fields


def carrera_table9_style_row(
    field,
    mesh: FEMMesh,
    problem_cfg: dict,
    maxima_rows: List[dict],
    *,
    scope: str = "global",
    section_x_over_L: float | None = None,
    section_x: float | None = None,
) -> dict:
    """
    Convert one set of bending displacement maxima to the Table-9 convention.

    The row stores both each scaled maximum and the coordinates where it occurs.
    """
    factor, l_over_a, scales, value_fields = _carrera_table9_reference_data(
        field, mesh, problem_cfg
    )

    rows = {str(row["name"]): row for row in maxima_rows}
    for required in ("ux", "uy", "uz"):
        if required not in rows:
            raise ValueError(
                f"Table-9-style report requires the '{required}' observable"
            )

    ux = rows["ux"]
    uy = rows["uy"]
    uz = rows["uz"]

    return {
        "model": "FEM 3D",
        "scope": scope,
        "section_x_over_L": section_x_over_L,
        "section_x": section_x,
        "l_over_a": l_over_a,
        "value_fields": value_fields,
        value_fields[0]: scales[0] * factor * float(ux["value"]),
        "ux_x": float(ux["x"]),
        "ux_y": float(ux["y"]),
        "ux_z": float(ux["z"]),
        value_fields[1]: scales[1] * factor * abs(float(uy["value"])),
        "uy_x": float(uy["x"]),
        "uy_y": float(uy["y"]),
        "uy_z": float(uy["z"]),
        value_fields[2]: scales[2] * factor * float(uz["value"]),
        "uz_x": float(uz["x"]),
        "uz_y": float(uz["y"]),
        "uz_z": float(uz["z"]),
    }


def carrera_table9_style_rows(
    field,
    mesh: FEMMesh,
    problem_cfg: dict,
    global_maxima_rows: List[dict],
    displacements: Dict[int, np.ndarray],
    requested_maxima: list,
    sections_x_over_L: Iterable[float],
) -> List[dict]:
    """
    Build one Table-9-style CSV dataset.

    Row 1 is the global maximum row used for direct paper comparison.
    Additional rows contain the same three observables evaluated independently
    on the requested longitudinal sections.
    """
    report_rows = [
        carrera_table9_style_row(
            field,
            mesh,
            problem_cfg,
            global_maxima_rows,
            scope="global",
        )
    ]

    seen = set()
    for raw_ratio in sections_x_over_L:
        ratio = float(raw_ratio)
        key = round(ratio, 12)
        if key in seen:
            continue
        seen.add(key)

        station = _station_at_x_over_L(mesh, ratio)
        section_maxima = displacement_maxima(
            mesh,
            displacements,
            requested_maxima,
            node_tags=station.nodes.values(),
        )

        report_rows.append(
            carrera_table9_style_row(
                field,
                mesh,
                problem_cfg,
                section_maxima,
                scope="section",
                section_x_over_L=ratio,
                section_x=station.x,
            )
        )

    return report_rows


def write_table9_style(path: str | Path, rows: List[dict]) -> None:
    """
    Write the global Table-9 row and requested section rows to one CSV file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    value_fields = rows[0]["value_fields"]
    fields = [
        "model",
        "scope",
        "section_x_over_L",
        "section_x",
        value_fields[0],
        "ux_x",
        "ux_y",
        "ux_z",
        value_fields[1],
        "uy_x",
        "uy_y",
        "uy_z",
        value_fields[2],
        "uz_x",
        "uz_y",
        "uz_z",
    ]

    def fmt(value):
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return f"{float(value):.6f}"

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({field: fmt(row.get(field)) for field in fields})


def print_table9_style(rows: List[dict]) -> None:
    """Print the global row and a compact view of requested section rows."""
    global_row = rows[0]
    f0, f1, f2 = global_row["value_fields"]

    print()
    print("Table-9-style result")
    print("====================")
    print(f"scope       x/L {f0:>14s} {f1:>18s} {f2:>14s}")
    print(
        f"{'global':<10s} {'-':>5s} "
        f"{global_row[f0]:>14.6f} "
        f"{global_row[f1]:>18.6f} "
        f"{global_row[f2]:>14.6f}"
    )

    for row in rows[1:]:
        print(
            f"{'section':<10s} {row['section_x_over_L']:>5.2f} "
            f"{row[f0]:>14.6f} "
            f"{row[f1]:>18.6f} "
            f"{row[f2]:>14.6f}"
        )


def _carrera_table10_reference_factor(
    field,
    mesh: FEMMesh,
    problem_cfg: dict,
) -> float:
    """
    Return the Table-10 normalization factor from the current CSF model.

    No published displacement/result value enters this calculation.
    """
    frame = i_section_frame(field, mesh.x0)

    a = frame.web.height
    b_top = frame.top.width
    b_bottom = frame.bottom.width

    tol_b = 1.0e-9 * max(1.0, abs(b_top), abs(b_bottom))
    if abs(b_top - b_bottom) > tol_b:
        raise ValueError(
            "Table-10-style reporting requires equal top and bottom flange "
            "widths at the reference section."
        )
    b = 0.5 * (b_top + b_bottom)

    E_values = [
        frame.bottom.material.E,
        frame.web.material.E,
        frame.top.material.E,
    ]
    tol_E = 1.0e-9 * max(1.0, *(abs(v) for v in E_values))
    if max(E_values) - min(E_values) > tol_E:
        raise ValueError(
            "Table-10-style normalization requires one reference Young's "
            "modulus at the start section. The FEM solve itself remains valid."
        )
    E_ref = sum(E_values) / len(E_values)

    L = mesh.x1 - mesh.x0
    load_amplitude = float(problem_cfg.get("amplitude", 1.0))
    if load_amplitude == 0.0:
        raise ValueError(
            "Table-10-style normalization requires non-zero load amplitude"
        )

    return (
        (math.pi ** 4) / 12.0
        * (a ** 3) * b / (L ** 4)
        * E_ref / load_amplitude
    )


def _maxima_by_name(maxima_rows: List[dict]) -> Dict[str, dict]:
    rows = {str(row["name"]): row for row in maxima_rows}
    for required in ("ux", "uy", "uz"):
        if required not in rows:
            raise ValueError(
                f"Table-10-style report requires the '{required}' observable"
            )
    return rows


def carrera_table10_style_row(
    field,
    mesh: FEMMesh,
    problem_cfg: dict,
    maxima_rows: List[dict],
    *,
    scope: str = "global",
    section_x_over_L: float | None = None,
    section_x: float | None = None,
) -> dict:
    """
    Convert one set of displacement maxima to the Table-10 display convention.

    The row also records where each maximum occurs.  For a section row,
    section_x_over_L and section_x identify the requested longitudinal section.
    """
    factor = _carrera_table10_reference_factor(field, mesh, problem_cfg)
    rows = _maxima_by_name(maxima_rows)

    ux = rows["ux"]
    uy = rows["uy"]
    uz = rows["uz"]

    return {
        "model": "FEM 3D",
        "scope": scope,
        "section_x_over_L": section_x_over_L,
        "section_x": section_x,
        "10_abs_ux_star": 10.0 * factor * abs(float(ux["value"])),
        "ux_x": float(ux["x"]),
        "ux_y": float(ux["y"]),
        "ux_z": float(ux["z"]),
        "10_abs_uy_star": 10.0 * factor * abs(float(uy["value"])),
        "uy_x": float(uy["x"]),
        "uy_y": float(uy["y"]),
        "uy_z": float(uy["z"]),
        "1e2_uz_star": 100.0 * factor * float(uz["value"]),
        "uz_x": float(uz["x"]),
        "uz_y": float(uz["y"]),
        "uz_z": float(uz["z"]),
    }


def _station_at_x_over_L(mesh: FEMMesh, x_over_L: float) -> StationMesh:
    """
    Return the FEM station exactly corresponding to one normalized x position.

    No longitudinal interpolation is hidden in the report.  A requested
    section must coincide with an existing FEM mesh station.
    """
    ratio = float(x_over_L)
    if ratio < 0.0 or ratio > 1.0:
        raise ValueError(
            f"report.sections_x_over_L value must be in [0,1], got {ratio}"
        )

    target_x = mesh.x0 + ratio * (mesh.x1 - mesh.x0)
    station = min(mesh.stations, key=lambda s: abs(s.x - target_x))

    tol = 1.0e-10 * max(1.0, abs(mesh.x0), abs(mesh.x1), abs(mesh.x1 - mesh.x0))
    if abs(station.x - target_x) > tol:
        raise ValueError(
            "requested report section does not coincide with a FEM longitudinal "
            f"station: x/L={ratio:g}, target x={target_x:g}, nearest x={station.x:g}. "
            "Choose section ratios compatible with mesh.longitudinal_divisions."
        )

    return station


def carrera_table10_style_rows(
    field,
    mesh: FEMMesh,
    problem_cfg: dict,
    global_maxima_rows: List[dict],
    displacements: Dict[int, np.ndarray],
    requested_maxima: list,
    sections_x_over_L: Iterable[float],
) -> List[dict]:
    """
    Build one Table-10-style CSV dataset.

    Row 1 is the global maximum row used for direct paper comparison.
    Additional rows contain the same three observables evaluated independently
    on the requested longitudinal sections.
    """
    report_rows = [
        carrera_table10_style_row(
            field,
            mesh,
            problem_cfg,
            global_maxima_rows,
            scope="global",
        )
    ]

    seen = set()
    for raw_ratio in sections_x_over_L:
        ratio = float(raw_ratio)
        key = round(ratio, 12)
        if key in seen:
            continue
        seen.add(key)

        station = _station_at_x_over_L(mesh, ratio)
        station_node_tags = list(station.nodes.values())
        section_maxima = displacement_maxima(
            mesh,
            displacements,
            requested_maxima,
            node_tags=station_node_tags,
        )

        report_rows.append(
            carrera_table10_style_row(
                field,
                mesh,
                problem_cfg,
                section_maxima,
                scope="section",
                section_x_over_L=ratio,
                section_x=station.x,
            )
        )

    return report_rows


def write_table10_style(path: str | Path, rows: List[dict]) -> None:
    """
    Write the global Table-10 row and requested section rows to one CSV file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "model",
        "scope",
        "section_x_over_L",
        "section_x",
        "10_abs_ux_star",
        "ux_x",
        "ux_y",
        "ux_z",
        "10_abs_uy_star",
        "uy_x",
        "uy_y",
        "uy_z",
        "1e2_uz_star",
        "uz_x",
        "uz_y",
        "uz_z",
    ]

    def fmt(value):
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return f"{float(value):.6f}"

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({field: fmt(row.get(field)) for field in fields})


def print_table10_style(rows: List[dict]) -> None:
    """Print the global row and a compact view of requested section rows."""
    global_row = rows[0]

    print()
    print("Table-10-style result")
    print("=====================")
    print("scope       x/L      10*|ux*|      10*|uy*|      1e2*uz*")
    print(
        f"{'global':<10s} {'-':>5s} "
        f"{global_row['10_abs_ux_star']:>12.6f} "
        f"{global_row['10_abs_uy_star']:>13.6f} "
        f"{global_row['1e2_uz_star']:>12.6f}"
    )

    for row in rows[1:]:
        print(
            f"{'section':<10s} {row['section_x_over_L']:>5.2f} "
            f"{row['10_abs_ux_star']:>12.6f} "
            f"{row['10_abs_uy_star']:>13.6f} "
            f"{row['1e2_uz_star']:>12.6f}"
        )


# ---------------------------------------------------------------------------
# Human-readable outputs
# ---------------------------------------------------------------------------

def displacement_maxima(
    mesh: FEMMesh,
    displacements: Dict[int, np.ndarray],
    requested: list,
    *,
    node_tags: Iterable[int] | None = None,
) -> List[dict]:
    component_index = {"x": 0, "y": 1, "z": 2}
    rows: List[dict] = []

    for item in requested:
        name = str(item["name"])
        source = str(item["source_component"]).lower()
        sign = float(item.get("sign", 1.0))
        operation = str(item["operation"]).lower()

        if source not in component_index:
            raise ValueError(f"unsupported source_component: {source}")

        i = component_index[source]

        best = None
        tags = displacements.keys() if node_tags is None else node_tags
        for tag in tags:
            disp = displacements[int(tag)]
            mapped = sign * float(disp[i])

            if operation == "max_abs":
                score = abs(mapped)
                value = abs(mapped)
            elif operation == "max":
                score = mapped
                value = mapped
            elif operation == "min":
                score = -mapped
                value = mapped
            else:
                raise ValueError(f"unsupported maxima operation: {operation}")

            if best is None or score > best[0]:
                x, y, z = mesh.nodes[tag]
                best = (score, value, tag, x, y, z)

        assert best is not None
        _, value, tag, x, y, z = best
        rows.append(
            {
                "name": name,
                "value": value,
                "node": tag,
                "x": x,
                "y": y,
                "z": z,
            }
        )

    return rows


def equilibrium_diagnostics(
    mesh: FEMMesh,
    loads: Dict[int, np.ndarray],
    reactions: Dict[int, np.ndarray],
) -> dict:
    applied_force = np.zeros(3)
    reaction_force = np.zeros(3)
    applied_moment = np.zeros(3)
    reaction_moment = np.zeros(3)

    applied_force_scale = 0.0
    applied_moment_scale = 0.0

    for tag, force in loads.items():
        r = np.asarray(mesh.nodes[tag], dtype=float)
        f = np.asarray(force, dtype=float)
        applied_force += f
        m = np.cross(r, f)
        applied_moment += m
        applied_force_scale += float(np.linalg.norm(f))
        applied_moment_scale += float(np.linalg.norm(m))

    for tag, force in reactions.items():
        r = np.asarray(mesh.nodes[tag], dtype=float)
        f = np.asarray(force, dtype=float)
        reaction_force += f
        reaction_moment += np.cross(r, f)

    force_residual = applied_force + reaction_force
    moment_residual = applied_moment + reaction_moment

    return {
        "force_residual": float(
            np.linalg.norm(force_residual) / max(applied_force_scale, 1.0)
        ),
        "moment_residual": float(
            np.linalg.norm(moment_residual) / max(applied_moment_scale, 1.0)
        ),
    }


def write_mesh_summary(path: str | Path, mesh: FEMMesh) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    material_keys = {_material_key(b.material) for b in mesh.bricks}

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["quantity", "value"])
        w.writerow(["nodes", len(mesh.nodes)])
        w.writerow(["brick_elements", len(mesh.bricks)])
        w.writerow(["material_states", len(material_keys)])
        w.writerow(["x_start", mesh.x0])
        w.writerow(["x_end", mesh.x1])
        w.writerow(["axial_anchor_node", mesh.axial_anchor_node])


def write_summary(path: str | Path, rows: List[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["name", "value", "node", "x", "y", "z"],
        )
        w.writeheader()
        w.writerows(rows)


def write_diagnostics(path: str | Path, diagnostics: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["quantity", "value"])
        for key in ("force_residual", "moment_residual"):
            w.writerow([key, diagnostics[key]])


def print_mesh_summary(mesh: FEMMesh) -> None:
    materials = {_material_key(b.material) for b in mesh.bricks}

    print("CSF-FEM3D mesh")
    print("================")
    print(f"x range          : {mesh.x0:g} -> {mesh.x1:g}")
    print(f"nodes            : {len(mesh.nodes)}")
    print(f"stdBrick elements: {len(mesh.bricks)}")
    print(f"material states  : {len(materials)}")
    print(f"axial anchor node: {mesh.axial_anchor_node}")


def print_result_summary(rows: List[dict], diagnostics: dict) -> None:
    print()
    print("Main results")
    print("============")
    for row in rows:
        print(
            f"{row['name']:>8s} : {row['value']:.12e} "
            f"at ({row['x']:.6g}, {row['y']:.6g}, {row['z']:.6g})"
        )

    print()
    print("Numerical checks")
    print("================")
    print(f"force residual : {diagnostics['force_residual']:.3e}")
    print(f"moment residual: {diagnostics['moment_residual']:.3e}")
