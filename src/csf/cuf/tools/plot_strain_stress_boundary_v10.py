# Version: CSF-CUF plot_strain_stress_boundary v14.2.7 - 2026-10-27
# v14.2.7: Classify voids using polygon.weightabs from field.section(x).
#          Absolute carrier != abs(polygon.weight). No endpoint fallback.
#          Reuse bridge.field; load the CSF model once in transverse mode.
#          Separate model loading from API-only sampling for regression tests.
#          Export the actual section weightabs and void mask in the NPZ.
# v14.2.4: Zero-absolute-weight cavities without third-party geometry dependencies.
#          Polygon clipping, area subtraction and physical-point selection.
# v14.2.2: Globally proportional vector density and length. Per-polygon direct
#          arrow sampling with one physical step based on the full section.
# v14.2.1: Initialize the material provider before polygon sampling; return local samples
#          to the plotters and persist their exact coordinates/values in the NPZ.
# v14.2: Direct Y-Z transverse maps and shear stress vector plot with one color scale.
#         Vector arrows use (tau_xy, tau_xz) and direct per-polygon samples.
#         New CLI --transverse-x, --transverse-grid, --transverse-vector-grid.
#         All prior Gauss / boundary modes remain available.
# v14.1: Gauss plot-mode compares only FEM integration points selected for plot trajectories.
# v14: native OpenSees Gauss comparison + element-material boundary stresses.
# v13 moving-domain and polygon-side handling remain unchanged.
# Revision-ID: c0f0f7cb-4e40-459e-9272-ae5d830a2120
#
# Changelog v13:
# - Recognize moving solved-field v5 through domain_vertices_at(x).
# - Match CSF polygons to mathematical checkpoint domains at EVERY sampled x.
# - Reject geometry mismatches and changing domain identities before recovery.
# - Retain exact polygon-side strain evaluation and native CSF constitutive law.
# - Preserve legacy recovery, FEM3D logic, plots and existing CLI arguments.
# - Add --no-plots for numerical-only recovery; print script path/version.
# - No changes to the solver, checkpoint, material law or sampling positions.
#
# Changelog v12:
# - FEM3D element-side selection now uses positive transverse area overlap
#   with the requested CSF polygon for axis-aligned extruded H8 elements.
# - One FEM element can belong to multiple CSF subdivisions; its existing
#   unaveraged H8 field is evaluated at the ORIGINAL sample position.
# - Preserve existing centroid-based assignment for other H8 geometries,
#   and reject ambiguous assignments instead of inventing a side.
# - No changes to CUF sampling, checkpoint data, or constitutive recovery.
#
# Changelog v11.1:
# - Added unique Revision-ID for auditability.
# - Header-only revision; no numerical or functional changes.
#
# Changelog v11:
# - For solved-field v4, select a polygon-side derivative explicitly using
#   the mathematical checkpoint domain index (validated against CSF geometry).
# - Original polygon-vertex sampling is unchanged; no inward displacement,
#   derivative averaging, interpolation, or fitted stress recovery.
# - Split plots into small page files to avoid very large 36-panel figures.
# - Persist numeric samples before plotting, even if PNG rendering is interrupted.
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
    The FEM and CSF must share the same physical domain and material law.
    For extruded rectangular H8 elements, FEM cells may cross purely internal
    CSF subdivisions. No unit conversion, nodal strain averaging or nearest-
    point extrapolation is performed. Polygon-side FEM traces are selected by
    positive cross-sectional area overlap and evaluated at the original point.

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


def map_checkpoint_domains_to_csf(field, section, *, x: float | None = None):
    """Map 1-based CSF polygons to 0-based solved-field domains at the SAME x.

    v4 stores fixed domains in ``solved_domain_vertices``. v5 stores moving
    domains and that v4-only property is None: use ``domain_vertices_at(x)``.
    None is returned only when the compiled field has no explicit solved
    domains (legacy recovery). Match physical vertices, never assume ordering.
    """
    if x is None:
        x = getattr(section, "z", None)
        if x is None:
            x = field.x_start
    x = float(x)
    if not math.isfinite(x):
        raise ValueError("domain-matching station must be finite")

    vertices_at = getattr(field, "domain_vertices_at", None)
    if callable(vertices_at):
        vertices = vertices_at(x)
    else:
        # Compatibility with pre-v5 compiled-field implementations.
        vertices = getattr(field, "solved_domain_vertices", None)
    if vertices is None:
        return None

    polygons = tuple(section.polygons)
    if len(polygons) != len(vertices):
        raise ValueError(
            "Solved-field checkpoint and supplied CSF YAML contain "
            f"different transverse domain counts at x={x:g} "
            f"({len(vertices)} vs {len(polygons)}). Use the matching CSF model."
        )
    if not polygons:
        raise ValueError(f"No transverse domains at x={x:g}")

    def match_vertices(a, b):
        if a.shape != b.shape:
            return False
        if not np.isfinite(a).all() or not np.isfinite(b).all():
            return False
        scale = max(1., float(np.max(np.abs(a))), float(np.max(np.abs(b))))
        atol = 1.e-10 * scale
        available = list(range(len(b)))
        for point in a:
            possible = [j for j in available if np.allclose(point, b[j], rtol=0., atol=atol)]
            if not possible:
                return False
            available.remove(possible[0])
        return True

    lookup = {}
    remaining = set(range(len(vertices)))
    for pi, polygon in enumerate(polygons, start=1):
        csf_vertices = np.asarray([(v.x, v.y) for v in polygon.vertices], dtype=float)
        matches = [idx for idx in sorted(remaining)
                   if match_vertices(csf_vertices, np.asarray(vertices[idx], dtype=float))]
        if len(matches) != 1:
            raise ValueError(
                "Solved-field checkpoint domain geometry does not match "
                f"CSF polygon {pi} at x={x:g}; matching domains={matches}. "
                "Check the CSF YAML, checkpoint and moving geometry."
            )
        lookup[pi] = matches[0]
        remaining.remove(matches[0])
    return lookup


