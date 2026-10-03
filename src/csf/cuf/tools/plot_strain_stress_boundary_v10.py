# Version: CSF-CUF plot_strain_stress_boundary v10 - 2026-10-03
# Changelog v10: FEM3D loader now accepts both the standardized
# fem3d_h8_displacement v1 schema and the legacy I-Shape raw H8 NPZ schema
# (nodes/elements/displacement/amplitude/x0/x1). No conversion or resampling.
# Changelog v9: optional inward-bisector sampling at polygon vertices; when
# --inward-offset is supplied, every plot is replicated at points shifted
# inside each polygon by the requested physical distance. Legacy output is unchanged.
# Changelog v8: optional native H8 FEM3D displacement/strain overlays; explicit
# CSF-law stress recovery; polygon-side selection; per-element exports, no averaging.
# Native model values only: no assumed unit system and no automatic scaling.
"""Recover and plot displacement, strain and stress along CSF polygon vertices.

Optional FEM3D comparison:
    --fem3d checkpoint.fem.npz overlays native H8 displacement and strain.
    --fem-stress-from-csf additionally recovers stress using the CSF material law.
    FEM and CUF must share physical axes, units, geometry and material partition.
    FEM mesh must conform to CSF polygon boundaries. No unit conversion, nodal
    strain averaging or nearest-point extrapolation is performed. Coincident
    polygon vertices are evaluated on their own polygon side.

Inputs:
    CUF output tree containing compiled displacement checkpoints (*.cuf.npz), or one explicit checkpoint
    original CSF YAML

For each sampled longitudinal station, the physical coordinates of every selected
CSF polygon vertex are obtained from the CSF geometry. At each moving boundary
point (x, y(x), z(x)):

    u       = compiled_field(x, y, z)
    epsilon = compiled_field.strain(x, y, z)
    C       = bridge.constitutive_provider.matrix(...)
    sigma   = C @ epsilon

The constitutive matrix therefore comes directly from the CUF-core provider.
No constitutive law is duplicated in this tool.

By default every polygon vertex identity is retained (``--vertices all``),
including coincident vertices belonging to different polygons. This is required
to recover material-side stresses unambiguously at polygon interfaces.
``--vertices unique`` remains available when a single representative value is desired.

Optional inward sampling:
    --inward-offset D keeps all original boundary plots and additionally repeats
    every plot at points shifted by distance D along the internal angle bisector
    of the corresponding polygon vertex. Collinear boundary vertices use the same
    rule through the coincident inward edge normals, which gives the inward normal.
    The distance is expressed in the native transverse model units.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np



CURVES = [
    ("ux", 0, "displacement", r"$u_x$", r"Displacement, $u_x$"),
    ("uy", 1, "displacement", r"$u_y$", r"Displacement, $u_y$"),
    ("uz", 2, "displacement", r"$u_z$", r"Displacement, $u_z$"),
    ("epsilon_xx", 0, "strain", r"$\varepsilon_{xx}$", r"Strain, $\varepsilon_{xx}$"),
    ("epsilon_yy", 1, "strain", r"$\varepsilon_{yy}$", r"Strain, $\varepsilon_{yy}$"),
    ("epsilon_zz", 2, "strain", r"$\varepsilon_{zz}$", r"Strain, $\varepsilon_{zz}$"),
    ("gamma_yz", 3, "strain", r"$\gamma_{yz}$", r"Shear strain, $\gamma_{yz}$"),
    ("gamma_xz", 4, "strain", r"$\gamma_{xz}$", r"Shear strain, $\gamma_{xz}$"),
    ("gamma_xy", 5, "strain", r"$\gamma_{xy}$", r"Shear strain, $\gamma_{xy}$"),
    ("sigma_xx", 0, "stress", r"$\sigma_{xx}$", r"Stress, $\sigma_{xx}$"),
    ("sigma_yy", 1, "stress", r"$\sigma_{yy}$", r"Stress, $\sigma_{yy}$"),
    ("sigma_zz", 2, "stress", r"$\sigma_{zz}$", r"Stress, $\sigma_{zz}$"),
    ("tau_yz", 3, "stress", r"$\tau_{yz}$", r"Stress, $\tau_{yz}$"),
    ("tau_xz", 4, "stress", r"$\tau_{xz}$", r"Stress, $\tau_{xz}$"),
    ("tau_xy", 5, "stress", r"$\tau_{xy}$", r"Stress, $\tau_{xy}$"),
]


def unique_vertices(section):
    """Return one CSF identity for each distinct physical vertex."""
    selectors = []
    aliases = {}
    for pi, polygon in enumerate(section.polygons):
        for vi, vertex in enumerate(polygon.vertices):
            identity = (pi, vi)
            for previous in selectors:
                pp, pv = previous
                other = section.polygons[pp].vertices[pv]
                if np.allclose(
                    [vertex.x, vertex.y],
                    [other.x, other.y],
                    rtol=0.0,
                    atol=1.0e-8,
                ):
                    aliases[previous].append(identity)
                    break
            else:
                selectors.append(identity)
                aliases[identity] = [identity]
    return selectors, aliases




def inward_bisector_point(polygon, vertex_index: int, distance: float) -> tuple[float, float]:
    """Move one polygon vertex inward by ``distance`` along its internal bisector.

    The direction is built from the inward unit normals of the two incident
    polygon edges. This also handles a collinear 180-degree boundary vertex:
    the two inward normals coincide and their sum is simply the inward normal.
    """
    distance = float(distance)
    if not math.isfinite(distance) or distance <= 0.0:
        raise ValueError("inward offset must be a positive finite distance")

    coords = np.asarray([(float(v.x), float(v.y)) for v in polygon.vertices], dtype=float)
    count = len(coords)
    if count < 3:
        raise ValueError("polygon must contain at least three vertices")
    vi = int(vertex_index)
    if not 0 <= vi < count:
        raise IndexError(f"vertex index {vi} outside polygon with {count} vertices")

    previous = coords[(vi - 1) % count]
    current = coords[vi]
    following = coords[(vi + 1) % count]
    incoming = current - previous
    outgoing = following - current
    incoming_norm = float(np.linalg.norm(incoming))
    outgoing_norm = float(np.linalg.norm(outgoing))
    if incoming_norm <= 0.0 or outgoing_norm <= 0.0:
        raise ValueError(f"degenerate polygon edge at vertex {vi}")

    x = coords[:, 0]
    y = coords[:, 1]
    signed_area2 = float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
    if abs(signed_area2) <= 64.0 * np.finfo(float).eps * max(1.0, float(np.max(np.abs(coords))) ** 2):
        raise ValueError("polygon orientation is undefined because its signed area is zero")

    def left_normal(edge):
        return np.asarray((-edge[1], edge[0]), dtype=float)

    if signed_area2 > 0.0:  # counter-clockwise polygon: interior is to the left
        normal_in = left_normal(incoming) / incoming_norm
        normal_out = left_normal(outgoing) / outgoing_norm
    else:  # clockwise polygon: interior is to the right
        normal_in = -left_normal(incoming) / incoming_norm
        normal_out = -left_normal(outgoing) / outgoing_norm

    direction = normal_in + normal_out
    direction_norm = float(np.linalg.norm(direction))
    if direction_norm <= 128.0 * np.finfo(float).eps:
        raise ValueError(
            f"internal bisector is undefined at polygon vertex {vi}; "
            "incident inward normals cancel"
        )
    direction /= direction_norm
    candidate = current + distance * direction

    from matplotlib.path import Path as PolygonPath
    path = PolygonPath(np.vstack((coords, coords[0])), closed=True)
    if not path.contains_point(candidate):
        raise ValueError(
            f"inward offset {distance:g} leaves polygon at vertex {vi}: "
            f"candidate=({candidate[0]:g}, {candidate[1]:g})"
        )
    return float(candidate[0]), float(candidate[1])


def offset_tag(value: float) -> str:
    """Filesystem-safe compact representation of one positive offset."""
    return f"{float(value):g}".replace("-", "m").replace("+", "").replace(".", "p")


def sample_geometry(csf_field, points: int, mode: str, inward_offset: float | None = None):
    """Follow homologous CSF polygon vertices, optionally shifted inside each polygon."""
    if points < 2:
        raise ValueError("--points must be >= 2")

    start = float(csf_field.s0.z)
    end = float(csf_field.s1.z)
    if end <= start:
        raise ValueError("CSF longitudinal end must exceed its start")

    x_values = np.linspace(start, end, int(points))
    sections = [csf_field.section(float(x)) for x in x_values]
    first = sections[0]

    if mode == "unique":
        selectors, aliases = unique_vertices(first)
        if not selectors:
            raise ValueError("No section vertices found")
    else:
        selectors = [
            (pi, vi)
            for pi, polygon in enumerate(first.polygons)
            for vi in range(len(polygon.vertices))
        ]
        aliases = {identity: [identity] for identity in selectors}

    point_ids = tuple(
        f"polygon_{pi + 1}_vertex_{vi}"
        for pi, vi in selectors
    )

    rows = []
    for x, section in zip(x_values, sections):
        if len(section.polygons) != len(first.polygons) or any(
            len(p.vertices) != len(q.vertices)
            for p, q in zip(section.polygons, first.polygons)
        ):
            raise ValueError(
                "Section topology changed: polygon/vertex identities cannot be followed"
            )

        if mode == "unique":
            current, current_aliases = unique_vertices(section)
            if current != selectors or current_aliases != aliases:
                raise ValueError(
                    "Coincident vertex identities change along the beam; "
                    "use --vertices all"
                )

        for point_id, (pi, vi) in zip(point_ids, selectors):
            polygon = section.polygons[pi]
            vertex = polygon.vertices[vi]
            if inward_offset is None:
                sample_y = float(vertex.x)
                sample_z = float(vertex.y)
            else:
                sample_y, sample_z = inward_bisector_point(polygon, vi, inward_offset)
            rows.append(
                {
                    "point": point_id,
                    "polygon_index": pi + 1,
                    "vertex_index": vi,
                    "polygon_name": first.polygons[pi].name,
                    "vertex_aliases": ";".join(
                        f"polygon_{pp + 1}_vertex_{pv}"
                        for pp, pv in aliases[(pi, vi)]
                    ),
                    "x": float(x),
                    "x_over_L": float((x - start) / (end - start)),
                    "y": sample_y,
                    "z": sample_z,
                }
            )

    if inward_offset is None:
        print("Boundary points: " + ", ".join(point_ids))
    else:
        print(f"Inward points (offset={float(inward_offset):g}): " + ", ".join(point_ids))
    return point_ids, rows, start, end


def _recover_boundary_field_sets(
    npz_path: Path,
    csf_yaml: Path,
    points: int,
    vertices: str,
    inward_offset: float | None = None,
):
    from csf.io.csf_reader import CSFReader
    from csf.io.csf_issues import CSFIssues
    from csf.cuf.csf_bridge import CSFCUFModelBridge
    from csf.cuf.solver.compiled_field import CompiledDisplacementField

    field = CompiledDisplacementField.load(npz_path)
    bridge = CSFCUFModelBridge.from_yaml(csf_yaml)

    result = CSFReader().read_file(str(csf_yaml))
    if not result.ok or result.field is None:
        raise ValueError(CSFIssues.format_report(result.issues))

    point_ids, geometry, start, end = sample_geometry(result.field, points, vertices)
    inward_geometry = None
    if inward_offset is not None:
        inward_ids, inward_geometry, inward_start, inward_end = sample_geometry(
            result.field, points, vertices, inward_offset=inward_offset
        )
        if inward_ids != point_ids or inward_start != start or inward_end != end:
            raise RuntimeError("inward sampling changed point identities or longitudinal domain")

    field_domain = np.asarray((field.x_start, field.x_end), dtype=float)
    csf_domain = np.asarray((start, end), dtype=float)
    scale = max(1.0, float(np.max(np.abs(np.r_[field_domain, csf_domain]))))
    atol = 64.0 * np.finfo(float).eps * scale
    if not np.allclose(field_domain, csf_domain, rtol=0.0, atol=atol):
        raise ValueError(
            "NPZ and CSF YAML longitudinal domains differ: "
            f"NPZ={tuple(field_domain)}, CSF={tuple(csf_domain)}"
        )

    constitutive_provider = bridge.constitutive_provider

    def recover(geometry_rows):
        recovered_rows = []
        for station in geometry_rows:
            x = float(station["x"])
            y = float(station["y"])
            z = float(station["z"])

            # The sampled point carries its CSF polygon identity. CUF material
            # domain ids are 1-based and follow polygon order, so use that
            # identity directly. This remains unambiguous after moving inward.
            domain_id = int(station["polygon_index"])

            displacement = np.asarray(field(x, y, z), dtype=float)
            strain = np.asarray(field.strain(x, y, z), dtype=float)

            if displacement.shape != (3,):
                raise RuntimeError(
                    f"compiled displacement returned shape {displacement.shape}, expected (3,)"
                )
            if strain.shape != (6,):
                raise RuntimeError(
                    f"compiled strain returned shape {strain.shape}, expected (6,)"
                )

            C = np.asarray(
                constitutive_provider.matrix(
                    x=x,
                    domain_id=domain_id,
                    y=y,
                    z=z,
                ),
                dtype=float,
            )
            if C.shape != (6, 6):
                raise RuntimeError(
                    f"CUF constitutive provider returned shape {C.shape}, expected (6, 6)"
                )

            stress = C @ strain
            row = dict(station)
            row["displacement"] = displacement
            row["strain"] = strain
            row["stress"] = stress
            recovered_rows.append(row)
        return recovered_rows

    rows = recover(geometry)
    inward_rows = recover(inward_geometry) if inward_geometry is not None else None
    return point_ids, rows, inward_rows


def recover_boundary_fields(npz_path: Path, csf_yaml: Path, points: int, vertices: str):
    """Backward-compatible boundary-only recovery used by earlier callers."""
    point_ids, rows, _ = _recover_boundary_field_sets(
        npz_path, csf_yaml, points, vertices, inward_offset=None
    )
    return point_ids, rows


def recover_boundary_and_inward_fields(
    npz_path: Path,
    csf_yaml: Path,
    points: int,
    vertices: str,
    inward_offset: float,
):
    """Recover both the original vertices and their inward-offset counterparts."""
    point_ids, rows, inward_rows = _recover_boundary_field_sets(
        npz_path, csf_yaml, points, vertices, inward_offset=inward_offset
    )
    if inward_rows is None:
        raise RuntimeError("inward recovery unexpectedly produced no rows")
    return point_ids, rows, inward_rows


class FEM3DH8:
    """Recover native H8 fields. No extrapolation or averaging across elements."""

    SIGNS = np.array([
        [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
        [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1],
    ], dtype=float)

    def __init__(self, path):
        from scipy.spatial import cKDTree

        path = Path(path).expanduser().resolve()
        with np.load(path, allow_pickle=False) as data:
            keys = set(data.files)

            standard_required = {
                "format", "coordinate_system", "element_type", "version",
                "connectivity_index_base", "coordinates", "displacements",
                "connectivity", "element_ids", "units",
            }
            legacy_i_shape_required = {
                "nodes", "elements", "displacement", "amplitude", "x0", "x1",
            }

            if standard_required.issubset(keys):
                for key, value in (
                    ("format", "fem3d_h8_displacement"),
                    ("coordinate_system", "CUF"),
                    ("element_type", "stdBrick"),
                ):
                    if str(np.asarray(data[key]).item()) != value:
                        raise ValueError(f"FEM3D requires {key}={value!r}")
                if int(np.asarray(data["version"]).item()) != 1:
                    raise ValueError("Unsupported FEM3D checkpoint version")
                base = int(np.asarray(data["connectivity_index_base"]).item())
                if base not in (0, 1):
                    raise ValueError("FEM3D connectivity_index_base must be 0 or 1")

                coords = np.asarray(data["coordinates"], dtype=float)
                disp = np.asarray(data["displacements"], dtype=float)
                raw_conn = np.asarray(data["connectivity"])
                if not np.issubdtype(raw_conn.dtype, np.integer):
                    raise ValueError("FEM3D connectivity must contain integer indices")
                conn = raw_conn.astype(np.int64) - base
                self.ids = np.asarray(data["element_ids"])
                self.units = str(np.asarray(data["units"]).item())
                self.source_schema = "fem3d_h8_displacement v1"

            elif legacy_i_shape_required.issubset(keys):
                # Legacy I-Shape FEM3D files are raw stdBrick H8 results.
                # Their generator writes coordinates directly as (x,y,z) in the
                # same physical axes used by the CUF comparison and stores
                # zero-based connectivity in ``elements``.
                coords = np.asarray(data["nodes"], dtype=float)
                disp = np.asarray(data["displacement"], dtype=float)
                raw_conn = np.asarray(data["elements"])
                if not np.issubdtype(raw_conn.dtype, np.integer):
                    raise ValueError("Legacy FEM3D elements must contain integer indices")
                conn = raw_conn.astype(np.int64)
                self.ids = np.arange(len(conn), dtype=np.int64)
                self.units = str(np.asarray(data["units"]).item()) if "units" in keys else "native"
                self.source_schema = "legacy I-Shape H8 NPZ"

                x0 = float(np.asarray(data["x0"]).reshape(-1)[0])
                x1 = float(np.asarray(data["x1"]).reshape(-1)[0])
                if not np.isfinite(x0) or not np.isfinite(x1) or x1 <= x0:
                    raise ValueError(f"Invalid legacy FEM3D longitudinal domain: x0={x0}, x1={x1}")

            else:
                raise ValueError(
                    "Unsupported FEM3D NPZ schema. Expected either "
                    "fem3d_h8_displacement v1 or legacy I-Shape keys "
                    "{nodes,elements,displacement,amplitude,x0,x1}. "
                    "Available keys: " + ", ".join(sorted(keys))
                )

        if coords.ndim != 2 or coords.shape[1] != 3 or disp.shape != coords.shape:
            raise ValueError("FEM3D coordinates/displacements must have shape (nodes, 3)")
        if conn.ndim != 2 or conn.shape[1] != 8 or not len(conn):
            raise ValueError("FEM3D connectivity must have shape (elements, 8)")
        if self.ids.shape != (len(conn),) or len(np.unique(self.ids)) != len(conn):
            raise ValueError("FEM3D element_ids must be unique, one per element")
        if conn.min() < 0 or conn.max() >= len(coords):
            raise ValueError("FEM3D connectivity index outside node array")
        if not np.isfinite(coords).all() or not np.isfinite(disp).all():
            raise ValueError("Non-finite FEM3D coordinates/displacements")

        self.coords, self.disp = coords[conn], disp[conn]
        self.low, self.high = self.coords.min(axis=1), self.coords.max(axis=1)
        self.centers = self.coords.mean(axis=1)
        box_centers = (self.low + self.high) / 2
        self.tree = cKDTree(box_centers)
        self.radius = float(np.linalg.norm((self.high - self.low) / 2, axis=1).max())
        self.tol = 1e-9 * max(1., float(np.ptp(coords, axis=0).max()))
        self.domain_cache = {}
        print(
            f"FEM3D: {len(conn)} H8 elements; schema={self.source_schema}; "
            f"native units={self.units}; no unit conversion"
        )

    @classmethod
    def shape(cls, q):
        t = 1.0 + cls.SIGNS * q
        n = t.prod(axis=1) / 8.0
        d = np.stack([
            cls.SIGNS[:, i] * t[:, (i + 1) % 3] * t[:, (i + 2) % 3] / 8.0
            for i in range(3)
        ], axis=1)
        return n, d

    def domain(self, element, csf_field):
        """Classify an element by its interior center; reject ambiguous membership."""
        from matplotlib.path import Path as PolygonPath
        if element not in self.domain_cache:
            center = self.centers[element]
            section = csf_field.section(float(center[0]))
            matches = []
            for pi, polygon in enumerate(section.polygons, 1):
                vertices = [(v.x, v.y) for v in polygon.vertices]
                if PolygonPath(vertices).contains_point(center[1:]):
                    matches.append(pi)
            if len(matches) != 1:
                raise ValueError(f"FEM element {self.ids[element]} has ambiguous CSF polygon membership: {matches}")
            self.domain_cache[element] = matches[0]
        return self.domain_cache[element]

    def evaluate(self, point):
        candidates = self.tree.query_ball_point(point, self.radius + self.tol)
        found = []
        for ei in sorted(candidates):
            if np.any(point < self.low[ei] - self.tol) or np.any(point > self.high[ei] + self.tol):
                continue
            q = np.zeros(3)
            for _ in range(25):
                n, d = self.shape(q)
                residual = n @ self.coords[ei] - point
                jac = self.coords[ei].T @ d
                if np.linalg.det(jac) <= 0:
                    raise ValueError(f"Invalid H8 Jacobian in element {self.ids[ei]}")
                if np.max(np.abs(residual)) <= self.tol:
                    break
                q -= np.linalg.solve(jac, residual)
            n, d = self.shape(q)
            if np.max(np.abs(q)) > 1 + 1e-7 or np.max(np.abs(n @ self.coords[ei] - point)) > self.tol:
                continue
            jac = self.coords[ei].T @ d
            grad = np.linalg.solve(jac.T, d.T).T
            du = self.disp[ei].T @ grad
            strain = np.array([du[0, 0], du[1, 1], du[2, 2],
                               du[1, 2] + du[2, 1], du[0, 2] + du[2, 0],
                               du[0, 1] + du[1, 0]])
            found.append((ei, n @ self.disp[ei], strain))
        if not found:
            raise ValueError(f"No FEM3D element contains point {tuple(point)}; check geometry and units")
        return found


def recover_fem_boundary(fem, geometry, csf_field, provider=None):
    rows = []
    for station in geometry:
        point = np.array([station[k] for k in ("x", "y", "z")], dtype=float)
        recovered = fem.evaluate(point)
        accepted = 0
        for ei, displacement, strain in recovered:
            # At shared CSF vertices, retain only the requested polygon side.
            if fem.domain(ei, csf_field) != int(station["polygon_index"]):
                continue
            row = {k: v for k, v in station.items() if k not in ("displacement", "strain", "stress")}
            row.update(element_id=int(fem.ids[ei]), displacement=displacement, strain=strain)
            row["stress"] = np.full(6, np.nan)
            if provider is not None:
                C = np.asarray(provider.matrix(x=point[0], y=point[1], z=point[2],
                                               domain_id=int(station["polygon_index"])), dtype=float)
                if C.shape != (6, 6) or not np.isfinite(C).all():
                    raise ValueError("Invalid constitutive matrix for FEM3D stress recovery")
                row["stress"] = C @ strain
            rows.append(row)
            accepted += 1
        if not accepted:
            raise ValueError(f"No FEM3D element on CSF polygon side {station['polygon_index']} at {tuple(point)}")
    return rows


def select_rows(rows, point_id):
    return sorted(
        (row for row in rows if row["point"] == point_id),
        key=lambda row: float(row["x_over_L"]),
    )


def point_coordinate_label(selected):
    first = selected[0]
    last = selected[-1]
    y0, z0 = float(first["y"]), float(first["z"])
    y1, z1 = float(last["y"]), float(last["z"])
    if np.allclose((y0, z0), (y1, z1), rtol=0.0, atol=1.0e-12):
        return f"y,z = ({y0:g}, {z0:g})"
    return f"y,z: ({y0:g}, {z0:g}) -> ({y1:g}, {z1:g})"


def curve_values(selected, kind: str, index: int):
    return np.asarray([row[kind][index] for row in selected], dtype=float)


def save_curve_plot(
    point_ids, rows, curve, output_dir: Path, dpi: int, fem_rows=None, fem_stress=False,
    *, filename_suffix: str = "", location_title: str = "CSF polygon vertices",
):
    name, index, kind, ylabel, title = curve
    nrows = math.ceil(len(point_ids) / 2)
    fig, axes = plt.subplots(
        nrows,
        2,
        figsize=(13.4, 3.4 * nrows),
        sharex=True,
        constrained_layout=True,
    )
    axes = np.atleast_1d(axes).ravel()

    for unused in axes[len(point_ids):]:
        unused.set_visible(False)

    for ax, point_id in zip(axes, point_ids):
        selected = select_rows(rows, point_id)
        x = np.asarray([row["x_over_L"] for row in selected], dtype=float)
        values = curve_values(selected, kind, index)
        ax.plot(x, values, linewidth=1.1, label="CSF-CUF")
        if fem_rows is not None and (kind != "stress" or fem_stress):
            reference = select_rows(fem_rows, point_id)
            label = "FEM3D (CSF constitutive law)" if kind == "stress" else "FEM3D (element values)"
            ax.scatter([r["x_over_L"] for r in reference],
                       curve_values(reference, kind, index), s=7, color="tab:orange",
                       alpha=0.65, label=label, zorder=3)
        ax.axhline(0.0, linewidth=0.7)
        ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
        ax.set_xlim(-0.025, 1.025)
        ax.set_xticks([0.0, 0.25, 0.50, 0.75, 1.0])
        ax.set_title(point_id.replace("_", " "))
        ax.text(
            0.03,
            0.04,
            point_coordinate_label(selected),
            transform=ax.transAxes,
            fontsize=8.5,
        )
        ax.legend(loc="best", fontsize=8)

    fig.suptitle(f"{title} along {location_title}", fontsize=15)
    fig.supxlabel("s = (x - x0) / L")
    fig.supylabel(ylabel)

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{name}_along_boundary{filename_suffix}.png"
    fig.savefig(path, dpi=dpi, bbox_inches="tight", pad_inches=0.10)
    plt.close(fig)
    return path


def save_npz(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        **({"element_id": np.asarray([r["element_id"] for r in rows]),
            "stress_source": np.array("CSF constitutive law" if np.isfinite(rows[0]["stress"]).all() else "not recovered")}
           if rows and "element_id" in rows[0] else {}),
        coordinate_system=np.array("CUF"),
        point=np.asarray([row["point"] for row in rows]),
        polygon_index=np.asarray([row["polygon_index"] for row in rows]),
        vertex_index=np.asarray([row["vertex_index"] for row in rows]),
        polygon_name=np.asarray([row["polygon_name"] for row in rows]),
        vertex_aliases=np.asarray([row["vertex_aliases"] for row in rows]),
        x=np.asarray([row["x"] for row in rows], dtype=float),
        x_over_L=np.asarray([row["x_over_L"] for row in rows], dtype=float),
        y=np.asarray([row["y"] for row in rows], dtype=float),
        z=np.asarray([row["z"] for row in rows], dtype=float),
        displacement=np.asarray([row["displacement"] for row in rows], dtype=float),
        strain=np.asarray([row["strain"] for row in rows], dtype=float),
        stress=np.asarray([row["stress"] for row in rows], dtype=float),
    )
    return path


def save_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "point", "polygon_index", "vertex_index", "polygon_name", "vertex_aliases",
        "x", "x_over_L", "y", "z",
        "ux", "uy", "uz",
        "epsilon_xx", "epsilon_yy", "epsilon_zz", "gamma_yz", "gamma_xz", "gamma_xy",
        "sigma_xx", "sigma_yy", "sigma_zz", "tau_yz", "tau_xz", "tau_xy",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        fem = bool(rows and "element_id" in rows[0])
        writer.writerow(header + (["element_id", "stress_source"] if fem else []))
        for row in rows:
            writer.writerow(
                [
                    row["point"], row["polygon_index"], row["vertex_index"],
                    row["polygon_name"], row["vertex_aliases"],
                    row["x"], row["x_over_L"], row["y"], row["z"],
                    *row["displacement"], *row["strain"], *row["stress"],
                ] + ([row["element_id"], "CSF constitutive law" if np.isfinite(row["stress"]).all() else "not recovered"] if fem else [])
            )
    return path


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Recover displacement, strain and stress along all selected CSF polygon "
            "vertices from a compiled CUF displacement checkpoint."
        )
    )
    parser.add_argument("--csf-yaml", type=Path, required=True, help="Original CSF YAML")
    parser.add_argument(
        "--cuf-output-root",
        type=Path,
        default=Path("output"),
        help="CUF output tree to scan recursively for *.cuf.npz (default: output)",
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=None,
        help="Process one explicit .cuf.npz checkpoint instead of scanning --cuf-output-root",
    )
    parser.add_argument("--points", type=int, default=201, help="Longitudinal samples (default: 201)")
    parser.add_argument(
        "--vertices",
        choices=("unique", "all"),
        default="all",
        help=(
            "Retain every polygon identity or merge coincident vertices "
            "(default: all; recommended for stresses at material interfaces)"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("strain_stress_boundary"),
        help="Output directory for PNG and sampled NPZ files",
    )
    parser.add_argument("--dpi", type=int, default=220, help="PNG resolution (default: 220)")
    parser.add_argument("--csv", type=Path, default=None, help="Optional CSV containing every recovered value")
    parser.add_argument("--fem3d", type=Path, default=None,
                        help="Optional native fem3d_h8_displacement v1 NPZ, in the same geometry, axes and units as CUF")
    parser.add_argument("--fem-stress-from-csf", action="store_true",
                        help="Explicitly use the CSF YAML constitutive law for FEM3D stresses; requires matching materials and a mesh conforming to CSF polygons")
    parser.add_argument(
        "--inward-offset",
        type=float,
        default=None,
        help=(
            "Optional positive distance in native transverse model units. "
            "Keeps every original boundary plot and additionally repeats every plot "
            "at points shifted inside each polygon along the internal vertex bisector."
        ),
    )
    return parser


def discover_checkpoints(cuf_output_root: Path, checkpoint: Path | None) -> list[Path]:
    if checkpoint is not None:
        path = checkpoint.expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        if not path.name.endswith(".cuf.npz"):
            raise ValueError(f"Checkpoint must end with .cuf.npz: {path}")
        return [path]

    root = cuf_output_root.expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    paths = sorted(path.resolve() for path in root.rglob("*.cuf.npz") if path.is_file())
    if not paths:
        raise FileNotFoundError(f"No .cuf.npz checkpoints found below {root}")
    return paths


def checkpoint_output_name(path: Path) -> str:
    return path.name.removesuffix(".cuf.npz")


def main():
    args = build_parser().parse_args()
    if args.fem_stress_from_csf and args.fem3d is None:
        raise ValueError("--fem-stress-from-csf requires --fem3d")
    if args.inward_offset is not None and (
        not math.isfinite(args.inward_offset) or args.inward_offset <= 0.0
    ):
        raise ValueError("--inward-offset must be a positive finite distance")
    fem = FEM3DH8(args.fem3d) if args.fem3d is not None else None
    fem_rows = None
    fem_inward_rows = None
    if fem is not None:
        from csf.io.csf_reader import CSFReader
        from csf.io.csf_issues import CSFIssues
        from csf.cuf.csf_bridge import CSFCUFModelBridge
        result = CSFReader().read_file(str(args.csf_yaml))
        if not result.ok or result.field is None:
            raise ValueError(CSFIssues.format_report(result.issues))
        provider = CSFCUFModelBridge.from_yaml(args.csf_yaml).constitutive_provider if args.fem_stress_from_csf else None
        print("FEM3D uses a mesh conforming to CSF polygons; interface values are selected by polygon side.")
        if provider is None:
            print("FEM3D stress overlay disabled: use --fem-stress-from-csf only when materials match.")
    checkpoints = discover_checkpoints(args.cuf_output_root, args.checkpoint)
    output_root = args.output_dir.expanduser().resolve()

    for checkpoint in checkpoints:
        if args.inward_offset is None:
            point_ids, rows = recover_boundary_fields(
                checkpoint,
                args.csf_yaml,
                points=args.points,
                vertices=args.vertices,
            )
            inward_rows = None
        else:
            point_ids, rows, inward_rows = recover_boundary_and_inward_fields(
                checkpoint,
                args.csf_yaml,
                points=args.points,
                vertices=args.vertices,
                inward_offset=args.inward_offset,
            )

        if fem is not None and fem_rows is None:
            fem_rows = recover_fem_boundary(fem, rows, result.field, provider)
            print(f"FEM3D recovered: {len(fem_rows)} element-side boundary samples")
        if fem is not None and inward_rows is not None and fem_inward_rows is None:
            fem_inward_rows = recover_fem_boundary(fem, inward_rows, result.field, provider)
            print(f"FEM3D inward recovered: {len(fem_inward_rows)} element-side samples")

        case_output_dir = output_root / checkpoint_output_name(checkpoint)
        for curve in CURVES:
            path = save_curve_plot(
                point_ids, rows, curve, case_output_dir, args.dpi,
                fem_rows, args.fem_stress_from_csf,
            )
            print(f"[ok] {path}")
            if inward_rows is not None:
                tag = offset_tag(args.inward_offset)
                inward_path = save_curve_plot(
                    point_ids, inward_rows, curve, case_output_dir, args.dpi,
                    fem_inward_rows, args.fem_stress_from_csf,
                    filename_suffix=f"_inward_{tag}",
                    location_title=(
                        "CSF polygon inward points "
                        f"(offset={args.inward_offset:g} model units)"
                    ),
                )
                print(f"[ok] {inward_path}")

        sampled_path = save_npz(case_output_dir / "sampled_boundary_fields.npz", rows)
        print(f"[ok] {sampled_path}")

        if fem_rows is not None:
            save_npz(case_output_dir / "sampled_fem3d_boundary_fields.npz", fem_rows)
            save_csv(case_output_dir / "sampled_fem3d_boundary_fields.csv", fem_rows)

        if args.csv is not None:
            csv_root = args.csv.expanduser().resolve()
            if len(checkpoints) == 1 and csv_root.suffix.lower() == ".csv":
                csv_path = csv_root
            else:
                csv_root.mkdir(parents=True, exist_ok=True)
                csv_path = csv_root / f"{checkpoint_output_name(checkpoint)}.csv"
            csv_path = save_csv(csv_path, rows)
            print(f"[ok] {csv_path}")


if __name__ == "__main__":
    main()
