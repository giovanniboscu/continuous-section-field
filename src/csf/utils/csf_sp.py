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

Torsion carrier policy
----------------------
sectionproperties reports composite Saint-Venant torsion as ``e.j`` because its
torsion assembly is weighted by the value stored as ``elastic_modulus``.

For the native sectionproperties run, CSF maps the axial/bending carrier to
``elastic_modulus``. The native ``sec.get_ej()`` result is therefore reported as
the sectionproperties native ``e.j`` result.

For CSF torsion, this bridge can also perform a dedicated torsion-only carrier
run where the value passed to sectionproperties as ``elastic_modulus`` is the
resolved CSF shear carrier ``G_i`` / ``shear_w_i``. The resulting
sectionproperties ``e.j`` value from that second run is reported as a CSF
torsion-carrier result, not as a native sectionproperties ``g.j`` output.
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml
from shapely.geometry import Polygon as ShapelyPolygon
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
verbose = False


@dataclass(frozen=True)
class Row:
    """One CSV geometry row from a CSF export block."""

    idx_polygon: int
    idx_container: Optional[int]
    s0_name: str
    s1_name: str
    w: Optional[float]
    shear_w: Optional[float]
    poisson: Optional[float]
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
    shear_w: Optional[float]
    poisson: float
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


def _require_defined_poisson(idx_polygon: int, value: Any) -> float:
    """Return a defined Poisson ratio or stop explicitly."""
    try:
        poisson = float(value)
    except Exception as exc:
        raise SystemExit(
            f"Not applicable: idx_polygon={idx_polygon} is not isotropic; invalid poisson={value!r}."
        ) from exc

    if math.isnan(poisson):
        raise SystemExit(
            f"Not applicable: idx_polygon={idx_polygon} is not isotropic; poisson is undefined."
        )

    return poisson