def validate_checkpoint_domain_lookups(field, csf_field, stations):
    """Validate full polygon geometry at every requested longitudinal station.

    The mapping must retain the same polygon/domain identities along the beam.
    A fixed mapping established at x_start alone would not detect a different
    taper, an interior trajectory mismatch, or a changed domain ordering.
    """
    xs = sorted(set(float(x) for x in stations))
    if not xs:
        raise ValueError("No stations supplied for checkpoint/CSF validation")
    lookups = {}
    for x in xs:
        current = map_checkpoint_domains_to_csf(field, csf_field.section(x), x=x)
        if lookups:
            reference = lookups[xs[0]]
            if current != reference:
                raise ValueError(
                    f"Checkpoint-to-CSF domain identities change at x={x:g}: "
                    f"initial mapping={reference}, current mapping={current}. "
                    "Do not select a stress side from a mismatching partition."
                )
        lookups[x] = current
    reference = lookups[xs[0]]
    if reference is None:
        print("[domains] legacy field: existing derivative recovery retained", flush=True)
    else:
        mapping = ", ".join(f"{pi}->{di}" for pi, di in sorted(reference.items()))
        print(
            f"[domains] validated {len(reference)} domains at {len(xs)} stations; "
            f"CSF polygon (1-based) -> checkpoint domain (0-based): {mapping}",
            flush=True,
        )
    return lookups


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
    domain_lookups = validate_checkpoint_domain_lookups(
        field, result.field, (station["x"] for station in geometry)
    )

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

            domain_lookup = domain_lookups[x]
            displacement = np.asarray(field(x, y, z), dtype=float)
            if domain_lookup is None:
                # Legacy representations: preserve the existing evaluation.
                strain = np.asarray(field.strain(x, y, z), dtype=float)
            else:
                # v4/v5: select the mathematical one-sided derivative at the exact
                # CSF vertex, using the already-known physical polygon side.
                side_index = domain_lookup[domain_id]
                strain = np.asarray(
                    field.strain(x, y, z, domain_index=side_index), dtype=float
                )

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
                has_element_material = {"element_E", "element_G", "element_nu"}.issubset(keys)
                self.element_E = np.asarray(data["element_E"], dtype=float) if has_element_material else None
                self.element_G = np.asarray(data["element_G"], dtype=float) if has_element_material else None
                self.element_nu = np.asarray(data["element_nu"], dtype=float) if has_element_material else None
                gauss_keys = {"gauss_natural_coordinates", "gauss_coordinates",
                              "gauss_stresses_opensees", "gauss_stresses_cuf_order",
                              "gauss_stress_components_opensees", "gauss_stress_components_cuf"}
                if gauss_keys & keys and not gauss_keys.issubset(keys):
                    raise ValueError("Incomplete native Gauss stress metadata; rerun FEM3D with the updated exporter")
                self.native_stresses = (np.asarray(data["gauss_stresses_cuf_order"], dtype=float)
                                        if gauss_keys.issubset(keys) else None)
                self.gauss_coordinates = (np.asarray(data["gauss_coordinates"], dtype=float)
                                          if gauss_keys.issubset(keys) else None)
                self.gauss_natural = (np.asarray(data["gauss_natural_coordinates"], dtype=float)
                                      if gauss_keys.issubset(keys) else None)
                if self.native_stresses is not None:
                    expected_os = ["sigma_xx", "sigma_yy", "sigma_zz", "tau_xy", "tau_yz", "tau_xz"]
                    expected_cuf = ["sigma_xx", "sigma_yy", "sigma_zz", "tau_yz", "tau_xz", "tau_xy"]
                    if list(data["gauss_stress_components_opensees"]) != expected_os or list(data["gauss_stress_components_cuf"]) != expected_cuf:
                        raise ValueError("Unexpected native stress component order in FEM3D checkpoint")
                    original = np.asarray(data["gauss_stresses_opensees"], dtype=float)
                    if not np.array_equal(self.native_stresses, original[:, :, [0,1,2,4,5,3]]):
                        raise ValueError("OpenSees-to-CUF stress component permutation is inconsistent")

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
                self.element_E = self.element_G = self.element_nu = None
                self.native_stresses = self.gauss_coordinates = self.gauss_natural = None

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

        if self.element_E is not None:
            for param in (self.element_E, self.element_G, self.element_nu):
                if param.shape != (len(conn),) or not np.isfinite(param).all():
                    raise ValueError("Element material arrays must contain one finite value per H8 element")
            if np.any(self.element_E <= 0) or np.any(self.element_G <= 0) or np.any(self.element_nu <= -1) or np.any(self.element_nu >= 0.5):
                raise ValueError("Invalid FEM element isotropic material parameters")
            if not np.allclose(self.element_E / (2 * (1 + self.element_nu)), self.element_G, rtol=1e-9):
                raise ValueError("FEM material E/G/nu metadata are inconsistent")
        self.coords, self.disp = coords[conn], disp[conn]
        if self.native_stresses is not None:
            if self.native_stresses.shape != (len(conn), 8, 6) or not np.isfinite(self.native_stresses).all():
                raise ValueError("Native OpenSees stress data must be finite (elements,8,6)")
            if self.gauss_coordinates.shape != (len(conn), 8, 3) or not np.isfinite(self.gauss_coordinates).all():
                raise ValueError("Gauss point coordinates must be finite (elements,8,3)")
            a = 1 / np.sqrt(3.)
            expected_gauss = np.asarray([(r,s,t) for r in (-a,a) for s in (-a,a) for t in (-a,a)])
            if self.gauss_natural.shape != (8,3) or not np.allclose(self.gauss_natural, expected_gauss, atol=1e-12):
                raise ValueError("Gauss natural coordinate ordering differs from OpenSees Brick.cpp")
            # Validate all saved Gauss coordinates by vectorized H8 interpolation.
            # Avoid 8 Python shape-function calls per element (432k for 54k H8).
            gauss_shape = np.asarray([self.shape(q)[0] for q in expected_gauss])
            from_source = np.einsum("gi,eij->egj", gauss_shape, self.coords, optimize=True)
            scale = max(1., float(np.abs(coords).max()))
            if not np.allclose(self.gauss_coordinates, from_source, rtol=0., atol=1e-9*scale):
                raise ValueError("Saved Gauss physical coordinates do not match the native H8 geometry")
        self.low, self.high = self.coords.min(axis=1), self.coords.max(axis=1)
        self.centers = self.coords.mean(axis=1)
        self.tol = 1e-9 * max(1., float(np.ptp(coords, axis=0).max()))
        # Classify by the geometry of the H8 element, not the CUF basis family.
        # For an extruded, axis-aligned rectangular element, its exact physical
        # transverse footprint is the box (y_min, y_max, z_min, z_max).
        # Other H8 elements retain the previous conservative centroid path.
        self.rectangular_prisms = self._rectangular_prism_mask()
        self.transverse_boxes = np.column_stack((
            self.low[:, 1], self.high[:, 1],
            self.low[:, 2], self.high[:, 2],
        ))
        box_centers = (self.low + self.high) / 2
        self.tree = cKDTree(box_centers)
        self.radius = float(np.linalg.norm((self.high - self.low) / 2, axis=1).max())
        self.domain_cache = {}
        print(
            f"FEM3D: {len(conn)} H8 elements; schema={self.source_schema}; "
            f"native units={self.units}; no unit conversion"
        )
        print(
            "FEM3D transverse prism geometry: "
            f"{int(np.count_nonzero(self.rectangular_prisms))}/{len(conn)} "
            "H8 elements support exact polygon-overlap side selection"
        )

    def _rectangular_prism_mask(self):
        """Identify exact extruded, axis-aligned H8 cells by their 8 corners."""
        vertices = self.coords
        lower = self.low
        upper = self.high
        nondegenerate = np.all(upper > lower, axis=1)
        # Each corner must have one of the two global bounds in every axis.
        at_lower = np.isclose(vertices, lower[:, None, :], rtol=0., atol=self.tol)
        at_upper = np.isclose(vertices, upper[:, None, :], rtol=0., atol=self.tol)
        on_corners = np.all(at_lower | at_upper, axis=(1, 2))
        # Exactly one vertex at each of the 8 box corners, in any numbering.
        corner_id = (at_upper[:, :, 0].astype(int) * 4
                     + at_upper[:, :, 1].astype(int) * 2
                     + at_upper[:, :, 2].astype(int))
        unique_corners = np.sort(corner_id, axis=1)
        correct = np.all(unique_corners == np.arange(8)[None, :], axis=1)
        return nondegenerate & on_corners & correct

    @staticmethod
    def _positive_polygon_rectangle_overlap(vertices, bounds):
        """Strict positive-area intersection; touching at a point/edge is excluded.

        Clips the CSF polygon to a physical y-z rectangle. The clipping
        procedure handles concave CSF polygons; no FEM mesh partition is
        presumed to coincide with internal CUF transverse domains.
        """
        polygon = [(float(y), float(z)) for y, z in vertices]
        ymin, ymax, zmin, zmax = map(float, bounds)
        if len(polygon) < 3:
            return False
        # Fast rejection of separated transverse bounding boxes.
        a = np.asarray(polygon, dtype=float)
        if (float(a[:, 0].max()) <= ymin or float(a[:, 0].min()) >= ymax
                or float(a[:, 1].max()) <= zmin or float(a[:, 1].min()) >= zmax):
            return False
        # Four Sutherland-Hodgman clipping halfplanes.
        for axis, bound, sign in ((0, ymin, 1), (0, ymax, -1),
                                  (1, zmin, 1), (1, zmax, -1)):
            if not polygon:
                return False
            clipped = []
            previous = polygon[-1]
            prev_signed = sign * (previous[axis] - bound)
            for current in polygon:
                curr_signed = sign * (current[axis] - bound)
                curr_inside = curr_signed >= 0.0
                prev_inside = prev_signed >= 0.0
                if curr_inside != prev_inside:
                    fraction = prev_signed / (prev_signed - curr_signed)
                    clipped.append((
                        previous[0] + fraction * (current[0] - previous[0]),
                        previous[1] + fraction * (current[1] - previous[1]),
                    ))
                if curr_inside:
                    clipped.append(current)
                previous, prev_signed, prev_inside = current, curr_signed, curr_inside
            polygon = clipped
        if len(polygon) < 3:
            return False
        # Center before computing area to avoid catastrophic cancellation for
        # large coordinate offsets (the area itself is translation-invariant).
        p = np.asarray(polygon, dtype=float)
        p -= p[0].copy()
        signed_double_area = (np.dot(p[:, 0], np.roll(p[:, 1], -1))
                              - np.dot(p[:, 1], np.roll(p[:, 0], -1)))
        scale = max(1., abs(ymax-ymin), abs(zmax-zmin),
                    float(np.ptp(a[:,0])), float(np.ptp(a[:,1])))
        area_tol = 64. * np.finfo(float).eps * scale**2
        return 0.5 * abs(float(signed_double_area)) > area_tol

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
        """Legacy side assignment for nonrectangular H8 geometries."""
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
                raise ValueError(
                    f"FEM element {self.ids[element]} has ambiguous CSF polygon "
                    f"membership with nonrectangular H8 geometry: {matches}"
                )
            self.domain_cache[element] = matches[0]
        return self.domain_cache[element]

    def intersects_polygon_side(self, element, polygon_index, section, csf_field, *, x=None):
        """Check genuine positive-area FEM/polygon overlap at the current x.

        For the user's straight-sided tapered T mesh, each cross section of an
        H8 cell is an axis-aligned rectangle. The footprint must be evaluated
        at the CURRENT longitudinal station, not at a reference centroid.
        """
        polygon = section.polygons[int(polygon_index) - 1]
        points = [(v.x, v.y) for v in polygon.vertices]
        if self.rectangular_prisms[element]:
            return self._positive_polygon_rectangle_overlap(points, self.transverse_boxes[element])
        if x is not None:
            vertices = self.coords[element]
            xa = float(self.low[element, 0])
            xb = float(self.high[element, 0])
            if xb <= xa:
                raise ValueError("Degenerate H8 longitudinal extent")
            f = (float(x)-xa)/(xb-xa)
            if f < -1e-8 or f > 1+1e-8:
                raise ValueError("FEM sampling point outside selected element")
            start=vertices[np.isclose(vertices[:, 0],xa,rtol=0.,atol=self.tol)]
            end=vertices[np.isclose(vertices[:, 0],xb,rtol=0.,atol=self.tol)]
            if len(start)==4 and len(end)==4:
                ys=(1-f)*np.sort(start[:,1]) + f*np.sort(end[:,1])
                zs=(1-f)*np.sort(start[:,2]) + f*np.sort(end[:,2])
                # Check both end faces are genuine y/z rectangles (not a warped
                # mesh), and that the taper is affine as generated by TSectionMesh.
                def rectangular(face):
                    y0,y1=np.min(face[:,1]),np.max(face[:,1])
                    z0,z1=np.min(face[:,2]),np.max(face[:,2])
                    return len({(round(float(y),10),round(float(z),10)) for _,y,z in face})==4 and all(
                        (abs(y-y0)<self.tol or abs(y-y1)<self.tol) and
                        (abs(z-z0)<self.tol or abs(z-z1)<self.tol) for _,y,z in face)
                if rectangular(start) and rectangular(end):
                    bounds=(float(ys.min()),float(ys.max()),float(zs.min()),float(zs.max()))
                    return self._positive_polygon_rectangle_overlap(points,bounds)
        # Retain conservative original behavior for unsupported warped cells.
        return self.domain(element,csf_field)==int(polygon_index)

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


def isotropic_element_C(E: float, G: float, nu: float) -> np.ndarray:
    """Isotropic 3D stiffness for CUF [xx, yy, zz, yz, xz, xy] tensor order."""
    lam = E * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
    C = np.zeros((6, 6), dtype=float)
    C[:3, :3] = lam
    C[0,0] += 2*G
    C[1,1] += 2*G
    C[2,2] += 2*G
    C[3,3] = C[4,4] = C[5,5] = G
    return C


