"""
Bridge between CSF and sectionproperties.

This tool uses sectionproperties as the finite-element-based section analysis
backend where applicable.

sectionproperties:
https://github.com/robbievanleeuwen/section-properties
License: MIT


This module exposes a compact but non-trivial topology bridge between CSF and
sectionproperties. The important point is that the bridge does *not* rebuild a
section by hand as one outer contour plus a flat list of holes. Instead, it
transfers the CSF nesting structure node by node.

Supported input modes
---------------------
1. Legacy text mode: parse one or more ``## GEOMETRY EXPORT ##`` blocks.
2. YAML mode: load a CSF model, sample ``field.section(z)``, read direct
   container topology from the field, and build the sectionproperties input.

Core bridge policy
------------------
- Every CSF polygon node contributes its own *local domain*.
- A node local domain is the node support region minus the outer envelopes of
  its direct children.
- Positive-weight nodes become active sectionproperties regions.
- Zero-weight nodes are still topologically important: their local domains are
  treated as explicit void candidates when hole seeds are computed.

Why this matters
----------------
This policy preserves general nesting for homogenized geometric properties and
fixes an important failure mode: a zero-weight void may disappear from the SP
view when it touches another region exactly on the boundary, especially in deep
 nested topologies. The bridge therefore computes local domains for *all* nodes,
not only for active ones.

"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml
from shapely.geometry import GeometryCollection as ShapelyGeometryCollection
from shapely.geometry import Polygon as ShapelyPolygon
from shapely.geometry import MultiPolygon as ShapelyMultiPolygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from sectionproperties.analysis import Section
from sectionproperties.pre import CompoundGeometry, Geometry

try:
    from sectionproperties.pre import Material
except Exception:  # pragma: no cover
    from sectionproperties.pre.pre import Material  # type: ignore

from csf.io.csf_reader import CSFReader
from csf.io.csf_rough_validator import validate_text


TOKEN_CELL = "@cell"
TOKEN_CLOSED = "@closed"
TOKEN_WALL = "@wall"


@dataclass(frozen=True)
class Row:
    """One CSV geometry row from a CSF export block."""

    idx_polygon: int
    idx_container: Optional[int]
    s0_name: str
    s1_name: str
    w: Optional[float]
    vertex_i: int
    x: float
    y: float


@dataclass(frozen=True)
class PolygonInput:
    """Minimal polygon payload consumed by the sectionproperties backend."""

    idx_polygon: int
    idx_container: Optional[int]
    name: str
    w: float
    is_cell: bool
    vertices: List[Tuple[float, float]]


@dataclass(frozen=True)
class NodeShape:
    """Cached geometric payload for one CSF polygon node."""

    support_region: ShapelyPolygon
    outer_envelope: ShapelyPolygon


# -----------------------------------------------------------------------------
# Generic helpers
# -----------------------------------------------------------------------------


def _parse_optional_int(s: str) -> Optional[int]:
    s = (s or "").strip()
    if s == "":
        return None
    return int(s)



def _parse_optional_float(s: str) -> Optional[float]:
    s = (s or "").strip()
    if s == "":
        return None
    return float(s)



def strip_wall_cell_suffix(name: str) -> str:
    """
    Remove the first occurrence of '@cell', '@wall', or '@closed'
    and everything after it.
    """
    if not name:
        return name

    low = name.lower()
    idxs = [
        i
        for i in (
            low.find(TOKEN_CELL),
            low.find(TOKEN_WALL),
            low.find(TOKEN_CLOSED),
        )
        if i >= 0
    ]
    if not idxs:
        return name

    return name[: min(idxs)]



def _name_has_cell_tag(name: str) -> bool:
    low = (name or "").lower()
    return (TOKEN_CELL in low) or (TOKEN_CLOSED in low)


# -----------------------------------------------------------------------------
# Legacy text mode
# -----------------------------------------------------------------------------


def _read_geometry_export_blocks(text: str) -> Dict[float, List[Row]]:
    """Return {z_value: [rows]} for each geometry export block found in the text."""
    lines = text.splitlines()
    blocks: Dict[float, List[Row]] = {}

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line != "## GEOMETRY EXPORT ##":
            i += 1
            continue

        z_value: Optional[float] = None
        j = i + 1
        while j < len(lines):
            s = lines[j].strip()
            if s.startswith("# z="):
                z_value = float(s.split("=", 1)[1].strip())
                j += 1
                break
            j += 1

        if z_value is None:
            raise ValueError("Found '## GEOMETRY EXPORT ##' but no '# z=...' line.")

        rows: List[Row] = []
        while j < len(lines):
            raw = lines[j]
            s = raw.strip()

            if s == "" or s.startswith("### ") or s == "## GEOMETRY EXPORT ##":
                break

            if s.startswith("#"):
                j += 1
                continue

            rec = next(csv.reader([raw]))
            if not rec:
                j += 1
                continue

            if rec[0].strip().lower() == "idx_polygon":
                j += 1
                continue

            if len(rec) < 8:
                raise ValueError(
                    f"z={z_value}: malformed CSV row (expected at least 8 fields): {rec!r}"
                )

            rows.append(
                Row(
                    idx_polygon=int(rec[0]),
                    idx_container=_parse_optional_int(rec[1]),
                    s0_name=(rec[2] or "").strip(),
                    s1_name=(rec[3] or "").strip(),
                    w=_parse_optional_float(rec[4]),
                    vertex_i=int(rec[5]),
                    x=float(rec[6]),
                    y=float(rec[7]),
                )
            )
            j += 1

        blocks[z_value] = rows
        i = j

    if not blocks:
        raise ValueError("No '## GEOMETRY EXPORT ##' blocks found.")

    return blocks



def _group_rows_by_polygon(rows: Iterable[Row]) -> Dict[int, List[Row]]:
    grouped: Dict[int, List[Row]] = {}
    for r in rows:
        grouped.setdefault(r.idx_polygon, []).append(r)
    return grouped



def _rows_to_polygon_inputs(rows: List[Row]) -> Dict[int, PolygonInput]:
    """Convert text-export rows to polygon inputs."""
    grouped = _group_rows_by_polygon(rows)
    result: Dict[int, PolygonInput] = {}

    for idx_polygon, group in grouped.items():
        group_sorted = sorted(group, key=lambda r: r.vertex_i)
        idx_container = group_sorted[0].idx_container

        s0_name = group_sorted[0].s0_name
        s1_name = group_sorted[0].s1_name
        joined_name = s0_name or s1_name

        if group_sorted[0].w is None:
            raise ValueError(f"idx_polygon={idx_polygon}: missing w value.")
        w = float(group_sorted[0].w)

        for r in group_sorted[1:]:
            if r.idx_container != idx_container:
                raise ValueError(
                    f"idx_polygon={idx_polygon}: inconsistent idx_container "
                    f"{idx_container!r} vs {r.idx_container!r}"
                )
            if r.w is None:
                raise ValueError(f"idx_polygon={idx_polygon}: missing w value.")
            if float(r.w) != w:
                raise ValueError(
                    f"idx_polygon={idx_polygon}: inconsistent w {w!r} vs {float(r.w)!r}"
                )

        vertices = [(r.x, r.y) for r in group_sorted]
        is_cell = _name_has_cell_tag(s0_name) or _name_has_cell_tag(s1_name)

        result[idx_polygon] = PolygonInput(
            idx_polygon=idx_polygon,
            idx_container=idx_container,
            name=joined_name,
            w=w,
            is_cell=is_cell,
            vertices=vertices,
        )

    return result



def _select_z_block(blocks: Dict[float, List[Row]], requested_z: Optional[float]) -> Tuple[float, List[Row]]:
    """Select one z block from legacy geometry-export text."""
    z_values = sorted(blocks.keys())
    if requested_z is None:
        z = z_values[0]
        return z, blocks[z]

    if requested_z not in blocks:
        raise SystemExit(f"Requested z={requested_z} not found. Available: {z_values}")

    return requested_z, blocks[requested_z]


# -----------------------------------------------------------------------------
# YAML mode
# -----------------------------------------------------------------------------


def _format_text_block(header: str, lines: List[str]) -> str:
    """Join a header and a list of diagnostic lines into one printable block."""
    out = [header]
    out.extend(str(line) for line in lines)
    return "\n".join(out)



def _format_reader_issues(issues: List[Any], header: str) -> str:
    """Format CSFReader issues into a readable multi-line message."""
    lines: List[str] = [header]

    for issue in issues:
        severity = str(getattr(issue, "severity", "ERROR"))
        code = getattr(issue, "code", None)
        path = getattr(issue, "path", None)
        message = getattr(issue, "message", str(issue))
        hint = getattr(issue, "hint", None)
        context = getattr(issue, "context", None)

        prefix = f"[{severity}]"
        if code:
            prefix += f" {code}"
        if path:
            prefix += f" {path}"

        lines.append(f"{prefix}: {message}")

        if hint:
            lines.append(f"Hint: {hint}")

        if isinstance(context, dict):
            snippet = context.get("snippet")
            if snippet:
                lines.append(str(snippet))

    return "\n".join(lines)



def _make_yaml_snippet(text: str, line_no: int, col_no: Optional[int] = None) -> str:
    """Build a compact YAML snippet around a specific location."""
    lines = text.splitlines()
    if not lines:
        return "<empty input>"

    lo = max(1, line_no - 2)
    hi = min(len(lines), line_no + 2)

    out: List[str] = []
    for ln in range(lo, hi + 1):
        prefix = ">>" if ln == line_no else "  "
        out.append(f"{prefix} {ln:4d} | {lines[ln - 1]}")
        if ln == line_no and col_no is not None and col_no > 0:
            caret_pos = len(f"{prefix} {ln:4d} | ") + (col_no - 1)
            out.append(" " * caret_pos + "^")
    return "\n".join(out)



def _load_run_config_yaml(run_config_path: Path) -> Dict[str, Any]:
    """Read and parse the run-config YAML with clear parser errors."""
    try:
        text = run_config_path.read_text(encoding="utf-8")
    except Exception as exc:
        raise SystemExit(
            f"Cannot read run-config YAML '{run_config_path}': {exc}"
        ) from exc

    try:
        data = yaml.safe_load(text)
    except Exception as exc:
        mark = getattr(exc, "problem_mark", None)
        if mark is not None:
            line_no = int(getattr(mark, "line", 0)) + 1
            col_no = int(getattr(mark, "column", 0)) + 1
            snippet = _make_yaml_snippet(text, line_no, col_no)
            raise SystemExit(
                f"Run-config YAML parse failed for '{run_config_path}': {exc}\n{snippet}"
            ) from exc

        raise SystemExit(
            f"Run-config YAML parse failed for '{run_config_path}': {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise SystemExit(
            f"Run-config YAML '{run_config_path}' must contain a mapping at the root."
        )

    return data



def _load_field_from_yaml(yaml_path: Path):
    """Rough-validate first, then load the CSF field through the official reader."""
    try:
        text = yaml_path.read_text(encoding="utf-8")
    except Exception as exc:
        raise SystemExit(f"Cannot read CSF YAML '{yaml_path}': {exc}") from exc

    ok, report_lines = validate_text(text, source=str(yaml_path))
    if not ok:
        raise SystemExit(
            _format_text_block(
                f"Prevalidation failed for '{yaml_path}':",
                report_lines,
            )
        )

    try:
        res = CSFReader().read_file(str(yaml_path))
    except Exception as exc:
        raise SystemExit(
            f"Unexpected failure while reading CSF YAML '{yaml_path}': {exc}"
        ) from exc

    issues = list(getattr(res, "issues", []) or [])
    if not getattr(res, "ok", False) or getattr(res, "field", None) is None:
        if issues:
            raise SystemExit(
                _format_reader_issues(
                    issues,
                    f"CSFReader failed for '{yaml_path}':",
                )
            )
        raise SystemExit(f"Could not load CSF model from '{yaml_path}'.")

    return res.field



def _load_station_set(run_config_path: Path, station_set_name: str) -> List[float]:
    """Load one station set from a small YAML run-config file."""
    data = _load_run_config_yaml(run_config_path)

    station_sets = data.get("station_sets")
    if not isinstance(station_sets, dict) or not station_sets:
        raise SystemExit(
            f"Run-config YAML '{run_config_path}' must contain a non-empty 'station_sets:' mapping."
        )

    if not isinstance(station_set_name, str) or not station_set_name.strip():
        raise SystemExit("A non-empty --station-set name is required.")

    if station_set_name not in station_sets:
        raise SystemExit(
            f"Station set '{station_set_name}' not found in '{run_config_path}'. "
            f"Available: {sorted(station_sets.keys())}"
        )

    z_values = station_sets[station_set_name]
    if not isinstance(z_values, list) or not z_values:
        raise SystemExit(
            f"station_sets.{station_set_name} must be a non-empty YAML list of numbers."
        )

    out: List[float] = []
    for i, z in enumerate(z_values):
        if type(z) not in (int, float):
            raise SystemExit(
                f"station_sets.{station_set_name}[{i}] must be numeric, got {z!r} "
                f"({type(z).__name__})."
            )
        out.append(float(z))

    return out



def _polygon_inputs_from_field(field, z: float) -> Dict[int, PolygonInput]:
    """
    Build polygon inputs directly from ``field.section(z)``.

    IMPORTANT:
    This function is intentionally topology-driven. It does not try to infer
    holes from polygon orientation or from boolean operations. Instead it reads:
    - the sampled polygon coordinates,
    - the sampled absolute weights,
    - the direct container relation from the CSF field.

    The rest of the bridge assumes that the polygon ordering used by
    ``field.section(z)`` and the indices referenced by
    ``field.build_direct_children_map(z)`` are consistent.
    """
    sec = field.section(float(z))
    children_map = field.build_direct_children_map(float(z))

    parent_of: Dict[int, Optional[int]] = {}
    for parent_idx, child_idx_list in children_map.items():
        for child_idx in child_idx_list:
            parent_of[child_idx] = parent_idx

    out: Dict[int, PolygonInput] = {}
    for idx, poly in enumerate(sec.polygons):
        if not hasattr(poly, "weightabs"):
            raise ValueError(
                f"idx_polygon={idx}: sampled polygon has no 'weightabs' attribute."
            )

        name = str(getattr(poly, "name", f"poly_{idx}"))
        vertices = [(float(v.x), float(v.y)) for v in poly.vertices]
        w_abs = float(poly.weightabs)

        out[idx] = PolygonInput(
            idx_polygon=idx,
            idx_container=parent_of.get(idx),
            name=name,
            w=w_abs,
            is_cell=_name_has_cell_tag(name),
            vertices=vertices,
        )

    return out


# -----------------------------------------------------------------------------
# sectionproperties backend
# -----------------------------------------------------------------------------


def _make_polygon(coords: List[Tuple[float, float]], label: str) -> ShapelyPolygon:
    """Build a shapely polygon without silently fixing invalid geometry."""
    poly = ShapelyPolygon(coords)

    if poly.is_empty:
        raise ValueError(f"{label}: shapely polygon is empty.")
    if not poly.is_valid:
        raise ValueError(
            f"{label}: shapely polygon is invalid "
            f"(likely self-intersection or malformed ring)."
        )
    if poly.geom_type != "Polygon":
        raise ValueError(f"{label}: expected Polygon, got {poly.geom_type}.")

    return poly



def _split_cell_polygon(vertices: List[Tuple[float, float]], label: str) -> Tuple[
    List[Tuple[float, float]],
    List[Tuple[float, float]],
]:
    """
    Split a slit-encoded @cell polygon into OUTER and INNER loops.

    Policy:
    - OUTER loop is detected by the first repeated occurrence of the first vertex.
    - INNER loop is the remaining tail after OUTER closure.
    - INNER explicit repeated endpoint is optional.
    """
    if len(vertices) < 8:
        raise ValueError(f"{label}: too few vertices for a slit-encoded @cell polygon.")

    first = vertices[0]
    i_outer_end: Optional[int] = None
    for i in range(1, len(vertices)):
        if vertices[i] == first:
            i_outer_end = i
            break

    if i_outer_end is None or i_outer_end < 3:
        raise ValueError(f"{label}: missing repeated first vertex for OUTER closure.")

    outer = vertices[:i_outer_end]
    inner = vertices[i_outer_end + 1 :]

    if len(inner) < 3:
        raise ValueError(f"{label}: insufficient INNER loop vertices.")

    if inner[0] == inner[-1]:
        inner = inner[:-1]

    if len(inner) < 3:
        raise ValueError(f"{label}: degenerate INNER loop after optional closure drop.")

    poly_a = _make_polygon(outer, f"{label} outer_candidate")
    poly_b = _make_polygon(inner, f"{label} inner_candidate")

    area_a = abs(poly_a.area)
    area_b = abs(poly_b.area)
    if area_a >= area_b:
        return outer, inner
    return inner, outer



def _collect_children(
    polygon_inputs: Dict[int, PolygonInput],
) -> Dict[Optional[int], List[int]]:
    """Build parent -> child polygon id mapping."""
    children: Dict[Optional[int], List[int]] = {}
    for pid, poly in polygon_inputs.items():
        children.setdefault(poly.idx_container, []).append(pid)
    return children



def _make_material(weight: float, label: str) -> Material:
    """
    Build a sectionproperties material that carries the polygon weight.

    IMPORTANT:
    For the bridge, ``weight`` is mapped into ``elastic_modulus`` so that SP can
    produce weighted/homogenized geometric properties. This is a bridge device.
    It should not be read as a general constitutive model for all SP outputs.

    A unique material instance is created for each geometry piece so that the
    region count and the material count remain aligned in sectionproperties.
    """
    if weight == 0.0:
        raise ValueError("Internal error: material requested for a zero-weight region.")
    if weight < 0.0:
        raise ValueError(
            f"Negative non-zero weight is not supported for sectionproperties material mapping: {weight}"
        )

    return Material(
        name=f"{label}:w={weight:g}",
        elastic_modulus=float(weight),
        poissons_ratio=0.0,
        yield_strength=1.0,
        density=1.0,
        color="lightgrey",
    )



def _geometry_from_region(region: ShapelyPolygon, weight: float, label: str) -> Geometry:
    """Convert one shapely region to one sectionproperties Geometry carrying weight."""
    material = _make_material(weight, label)
    return Geometry(geom=region, material=material)



def _union_or_raise(polys: List[ShapelyPolygon], label: str) -> BaseGeometry:
    """Union helper with explicit error on empty output."""
    out = unary_union(polys)
    if out.is_empty:
        raise ValueError(f"{label}: union produced an empty geometry.")
    return out



def _polygon_parts_from_geometry(geom: BaseGeometry, label: str) -> List[ShapelyPolygon]:
    """
    Extract polygon parts from a shapely result.

    Lower-dimensional leftovers created by exact boundary contact are ignored.
    The bridge only accepts polygonal area regions as valid domain pieces.
    """
    if geom.is_empty:
        return []

    if geom.geom_type == "Polygon":
        parts = [geom]
    elif geom.geom_type == "MultiPolygon":
        parts = list(geom.geoms)
    elif geom.geom_type == "GeometryCollection":
        parts = [g for g in geom.geoms if g.geom_type == "Polygon" and not g.is_empty]
    else:
        raise ValueError(f"{label}: expected polygonal geometry, got {geom.geom_type}.")

    out: List[ShapelyPolygon] = []
    for i, part in enumerate(parts):
        if part.is_empty:
            continue
        if part.geom_type != "Polygon":
            raise ValueError(f"{label}: part {i} is not a Polygon.")
        if not part.is_valid:
            raise ValueError(f"{label}: invalid polygon part {i}.")
        out.append(part)

    return out


def _looks_like_slit_encoded_polygon(vertices: List[Tuple[float, float]]) -> bool:
    """
    Detect a slit-encoded multi-loop polygon by an early repeated first vertex.
    """
    if len(vertices) < 8:
        return False

    first = vertices[0]
    for i in range(1, len(vertices) - 3):
        if vertices[i] == first:
            return True

    return False


def _build_node_shapes(
    polygon_inputs: Dict[int, PolygonInput],
) -> Dict[int, NodeShape]:
    """
    Build cached support regions and parent-cutout envelopes for each node.

    support_region:
    - standard polygon -> full polygon area
    - @cell polygon     -> outer shell with intrinsic inner hole

    outer_envelope:
    - the polygon area that must be removed from the direct parent domain
    - standard polygon -> full polygon
    - @cell polygon     -> outer shell only
    """
    out: Dict[int, NodeShape] = {}

    for pid, poly in polygon_inputs.items():
        label = f"idx_polygon={pid}"

        if poly.is_cell:
            outer_xy, inner_xy = _split_cell_polygon(poly.vertices, label)
            outer_poly = _make_polygon(outer_xy, f"{label} outer")
            inner_poly = _make_polygon(inner_xy, f"{label} inner")
            support_region = ShapelyPolygon(
                shell=list(outer_poly.exterior.coords)[:-1],
                holes=[list(inner_poly.exterior.coords)[:-1]],
            )
            if support_region.is_empty:
                raise ValueError(f"{label}: intrinsic @cell region is empty.")
            if not support_region.is_valid:
                raise ValueError(f"{label}: intrinsic @cell region is invalid.")
            out[pid] = NodeShape(
                support_region=support_region,
                outer_envelope=support_region,  # @cell never cuts more than its own wall
            )
            continue

        if _looks_like_slit_encoded_polygon(poly.vertices):
            raise ValueError(
                f"{label} ({poly.name}): polygon looks slit-encoded but is not tagged as @cell/@closed."
            )

        outer_poly = _make_polygon(poly.vertices, label)
        out[pid] = NodeShape(
            support_region=outer_poly,
            outer_envelope=outer_poly,
        )



    return out



# -----------------------------------------------------------------------------
# IMPORTANT TOPOLOGY STEP
# Compute local domains for every node, including zero-weight nodes.
# -----------------------------------------------------------------------------

def _compute_node_local_domains(
    polygon_inputs: Dict[int, PolygonInput],
) -> Dict[int, List[ShapelyPolygon]]:
    """
    Build the local domain partition for every CSF node.

    THIS IS THE CENTRAL TOPOLOGICAL STEP OF THE BRIDGE.

    Local-domain policy:
    - start from the node support region
    - remove the outer envelopes of all direct children
    - keep only polygonal area pieces

    Why this is computed for *all* nodes, including ``w = 0``:
    - a zero-weight node does not become an active SP region,
    - but its local domain may still be a real explicit void in the CSF model,
    - and that void must survive exact boundary-touching and deep nesting cases.
    """
    children = _collect_children(polygon_inputs)
    node_shapes = _build_node_shapes(polygon_inputs)
    local_domains: Dict[int, List[ShapelyPolygon]] = {}

    for pid in polygon_inputs:
        label = f"idx_polygon={pid}"
        region: BaseGeometry = node_shapes[pid].support_region

        child_cutouts: List[ShapelyPolygon] = [
            node_shapes[child_id].outer_envelope
            for child_id in children.get(pid, [])
        ]

        if child_cutouts:
            region = region.difference(
                _union_or_raise(child_cutouts, f"{label} direct_children")
            )

        local_domains[pid] = _polygon_parts_from_geometry(region, f"{label} local_domain")

    return local_domains



def _build_sectionproperties_geometry(
    polygon_inputs: Dict[int, PolygonInput],
    local_domains: Dict[int, List[ShapelyPolygon]],
) -> Geometry | CompoundGeometry:
    """
    Build the sectionproperties geometry from parsed polygon inputs.

    IMPORTANT SEPARATION OF ROLES:
    - ``w > 0`` local-domain pieces -> active SP regions
    - ``w = 0`` local-domain pieces -> not active material, but still topological
      void candidates handled later when hole seeds are computed

    This separation is what keeps the bridge consistent with CSF when explicit
    voids touch other regions exactly on the boundary.
    """
    pieces: List[Geometry] = []

    for pid, poly in polygon_inputs.items():
        if poly.w == 0.0:
            continue

        for i, part in enumerate(local_domains.get(pid, [])):
            part_label = f"idx_polygon={pid}:part={i}"
            pieces.append(_geometry_from_region(part, poly.w, part_label))

    if not pieces:
        raise ValueError("No active solid regions found.")

    if len(pieces) == 1:
        return pieces[0]

    return CompoundGeometry(pieces)



def _polygon_list_from_sectionproperties_geometry(
    geom: Geometry | CompoundGeometry,
) -> List[ShapelyPolygon]:
    """
    Extract shapely polygon regions from a sectionproperties geometry object.

    The bridge only creates polygon-based regions, so any non-polygon payload is
    treated as an internal error.
    """
    if isinstance(geom, CompoundGeometry):
        geoms = list(geom.geoms)
    else:
        geoms = [geom]

    polys: List[ShapelyPolygon] = []
    for i, item in enumerate(geoms):
        region = item.geom
        if region.geom_type != "Polygon":
            raise ValueError(
                f"sectionproperties region {i}: expected Polygon, got {region.geom_type}."
            )
        polys.append(region)

    return polys



def _interior_ring_polygons(region_polys: List[ShapelyPolygon]) -> List[ShapelyPolygon]:
    """
    Convert all interior rings of active regions into polygonal void candidates.
    """
    out: List[ShapelyPolygon] = []

    for i, region in enumerate(region_polys):
        for j, interior in enumerate(region.interiors):
            hole_area = ShapelyPolygon(interior)
            if hole_area.is_empty:
                continue
            if not hole_area.is_valid:
                raise ValueError(f"region {i} interior {j}: invalid hole polygon.")
            out.append(hole_area)

    return out



# -----------------------------------------------------------------------------
# IMPORTANT VOID TRANSFER STEP
# Explicit CSF voids must survive in SP even when they touch other regions
# exactly on the boundary.
# -----------------------------------------------------------------------------

def _compute_effective_hole_points(
    region_polys: List[ShapelyPolygon],
    polygon_inputs: Dict[int, PolygonInput],
    local_domains: Dict[int, List[ShapelyPolygon]],
) -> List[Tuple[float, float]]:
    """
    Compute robust hole seed points for the actual voids in the active geometry.

    THIS FUNCTION FIXES THE MAIN TOPOLOGY TRANSFER ISSUE DISCOVERED DURING
    TESTING.

    Why this is needed:
    - a zero-weight CSF node may represent an explicit void even when it does not
      appear as an interior ring of the active regions
    - exact boundary contact can remove the interior-ring signal while the void
      still exists topologically
    - nested descendants may create active islands inside a zero-weight node

    Policy:
    - collect void candidates from two sources:
      1) interior rings of the active regions
      2) local-domain pieces of all zero-weight nodes
    - merge all void candidates
    - subtract the union of all active regions
    - place one hole seed inside each connected residual void component

    In other words: explicit CSF voids are not inferred only from active-region
    interiors; they are also transferred directly from zero-weight node domains.
    """
    if not region_polys:
        return []

    active_union = unary_union(region_polys)

    void_candidates: List[ShapelyPolygon] = []
    void_candidates.extend(_interior_ring_polygons(region_polys))

    for pid, poly in polygon_inputs.items():
        if poly.w != 0.0:
            continue
        void_candidates.extend(local_domains.get(pid, []))

    if not void_candidates:
        return []

    candidate_union = _union_or_raise(void_candidates, "explicit_void_candidates")
    effective_void = candidate_union.difference(active_union)
    void_parts = _polygon_parts_from_geometry(
        effective_void,
        "explicit_void_candidates effective_void",
    )

    hole_points: List[Tuple[float, float]] = []
    for i, part in enumerate(void_parts):
        seed = part.representative_point()
        if seed.is_empty:
            raise ValueError(f"effective_void part {i}: empty representative point.")
        hole_points.append((float(seed.x), float(seed.y)))

    return hole_points



def _apply_effective_hole_points(
    geom: Geometry | CompoundGeometry,
    polygon_inputs: Dict[int, PolygonInput],
    local_domains: Dict[int, List[ShapelyPolygon]],
) -> Geometry | CompoundGeometry:
    """
    Override sectionproperties hole seeds with points that lie in the true voids.

    This uses both:
    - interior rings already present in the active regions
    - explicit local domains of zero-weight CSF nodes
    """
    region_polys = _polygon_list_from_sectionproperties_geometry(geom)
    geom.holes = _compute_effective_hole_points(region_polys, polygon_inputs, local_domains)
    return geom



# -----------------------------------------------------------------------------
# CONNECTEDNESS POLICY USED ONLY BY THE BRIDGE
# -----------------------------------------------------------------------------

def _geometry_is_connected(geom: Geometry | CompoundGeometry) -> bool:
    """
    Return True when the union of all active regions is one connected polygon.

    NOTE:
    This is a bridge policy, not a CSF theorem. The decision is made with
    Shapely ``unary_union`` on the final active SP regions. It is used only to
    decide whether the bridge will attempt SP warping calculations.
    """
    region_polys = _polygon_list_from_sectionproperties_geometry(geom)
    if not region_polys:
        return False
    union_geom = unary_union(region_polys)
    return union_geom.geom_type == "Polygon"


# -----------------------------------------------------------------------------
# Analysis helpers
# -----------------------------------------------------------------------------


def _analyse_one_geometry(z: float, polygon_inputs: Dict[int, PolygonInput], mesh: float, plot: bool, warping: bool = True) -> None:
    """
    Mesh, analyse, and print one station.

    Execution order matters:
    1. compute local domains for all CSF nodes
    2. build active SP geometry from positive-weight pieces only
    3. inject hole seeds from actual voids, including zero-weight nodes
    4. mesh
    5. compute geometric properties
    6. compute warping only if the final active geometry is connected according
       to the bridge policy implemented in ``_geometry_is_connected``
    """
    local_domains = _compute_node_local_domains(polygon_inputs)
    geom = _build_sectionproperties_geometry(polygon_inputs, local_domains)
    geom = _apply_effective_hole_points(geom, polygon_inputs, local_domains)
    geom = geom.create_mesh(mesh_sizes=mesh)

    sec = Section(geometry=geom)
    sec.calculate_geometric_properties()

    if warping:
        if _geometry_is_connected(geom):
            sec.calculate_warping_properties()
        else:
            print(
                "WARNING: Warping analysis skipped because the geometry contains disjoint regions."
            )

    print(f"z = {z}")
    print(f"mesh_sizes = {mesh}")
    print("sectionproperties results:")
    sec.display_results()

    if plot:
        import matplotlib.pyplot as plt

        geom.plot_geometry()
        sec.plot_mesh(materials=False)
        plt.show()


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------


def main() -> None:
    """Command-line entry point."""
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "path",
        nargs="?",
        type=Path,
        help="Legacy text file containing CSF geometry export block(s).",
    )
    ap.add_argument("--yaml", dest="yaml_path", type=Path, default=None, help="CSF YAML model.")
    ap.add_argument(
        "--run-config",
        type=Path,
        default=None,
        help="YAML file containing station_sets.",
    )
    ap.add_argument(
        "--station-set",
        type=str,
        default=None,
        help="Name of the station set to use from the run-config file.",
    )
    ap.add_argument(
        "--z",
        type=float,
        default=None,
        help="Explicit z station. In YAML mode this overrides station_sets. In legacy text mode it selects one export block.",
    )
    ap.add_argument("--mesh", type=float, default=1.0, help="Max mesh element area.")
    ap.add_argument("--plot", action="store_true", help="Plot geometry and mesh.")
    ap.add_argument("--no-warping", dest="no_warping", action="store_true", help="Skip warping FEM (e.j, shear centre). Significantly faster when torsional constant is not needed.")
    args = ap.parse_args()

    if args.yaml_path is not None:
        if args.path is not None:
            raise SystemExit("Do not pass the legacy text path together with --yaml.")

        field = _load_field_from_yaml(args.yaml_path)

        if args.z is not None:
            z_values = [float(args.z)]
        else:
            if args.run_config is None:
                raise SystemExit("YAML mode requires --run-config unless --z is provided.")
            if not args.station_set:
                raise SystemExit("YAML mode requires --station-set unless --z is provided.")
            z_values = _load_station_set(args.run_config, args.station_set)

        for i, z in enumerate(z_values):
            if i > 0:
                print("\n" + "-" * 80)
            polygon_inputs = _polygon_inputs_from_field(field, z)
            _analyse_one_geometry(z, polygon_inputs, args.mesh, args.plot, warping=not args.no_warping)
        return

    if args.path is None:
        raise SystemExit("Provide either a legacy text file path or --yaml.")

    text = args.path.read_text(encoding="utf-8", errors="replace")
    blocks = _read_geometry_export_blocks(text)
    z, rows = _select_z_block(blocks, args.z)
    polygon_inputs = _rows_to_polygon_inputs(rows)
    _analyse_one_geometry(z, polygon_inputs, args.mesh, args.plot, warping=not args.no_warping)



# =============================================================================
# PUBLIC API
# =============================================================================
# Two entry points are exposed for programmatic use.  Everything else in this
# module is considered private implementation detail and may change without
# notice.
# =============================================================================


def load_yaml(path: "str | Path") -> Any:
    """Load a CSF model from a YAML file and return the field object.

    This is a thin public wrapper around the internal YAML loader.  The
    returned object is a ``ContinuousSectionField`` instance that can be
    passed directly to :func:`analyse`.

    Parameters
    ----------
    path:
        Path to the CSF YAML file (``str`` or :class:`pathlib.Path`).

    Returns
    -------
    ContinuousSectionField
        The loaded CSF field, ready for sampling.

    Raises
    ------
    SystemExit
        If the file cannot be read or the CSF model fails validation.

    Example
    -------
    >>> field = load_yaml("my_section.yaml")
    >>> sec = analyse(field, z=15.0)
    >>> print(sec.get_ea())
    """
    return _load_field_from_yaml(Path(path))


def analyse(field: Any, z: float, mesh: float = 1.0, warping: bool = True) -> "Section":
    """Analyse a CSF field at a given longitudinal position.

    Samples the CSF field at ``z``, builds the sectionproperties geometry,
    meshes it, and runs the geometric analysis.  Warping analysis is also
    performed when the active geometry is connected (i.e. contains no
    disjoint regions); otherwise a warning is printed and warping properties
    are left uncomputed.

    The returned :class:`sectionproperties.analysis.Section` object exposes
    the full sectionproperties API.  In particular ``e.j`` (Saint-Venant
    torsional constant via FEM) is available when warping was computed.

    Parameters
    ----------
    field:
        A ``ContinuousSectionField`` instance, typically obtained from
        :func:`load_yaml` or constructed directly via the CSF Python API.
    z:
        Longitudinal coordinate at which to sample the section.
    mesh:
        Maximum triangular element area for the sectionproperties mesh.
        Smaller values give more accurate results at the cost of speed.
        Default is ``1.0`` (same length units as the CSF model).
    warping:
        If ``True`` (default), warping properties (``e.j``, shear centre,
        etc.) are computed when the geometry is connected.  Set to ``False``
        to skip the warping FEM — significantly faster when ``e.j`` is not
        needed.

    Returns
    -------
    sectionproperties.analysis.Section
        A fully analysed Section object.  Geometric properties are always
        available.  Warping properties (``e.j``, shear centre, etc.) are
        available only when the geometry is connected.

    Example
    -------
    Given a prismatic hollow circular tower (outer radius 5 m, wall ~0.43 m,
    weight = 1.0) sampled at z = 0.0:

    >>> from csf.utils.csf_sp import load_yaml, analyse
    >>> field = load_yaml("twist_tower.yaml")
    >>> sec = analyse(field, z=0.0)
    >>>
    >>> # Saint-Venant torsional constant (FEM warping)
    >>> print(sec.get_ej())
    182.099                          # CSF J_sv_vroark ≈ 182.0
    >>>
    >>> # Centroidal second moments of area (Ixx, Iyy, Ixy)
    >>> print(sec.get_eic())
    (91.049, 91.049, ~0.0)           # CSF Ix = Iy = 91.049 (circular symmetry)

    Note: SP exposes composite-aware getters (``get_ej``, ``get_eic``, etc.)
    because the bridge always assigns material properties to regions.
    Use ``get_ej()`` instead of ``get_j()`` to avoid a RuntimeError even
    when all polygon weights are equal to 1.0.
    """
    polygon_inputs = _polygon_inputs_from_field(field, float(z))

    local_domains = _compute_node_local_domains(polygon_inputs)
    geom = _build_sectionproperties_geometry(polygon_inputs, local_domains)
    geom = _apply_effective_hole_points(geom, polygon_inputs, local_domains)
    geom = geom.create_mesh(mesh_sizes=float(mesh))

    sec = Section(geometry=geom)
    sec.calculate_geometric_properties()

    if warping:
        if _geometry_is_connected(geom):
            sec.calculate_warping_properties()
        else:
            print(
                "WARNING: Warping analysis skipped because the geometry contains disjoint regions."
            )

    return sec


if __name__ == "__main__":
    main()