def _read_optional_shear_w(idx_polygon: int, poly: Any) -> Optional[float]:
    """
    Read the sampled CSF shear carrier when it is explicitly available.

    No default value is invented here. If the sampled polygon does not expose a
    shear carrier, the torsion-carrier run is reported as unavailable.
    """
    for attr_name in ("shear_weightabs", "shear_w"):
        if not hasattr(poly, attr_name):
            continue

        value = getattr(poly, attr_name)
        if value is None:
            return None

        try:
            shear_w = float(value)
        except Exception as exc:
            raise SystemExit(
                f"Not applicable: idx_polygon={idx_polygon} has invalid {attr_name}={value!r}."
            ) from exc

        if math.isnan(shear_w):
            return None

        return shear_w

    return None


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
        header: Optional[List[str]] = None
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
                header = [c.strip() for c in rec]
                required = [
                    "idx_polygon",
                    "idx_container",
                    "s0_name",
                    "s1_name",
                    "w",
                    "shear_w",
                    "poisson",
                    "vertex_i",
                    "x",
                    "y",
                ]
                missing = [c for c in required if c not in header]
                if missing:
                    raise SystemExit(
                        "CSV geometry export is not applicable to the isotropic SP bridge; "
                        f"missing columns: {missing}"
                    )
                j += 1
                continue

            if header is None:
                raise SystemExit(
                    "CSV geometry export is not applicable to the isotropic SP bridge; missing header."
                )

            if len(rec) < len(header):
                raise ValueError(
                    f"z={z_value}: malformed CSV row (expected {len(header)} fields): {rec!r}"
                )

            row = {name: rec[i].strip() for i, name in enumerate(header)}

            rows.append(
                Row(
                    idx_polygon=int(row["idx_polygon"]),
                    idx_container=_parse_optional_int(row["idx_container"]),
                    s0_name=row["s0_name"],
                    s1_name=row["s1_name"],
                    w=_parse_optional_float(row["w"]),
                    shear_w=_parse_optional_float(row["shear_w"]),
                    poisson=_parse_optional_float(row["poisson"]),
                    vertex_i=int(row["vertex_i"]),
                    x=float(row["x"]),
                    y=float(row["y"]),
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

        shear_w = group_sorted[0].shear_w

        poisson_raw = group_sorted[0].poisson
        if poisson_raw is None:
            raise SystemExit(
                f"Not applicable: idx_polygon={idx_polygon} is not isotropic; missing poisson."
            )
        poisson = _require_defined_poisson(idx_polygon, poisson_raw)

        if verbose:
            print(
                f"DEBUG poisson CSV idx={idx_polygon} name={joined_name} "
                f"w={w} shear_w={shear_w} poisson={poisson}"
            )

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
            if r.shear_w != shear_w:
                raise ValueError(
                    f"idx_polygon={idx_polygon}: inconsistent shear_w "
                    f"{shear_w!r} vs {r.shear_w!r}"
                )
            if r.poisson != poisson_raw:
                raise ValueError(
                    f"idx_polygon={idx_polygon}: inconsistent poisson "
                    f"{poisson_raw!r} vs {r.poisson!r}"
                )

        vertices = [(r.x, r.y) for r in group_sorted]
        is_cell = _name_has_cell_tag(s0_name) or _name_has_cell_tag(s1_name)

        result[idx_polygon] = PolygonInput(
            idx_polygon=idx_polygon,
            idx_container=idx_container,
            name=joined_name,
            w=w,
            shear_w=shear_w,
            poisson=poisson,
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
    - the sampled absolute shear carrier when present,
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
        shear_w = _read_optional_shear_w(idx, poly)

        if not hasattr(poly, "poisson"):
            raise SystemExit(
                f"Not applicable: idx_polygon={idx} is not isotropic; missing poisson."
            )

        poisson = _require_defined_poisson(idx, getattr(poly, "poisson"))

        if verbose:
            print(
                f"DEBUG poisson YAML idx={idx} name={name} "
                f"w={w_abs} shear_w={shear_w} poisson={poisson}"
            )

        out[idx] = PolygonInput(
            idx_polygon=idx,
            idx_container=parent_of.get(idx),
            name=name,
            w=w_abs,
            shear_w=shear_w,
            poisson=poisson,
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
    - If the tail closes back to the first OUTER vertex, that last point is dropped.
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

    # Some slit-encoded @cell polygons close the full path by returning to the
    # first OUTER vertex after the INNER loop. That point is not part of INNER.
    if inner[-1] == first:
        inner = inner[:-1]

    if len(inner) < 3:
        raise ValueError(f"{label}: degenerate INNER loop after outer closure drop.")

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


def _make_material(weight: float, poisson: float, label: str) -> Material:
    """
    Build a sectionproperties material from the current carrier and Poisson data.

    Bridge convention:
    - the current carrier is mapped to sectionproperties ``elastic_modulus``
    - ``poisson`` is mapped to ``poissons_ratio``
    - sectionproperties internally uses ``elastic_modulus`` as the torsion carrier
    """
    if weight == 0.0:
        raise ValueError("Internal error: material requested for a zero-weight region.")
    if weight < 0.0:
        raise ValueError(
            f"Negative non-zero weight is not supported for sectionproperties material mapping: {weight}"
        )
    if math.isnan(float(poisson)):
        raise ValueError("Internal error: material requested with undefined poisson.")

    return Material(
        name=f"{label}:carrier={weight:g}:nu={poisson:g}",
        elastic_modulus=float(weight),
        poissons_ratio=float(poisson),
        yield_strength=1.0,
        density=1.0,
        color="lightgrey",
    )


def _geometry_from_region(region: ShapelyPolygon, poly: PolygonInput, label: str) -> Geometry:
    """Convert one shapely region to one sectionproperties Geometry carrying CSF material data."""
    material = _make_material(poly.w, poly.poisson, label)
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
    """Detect a slit-encoded multi-loop polygon by an early repeated first vertex."""
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
                outer_envelope=support_region,
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
            pieces.append(_geometry_from_region(part, poly, part_label))

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
    """Convert all interior rings of active regions into polygonal void candidates."""
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
    Compute robust hole seed points for explicit CSF voids.

    Policy:
    - only zero-weight CSF nodes create global void candidates;
    - interior rings of active regions are not promoted to global voids;
    - @cell intrinsic inner loops remain local to the @cell geometry.
    """
    if not region_polys:
        return []

    active_union = unary_union(region_polys)

    void_candidates: List[ShapelyPolygon] = []

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
    """Add CSF-derived hole seeds without deleting hole seeds already found by SP."""
    region_polys = _polygon_list_from_sectionproperties_geometry(geom)
    computed_holes = _compute_effective_hole_points(
        region_polys,
        polygon_inputs,
        local_domains,
    )

    if computed_holes:
        existing_holes = list(getattr(geom, "holes", []) or [])
        geom.holes = existing_holes + [
            hole for hole in computed_holes if hole not in existing_holes
        ]

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
# Torsion carrier helpers
# -----------------------------------------------------------------------------


def _make_torsion_carrier_inputs(
    polygon_inputs: Dict[int, PolygonInput],
) -> Dict[int, PolygonInput]:
    """
    Replace the normal CSF carrier ``w`` with the resolved shear carrier.

    This is the explicit carrier substitution used by the torsion-only run:

        E_SP := G_i / shear_w_i

    No fallback is applied. If the sampled CSF model does not provide shear_w
    for every polygon node, the torsion-carrier result is not computed.
    """
    missing = [
        pid
        for pid, poly in polygon_inputs.items()
        if poly.shear_w is None
    ]
    if missing:
        raise ValueError(
            "CSF torsion-carrier result is not available: missing shear_w for "
            f"idx_polygon={missing}."
        )

    out: Dict[int, PolygonInput] = {}
    for pid, poly in polygon_inputs.items():
        shear_w = float(poly.shear_w)  # type: ignore[arg-type]
        if shear_w < 0.0:
            raise ValueError(
                f"CSF torsion-carrier result is not available: "
                f"idx_polygon={pid} has negative shear_w={shear_w}."
            )
        out[pid] = replace(poly, w=shear_w)

    return out


def _build_meshed_geometry(
    polygon_inputs: Dict[int, PolygonInput],
    mesh: float,
) -> Tuple[Geometry | CompoundGeometry, Dict[int, List[ShapelyPolygon]]]:
    """Build the meshed sectionproperties geometry for a given carrier field."""
    local_domains = _compute_node_local_domains(polygon_inputs)
    geom = _build_sectionproperties_geometry(polygon_inputs, local_domains)
    geom = _apply_effective_hole_points(geom, polygon_inputs, local_domains)
    geom = geom.create_mesh(mesh_sizes=mesh)
    return geom, local_domains


def _compute_torsion_carrier_result(
    polygon_inputs: Dict[int, PolygonInput],
    mesh: float,
) -> float:
    """
    Compute the CSF torsion-carrier result through a dedicated SP run.

    The returned value is the sectionproperties ``e.j`` value obtained after
    substituting the carrier:

        E_SP := G_i / shear_w_i

    It is intentionally not named ``g.j`` because sectionproperties does not
    expose a native ``g.j`` result.
    """
    carrier_inputs = _make_torsion_carrier_inputs(polygon_inputs)
    geom, _ = _build_meshed_geometry(carrier_inputs, mesh)

    if not _geometry_is_connected(geom):
        raise ValueError(
            "CSF torsion-carrier result is not available: geometry contains disjoint regions."
        )

    sec = Section(geometry=geom)
    sec.calculate_geometric_properties()
    sec.calculate_warping_properties()
    return float(sec.get_ej())


def _print_torsion_results(
    sec: Section,
    polygon_inputs: Dict[int, PolygonInput],
    mesh: float,
) -> None:
    """
    Print native SP torsion and CSF torsion-carrier output.

    The second value is labelled as a CSF carrier result, not as an SP-native
    ``g.j`` quantity.
    """
    print("csf_sp torsion carrier results:")

    native_ej = float(sec.get_ej())
    print(f"  sectionproperties native e.j [E_i carrier] = {native_ej:.12g}")

    try:
        carrier_result = _compute_torsion_carrier_result(polygon_inputs, mesh)
    except ValueError as exc:
        print(f"  CSF torsion carrier J [SP e.j with E_SP := G_i] = not available ({exc})")
        return

    print(
        "  CSF torsion carrier J "
        f"[SP e.j with E_SP := G_i/shear_w_i] = {carrier_result:.12g}"
    )


# -----------------------------------------------------------------------------
# Analysis helpers
# -----------------------------------------------------------------------------


def _analyse_one_geometry(
    z: float,
    polygon_inputs: Dict[int, PolygonInput],
    mesh: float,
    plot: bool,
    warping: bool = True,
) -> None:
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
    7. when warping is available, print both the native SP ``e.j`` result and
       the CSF torsion-carrier result obtained by the dedicated ``E_SP := G_i``
       run
    """
    geom, _local_domains = _build_meshed_geometry(polygon_inputs, mesh)

    sec = Section(geometry=geom)
    sec.calculate_geometric_properties()

    warping_computed = False
    if warping:
        if _geometry_is_connected(geom):
            sec.calculate_warping_properties()
            warping_computed = True
        else:
            print(
                "WARNING: Warping analysis skipped because the geometry contains disjoint regions."
            )

    print(f"z = {z}")
    print(f"mesh_sizes = {mesh}")
    print("sectionproperties results:")
    sec.display_results()

    if warping_computed:
        _print_torsion_results(sec, polygon_inputs, mesh)

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
    ap.add_argument(
        "--no-warping",
        dest="no_warping",
        action="store_true",
        help="Skip warping FEM. Native e.j and CSF torsion-carrier J are not computed.",
    )
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
# Two main entry points are exposed for programmatic use:
# - load_yaml(...)
# - analyse(...)
#
# A torsion-specific helper is also exposed:
# - analyse_torsion_carrier(...)
#
# Everything else in this module is considered private implementation detail and
# may change without notice.
# =============================================================================


def load_yaml(path: "str | Path") -> Any:
    """Load a CSF model from a YAML file and return the field object.

    This is a thin public wrapper around the internal YAML loader. The returned
    object is a ``ContinuousSectionField`` instance that can be passed directly
    to :func:`analyse`.

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
    """
    return _load_field_from_yaml(Path(path))


def analyse(field: Any, z: float, mesh: float = 1.0, warping: bool = True) -> "Section":
    """Analyse a CSF field at a given longitudinal position.

    Samples the CSF field at ``z``, builds the sectionproperties geometry,
    meshes it, and runs the geometric analysis. Warping analysis is also
    performed when the active geometry is connected.

    The returned :class:`sectionproperties.analysis.Section` object exposes the
    full sectionproperties API.

    Torsion note
    ------------
    ``sec.get_ej()`` is the native sectionproperties result. It is an ``e.j``
    result because sectionproperties weights composite torsion with the value
    stored as ``elastic_modulus``.

    To compute the CSF torsion-carrier result based on the resolved shear field,
    use :func:`analyse_torsion_carrier`. That helper performs a dedicated
    torsion-only run with:

        E_SP := G_i / shear_w_i

    and returns the resulting sectionproperties ``e.j`` value as a CSF
    torsion-carrier result.

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
    warping:
        If ``True`` (default), warping properties (native ``e.j``, shear centre,
        etc.) are computed when the geometry is connected. Set to ``False`` to
        skip the warping FEM.

    Returns
    -------
    sectionproperties.analysis.Section
        A fully analysed Section object. Geometric properties are always
        available. Warping properties are available only when warping is enabled
        and the geometry is connected.
    """
    polygon_inputs = _polygon_inputs_from_field(field, float(z))

    geom, _local_domains = _build_meshed_geometry(polygon_inputs, float(mesh))

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


def analyse_torsion_carrier(field: Any, z: float, mesh: float = 1.0) -> float:
    """Return the CSF torsion-carrier result at a station.

    This performs a dedicated sectionproperties torsion-only run after replacing
    the normal axial/bending carrier by the resolved CSF shear carrier:

        E_SP := G_i / shear_w_i

    The returned scalar is the sectionproperties ``e.j`` value from that carrier
    run. It is intentionally exposed as a CSF torsion-carrier result, not as a
    native sectionproperties ``g.j`` output.

    Parameters
    ----------
    field:
        A ``ContinuousSectionField`` instance.
    z:
        Longitudinal coordinate at which to sample the section.
    mesh:
        Maximum triangular element area for the sectionproperties mesh.

    Returns
    -------
    float
        The carrier-weighted torsional result computed with ``E_SP := G_i``.

    Raises
    ------
    ValueError
        If the sampled CSF model does not expose ``shear_w`` for every polygon,
        or if the active carrier geometry is disconnected.
    """
    polygon_inputs = _polygon_inputs_from_field(field, float(z))
    return _compute_torsion_carrier_result(polygon_inputs, float(mesh))


if __name__ == "__main__":
    main()