def recover_fem_boundary(fem, geometry, csf_field, provider=None, *, stress_source="none"):
    rows = []
    previous_x = None
    section = None
    for station in geometry:
        point = np.array([station[k] for k in ("x", "y", "z")], dtype=float)
        if previous_x != float(point[0]):
            section = csf_field.section(float(point[0]))
            previous_x = float(point[0])
        recovered = fem.evaluate(point)
        accepted = 0
        for ei, displacement, strain in recovered:
            # Intersect the actual FEM footprint with the requested CSF side.
            # A FEM cell may cross an internal CUF-domain interface; evaluate
            # its original H8 field exactly at this point, without averaging.
            if not fem.intersects_polygon_side(
                ei, station["polygon_index"], section, csf_field, x=float(point[0])
            ):
                continue
            row = {k: v for k, v in station.items() if k not in ("displacement", "strain", "stress")}
            row.update(element_id=int(fem.ids[ei]), displacement=displacement, strain=strain)
            row["stress"] = np.full(6, np.nan)
            if stress_source == "csf":
                C = np.asarray(provider.matrix(x=point[0], y=point[1], z=point[2],
                                               domain_id=int(station["polygon_index"])), dtype=float)
                if C.shape != (6, 6) or not np.isfinite(C).all():
                    raise ValueError("Invalid CSF constitutive matrix for FEM3D stress recovery")
                row["stress"] = C @ strain
            elif stress_source == "element":
                C = isotropic_element_C(fem.element_E[ei], fem.element_G[ei], fem.element_nu[ei])
                row["stress"] = C @ strain
            row["stress_source"] = stress_source
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
            label = ("FEM3D (" + str(reference[0].get("stress_source", "recovered")) + " material)"
                     if kind == "stress" else "FEM3D (H8 displacement/strain)")
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
            "stress_source": np.array(rows[0].get("stress_source", "not recovered"))}
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
                ] + ([row["element_id"], row.get("stress_source", "not recovered")] if fem else [])
            )
    return path


def select_gauss_plot_samples(fem, csf_field, points: int, vertices: str):
    """Choose only the native FEM Gauss points required for plotted vertex traces.

    For each requested longitudinal station, select its nearest available FEM
    Gauss x-plane, then one nearest *interior* Gauss point per CSF polygon vertex.
    Selection stays within the SAME CSF polygon side; there is no stress averaging,
    projection, extrapolation, or FEM stress reconstruction. Selected Gauss
    coordinates (not the nominal vertex coordinates) remain the evaluation
    coordinates and are saved with their transverse distance from each vertex.

    The actual number of stations can be lower than --points when the FEM mesh
    contains fewer distinct Gauss x-planes. Every selected point is native.
    """
    from matplotlib.path import Path as PolygonPath

    if fem.gauss_coordinates is None or fem.native_stresses is None:
        raise ValueError("Plot-mode Gauss sampling requires native FEM Gauss stresses and coordinates")
    first = csf_field.section(float(csf_field.s0.z))
    if vertices == "unique":
        selectors, _ = unique_vertices(first)
    else:
        selectors = [(pi, vi) for pi, poly in enumerate(first.polygons)
                     for vi in range(len(poly.vertices))]
    if not selectors:
        raise ValueError("No plotted CSF polygon vertices selected")
    point_ids = tuple(f"polygon_{pi+1}_vertex_{vi}" for pi, vi in selectors)
    # Moving H8 physical coordinates may differ at the last few floating-point
    # bits for mathematically identical Gauss x-planes. Bin using a dimensional
    # tolerance; keep the *original* Gauss coordinates when evaluating stresses.
    xyz = fem.gauss_coordinates.reshape(-1, 3)
    start, end = float(csf_field.s0.z), float(csf_field.s1.z)
    length = end - start
    if length <= 0.0:
        raise ValueError("Invalid longitudinal CSF domain")
    resolution = 1e-10 * max(1.0, abs(start), abs(end), length)
    plane_keys = np.rint((xyz[:, 0] - start) / resolution).astype(np.int64)
    ordered = np.argsort(plane_keys, kind="stable")
    unique_keys, first_indices, counts = np.unique(
        plane_keys[ordered], return_index=True, return_counts=True
    )
    x_planes = np.asarray([xyz[ordered[offset], 0] for offset in first_indices])
    targets = np.linspace(start, end, points)
    insert = np.searchsorted(x_planes, targets)
    hi = np.clip(insert, 0, len(x_planes)-1)
    lo = np.clip(insert-1, 0, len(x_planes)-1)
    nearest = np.where(np.abs(x_planes[hi]-targets) < np.abs(x_planes[lo]-targets), hi, lo)
    chosen_plane_indices = np.unique(nearest)
    selections = []
    max_offset = 0.0
    for plane_idx in chosen_plane_indices:
        x = float(x_planes[plane_idx])
        section = csf_field.section(x)
        if len(section.polygons) != len(first.polygons):
            raise ValueError("CSF polygon count changed along the beam")
        begin = first_indices[plane_idx]
        indices = ordered[begin:begin + counts[plane_idx]]
        transverse = xyz[indices, 1:]
        # Vectorized membership over all available H8 Gauss points in this plane.
        for pi, poly in enumerate(section.polygons):
            relevant = [(pid, vi) for pid, (pidx, vi) in zip(point_ids, selectors)
                        if pidx == pi]
            if not relevant:
                continue
            corners = np.asarray([(v.x, v.y) for v in poly.vertices], dtype=float)
            scale = max(1.0, float(np.max(np.abs(corners))))
            inside = PolygonPath(corners).contains_points(transverse, radius=-1e-10*scale)
            local = np.flatnonzero(inside)
            if not len(local):
                raise ValueError(
                    f"No native FEM Gauss point inside CSF polygon {pi+1} at x={x:g}; "
                    "align/refine the FEM mesh or use boundary reconstruction"
                )
            candidates = transverse[local]
            for point_id, vi in relevant:
                target = corners[vi]
                distances2 = np.sum((candidates - target)**2, axis=1)
                winner = int(indices[local[int(np.argmin(distances2))]])
                ei, gi = divmod(winner, 8)
                dist = float(np.sqrt(np.min(distances2)))
                max_offset = max(max_offset, dist)
                selections.append({
                    "element_array_index": int(ei), "gauss_array_index": int(gi),
                    "point": point_id, "vertex_index": int(vi),
                    "polygon_index": pi+1,
                    "polygon_name": str(first.polygons[pi].name),
                    "target_y": float(target[0]), "target_z": float(target[1]),
                    "transverse_offset": dist,
                })
    expected = len(chosen_plane_indices) * len(point_ids)
    if len(selections) != expected:
        raise RuntimeError(f"Gauss plot selection produced {len(selections)} points; expected {expected}")
    print(f"[gauss] plot-only sampling: {len(chosen_plane_indices)} Gauss x-planes "
          f"x {len(point_ids)} polygon-side vertex traces = {len(selections)} CUF evaluations "
          f"(out of {len(xyz)} available native Gauss points); "
          f"max transverse vertex offset={max_offset:g}", flush=True)
    return point_ids, selections


def recover_gauss_native_comparison(fem, cuf_checkpoint: Path, csf_yaml: Path, *,
                                    points: int = 201, vertices: str = "all",
                                    sampling: str = "plot"):
    """Compare OpenSees native and CUF stresses at identical Gauss coordinates.

    Plot mode selects one near-vertex, same-domain Gauss point for each trace
    and FEM Gauss x-station. Neither native FEM stresses nor CUF stresses are
    extrapolated to the actual CSF vertex. The physical offset is recorded.
    """
    from matplotlib.path import Path as PolygonPath
    from csf.io.csf_reader import CSFReader
    from csf.io.csf_issues import CSFIssues
    from csf.cuf.csf_bridge import CSFCUFModelBridge
    from csf.cuf.solver.compiled_field import CompiledDisplacementField

    if fem.native_stresses is None:
        raise ValueError("FEM NPZ does not contain native Gauss stresses. Rerun the updated stdBrick FEM exporter.")
    compiled = CompiledDisplacementField.load(cuf_checkpoint)
    read = CSFReader().read_file(str(csf_yaml))
    if not read.ok or read.field is None:
        raise ValueError(CSFIssues.format_report(read.issues))
    csf_field = read.field
    provider = CSFCUFModelBridge.from_yaml(csf_yaml).constitutive_provider
    x0, x1 = float(csf_field.s0.z), float(csf_field.s1.z)
    tol = 1e-9 * max(1.0, abs(x0), abs(x1))
    if not np.allclose([compiled.x_start, compiled.x_end], [x0,x1], rtol=0., atol=tol):
        raise ValueError("CUF checkpoint and CSF longitudinal extents differ")
    # Plot mode does not visit unplotted integration points. Full mode retains
    # the previous exhaustive validation/recovery for explicit research audits.
    if sampling == "plot":
        point_ids, selections = select_gauss_plot_samples(fem, csf_field, points, vertices)
        lookup_x = sorted(set(float(fem.gauss_coordinates[item["element_array_index"],
                                                       item["gauss_array_index"], 0])
                              for item in selections))
        # Numerical differences among nominally identical x-planes are possible;
        # each coordinate is validated once before the CUF comparison.
        lookups = validate_checkpoint_domain_lookups(compiled, csf_field, lookup_x)
    elif sampling == "all":
        point_ids = None
        selections = ({"element_array_index": ei, "gauss_array_index": gi}
                      for ei in range(len(fem.ids)) for gi in range(8))
        xs = np.unique(fem.gauss_coordinates[:,:,0])
        lookups = validate_checkpoint_domain_lookups(compiled, csf_field, xs)
    else:
        raise ValueError(f"Unknown Gauss sampling mode: {sampling!r}")
    rows = []
    for selection in selections:
            ei = selection["element_array_index"]
            gi = selection["gauss_array_index"]
            x, y, z = map(float, fem.gauss_coordinates[ei,gi])
            section = csf_field.section(x) if sampling == "all" else None
            if sampling == "plot":
                pi = selection["polygon_index"]
            else:
                owners = []
                for pi_candidate, polygon in enumerate(section.polygons, 1):
                    polygon_xy = np.asarray([(v.x,v.y) for v in polygon.vertices], dtype=float)
                    scale = max(1., float(np.abs(polygon_xy).max()))
                    if PolygonPath(polygon_xy).contains_point((y,z), radius=-1e-10*scale):
                        owners.append(pi_candidate)
                if len(owners) != 1:
                    raise ValueError(
                        f"Gauss point FEM element {fem.ids[ei]}, point {gi+1} at {(x,y,z)} "
                        f"has {len(owners)} CSF material-side owners {owners}; refine/align the FEM mesh"
                    )
                pi = owners[0]
            lookup = lookups[x]
            if lookup is None:
                strain = np.asarray(compiled.strain(x,y,z), dtype=float)
            else:
                strain = np.asarray(compiled.strain(x,y,z,domain_index=lookup[pi]), dtype=float)
            C = np.asarray(provider.matrix(x=x,domain_id=pi,y=y,z=z),dtype=float)
            if strain.shape != (6,) or C.shape != (6,6):
                raise ValueError("Invalid CUF strain or constitutive matrix at native Gauss point")
            sigma_cuf = C @ strain
            sigma_fem = fem.native_stresses[ei,gi]
            if not np.isfinite(sigma_cuf).all():
                raise ValueError("Non-finite CUF stress at Gauss point")
            rows.append({"element_id":int(fem.ids[ei]), "gauss_index":gi+1,
                         "polygon_index":pi,
                         "polygon_name":(selection["polygon_name"] if sampling == "plot"
                                         else section.polygons[pi-1].name),
                         "x":x, "y":y, "z":z, "x_over_L":(x-x0)/(x1-x0),
                         "stress_fem":sigma_fem, "stress_cuf":sigma_cuf,
                         "stress_difference":sigma_fem-sigma_cuf,
                         "strain_cuf":strain,
                         **({key:selection[key] for key in (
                             "point", "vertex_index", "target_y", "target_z", "transverse_offset")}
                            if sampling == "plot" else {})})
    return rows


