"""
Bridge a CSF geometry export block to sectionproperties.

The script reads text blocks in the form:

    ## GEOMETRY EXPORT ##
    # z=...
    idx_polygon,idx_container,s0_name,s1_name,w,vertex_i,x,y
    ...

and builds a sectionproperties Geometry / CompoundGeometry object.

Design rules implemented here
-----------------------------

1. The input may contain N polygons.

2. Weight rule:
       - w == 0.0  -> polygon is treated as a void
       - w != 0.0  -> polygon is treated as an active polygon and keeps that w

3. Standard polygons:
       - geometry follows idx_container nesting
       - direct void children are subtracted from their direct container
       - active polygons keep their own weight

4. @cell / @closed polygons:
       - a polygon is treated as @cell if "@cell" or "@closed" appears in
         s0_name OR s1_name in at least one row of that polygon
       - the polygon is interpreted as a slit-encoded closed cell
       - the first repeated occurrence of the first vertex closes the OUTER loop
       - the remaining tail defines the INNER loop
       - explicit closure of the INNER loop is optional

5. For sectionproperties:
       - a @cell polygon is converted to:
             OUTER solid region
             INNER void region

6. No other assumptions are introduced.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from shapely.geometry import Polygon as ShapelyPolygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

# sectionproperties imports
from sectionproperties.pre import Geometry, CompoundGeometry
from sectionproperties.analysis import Section

# Material import path can differ across sectionproperties versions.
try:
    from sectionproperties.pre import Material
except Exception:  # pragma: no cover
    from sectionproperties.pre.pre import Material  # type: ignore


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
    """
    Parsed polygon input before conversion to sectionproperties geometry.
    """

    idx_polygon: int
    idx_container: Optional[int]
    s0_name: str
    s1_name: str
    w: float
    is_cell: bool
    vertices: List[Tuple[float, float]]


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
        i for i in (
            low.find(TOKEN_CELL),
            low.find(TOKEN_WALL),
            low.find(TOKEN_CLOSED),
        )
        if i >= 0
    ]
    if not idxs:
        return name

    return name[: min(idxs)]


def _row_has_cell_tag(r: Row) -> bool:
    """
    Return True if the row contains @cell or @closed in s0_name or s1_name.
    """
    s0 = (r.s0_name or "").lower()
    s1 = (r.s1_name or "").lower()
    return (
        (TOKEN_CELL in s0)
        or (TOKEN_CLOSED in s0)
        or (TOKEN_CELL in s1)
        or (TOKEN_CLOSED in s1)
    )


def _read_geometry_export_blocks(text: str) -> Dict[float, List[Row]]:
    """
    Return {z_value: [rows]} for each geometry export block found in the text.
    """
    lines = text.splitlines()
    blocks: Dict[float, List[Row]] = {}

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line != "## GEOMETRY EXPORT ##":
            i += 1
            continue

        # Read z line.
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

        # Read rows until blank line, next analysis block, or next geometry block.
        while j < len(lines):
            raw = lines[j]
            s = raw.strip()

            if s == "" or s.startswith("### ") or s == "## GEOMETRY EXPORT ##":
                break

            # Skip comments and the CSV header.
            if s.startswith("#"):
                j += 1
                continue

            rec = next(csv.reader([raw]))
            if not rec:
                j += 1
                continue

            # Skip header line robustly.
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
    """
    Group rows by idx_polygon.
    """
    grouped: Dict[int, List[Row]] = {}
    for r in rows:
        grouped.setdefault(r.idx_polygon, []).append(r)
    return grouped


def _rows_to_polygon_inputs(rows: List[Row]) -> Dict[int, PolygonInput]:
    """
    Convert row groups to polygon inputs with strict consistency checks.
    """
    grouped = _group_rows_by_polygon(rows)
    result: Dict[int, PolygonInput] = {}

    for idx_polygon, group in grouped.items():
        group_sorted = sorted(group, key=lambda r: r.vertex_i)

        idx_container = group_sorted[0].idx_container
        s0_name = group_sorted[0].s0_name
        s1_name = group_sorted[0].s1_name

        # Keep explicit error if w is missing for this polygon.
        if group_sorted[0].w is None:
            raise ValueError(f"idx_polygon={idx_polygon}: missing w value.")

        w = float(group_sorted[0].w)

        # Enforce per-polygon consistency.
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
        is_cell = any(_row_has_cell_tag(r) for r in group_sorted)

        result[idx_polygon] = PolygonInput(
            idx_polygon=idx_polygon,
            idx_container=idx_container,
            s0_name=s0_name,
            s1_name=s1_name,
            w=w,
            is_cell=is_cell,
            vertices=vertices,
        )

    return result


def _make_polygon(coords: List[Tuple[float, float]], label: str) -> ShapelyPolygon:
    """
    Build a shapely polygon without silently fixing invalid geometry.
    """
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

    # Decide which loop is OUTER by area magnitude.
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
    """
    Build parent -> child polygon id mapping.
    """
    children: Dict[Optional[int], List[int]] = {}
    for pid, poly in polygon_inputs.items():
        children.setdefault(poly.idx_container, []).append(pid)
    return children


def _make_material(weight: float) -> Material:
    """
    Build a sectionproperties material that carries the polygon weight.

    The elastic modulus is set equal to w so that composite-style section
    properties can reflect the CSF weight when the installed sectionproperties
    version uses material weighting.

    A negative non-zero weight is rejected explicitly.
    """
    if weight == 0.0:
        raise ValueError("Internal error: material requested for a void polygon.")

    if weight < 0.0:
        raise ValueError(
            f"Negative non-zero weight is not supported for sectionproperties material mapping: {weight}"
        )

    return Material(
        name=f"w={weight:g}",
        elastic_modulus=float(weight),
        poissons_ratio=0.0,
        yield_strength=1.0,
        density=1.0,
        color="lightgrey",
    )


def _geometry_from_region(region: ShapelyPolygon, weight: float) -> Geometry:
    """
    Convert one shapely region to one sectionproperties Geometry carrying weight.
    """
    material = _make_material(weight)
    return Geometry(geom=region, material=material)


def _union_or_raise(polys: List[ShapelyPolygon], label: str) -> BaseGeometry:
    """
    Union helper with explicit error on empty output.
    """
    out = unary_union(polys)
    if out.is_empty:
        raise ValueError(f"{label}: union produced an empty geometry.")
    return out


def _build_standard_region(
    pid: int,
    polygon_inputs: Dict[int, PolygonInput],
    children: Dict[Optional[int], List[int]],
) -> Optional[Geometry]:
    """
    Build one standard (non-@cell) active root region.

    Rule:
    - active root polygon starts as a solid region
    - direct void children are subtracted from that region
    - direct active children are not merged here; they are handled as separate regions
    """
    poly = polygon_inputs[pid]

    if poly.w == 0.0:
        return None

    label = f"idx_polygon={pid}"
    root_region = _make_polygon(poly.vertices, label)

    void_children = [
        child_id
        for child_id in children.get(pid, [])
        if (not polygon_inputs[child_id].is_cell) and polygon_inputs[child_id].w == 0.0
    ]

    if void_children:
        void_union = _union_or_raise(
            [
                _make_polygon(polygon_inputs[child_id].vertices, f"idx_polygon={child_id}")
                for child_id in void_children
            ],
            f"{label} void_children",
        )
        root_region = root_region.difference(void_union)
        if root_region.is_empty:
            raise ValueError(f"{label}: subtraction produced empty region.")
        if root_region.geom_type != "Polygon":
            raise ValueError(
                f"{label}: subtraction produced {root_region.geom_type}; expected Polygon."
            )
        if not root_region.is_valid:
            raise ValueError(f"{label}: invalid region after void subtraction.")

    return _geometry_from_region(root_region, poly.w)


def _build_cell_regions(pid: int, poly: PolygonInput) -> List[Geometry]:
    """
    Build sectionproperties geometries for a @cell polygon.

    Conversion rule:
    - OUTER loop -> active solid region with the polygon weight
    - INNER loop -> void, subtracted from OUTER
    """
    label = f"idx_polygon={pid}"
    if poly.w == 0.0:
        return []

    outer_xy, inner_xy = _split_cell_polygon(poly.vertices, label)

    outer_poly = _make_polygon(outer_xy, f"{label} outer")
    inner_poly = _make_polygon(inner_xy, f"{label} inner")

    region = outer_poly.difference(inner_poly)
    if region.is_empty:
        raise ValueError(f"{label}: OUTER - INNER produced empty region.")
    if region.geom_type != "Polygon":
        raise ValueError(
            f"{label}: OUTER - INNER produced {region.geom_type}; expected Polygon."
        )
    if not region.is_valid:
        raise ValueError(f"{label}: invalid @cell region after subtraction.")

    return [_geometry_from_region(region, poly.w)]


def _build_sectionproperties_geometry(
    polygon_inputs: Dict[int, PolygonInput],
) -> Geometry | CompoundGeometry:
    """
    Build the sectionproperties geometry from parsed polygon inputs.
    """
    children = _collect_children(polygon_inputs)

    pieces: List[Geometry] = []

    # 1. Add @cell polygons as standalone weighted regions.
    for pid, poly in polygon_inputs.items():
        if poly.is_cell:
            pieces.extend(_build_cell_regions(pid, poly))

    # 2. Add standard root active polygons.
    for pid, poly in polygon_inputs.items():
        if poly.is_cell:
            continue
        if poly.idx_container is not None:
            continue

        g = _build_standard_region(pid, polygon_inputs, children)
        if g is not None:
            pieces.append(g)

    # 3. Add standard non-root active polygons that are not voids.
    #    This preserves the current behavior where extra active polygons
    #    remain explicit regions instead of being silently merged away.
    for pid, poly in polygon_inputs.items():
        if poly.is_cell:
            continue
        if poly.idx_container is None:
            continue
        if poly.w == 0.0:
            continue

        # Active child polygons are kept as separate solid regions.
        region = _make_polygon(poly.vertices, f"idx_polygon={pid}")
        pieces.append(_geometry_from_region(region, poly.w))

    if not pieces:
        raise ValueError("No active solid regions found.")

    if len(pieces) == 1:
        return pieces[0]

    out: Geometry | CompoundGeometry = pieces[0]
    for g in pieces[1:]:
        out = out + g
    return out


def _select_z_block(blocks: Dict[float, List[Row]], requested_z: Optional[float]) -> Tuple[float, List[Row]]:
    """
    Select the requested z block, or the first sorted block if no z is requested.
    """
    z_values = sorted(blocks.keys())
    if requested_z is None:
        z = z_values[0]
        return z, blocks[z]

    if requested_z not in blocks:
        raise SystemExit(f"Requested z={requested_z} not found. Available: {z_values}")

    return requested_z, blocks[requested_z]


def main() -> None:
    """
    Command-line entry point.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("path", type=Path, help="Text file containing CSF geometry export block(s).")
    ap.add_argument("--z", type=float, default=None, help="Which z block to use. If omitted, the first block is used.")
    ap.add_argument("--mesh", type=float, default=1.0, help="Max mesh element area.")
    ap.add_argument("--plot", action="store_true", help="Plot geometry and mesh.")
    args = ap.parse_args()

    text = args.path.read_text(encoding="utf-8", errors="replace")
    blocks = _read_geometry_export_blocks(text)
    z, rows = _select_z_block(blocks, args.z)

    polygon_inputs = _rows_to_polygon_inputs(rows)
    geom = _build_sectionproperties_geometry(polygon_inputs)

    # Mesh and analyse.
    geom = geom.create_mesh(mesh_sizes=args.mesh)
    sec = Section(geometry=geom)
    sec.calculate_geometric_properties()
    sec.calculate_warping_properties()

    print(f"z = {z}")
    print("sectionproperties results:")
    sec.display_results()

    if args.plot:
        import matplotlib.pyplot as plt

        geom.plot_geometry()
        sec.plot_mesh(materials=False)
        plt.show()


if __name__ == "__main__":
    main()