def save_gauss_comparison(output_dir: Path, rows, dpi: int, *, no_plots: bool,
                          max_vertices_per_plot: int = 8):
    """Save exact native Gauss values; plot-mode draws vertex-associated traces."""
    output_dir.mkdir(parents=True, exist_ok=True)
    keys = ("element_id", "gauss_index", "polygon_index", "polygon_name",
            "x", "y", "z", "x_over_L")
    if rows and "point" in rows[0]:
        keys = (*keys, "point", "vertex_index", "target_y", "target_z",
                "transverse_offset")
    records = {key: np.asarray([r[key] for r in rows]) for key in keys}
    for col in ("stress_fem", "stress_cuf", "stress_difference", "strain_cuf"):
        records[col] = np.asarray([r[col] for r in rows],dtype=float)
    records["stress_components"] = np.asarray(
        ["sigma_xx", "sigma_yy", "sigma_zz", "tau_yz", "tau_xz", "tau_xy"])
    records["stress_fem_source"] = np.asarray("OpenSees native stdBrick Gauss stresses")
    records["stress_cuf_source"] = np.asarray("CUF strain times CSF constitutive matrix at the same point")
    path = output_dir / "sampled_gauss_native_comparison.npz"
    np.savez_compressed(path, **records)
    print(f"[ok] {path} ({len(rows)} native Gauss points)",flush=True)
    csv_path = output_dir / "sampled_gauss_native_comparison.csv"
    with csv_path.open("w", newline="") as out:
        writer = csv.writer(out)
        comps = list(records["stress_components"])
        writer.writerow(list(keys) + [f"fem_{c}" for c in comps]
                        + [f"cuf_{c}" for c in comps] + [f"fem_minus_cuf_{c}" for c in comps])
        for row in rows:
            writer.writerow([row[k] for k in keys] + list(row["stress_fem"])
                            + list(row["stress_cuf"]) + list(row["stress_difference"]))
    print(f"[ok] {csv_path}",flush=True)
    if no_plots:
        return
    # Native Gauss traces corresponding to the vertex panels from the boundary
    # visualizer; points are nearby *interior* Gauss positions, never the vertices.
    if rows and "point" in rows[0]:
        trace_ids = list(dict.fromkeys(row["point"] for row in rows))
        for comp_idx, comp in enumerate(records["stress_components"]):
            for page_start in range(0, len(trace_ids), max_vertices_per_plot):
                page_ids = trace_ids[page_start:page_start+max_vertices_per_plot]
                nrows = math.ceil(len(page_ids)/2)
                fig, axes = plt.subplots(nrows, 2, figsize=(13.4, 3.4*nrows),
                                         constrained_layout=True, sharex=True)
                for ax in np.ravel(axes)[len(page_ids):]:
                    ax.set_visible(False)
                for ax, point_id in zip(np.ravel(axes),page_ids):
                    selected = sorted((r for r in rows if r["point"]==point_id),
                                      key=lambda r: r["x_over_L"])
                    t = [r["x_over_L"] for r in selected]
                    ax.scatter(t,[r["stress_fem"][comp_idx] for r in selected],s=9,
                               label="OpenSees native Gauss",alpha=.8)
                    ax.scatter(t,[r["stress_cuf"][comp_idx] for r in selected],s=9,
                               label="CUF at same Gauss points",alpha=.8)
                    max_dist = max(r["transverse_offset"] for r in selected)
                    ax.set_title(f"{point_id.replace('_',' ')} (offset <= {max_dist:.3g})")
                    ax.grid(True,alpha=.25)
                    ax.legend(fontsize=7)
                fig.suptitle(f"{comp}: nearest native Gauss points to CSF plotted vertices")
                fig.supxlabel("s=(x-x0)/L (actual FEM Gauss stations)")
                fig.supylabel(comp)
                filename=(f"{comp}_along_gauss_part{1+page_start//max_vertices_per_plot:02d}.png"
                          if len(trace_ids)>max_vertices_per_plot else f"{comp}_along_gauss.png")
                fig.savefig(output_dir/filename,dpi=dpi)
                plt.close(fig)
        return
    polygon_ids = sorted(set(row["polygon_index"] for row in rows))
    for comp_idx, comp in enumerate(records["stress_components"]):
        ncols=2
        nrows=math.ceil(len(polygon_ids)/ncols)
        fig, axes=plt.subplots(nrows,ncols,figsize=(13,3.6*nrows),
                               constrained_layout=True,sharex=True)
        for ax in np.ravel(axes)[len(polygon_ids):]:
            ax.set_visible(False)
        for ax, pi in zip(np.ravel(axes),polygon_ids):
            chosen=[r for r in rows if r["polygon_index"]==pi]
            x=[r["x_over_L"] for r in chosen]
            fem=[r["stress_fem"][comp_idx] for r in chosen]
            cuf=[r["stress_cuf"][comp_idx] for r in chosen]
            ax.scatter(x,cuf,s=5,alpha=.4,label="CUF at FEM Gauss points")
            ax.scatter(x,fem,s=5,alpha=.4,label="OpenSees native Gauss stresses")
            ax.set_title(f"polygon {pi}: {chosen[0]['polygon_name']}")
            ax.grid(True,alpha=.25)
            ax.legend(fontsize=7)
        fig.suptitle(f"{comp}: exact Gauss point comparison (no averaging)")
        fig.supxlabel("s = (x - x0)/L")
        fig.supylabel(comp)
        fig.savefig(output_dir / f"{comp}_along_gauss.png",dpi=dpi)
        plt.close(fig)




def _clip_polygon_to_rectangle(vertices, bounds):
    """Clip a polygon against an axis-aligned rectangle in the Y-Z plane.

    Parameters
    ----------
    vertices : array-like, shape (n, 2)
        Polygon vertices as (y, z) pairs.
    bounds : tuple(float, float, float, float)
        Rectangle bounds (ymin, ymax, zmin, zmax).

    Returns
    -------
    np.ndarray, shape (m, 2)
        Vertices of the clipped polygon. Empty if the intersection has no area.
    """
    polygon = [(float(y), float(z)) for y, z in np.asarray(vertices, dtype=float)]
    ymin, ymax, zmin, zmax = map(float, bounds)
    if len(polygon) < 3:
        return np.empty((0, 2), dtype=float)
    a = np.asarray(polygon, dtype=float)
    if (float(a[:, 0].max()) <= ymin or float(a[:, 0].min()) >= ymax
            or float(a[:, 1].max()) <= zmin or float(a[:, 1].min()) >= zmax):
        return np.empty((0, 2), dtype=float)
    for axis, bound, sign in ((0, ymin, 1), (0, ymax, -1),
                              (1, zmin, 1), (1, zmax, -1)):
        if not polygon:
            return np.empty((0, 2), dtype=float)
        clipped = []
        previous = polygon[-1]
        prev_signed = sign * (previous[axis] - bound)
        for current in polygon:
            curr_signed = sign * (current[axis] - bound)
            curr_inside = curr_signed >= 0.0
            prev_inside = prev_signed >= 0.0
            if curr_inside != prev_inside:
                fraction = prev_signed / (prev_signed - curr_signed)
                clipped.append((
                    previous[0] + fraction * (current[0] - previous[0]),
                    previous[1] + fraction * (current[1] - previous[1]),
                ))
            if curr_inside:
                clipped.append(current)
            previous, prev_signed = current, curr_signed
        polygon = clipped
    if len(polygon) < 3:
        return np.empty((0, 2), dtype=float)
    p = np.asarray(polygon, dtype=float)
    scale = max(1., abs(ymax - ymin), abs(zmax - zmin), float(np.ptp(a[:, 0])), float(np.ptp(a[:, 1])))
    # Remove duplicate consecutive points introduced by clipping on aligned edges.
    keep = [0]
    tol = 64.0 * np.finfo(float).eps * scale
    for i in range(1, len(p)):
        if np.linalg.norm(p[i] - p[keep[-1]]) > tol:
            keep.append(i)
    p = p[keep]
    if len(p) >= 2 and np.linalg.norm(p[0] - p[-1]) <= tol:
        p = p[:-1]
    if len(p) < 3:
        return np.empty((0, 2), dtype=float)
    area2 = float(np.dot(p[:, 0], np.roll(p[:, 1], -1)) - np.dot(p[:, 1], np.roll(p[:, 0], -1)))
    area_tol = 64.0 * np.finfo(float).eps * scale**2
    if 0.5 * abs(area2) <= area_tol:
        return np.empty((0, 2), dtype=float)
    return p


def _polygon_area_centroid(vertices):
    """Return positive area and centroid of a nondegenerate planar polygon."""
    p = np.asarray(vertices, dtype=float)
    if p.ndim != 2 or p.shape[0] < 3 or p.shape[1] != 2:
        raise ValueError("Expected polygon vertices with shape (n, 2)")
    x = p[:, 0]
    y = p[:, 1]
    cross = x * np.roll(y, -1) - np.roll(x, -1) * y
    area2 = float(np.sum(cross))
    area = 0.5 * abs(area2)
    if area <= 0.0:
        raise ValueError("Degenerate polygon has zero area")
    centroid = np.array([
        np.sum((x + np.roll(x, -1)) * cross),
        np.sum((y + np.roll(y, -1)) * cross),
    ], dtype=float) / (3.0 * area2)
    return area, centroid


def _evaluate_cuf_state(field, provider, domain_lookup, domain_id: int, x: float, y: float, z: float):
    u = np.asarray(field(x, y, z), dtype=float)
    if domain_lookup is None:
        eps = np.asarray(field.strain(x, y, z), dtype=float)
    else:
        eps = np.asarray(field.strain(x, y, z, domain_index=domain_lookup[domain_id]), dtype=float)
    C = np.asarray(provider.matrix(x=x, domain_id=domain_id, y=y, z=z), dtype=float)
    if u.shape != (3,) or eps.shape != (6,) or C.shape != (6, 6):
        raise RuntimeError(f"Unexpected CUF field/material shape at x,y,z=({x:g},{y:g},{z:g})")
    sigma = C @ eps
    if not (np.isfinite(u).all() and np.isfinite(eps).all() and np.isfinite(sigma).all()):
        raise ValueError(f"Non-finite CUF value in polygon {domain_id} at ({x:g},{y:g},{z:g})")
    return u, eps, sigma


def _sample_polygon_cells(field, provider, domain_lookup, domain_id: int, x: float,
                          vertices, target_step: float, void_vertices=()):
    """Directly sample one CUF value per local polygon cell.

    The local grid is built from the polygon bounding box using an approximately
    uniform target step. Every cell whose intersection with the polygon has
    positive area is represented, and the CUF state is evaluated at the
    centroid of that clipped cell. No interpolation is used.
    """
    # Work with the existing polygon-rectangle clipping, without shapely.
    # The positive-area material cell is the exterior intersection minus
    # the zero-weight cavity intersections. No CUF evaluations occur in voids.
    from matplotlib.path import Path as PolygonPath
    exterior_path = PolygonPath(np.asarray(vertices, dtype=float))
    cavity_paths = [PolygonPath(np.asarray(v, dtype=float)) for v in void_vertices]
    local_voids = [np.asarray(v, dtype=float) for v in void_vertices]
    vertices = np.asarray(vertices, dtype=float)
    y_min, z_min = np.min(vertices, axis=0)
    y_max, z_max = np.max(vertices, axis=0)
    y_span = float(y_max - y_min)
    z_span = float(z_max - z_min)
    if y_span <= 0.0 or z_span <= 0.0:
        raise ValueError(f"Degenerate polygon {domain_id} bounding box")
    step = max(float(target_step), 64.0 * np.finfo(float).eps * max(1.0, y_span, z_span))
    ny = max(1, int(math.ceil(y_span / step)))
    nz = max(1, int(math.ceil(z_span / step)))
    y_edges = np.linspace(y_min, y_max, ny + 1)
    z_edges = np.linspace(z_min, z_max, nz + 1)
    mask = np.zeros((nz, ny), dtype=bool)
    sample_y = np.full((nz, ny), np.nan, dtype=float)
    sample_z = np.full((nz, ny), np.nan, dtype=float)
    displacement = np.full((nz, ny, 3), np.nan, dtype=float)
    strain = np.full((nz, ny, 6), np.nan, dtype=float)
    stress = np.full((nz, ny, 6), np.nan, dtype=float)
    for iz in range(nz):
        for iy in range(ny):
            rect = (y_edges[iy], y_edges[iy + 1], z_edges[iz], z_edges[iz + 1])
            clipped = _clip_polygon_to_rectangle(vertices, rect)
            if len(clipped) < 3:
                continue
            exterior_area, exterior_center = _polygon_area_centroid(clipped)
            # A clipped cavity must be subtracted only where it overlaps
            # the exterior. In CSF, cavities are nested inside the exterior.
            hole_area = 0.0
            hole_moment = np.zeros(2, dtype=float)
            for hole in local_voids:
                clipped_hole = _clip_polygon_to_rectangle(hole, rect)
                if len(clipped_hole) >= 3:
                    area, center = _polygon_area_centroid(clipped_hole)
                    hole_area += area
                    hole_moment += area * center
            physical_area = exterior_area - hole_area
            area_tol = 1.0e-12 * max(1.0, exterior_area)
            if physical_area <= area_tol:
                continue
            candidate = (exterior_area * exterior_center - hole_moment) / physical_area
            def is_material(point):
                return (exterior_path.contains_point(point) and
                        not any(path.contains_point(point) for path in cavity_paths))
            if not is_material(candidate):
                # The centroid of a disconnected or ring-like cell can lie
                # within a hole. Pick an actual material point instead.
                ya, yb, za, zb = rect
                candidate = None
                for resolution in (3, 7, 15):
                    for fz in (np.arange(resolution) + 0.5) / resolution:
                        for fy in (np.arange(resolution) + 0.5) / resolution:
                            point = (ya + fy*(yb-ya), za + fz*(zb-za))
                            if is_material(point):
                                candidate = point
                                break
                        if candidate is not None:
                            break
                    if candidate is not None:
                        break
                if candidate is None:
                    raise ValueError(f"Unable to select physical sample in polygon {domain_id} at x={x:g}")
            y, z = float(candidate[0]), float(candidate[1])
            u, eps, sigma = _evaluate_cuf_state(field, provider, domain_lookup, domain_id, x, y, z)
            mask[iz, iy] = True
            sample_y[iz, iy] = y
            sample_z[iz, iy] = z
            displacement[iz, iy] = u
            strain[iz, iy] = eps
            stress[iz, iy] = sigma
    if not np.any(mask):
        raise ValueError(f"No positive-area local cells inside CSF polygon {domain_id}")
    return {
        "domain_id": int(domain_id),
        "vertices": vertices,
        "y_edges": y_edges,
        "z_edges": z_edges,
        "mask": mask,
        "sample_y": sample_y,
        "sample_z": sample_z,
        "displacement": displacement,
        "strain": strain,
        "stress": stress,
    }


def _section_absolute_weights(section) -> tuple[float, ...]:
    """Read evaluated absolute carriers from a CSF Section, without inference.

    ``section`` must be the object returned by ``csf_field.section(x)``.
    CSF exposes ``weightabs`` separately from the algebraic ``weight`` used
    for section composition.  In particular, ``abs(polygon.weight)`` is NOT
    the absolute constitutive carrier.  No YAML access, endpoint queries,
    reconstructed laws, guessed defaults, or near-zero thresholds belong here.
    """
    weights = []
    for domain_id, polygon in enumerate(section.polygons, start=1):
        try:
            raw = polygon.weightabs
        except AttributeError as exc:
            raise ValueError(
                f"CSF polygon {domain_id} has no evaluated weightabs; "
                "supply a Section returned by csf_field.section(x)"
            ) from exc
        if raw is None:
            raise ValueError(
                f"CSF polygon {domain_id} has weightabs=None; "
                "an evaluated absolute carrier is required"
            )
        try:
            weightabs = float(raw)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(
                f"CSF polygon {domain_id} has invalid weightabs={raw!r}"
            ) from exc
        if not math.isfinite(weightabs) or weightabs < 0.0:
            raise ValueError(
                f"CSF polygon {domain_id} has invalid weightabs={weightabs!r}; "
                "expected a finite, nonnegative absolute carrier"
            )
        weights.append(weightabs)
    return tuple(weights)


def recover_transverse_fields(npz_path: Path, csf_yaml: Path, x: float, grid: int, vector_grid: int = 60):
    """Load the two models through their public APIs, then sample the section.

    The bridge owns CSF loading/validation and the constitutive provider.
    There is deliberately no second CSFReader, raw YAML parsing, or checkpoint
    decoding here.  Geometry and weights are obtained from its evaluated field.
    """
    from csf.cuf.csf_bridge import CSFCUFModelBridge
    from csf.cuf.solver.compiled_field import CompiledDisplacementField

    field = CompiledDisplacementField.load(npz_path)
    bridge = CSFCUFModelBridge.from_yaml(csf_yaml)
    return _sample_transverse_fields(field, bridge, x, grid, vector_grid)


def _sample_transverse_fields(field, bridge, x: float, grid: int, vector_grid: int = 60):
    """Sample already loaded CSF/CUF models using only their public APIs.

    The evaluated Section is authoritative for current geometry, names and
    absolute weights.  The bridge remains authoritative for constitutive
    matrices; the compiled CUF field remains authoritative for displacement
    and strain.  This routine performs no model-file I/O.
    """
    from matplotlib.path import Path as PolygonPath

    if grid < 2:
        raise ValueError("--transverse-grid must be >= 2")
    if vector_grid < 1:
        raise ValueError("--transverse-vector-grid must be >= 1")
    if not math.isfinite(x):
        raise ValueError("--transverse-x must be finite")

    provider = bridge.constitutive_provider
    csf_field = bridge.field
    start, end = map(float, bridge.longitudinal_domain())
    if end <= start:
        raise ValueError("CSF longitudinal end must exceed its start")
    if not start <= x <= end:
        raise ValueError(f"--transverse-x={x:g} outside CSF interval [{start:g}, {end:g}]")

    field_domain = np.asarray((field.x_start, field.x_end), dtype=float)
    csf_domain = np.asarray((start, end), dtype=float)
    scale = max(1.0, float(np.max(np.abs(np.r_[field_domain, csf_domain]))))
    atol = 64.0 * np.finfo(float).eps * scale
    if not np.allclose(field_domain, csf_domain, rtol=0.0, atol=atol):
        raise ValueError(
            "NPZ and CSF YAML longitudinal domains differ: "
            f"NPZ={tuple(field_domain)}, CSF={tuple(csf_domain)}"
        )

    section = csf_field.section(x)
    polygons = tuple(section.polygons)
    if not polygons:
        raise ValueError(f"No CSF polygons at x={x:g}")
    # Verify the checkpoint's mathematical domain geometry and identity at x.
    # Unlike the older v12.1 mapping, this also supports moving v5 domains.
    domain_lookups = validate_checkpoint_domain_lookups(field, csf_field, (start, x))
    domain_lookup = domain_lookups[float(x)]
    polygon_vertices = [
        np.asarray([(v.x, v.y) for v in polygon.vertices], dtype=float)
        for polygon in polygons
    ]
    if any(len(vertices) < 3 for vertices in polygon_vertices):
        raise ValueError("Transverse maps require polygons with at least three vertices")
    weightabs = _section_absolute_weights(section)
    is_void = tuple(value == 0.0 for value in weightabs)
    material_ids = [i for i, void in enumerate(is_void) if not void]
    void_vertices = [polygon_vertices[i] for i, void in enumerate(is_void) if void]
    if not material_ids:
        raise ValueError("No nonzero-weight material polygons in this CSF section")
    print(f"[transverse] section(x={x:g}) polygon.weightabs: "
          f"{list(weightabs)}", flush=True)
    print(f"[transverse] zero-absolute-weight void polygons: "
          f"{[i+1 for i, void in enumerate(is_void) if void]}", flush=True)
    vertices_all = np.concatenate(polygon_vertices, axis=0)
    y_min, z_min = np.min(vertices_all, axis=0)
    y_max, z_max = np.max(vertices_all, axis=0)
    if y_max <= y_min or z_max <= z_min:
        raise ValueError("CSF section has a degenerate transverse bounding box")

    target_step = max(float(y_max - y_min), float(z_max - z_min)) / float(grid)
    polygon_cells = [
        _sample_polygon_cells(field, provider, domain_lookup, pi, x, polygon_vertices[pi-1],
                              target_step, void_vertices=void_vertices)
        for pi in (i+1 for i in material_ids)
    ]

    # The SAME physical arrow spacing applies throughout the full Y-Z section;
    # polygons are only clipping/sampling domains, never independent scale units.
    section_span = max(float(y_max - y_min), float(z_max - z_min))
    vector_step = section_span / float(vector_grid)
    vector_cells = [
        _sample_polygon_cells(field, provider, domain_lookup, pi, x, polygon_vertices[pi-1],
                              vector_step, void_vertices=void_vertices)
        for pi in (i+1 for i in material_ids)
    ]

    y_edges = np.linspace(y_min, y_max, grid + 1)
    z_edges = np.linspace(z_min, z_max, grid + 1)
    y_centers = 0.5 * (y_edges[:-1] + y_edges[1:])
    z_centers = 0.5 * (z_edges[:-1] + z_edges[1:])
    yy, zz = np.meshgrid(y_centers, z_centers)
    transverse_points = np.column_stack((yy.ravel(), zz.ravel()))
    polygon_index = np.zeros((grid, grid), dtype=np.int32)
    displacement = np.full((grid, grid, 3), np.nan, dtype=float)
    strain = np.full((grid, grid, 6), np.nan, dtype=float)
    stress = np.full((grid, grid, 6), np.nan, dtype=float)

    # Exclude geometrical edges: do not accidentally select one-sided derivatives
    # at shared interfaces. Clip drawn cells back to the exact polygon outline.
    boundary_tol = 64.0 * np.finfo(float).eps * max(
        1.0, float(np.max(np.abs(vertices_all)))
    )
    void_mask = np.zeros((grid, grid), dtype=bool)
    for vertices in void_vertices:
        path = PolygonPath(np.vstack((vertices, vertices[0])), closed=True)
        void_mask |= path.contains_points(transverse_points, radius=boundary_tol).reshape(grid, grid)
    for pi in (i+1 for i in material_ids):
        vertices = polygon_vertices[pi-1]
        path = PolygonPath(np.vstack((vertices, vertices[0])), closed=True)
        inside = path.contains_points(transverse_points, radius=-boundary_tol).reshape(grid, grid)
        inside &= ~void_mask
        if np.any(inside & (polygon_index != 0)):
            raise ValueError(f"Overlapping CSF polygon interiors at x={x:g} (polygon {pi})")
        if not np.any(inside):
            # The legacy global-grid NPZ has no center in this thin polygon.
            # Its direct per-polygon samples still cover it in every plot.
            continue
        polygon_index[inside] = pi
        for iz, iy in np.argwhere(inside):
            y, z = float(y_centers[iy]), float(z_centers[iz])
            u, eps, sigma = _evaluate_cuf_state(field, provider, domain_lookup, pi, x, y, z)
            displacement[iz, iy] = u
            strain[iz, iy] = eps
            stress[iz, iy] = sigma

    return {
        "x": float(x),
        "x_over_L": float((x - start) / (end - start)),
        "y_edges": y_edges,
        "z_edges": z_edges,
        "polygon_index": polygon_index,
        "section_vertices": polygon_vertices,
        "void_vertices": void_vertices,
        "polygon_names": [str(p.name) for p in polygons],
        "polygon_weightabs": np.asarray(weightabs, dtype=float),
        "polygon_is_void": np.asarray(is_void, dtype=bool),
        "displacement": displacement,
        "strain": strain,
        "stress": stress,
        # Direct, independent field samples.  One global physical step controls
        # the arrows even when the section contains polygons of different sizes.
        "polygon_cells": polygon_cells,
        "vector_cells": vector_cells,
        "vector_grid": int(vector_grid),
        "vector_step": float(vector_step),
    }


def save_transverse_npz(path: Path, samples):
    """Save original global-grid samples and the direct plotted polygon samples."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # Keep legacy dense-array keys for existing NPZ consumers, and additionally
    # persist exact per-polygon evaluation points used by all current plots.
    polygons = samples.get("polygon_cells") or []
    extra = {}
    # Add authoritative section metadata without removing any legacy NPZ key.
    if "polygon_weightabs" in samples:
        extra["polygon_weightabs"] = np.asarray(samples["polygon_weightabs"], dtype=float)
        extra["polygon_is_void"] = np.asarray(samples["polygon_is_void"], dtype=bool)
    if polygons:
        extra.update({
            "polygon_sample_domain": np.concatenate([
                np.full(int(poly["mask"].sum()), poly["domain_id"], dtype=np.int32)
                for poly in polygons
            ]),
            "polygon_sample_y": np.concatenate([
                poly["sample_y"][poly["mask"]] for poly in polygons
            ]),
            "polygon_sample_z": np.concatenate([
                poly["sample_z"][poly["mask"]] for poly in polygons
            ]),
            "polygon_sample_displacement": np.concatenate([
                poly["displacement"][poly["mask"]] for poly in polygons
            ]),
            "polygon_sample_strain": np.concatenate([
                poly["strain"][poly["mask"]] for poly in polygons
            ]),
            "polygon_sample_stress": np.concatenate([
                poly["stress"][poly["mask"]] for poly in polygons
            ]),
        })
    vector_cells = samples.get("vector_cells") or []
    if vector_cells:
        extra.update({
            "vector_sample_domain": np.concatenate([
                np.full(int(poly["mask"].sum()), poly["domain_id"], dtype=np.int32)
                for poly in vector_cells
            ]),
            "vector_sample_y": np.concatenate([
                poly["sample_y"][poly["mask"]] for poly in vector_cells
            ]),
            "vector_sample_z": np.concatenate([
                poly["sample_z"][poly["mask"]] for poly in vector_cells
            ]),
            "vector_sample_tau_xy": np.concatenate([
                poly["stress"][:, :, 5][poly["mask"]] for poly in vector_cells
            ]),
            "vector_sample_tau_xz": np.concatenate([
                poly["stress"][:, :, 4][poly["mask"]] for poly in vector_cells
            ]),
            "vector_step": np.array(samples["vector_step"]),
        })
    np.savez_compressed(
        path,
        coordinate_system=np.array("CUF"),
        x=np.array(samples["x"]),
        x_over_L=np.array(samples["x_over_L"]),
        y_edges=samples["y_edges"],
        z_edges=samples["z_edges"],
        polygon_index=samples["polygon_index"],  # 0 means outside the section
        polygon_names=np.asarray(samples["polygon_names"]),
        displacement=samples["displacement"],
        strain=samples["strain"],
        stress=samples["stress"],
        **extra,
    )
    return path


def save_transverse_map(samples, curve, output_dir: Path, dpi: int):
    """Plot direct cell samples polygon by polygon, with no interpolation."""
    from matplotlib.patches import Polygon as PolygonPatch

    name, component, kind, colorbar_label, title = curve
    polygons = samples.get("polygon_cells")
    if polygons:
        finite_list = []
        for poly in polygons:
            values = poly[kind][:, :, component]
            finite = values[np.isfinite(values)]
            if finite.size:
                finite_list.append(finite)
        if not finite_list:
            raise ValueError(f"No finite transverse samples for {name}")
        finite_values = np.concatenate(finite_list)
        vmin, vmax = float(finite_values.min()), float(finite_values.max())
        fig, ax = plt.subplots(figsize=(8.0, 6.2), constrained_layout=True)
        try:
            mesh = None
            all_vertices = []
            for poly in polygons:
                vertices = np.asarray(poly["vertices"], dtype=float)
                all_vertices.append(vertices)
                values = np.ma.masked_where(~poly["mask"], poly[kind][:, :, component])
                mesh = ax.pcolormesh(
                    poly["y_edges"], poly["z_edges"], values,
                    cmap="coolwarm", vmin=vmin, vmax=vmax, shading="flat",
                    antialiased=False,
                )
                boundary = PolygonPatch(vertices, closed=True, fill=False, edgecolor="black", linewidth=0.8)
                ax.add_patch(boundary)
                mesh.set_clip_path(boundary)
            for void in samples.get("void_vertices", ()):
                ax.add_patch(PolygonPatch(void, closed=True, facecolor="white",
                                          edgecolor="black", linewidth=0.9, zorder=10))
            verts_all = np.concatenate(all_vertices, axis=0)
            fig.colorbar(mesh, ax=ax, label=colorbar_label)
            ax.set_xlim(float(np.min(verts_all[:, 0])), float(np.max(verts_all[:, 0])))
            ax.set_ylim(float(np.min(verts_all[:, 1])), float(np.max(verts_all[:, 1])))
            ax.set_aspect("equal", adjustable="box")
            ax.set_xlabel("y")
            ax.set_ylabel("z")
            ax.set_title(
                f"{title} on Y-Z section at x={samples['x']:g} "
                f"(s={samples['x_over_L']:.5g})"
            )
            output_dir.mkdir(parents=True, exist_ok=True)
            path = output_dir / f"{name}_transverse.png"
            fig.savefig(path, dpi=dpi, bbox_inches="tight", pad_inches=0.10)
            return path
        finally:
            plt.close(fig)

    # Fallback for legacy sample dictionaries without polygon_cells.
    values = samples[kind][:, :, component]
    y_edges, z_edges = samples["y_edges"], samples["z_edges"]
    polygon_index = samples["polygon_index"]
    finite_values = values[np.isfinite(values)]
    if not finite_values.size:
        raise ValueError(f"No finite transverse samples for {name}")
    vmin, vmax = float(finite_values.min()), float(finite_values.max())

    fig, ax = plt.subplots(figsize=(8.0, 6.2), constrained_layout=True)
    try:
        mesh = None
        for pi, vertices in enumerate(samples["section_vertices"], start=1):
            iz, iy = np.where(polygon_index == pi)
            if not len(iy):
                continue
            iz0, iz1 = int(iz.min()), int(iz.max()) + 1
            iy0, iy1 = int(iy.min()), int(iy.max()) + 1
            sl = (slice(iz0, iz1), slice(iy0, iy1))
            pixels = np.ma.masked_where(polygon_index[sl] != pi, values[sl])
            mesh = ax.pcolormesh(
                y_edges[iy0:iy1 + 1], z_edges[iz0:iz1 + 1], pixels,
                cmap="coolwarm", vmin=vmin, vmax=vmax, shading="flat",
                antialiased=False,
            )
            boundary = PolygonPatch(vertices, closed=True, fill=False, edgecolor="black", linewidth=0.8)
            ax.add_patch(boundary)
            mesh.set_clip_path(boundary)

        fig.colorbar(mesh, ax=ax, label=colorbar_label)
        ax.set_xlim(y_edges[0], y_edges[-1])
        ax.set_ylim(z_edges[0], z_edges[-1])
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("y")
        ax.set_ylabel("z")
        ax.set_title(
            f"{title} on Y-Z section at x={samples['x']:g} "
            f"(s={samples['x_over_L']:.5g})"
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{name}_transverse.png"
        fig.savefig(path, dpi=dpi, bbox_inches="tight", pad_inches=0.10)
        return path
    finally:
        plt.close(fig)


def save_shear_stress_vector_transverse(samples, output_dir: Path, dpi: int, arrow_grid: int = 60):
    """Display transverse shear traction with globally scaled direct CUF arrows.

    Every polygon receives the same *physical* vector sampling step, based on
    the entire section extent. For narrow polygons, their local cells still
    contain at least one row/column. Both color and vector samples come from
    direct analytical CUF field evaluations, with no interpolation.
    """
    from matplotlib.patches import Polygon as PolygonPatch

    if arrow_grid < 1:
        raise ValueError("--transverse-vector-grid must be >= 1")
    polygons = samples["polygon_cells"]
    vector_cells = samples["vector_cells"]
    if int(samples["vector_grid"]) != int(arrow_grid) or len(vector_cells) != len(polygons):
        raise ValueError("Arrow samples must match the requested vector grid and CSF polygons")

    vertices_all = np.concatenate([np.asarray(p["vertices"], dtype=float) for p in polygons])
    y_min, z_min = np.min(vertices_all, axis=0)
    y_max, z_max = np.max(vertices_all, axis=0)
    section_span = max(float(y_max - y_min), float(z_max - z_min))
    spacing = float(samples["vector_step"])
    # One physical size for all arrows; polygon subdivisions do not rescale them.
    arrow_length = min(0.70 * spacing, 0.032 * section_span)
    arrow_width = min(0.0022, 0.060 / float(arrow_grid))

    scalar_values = [np.hypot(poly["stress"][:, :, 5], poly["stress"][:, :, 4])
                     for poly in polygons]
    vector_values = [np.hypot(poly["stress"][:, :, 5], poly["stress"][:, :, 4])
                     for poly in vector_cells]
    finite = [a[np.isfinite(a)] for a in scalar_values + vector_values if np.isfinite(a).any()]
    if not finite:
        raise ValueError("No finite shear stress samples for the vector map")
    peak = max(float(np.max(a)) for a in finite)
    threshold = peak * 1.0e-6

    fig, ax = plt.subplots(figsize=(9.5, 6.4), constrained_layout=True)
    try:
        mesh = None
        count = 0
        for poly, vectors, magnitude in zip(polygons, vector_cells, scalar_values):
            vertices = np.asarray(poly["vertices"], dtype=float)
            pixels = np.ma.masked_where(~poly["mask"], magnitude)
            mesh = ax.pcolormesh(
                poly["y_edges"], poly["z_edges"], pixels,
                cmap="turbo", vmin=0.0, vmax=peak if peak > 0.0 else 1.0,
                shading="flat", antialiased=False, zorder=1,
            )
            boundary = PolygonPatch(
                vertices, closed=True, fill=False,
                edgecolor="black", linewidth=0.85, zorder=4,
            )
            ax.add_patch(boundary)
            mesh.set_clip_path(boundary)

            # The arrow grid is defined by physical dimensions of the WHOLE
            # section and independently sampled inside this polygon.
            v_stress = vectors["stress"]
            tau_y = v_stress[:, :, 5]
            tau_z = v_stress[:, :, 4]
            v_magnitude = np.hypot(tau_y, tau_z)
            selection = (vectors["mask"] & np.isfinite(tau_y) &
                         np.isfinite(tau_z) & (v_magnitude > threshold))
            rows, cols = np.where(selection)
            if len(rows):
                mod = v_magnitude[rows, cols]
                quiver = ax.quiver(
                    vectors["sample_y"][rows, cols],
                    vectors["sample_z"][rows, cols],
                    (tau_y[rows, cols] / mod) * arrow_length,
                    (tau_z[rows, cols] / mod) * arrow_length,
                    angles="xy", scale_units="xy", scale=1,
                    pivot="mid", color="black", edgecolors="white",
                    linewidths=0.12, width=arrow_width,
                    headwidth=3.8, headlength=5.0, headaxislength=4.4,
                    zorder=3,
                )
                quiver.set_clip_path(boundary)
                count += len(rows)

        for void in samples.get("void_vertices", ()):
            ax.add_patch(PolygonPatch(void, closed=True, facecolor="white",
                                      edgecolor="black", linewidth=0.9, zorder=10))
        fig.colorbar(mesh, ax=ax, label=r"$\sqrt{\tau_{xy}^2+\tau_{xz}^2}$")
        ax.set_xlim(float(y_min), float(y_max))
        ax.set_ylim(float(z_min), float(z_max))
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("y")
        ax.set_ylabel("z")
        ax.set_title(
            f"Vectorial shear stress distribution at x={samples['x']:g} "
            f"(s={samples['x_over_L']:.5g})"
        )
        if peak == 0:
            ax.text(0.5, 0.98, "Zero shear stress: no directions to display",
                    transform=ax.transAxes, ha="center", va="top", fontsize=8)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / "shear_stress_vector_transverse.png"
        fig.savefig(path, dpi=dpi, bbox_inches="tight", pad_inches=0.10)
        print(
            f"[transverse] shear vector arrows={count}; "
            f"global vector step={spacing:g}; arrow length={arrow_length:g}; "
            f"output={path}", flush=True,
        )
        return path
    finally:
        plt.close(fig)


def run_transverse_mode(args, checkpoints: list[Path], output_root: Path):
    """CUF-only transverse section maps; do not run the longitudinal plot loop."""
    if args.transverse_grid < 2:
        raise ValueError("--transverse-grid must be >= 2")
    if args.transverse_vector_grid < 1:
        raise ValueError("--transverse-vector-grid must be >= 1")
    if not math.isfinite(args.transverse_x):
        raise ValueError("--transverse-x must be finite")
    if (args.fem3d is not None or args.fem_stress_from_csf
            or args.inward_offset is not None or args.csv is not None):
        raise ValueError(
            "--transverse-x is CUF-only and cannot be combined with "
            "--fem3d, --fem-stress-from-csf, --inward-offset or --csv"
        )

    x_tag = f"{args.transverse_x:.12g}".replace("-", "m").replace("+", "").replace(".", "p")
    for checkpoint in checkpoints:
        samples = recover_transverse_fields(
            checkpoint, args.csf_yaml, args.transverse_x, args.transverse_grid,
            vector_grid=args.transverse_vector_grid,
        )
        case_output_dir = (
            output_root / checkpoint_output_name(checkpoint) / f"transverse_x_{x_tag}"
        )
        color_evaluations = sum(int(poly["mask"].sum()) for poly in samples["polygon_cells"])
        vector_evaluations = sum(int(poly["mask"].sum()) for poly in samples["vector_cells"])
        print(
            f"[transverse] x={samples['x']:g}; "
            f"section grid={args.transverse_grid}; vector grid={args.transverse_vector_grid}; "
            f"direct CUF color evaluations={color_evaluations}; "
            f"direct CUF vector evaluations={vector_evaluations}", flush=True
        )
        sampled_path = save_transverse_npz(
            case_output_dir / "sampled_transverse_fields.npz", samples
        )
        print(f"[ok] {sampled_path}", flush=True)
        if not args.no_plots:
            for curve in CURVES:
                path = save_transverse_map(samples, curve, case_output_dir, args.dpi)
                print(f"[ok] {path}", flush=True)
            save_shear_stress_vector_transverse(
                samples, case_output_dir, args.dpi, args.transverse_vector_grid
            )
        print(f"[transverse] output directory: {case_output_dir}", flush=True)


def build_parser():
    parser = argparse.ArgumentParser(
        description=("Compare CSF-CUF with native OpenSees stdBrick FEM3D results. "
                     "Boundary stresses are reconstructed at polygon vertices; "
                     "Gauss stresses are compared at original integration points."),
        epilog=("EXAMPLES:\n"
                "  Boundary, element material: --stress-mode boundary --fem-stress-from-element\n"
                "  Boundary, CSF material:     --stress-mode boundary --fem-stress-from-csf\n"
                "  Gauss plots (fast):         --stress-mode gauss --gauss-sampling plot --points 201\n"
                "  Exhaustive Gauss audit:     --stress-mode gauss --gauss-sampling all\n"
                "  Both comparisons:           --stress-mode both --fem-stress-from-element\n"
                "  Export without PNGs:        --no-plots\n"
                "Gauss mode requires an updated stdBrick FEM NPZ containing "
                "gauss_stresses_opensees and physical Gauss point coordinates. "
                "All geometry, axes, loads, units and material regions must match."),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    inputs = parser.add_argument_group("input files")
    inputs.add_argument("--csf-yaml",type=Path,required=True,
                        help="Six-polygon (or other matching) CSF section YAML used by the CUF checkpoint.")
    inputs.add_argument("--cuf-output-root",type=Path,default=Path("output"),
                        help="Directory scanned recursively for *.cuf.npz (default: ./output).")
    inputs.add_argument("--checkpoint",type=Path,default=None,
                        help="Single CUF .cuf.npz checkpoint; overrides --cuf-output-root scan.")
    inputs.add_argument("--fem3d",type=Path,default=None,
                        help="Native stdBrick FEM3D NPZ with H8 mesh/displacements; for Gauss mode it must also contain OpenSees native stresses.")
    methods = parser.add_argument_group("comparison methods")
    methods.add_argument("--stress-mode",choices=("auto","boundary","gauss","both"),default="auto",
                         help=("auto (default): both if --fem3d has native Gauss stresses, else boundary. "
                               "boundary: sampled CSF polygon vertices; gauss: actual OpenSees integration points; "
                               "both: separate boundary and Gauss outputs. gauss/both require --fem3d with native Gauss stresses."))
    source = methods.add_mutually_exclusive_group()
    source.add_argument("--fem-stress-from-csf",action="store_true",
                        help="Boundary only: FEM H8 strains times continuously varying CSF constitutive matrix AT EACH VERTEX. Different from the slice-midpoint material assigned to each OpenSees element.")
    source.add_argument("--fem-stress-from-element",action="store_true",
                        help="Boundary only: FEM H8 strains times the exact E/G/nu assigned to the containing OpenSees element (piecewise constant per longitudinal FEM slice). Default when element material metadata exists.")
    methods.add_argument("--gauss-sampling", choices=("plot", "all"), default="plot",
                         help=("plot (default): evaluate CUF only at the nearest true FEM Gauss point "
                               "INSIDE EACH POLYGON for each selected vertex trace and requested x-station. "
                               "This does NOT extrapolate native FEM stresses to the vertex; "
                               "the distance from each vertex is exported. "
                               "all: compare every native Gauss point (very slow and memory intensive)."))
    transverse_args = parser.add_argument_group("CUF-only transverse section maps")
    transverse_args.add_argument(
        "--transverse-x", type=float, default=None,
        help="Physical longitudinal x for direct-sampled Y-Z section maps; replaces comparisons",
    )
    transverse_args.add_argument(
        "--transverse-grid", type=int, default=120,
        help="Approximate cells across the largest section dimension for direct transverse fields (default: 120)",
    )
    transverse_args.add_argument(
        "--transverse-vector-grid", type=int, default=60,
        help="Approximate arrows along the longest side of the complete section (default: 60); consistent physical spacing and arrow length",
    )
    sampling = parser.add_argument_group("boundary and targeted Gauss plotting")
    sampling.add_argument("--points",type=int,default=201,
                          help="Boundary: number of vertex x-stations including ends. "
                               "Gauss plot: target x-stations snapped to existing FEM Gauss x-planes (default: 201).")
    sampling.add_argument("--vertices",choices=("unique","all"),default="all",
                          help="all (default): retain each polygon-side vertex; unique: merge coincident points (not recommended for interface stresses).")
    sampling.add_argument("--inward-offset",type=float,default=None,
                          help="Also recover a point this distance inside each polygon vertex, in native section units; boundary results are retained.")
    outputs = parser.add_argument_group("outputs")
    outputs.add_argument("--output-dir",type=Path,default=Path("strain_stress_boundary"),
                         help="Root directory for per-checkpoint NPZ, CSV and PNG outputs (default: ./strain_stress_boundary).")
    outputs.add_argument("--csv",type=Path,default=None,
                         help="Additional optional CSV path for CUF boundary samples; Gauss CSV is always saved in Gauss mode.")
    outputs.add_argument("--no-plots",action="store_true",
                         help="Save numerical NPZ/CSV samples only; skip every PNG figure (useful to test the pipeline).")
    outputs.add_argument("--dpi",type=int,default=220,help="Resolution of PNG plots (default: 220).")
    outputs.add_argument("--max-vertices-per-plot",type=int,default=8,
                         help="Maximum polygon vertex panels per boundary PNG page (default: 8).")
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
    print(f"[visualizer] v14.2.7: {Path(__file__).resolve()}", flush=True)
    if args.max_vertices_per_plot < 1 or args.dpi < 1 or args.points < 2:
        raise ValueError("--points must be >=2 and --dpi / --max-vertices-per-plot >=1")
    if args.inward_offset is not None and (not math.isfinite(args.inward_offset) or args.inward_offset <= 0):
        raise ValueError("--inward-offset requires a strictly positive finite distance")
    if (args.fem_stress_from_csf or args.fem_stress_from_element) and args.fem3d is None:
        raise ValueError("--fem-stress-from-* requires --fem3d")
    if args.transverse_x is not None:
        checkpoints = discover_checkpoints(args.cuf_output_root, args.checkpoint)
        run_transverse_mode(args, checkpoints, args.output_dir.expanduser().resolve())
        return
    fem = FEM3DH8(args.fem3d) if args.fem3d is not None else None
    mode = args.stress_mode
    if mode == "auto":
        mode = "both" if fem is not None and fem.native_stresses is not None else "boundary"
    if mode in ("gauss", "both") and (fem is None or fem.native_stresses is None):
        raise ValueError(f"--stress-mode {mode} requires --fem3d with native Gauss stresses (rerun updated stdBrick FEM solver)")
    if mode == "gauss" and (args.fem_stress_from_csf or args.fem_stress_from_element or args.inward_offset is not None):
        raise ValueError("--fem-stress-from-* and --inward-offset apply only to boundary/both, not gauss-only mode")
    if args.fem_stress_from_element:
        source = "element"
    elif args.fem_stress_from_csf:
        source = "csf"
    elif fem is not None and fem.element_E is not None:
        source = "element"
    else:
        source = "none"
    if mode in ("boundary","both") and source == "element" and (fem is None or fem.element_E is None):
        raise ValueError("--fem-stress-from-element requires FEM NPZ element_E, element_G and element_nu metadata")
    print(f"[visualizer] stress-mode={mode}; boundary FEM stress material={source}; "
          f"gauss-sampling={args.gauss_sampling}")
    result = None
    provider = None
    if fem is not None and mode in ("boundary", "both"):
        from csf.io.csf_reader import CSFReader
        from csf.io.csf_issues import CSFIssues
        result=CSFReader().read_file(str(args.csf_yaml))
        if not result.ok or result.field is None:
            raise ValueError(CSFIssues.format_report(result.issues))
        if source == "csf":
            from csf.cuf.csf_bridge import CSFCUFModelBridge
            provider = CSFCUFModelBridge.from_yaml(args.csf_yaml).constitutive_provider
    checkpoints = discover_checkpoints(args.cuf_output_root, args.checkpoint)
    output_root=args.output_dir.expanduser().resolve()
    for checkpoint in checkpoints:
        case_dir=output_root/checkpoint_output_name(checkpoint)
        case_dir.mkdir(parents=True,exist_ok=True)
        if mode in ("boundary","both"):
            if args.inward_offset is None:
                ids, rows = recover_boundary_fields(checkpoint,args.csf_yaml,points=args.points,vertices=args.vertices)
                inward_rows=None
            else:
                ids, rows, inward_rows = recover_boundary_and_inward_fields(
                    checkpoint,args.csf_yaml,points=args.points,vertices=args.vertices,
                    inward_offset=args.inward_offset)
            save_npz(case_dir/"sampled_boundary_fields.npz",rows)
            fem_rows = None
            fem_inward_rows = None
            if fem is not None:
                fem_rows = recover_fem_boundary(fem,rows,result.field,provider,stress_source=source)
                save_npz(case_dir/"sampled_fem3d_boundary_fields.npz",fem_rows)
                save_csv(case_dir/"sampled_fem3d_boundary_fields.csv",fem_rows)
                print(f"[ok] boundary FEM values: {len(fem_rows)} one-sided element samples")
                if inward_rows is not None:
                    fem_inward_rows=recover_fem_boundary(fem,inward_rows,result.field,provider,stress_source=source)
                    tag=offset_tag(args.inward_offset)
                    save_npz(case_dir/f"sampled_fem3d_boundary_fields_inward_{tag}.npz",fem_inward_rows)
                    save_csv(case_dir/f"sampled_fem3d_boundary_fields_inward_{tag}.csv",fem_inward_rows)
            if inward_rows is not None:
                tag=offset_tag(args.inward_offset)
                save_npz(case_dir/f"sampled_boundary_fields_inward_{tag}.npz",inward_rows)
            if not args.no_plots:
                page_size=args.max_vertices_per_plot
                pages=[ids[i:i+page_size] for i in range(0,len(ids),page_size)]
                for curve in CURVES:
                    for j, page in enumerate(pages,1):
                        suffix=f"_part{j:02d}" if len(pages)>1 else ""
                        save_curve_plot(page,rows,curve,case_dir,args.dpi,fem_rows,source!="none",filename_suffix=suffix)
                        if inward_rows is not None:
                            save_curve_plot(page,inward_rows,curve,case_dir,args.dpi,
                                            fem_inward_rows,source!="none",
                                            filename_suffix=f"_inward_{tag}{suffix}",
                                            location_title=f"CSF polygon inward points (offset={args.inward_offset:g})")
            if args.csv is not None:
                csv_root=args.csv.expanduser().resolve()
                if len(checkpoints)==1 and csv_root.suffix.lower()==".csv":
                    csv_path=csv_root
                else:
                    csv_root.mkdir(parents=True,exist_ok=True)
                    csv_path=csv_root/f"{checkpoint_output_name(checkpoint)}.csv"
                save_csv(csv_path,rows)
            print(f"[ok] boundary results: {case_dir}",flush=True)
        if mode in ("gauss", "both"):
            gauss_rows=recover_gauss_native_comparison(
                fem,checkpoint,args.csf_yaml,points=args.points,
                vertices=args.vertices,sampling=args.gauss_sampling)
            save_gauss_comparison(case_dir/"gauss",gauss_rows,args.dpi,
                                  no_plots=args.no_plots,
                                  max_vertices_per_plot=args.max_vertices_per_plot)
    print(f"[ok] comparisons completed: {output_root}",flush=True)


if __name__ == "__main__":
    main()
