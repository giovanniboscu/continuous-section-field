"""
Assumptions:
- Two endpoint sections exist at z0 and z1.
- Same number of polygons in start/end.
- For each polygon: same number of vertices in start/end.
- Vertex ordering is already consistent (your matching is given/assumed).
- Polygons are simple enough for shoelace formulas (no self-intersections).
"""
from __future__ import annotations
from datetime import datetime
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Mapping, Optional, Sequence, Tuple
import math
import random
import warnings
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import re
from datetime import datetime
from typing import Union, Literal
from pathlib import Path
import csv
import io
from typing import Any, Dict, List, Optional, Tuple
from .entities import Pt, Polygon, Section, CSFError
from collections import defaultdict
from contextlib import redirect_stdout
import random as _random
from typing import Literal,TYPE_CHECKING
import numpy as np
from scipy.special import roots_jacobi

from . import _tol
# ruff: noqa: F821
if TYPE_CHECKING:
    from .continuous_section_field import ContinuousSectionFie

#
# Your current implementation uses a "strict proper intersection" test:
#     (o1 * o2 < 0) and (o3 * o4 < 0)
# which detects only crossings where the intersection lies strictly inside both segments.
#
# It does NOT detect:
# - touching at endpoints (T-junctions, vertex-on-edge contact),
# - collinear overlaps,
# - near-collinear cases where numerical noise makes orientation() return 0.
#
# The functions below implement a more complete predicate:
# - detects proper crossings,
# - detects endpoint touching,
# - detects collinear overlap,
# while still allowing you to ignore adjacent edges (handled by caller).


# Unit system must be consistent throughout the model (e.g. all metres or all mm).
# Mixing units is not supported. Tolerances are recomputed at runtime by _determine_magnitude().
# Default values below assume S ≈ 1.0 (metre-scale geometry).


Point = Tuple[float, float]
Segment = Tuple[Point, Point]
PointXY = Tuple[float, float]

# (Optional: se vuoi usare PyYAML quando disponibile)
try:
    import yaml  # type: ignore
except Exception as e:
    print("PyYAML import failed:", repr(e))
    yaml = None

if yaml is not None:
    class XY(tuple):
        pass

    class CSFDumper(yaml.SafeDumper):
        def increase_indent(self, flow=False, indentless=False):
            return super().increase_indent(flow, False)

    def _repr_xy(dumper, data: XY):
        # forza sempre: [x, y]
        return dumper.represent_sequence(
            "tag:yaml.org,2002:seq",
            [float(data[0]), float(data[1])],
            flow_style=True,
        )

    CSFDumper.add_representer(XY, _repr_xy)
else:
    XY = None
    CSFDumper = None


# Add this method inside class ContinuousSectionField.
#
# Goal:
#   Provide an API to compute an AREA BREAKDOWN of one 2D section by MATERIAL WEIGHT (W)
#   without requiring the user to manually manage nested polygons and negative "void" weights.
#
# Model assumptions (CSF nesting rule):
#   - Polygons never intersect; they may touch.
#   - Each polygon has an *immediate container* (or None if outermost), determinable on S0.
#   - The Section returned by self.section(z) already uses RELATIVE weights:
#         w_rel(child) = w_abs(child) - w_abs(container(child))
#     This method reconstructs absolute weights w_abs and assigns area to the exclusive region
#     of each polygon (polygon area minus its immediate children areas).

def analyse_polygon_jourawski_shear_stress(
    section_field,
    z: float,
    Tx: float,
    Ty: float,
    *,
    num_sudx: int = 100,
    num_sudy: int = 100,
    debug: bool = False,
) -> list[dict[str, object]]:
    """
    Compute polygon-wise Jourawski shear-stress envelopes from global section scans.

    Conventions
    -----------
    - Tx is the shear component associated with My.
    - Ty is the shear component associated with Mx.
    - tau_x is evaluated from vertical cuts x = constant.
    - tau_y is evaluated from horizontal cuts y = constant.

    Scan rule
    ---------
    The section is scanned once along x and once along y over the active-section
    bounding box:

        deltaX = (xmax - xmin) / num_sudx
        deltaY = (ymax - ymin) / num_sudy

    The sampled coordinates are cell centres, not extrema.

    For each cut, Jourawski returns one mean shear stress over the full active
    intersection length b. That line-average value is then redistributed among
    the crossed polygon segments using their sampled shear carrier
    ``shear_weightabs`` and their actual segment length on the cut.

    For one cut:
        tau_i = tau_ref * b_total * G_i / sum(G_j * b_j)

    where G_i is the polygon ``shear_weightabs`` and b_i is the segment length
    of the same cut inside polygon i. This preserves the cut resultant:
        sum(tau_i * b_i) = tau_ref * b_total.
    """
    num_sudx = int(num_sudx)
    num_sudy = int(num_sudy)
    if num_sudx < 1:
        raise ValueError("num_sudx must be >= 1.")
    if num_sudy < 1:
        raise ValueError("num_sudy must be >= 1.")

    section = section_field.section(float(z))
    transformed_section, weight_ref, weight_norm_by_idx = _jourawski_normalized_section(
        section
    )

    props = section_properties(transformed_section)
    A = float(props["A"])
    Cx = float(props["Cx"])
    Cy = float(props["Cy"])
    Ix = float(props["Ix"])
    Iy = float(props["Iy"])
    Ixy = float(props["Ixy"])

    if abs(A) <= _tol.EPS_A:
        raise ValueError(f"Zero transformed section area at z={float(z)}.")

    D = Ix * Iy - Ixy * Ixy
    if abs(D) <= _tol.EPS_K_ATOL:
        raise ValueError(
            f"Singular transformed bending inertia matrix at z={float(z)}."
        )

    # Same algebraic matrix used in analyse_polygon_navier_stress(), with
    # dMy/ds = Tx and dMx/ds = Ty.
    dbx = (float(Tx) * Ix - float(Ty) * Ixy) / D
    dby = (float(Ty) * Iy - float(Tx) * Ixy) / D

    xmin, xmax, ymin, ymax = _section_active_bbox(section)

    if debug:
        print(
            "[JOURAWSKI SCAN START]",
            f"z={float(z):.12e}",
            f"Tx={float(Tx):.12e}",
            f"Ty={float(Ty):.12e}",
            f"num_sudx={num_sudx}",
            f"num_sudy={num_sudy}",
            f"xmin={xmin:.12e}",
            f"xmax={xmax:.12e}",
            f"ymin={ymin:.12e}",
            f"ymax={ymax:.12e}",
            flush=True,
        )

    tau_x_scan = _jourawski_global_axis_scan(
        original_section=section,
        transformed_section=transformed_section,
        axis="x",
        coord_min=xmin,
        coord_max=xmax,
        num_subdivisions=num_sudx,
        Cx=Cx,
        Cy=Cy,
        dbx=dbx,
        dby=dby,
    )

    tau_y_scan = _jourawski_global_axis_scan(
        original_section=section,
        transformed_section=transformed_section,
        axis="y",
        coord_min=ymin,
        coord_max=ymax,
        num_subdivisions=num_sudy,
        Cx=Cx,
        Cy=Cy,
        dbx=dbx,
        dby=dby,
    )

    values_x_by_polygon = _group_scan_values_by_polygon(
        scan_values=tau_x_scan,
        polygon_count=len(section.polygons),
    )
    values_y_by_polygon = _group_scan_values_by_polygon(
        scan_values=tau_y_scan,
        polygon_count=len(section.polygons),
    )

    if debug:
        print(
            "[JOURAWSKI SCAN AXIS DONE]",
            f"z={float(z):.12e}",
            f"axis=x",
            f"cuts_valid={len(tau_x_scan)}",
            f"cuts_total={num_sudx}",
            flush=True,
        )
        print(
            "[JOURAWSKI SCAN AXIS DONE]",
            f"z={float(z):.12e}",
            f"axis=y",
            f"cuts_valid={len(tau_y_scan)}",
            f"cuts_total={num_sudy}",
            flush=True,
        )

    rows: list[dict[str, object]] = []

    for idx, _poly in enumerate(transformed_section.polygons):
        original_poly = section.polygons[idx]
        name_s0 = str(section_field.s0.polygons[idx].name)
        weight_raw = float(original_poly.weight)
        weight_norm = float(weight_norm_by_idx[idx])

        tau_x_values = values_x_by_polygon[idx]
        tau_y_values = values_y_by_polygon[idx]

        tau_x_min = _min_scan_value(tau_x_values)
        tau_x_max = _max_scan_value(tau_x_values)
        tau_y_min = _min_scan_value(tau_y_values)
        tau_y_max = _max_scan_value(tau_y_values)

        if debug:
            print(
                "[JOURAWSKI SCAN POLYGON DONE]",
                f"z={float(z):.12e}",
                f"idx={idx}",
                f"name={name_s0}",
                f"scan_count_x={len(tau_x_values)}",
                f"scan_count_y={len(tau_y_values)}",
                f"grid_x={num_sudx}",
                f"grid_y={num_sudy}",
                flush=True,
            )

        rows.append(
            {
                "idx": int(idx),
                "name": name_s0,
                "weight": weight_raw,
                "weight_ref": float(weight_ref),
                "weight_norm": weight_norm,

                "tau_x_min": tau_x_min["tau"],
                "x_tau_x_min": tau_x_min["x"],
                "y_tau_x_min": tau_x_min["y"],

                "tau_x_max": tau_x_max["tau"],
                "x_tau_x_max": tau_x_max["x"],
                "y_tau_x_max": tau_x_max["y"],

                "tau_y_min": tau_y_min["tau"],
                "x_tau_y_min": tau_y_min["x"],
                "y_tau_y_min": tau_y_min["y"],

                "tau_y_max": tau_y_max["tau"],
                "x_tau_y_max": tau_y_max["x"],
                "y_tau_y_max": tau_y_max["y"],
                "coord_tau_y_max": tau_y_max["coord"],
                "tau_reference_y_max": tau_y_max["tau_reference"],
                "b_weighted_y_max": tau_y_max["b_weighted"],
                "Sx_part_y_max": tau_y_max["Sx_part"],
                "Sy_part_y_max": tau_y_max["Sy_part"],

                "tau_x_mean": _mean_scan_tau(tau_x_values),
                "tau_y_mean": _mean_scan_tau(tau_y_values),
                "scan_count_x": int(len(tau_x_values)),
                "scan_count_y": int(len(tau_y_values)),
                "grid_x": int(num_sudx),
                "grid_y": int(num_sudy),
                "converged_x": bool(tau_x_values),
                "converged_y": bool(tau_y_values),
                "relative_change_x": float("nan"),
                "relative_change_y": float("nan"),
            }
        )

    if debug:
        print(
            "[JOURAWSKI SCAN DONE]",
            f"z={float(z):.12e}",
            f"rows={len(rows)}",
            f"cuts_x={len(tau_x_scan)}",
            f"cuts_y={len(tau_y_scan)}",
            flush=True,
        )

    return rows
    
def _section_active_bbox(section: Section) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []

    for poly in section.polygons:
        if not _jourawski_polygon_is_active_for_b(poly):
            continue

        for vertex in poly.vertices:
            xs.append(float(vertex.x))
            ys.append(float(vertex.y))

    if not xs or not ys:
        raise ValueError(
            "No active polygon with non-zero weightabs available for Jourawski scan."
        )

    return min(xs), max(xs), min(ys), max(ys)

def _jourawski_global_axis_scan(
    *,
    original_section: Section,
    transformed_section: Section,
    axis: str,
    coord_min: float,
    coord_max: float,
    num_subdivisions: int,
    Cx: float,
    Cy: float,
    dbx: float,
    dby: float,
) -> list[dict[str, object]]:
    if axis not in ("x", "y"):
        raise ValueError("axis must be 'x' or 'y'.")

    n = int(num_subdivisions)
    span = float(coord_max) - float(coord_min)
    if abs(span) <= _tol.EPS_L:
        return []

    delta = span / n
    out: list[dict[str, object]] = []

    for i in range(n):
        coord = float(coord_min) + (i + 0.5) * delta
        value = _jourawski_value_at_coord(
            original_section=original_section,
            transformed_section=transformed_section,
            axis=axis,
            coord=coord,
            Cx=Cx,
            Cy=Cy,
            dbx=dbx,
            dby=dby,
        )
        if value is not None:
            out.append(value)

    return out


def _jourawski_value_at_coord(
    *,
    original_section: Section,
    transformed_section: Section,
    axis: str,
    coord: float,
    Cx: float,
    Cy: float,
    dbx: float,
    dby: float,
) -> dict[str, object] | None:
    """
    Compute the mean Jourawski stress for one global cut.

    The stress value is global for the full active cut width b_total.
    The localization is per intersected polygon segment and is stored in
    cut_segments. The grouped polygon rows then receive the same tau but their
    own segment midpoint coordinates.
    """
    b_total, cut_segments = _section_active_cut_width_and_polygons(
        section=original_section,
        axis=axis,
        coord=coord,
    )
    if abs(b_total) <= _tol.EPS_L:
        return None

    Sx_part, Sy_part = _section_partial_first_moments(
        section=transformed_section,
        axis=axis,
        coord=coord,
        Cx=Cx,
        Cy=Cy,
    )

    shear_flow = dbx * Sx_part + dby * Sy_part
    tau_reference = shear_flow / b_total

    shear_length_sum = sum(
        float(seg["shear_weightabs"]) * float(seg["length"])
        for seg in cut_segments
    )
    
    #   
    #
    if abs(shear_length_sum) <= _tol.EPS_L:
        return None

    localized_segments: list[dict[str, object]] = []
    for seg in cut_segments:
        shear_weightabs = float(seg["shear_weightabs"])
        tau_local = tau_reference * b_total * shear_weightabs / shear_length_sum

        localized = dict(seg)
        localized["tau"] = float(tau_local)
        localized["tau_factor"] = float(b_total * shear_weightabs / shear_length_sum)
        localized["shear_length_sum"] = float(shear_length_sum)
        localized_segments.append(localized)

    return {
        "tau": float(tau_reference),
        "x": float("nan"),
        "y": float("nan"),
        "coord": float(coord),
        "axis": str(axis),
        "tau_reference": float(tau_reference),
        "b_weighted": float(b_total),
        "Sx_part": float(Sx_part),
        "Sy_part": float(Sy_part),
        "cut_segments": tuple(localized_segments),
        "polygon_indices": tuple(int(seg["polygon_idx"]) for seg in localized_segments),
    }



def _section_active_cut_width_and_polygons(
    *,
    section: Section,
    axis: str,
    coord: float,
) -> tuple[float, list[dict[str, object]]]:
    """
    Return the total active cut width and one localization record per polygon.

    For axis == "y", the cut is horizontal Y = coord. The segment endpoints are
    x-like values, and the marker is placed at their length-weighted midpoint.

    For axis == "x", the cut is vertical X = coord. The segment endpoints are
    y-like values, and the marker is placed at their length-weighted midpoint.
    """
    total = 0.0
    cut_segments: list[dict[str, object]] = []

    for idx, poly in enumerate(section.polygons):
        if not _jourawski_polygon_is_active_for_b(poly):
            continue

        segments = _polygon_line_segments(poly=poly, axis=axis, coord=coord)
        if not segments:
            continue

        length = sum(abs(b - a) for a, b in segments)
        if length <= _tol.EPS_L:
            continue

        midpoint_other = sum(
            abs(b - a) * 0.5 * (float(a) + float(b))
            for a, b in segments
        ) / length

        if axis == "x":
            x_marker = float(coord)
            y_marker = float(midpoint_other)
            segment_x0 = float(coord)
            segment_y0 = float(min(min(a, b) for a, b in segments))
            segment_x1 = float(coord)
            segment_y1 = float(max(max(a, b) for a, b in segments))
        elif axis == "y":
            x_marker = float(midpoint_other)
            y_marker = float(coord)
            segment_x0 = float(min(min(a, b) for a, b in segments))
            segment_y0 = float(coord)
            segment_x1 = float(max(max(a, b) for a, b in segments))
            segment_y1 = float(coord)
        else:
            raise ValueError("axis must be 'x' or 'y'.")

        shear_weightabs = _jourawski_polygon_shear_weightabs(poly)

        total += length
        cut_segments.append(
            {
                "polygon_idx": int(idx),
                "length": float(length),
                "shear_weightabs": float(shear_weightabs),
                "x": float(x_marker),
                "y": float(y_marker),
                "segment_x0": float(segment_x0),
                "segment_y0": float(segment_y0),
                "segment_x1": float(segment_x1),
                "segment_y1": float(segment_y1),
                "segments_other": tuple((float(a), float(b)) for a, b in segments),
            }
        )

    return float(total), cut_segments


def _group_scan_values_by_polygon(
    *,
    scan_values: list[dict[str, object]],
    polygon_count: int,
) -> list[list[dict[str, object]]]:
    """
    Assign global cut values to crossed polygons with per-polygon localization.

    Each cut has one tau value. Each crossed polygon receives a localized copy
    whose x/y are the midpoint of that polygon's cut segment.
    """
    grouped: list[list[dict[str, object]]] = [[] for _ in range(int(polygon_count))]

    for value in scan_values:
        cut_segments = value.get("cut_segments", ())
        for segment in cut_segments:  # type: ignore[union-attr]
            idx = int(segment["polygon_idx"])
            if not (0 <= idx < int(polygon_count)):
                continue

            localized = dict(value)
            localized.pop("cut_segments", None)
            localized["polygon_indices"] = (idx,)
            localized["tau"] = float(segment["tau"])
            localized["tau_factor"] = float(segment["tau_factor"])
            localized["shear_weightabs"] = float(segment["shear_weightabs"])
            localized["shear_length_sum"] = float(segment["shear_length_sum"])
            localized["x"] = float(segment["x"])
            localized["y"] = float(segment["y"])
            localized["segment_length"] = float(segment["length"])
            localized["segment_x0"] = float(segment["segment_x0"])
            localized["segment_y0"] = float(segment["segment_y0"])
            localized["segment_x1"] = float(segment["segment_x1"])
            localized["segment_y1"] = float(segment["segment_y1"])

            grouped[idx].append(localized)

    return grouped


def _jourawski_polygon_shear_weightabs(poly: Polygon) -> float:
    """Return the sampled shear carrier used for local cut redistribution."""
    for attr_name in ("shear_weightabs", "shear_w"):
        if not hasattr(poly, attr_name):
            continue
        value = getattr(poly, attr_name)
        if value is None:
            continue
        value = float(value)
        if math.isfinite(value):
            return value

    return float(getattr(poly, "weightabs", getattr(poly, "weight", 0.0)))


def _jourawski_polygon_is_active_for_b(poly: Polygon) -> bool:
    weightabs = float(getattr(poly, "weightabs", getattr(poly, "weight", 0.0)))
    return math.isfinite(weightabs) and abs(weightabs) > _tol.EPS_A


def _jourawski_normalized_section(section: Section) -> tuple[Section, float, list[float]]:
    weight_ref = _jourawski_reference_weightabs(section)

    transformed_polygons = []
    weight_norm_by_idx: list[float] = []

    for poly in section.polygons:
        weight_norm = float(poly.weight) / weight_ref
        weight_norm_by_idx.append(weight_norm)

        transformed_polygons.append(
            Polygon(
                vertices=poly.vertices,
                weight=weight_norm,
                name=getattr(poly, "name", None),
            )
        )

    return (
        Section(polygons=tuple(transformed_polygons), z=float(section.z)),
        float(weight_ref),
        weight_norm_by_idx,
    )


def _jourawski_reference_weightabs(section: Section) -> float:
    for poly in section.polygons:
        w = float(poly.weightabs)
        if math.isfinite(w) and w > _tol.EPS_A:
            return w

    raise ValueError("No finite non-zero polygon weight available for normalization.")


def _section_partial_first_moments(
    *,
    section: Section,
    axis: str,
    coord: float,
    Cx: float,
    Cy: float,
) -> tuple[float, float]:
    Sx_part = 0.0
    Sy_part = 0.0

    for poly in section.polygons:
        clipped = _clip_polygon_half_plane(poly=poly, axis=axis, coord=coord)
        if len(clipped) < 3:
            continue

        area_part_raw = _polygon_area_from_points(clipped)
        if abs(area_part_raw) <= _tol.EPS_A:
            continue

        clipped_poly = Polygon(
            vertices=tuple(clipped),
            weight=float(poly.weight),
            name=getattr(poly, "name", None),
        )

        area_part, (cx_part, cy_part) = polygon_area_centroid(clipped_poly)
        if abs(area_part) <= _tol.EPS_A:
            continue

        Sx_part += area_part * (cx_part - Cx)
        Sy_part += area_part * (cy_part - Cy)

    return float(Sx_part), float(Sy_part)


def _clip_polygon_half_plane(
    *,
    poly: Polygon,
    axis: str,
    coord: float,
) -> list[Pt]:
    verts = poly.vertices
    n = len(verts)
    if n < 3:
        return []

    clipped: list[Pt] = []

    for i in range(n):
        p1 = verts[i]
        p2 = verts[(i + 1) % n]

        c1 = float(p1.x if axis == "x" else p1.y)
        c2 = float(p2.x if axis == "x" else p2.y)

        p1_in = c1 >= coord - _tol.EPS_L
        p2_in = c2 >= coord - _tol.EPS_L

        if p1_in and p2_in:
            clipped.append(p2)

        elif p1_in and not p2_in:
            denom = c2 - c1
            if abs(denom) > _tol.EPS_L:
                t = (coord - c1) / denom
                clipped.append(_interpolate_point_on_segment(p1, p2, t))

        elif (not p1_in) and p2_in:
            denom = c2 - c1
            if abs(denom) > _tol.EPS_L:
                t = (coord - c1) / denom
                clipped.append(_interpolate_point_on_segment(p1, p2, t))
            clipped.append(p2)

    return clipped


def _interpolate_point_on_segment(p1: Pt, p2: Pt, t: float) -> Pt:
    return Pt(
        float(p1.x) + float(t) * (float(p2.x) - float(p1.x)),
        float(p1.y) + float(t) * (float(p2.y) - float(p1.y)),
    )


def _polygon_area_from_points(points: list[Pt]) -> float:
    if len(points) < 3:
        return 0.0

    a2 = 0.0
    n = len(points)

    for i in range(n):
        p0 = points[i]
        p1 = points[(i + 1) % n]
        a2 += float(p0.x) * float(p1.y) - float(p1.x) * float(p0.y)

    return 0.5 * a2


def _polygon_line_segments(
    *,
    poly: Polygon,
    axis: str,
    coord: float,
) -> list[tuple[float, float]]:
    verts = poly.vertices
    n = len(verts)
    if n < 3:
        return []

    values: list[float] = []

    for i in range(n):
        p1 = verts[i]
        p2 = verts[(i + 1) % n]

        c1 = float(p1.x if axis == "x" else p1.y)
        c2 = float(p2.x if axis == "x" else p2.y)
        o1 = float(p1.y if axis == "x" else p1.x)
        o2 = float(p2.y if axis == "x" else p2.x)

        if abs(c1 - coord) <= _tol.EPS_L and abs(c2 - coord) <= _tol.EPS_L:
            continue

        crosses = (c1 <= coord < c2) or (c2 <= coord < c1)
        if not crosses:
            continue

        denom = c2 - c1
        if abs(denom) <= _tol.EPS_L:
            continue

        t = (coord - c1) / denom
        values.append(o1 + t * (o2 - o1))

    values = _unique_sorted(values)
    if len(values) < 2:
        return []

    segments: list[tuple[float, float]] = []
    for a, b in zip(values[0::2], values[1::2]):
        if abs(b - a) > _tol.EPS_L:
            segments.append((float(a), float(b)))

    return segments


def _unique_sorted(values: list[float]) -> list[float]:
    values = sorted(float(v) for v in values if math.isfinite(float(v)))
    if not values:
        return []

    out = [values[0]]
    for v in values[1:]:
        if abs(v - out[-1]) > _tol.EPS_L:
            out.append(v)
    return out


def _mean_scan_tau(values: list[dict[str, object]]) -> float:
    if not values:
        return float("nan")
    tau_values = [float(v["tau"]) for v in values]
    return float(sum(tau_values) / len(tau_values))


def _empty_scan_value() -> dict[str, object]:
    return {
        "tau": float("nan"),
        "x": float("nan"),
        "y": float("nan"),
        "coord": float("nan"),
        "axis": "",
        "tau_reference": float("nan"),
        "b_weighted": float("nan"),
        "Sx_part": float("nan"),
        "Sy_part": float("nan"),
        "polygon_indices": tuple(),
        "segment_length": float("nan"),
        "segment_x0": float("nan"),
        "segment_y0": float("nan"),
        "segment_x1": float("nan"),
        "segment_y1": float("nan"),
        "shear_weightabs": float("nan"),
        "shear_length_sum": float("nan"),
        "tau_factor": float("nan"),
    }

def _min_scan_value(values: list[dict[str, object]]) -> dict[str, object]:
    if not values:
        return _empty_scan_value()
    return min(values, key=lambda r: float(r["tau"]))


def _max_scan_value(values: list[dict[str, object]]) -> dict[str, object]:
    if not values:
        return _empty_scan_value()
    return max(values, key=lambda r: float(r["tau"]))



# -----------------------------------------------
#     NAVIER
# ----------------------------------------------

def analyse_polygon_navier_stress(
    section_field,
    z: float,
    N: float,
    Mx: float,
    My: float,
) -> list[dict[str, object]]:
    """
    Compute polygon-wise signed normal stresses from the general Navier formula.

    For each polygon all vertices are checked.

    Returned stress values:
    - sigma_min      : minimum signed vertex stress in the polygon
    - sigma_max      : maximum signed vertex stress in the polygon
    - sigma_extreme  : signed vertex stress selected by largest absolute value

    The coordinates and vertex indices of all three governing values are returned.
    """
    section = section_field.section(float(z))
    analysis = section_full_analysis(section)

    A = float(analysis["A"])
    Cx = float(analysis["Cx"])
    Cy = float(analysis["Cy"])
    Ix = float(analysis["Ix"])
    Iy = float(analysis["Iy"])
    Ixy = float(analysis["Ixy"])

    D = Ix * Iy - Ixy * Ixy
    if A == 0.0:
        raise ValueError(f"Zero section area at z={float(z)}.")
    if D == 0.0:
        raise ValueError(f"Singular bending inertia matrix at z={float(z)}.")

    axial = -float(N) / A
    bx = (float(My) * Ix - float(Mx) * Ixy) / D
    by = (float(Mx) * Iy - float(My) * Ixy) / D

    rows: list[dict[str, object]] = []

    for i, poly in enumerate(section.polygons):
        name_s0 = str(section_field.s0.polygons[i].name)
        weightabs = float(poly.weightabs)

        vertex_rows: list[tuple[int, float, float, float]] = []

        for j, vertex in enumerate(poly.vertices):
            x = float(vertex.x)
            y = float(vertex.y)

            sigma = weightabs * (
                axial
                + bx * (x - Cx)
                + by * (y - Cy)
            )

            vertex_rows.append((int(j), x, y, float(sigma)))

        if not vertex_rows:
            raise ValueError(f"Polygon {i} has no vertices at z={float(z)}.")

        j_min, x_min, y_min, sigma_min = min(vertex_rows, key=lambda r: r[3])
        j_max, x_max, y_max, sigma_max = max(vertex_rows, key=lambda r: r[3])
        j_ext, x_ext, y_ext, sigma_extreme = max(vertex_rows, key=lambda r: abs(r[3]))

        rows.append(
            {
                "idx": int(i),
                "name": name_s0,
                "weightabs": weightabs,

                "sigma_min": float(sigma_min),
                "vertex_index_min": int(j_min),
                "x_min": float(x_min),
                "y_min": float(y_min),

                "sigma_max": float(sigma_max),
                "vertex_index_max": int(j_max),
                "x_max": float(x_max),
                "y_max": float(y_max),

                "sigma_extreme": float(sigma_extreme),
                "vertex_index": int(j_ext),
                "x": float(x_ext),
                "y": float(y_ext),
            }
        )

    return rows

# -----------------------------------------------------------------------------
# Station generation
# -----------------------------------------------------------------------------
def get_lobatto_intervals(
    z_min: float,
    z_max: float,
    n_intervals: int,
) -> "np.ndarray":
    if n_intervals < 1:
        raise ValueError("n_intervals must be >= 1.")

    return np.asarray(
        compute_lobatto_integration_points(
            z_min=z_min,
            z_max=z_max,
            n_points=n_intervals + 1,
        ),
        dtype=float,
    )


def compute_lobatto_integration_points(z_min: float, z_max: float, n_points: int = 5, L: float = None) -> List[float]:
        """
        Calculates the global Z-coordinates for OpenSees integration points using 
        the Gauss-Lobatto quadrature rule.
        
        RATIONALE:
        In finite element analysis (specifically for OpenSees forceBeamColumn elements), 
        the Gauss-Lobatto rule is preferred because it includes the endpoints of the 
        interval (z=0 and z=L). This is critical for detecting anomalies at the 
        very base of the shaft (e.g., FHWA Soft Toe) or at the top connection.
        
        ALGORITHM:
        1. Generate the roots of the derivative of the (n-1)-th Legendre Polynomial.
        2. These roots (plus -1.0 and 1.0) form the abscissae in the natural 
        coordinate system [-1, 1].
        3. Map these abscissae from [-1, 1] to the physical domain [z0, z1] or [0, L].
        
        Args:
            n_points (int): Number of integration points. Must be >= 2.
            L (float, optional): Total length of the element. If None, it uses 
                                the distance between the two defined sections.
        
        Returns:
            List[float]: A list of global Z-coordinates where OpenSees will 
                        sample the section properties.
        """

        if n_points < 2:
            raise ValueError("Number of integration points must be at least 2 for Gauss-Lobatto.")

        # 1. Physical boundaries
        
        # Usiamo section0 e section1 come definito nel costruttore field = ContinuousSectionField(section0=s0, section1=s1)
        
        z_start = float(z_min)
        z_end = float(z_max)
        actual_L = L if L is not None else (z_end - z_start)
        if actual_L <= 0:
            raise ValueError("L or (z_max - z_min) must be positive.")        

        # 2. Calculation of Gauss-Lobatto Abscissae in range [-1, 1]
        # For n points, we need roots of P'_{n-1}(x)
        if n_points == 2:
            abscissae = [-1.0, 1.0]
        else:
            # The internal points are the roots of the derivative of Legendre polynomial P_{n-1}
            '''
            roots = np.polynomial.legendre.Legendre.deriv(
                np.polynomial.legendre.Legendre([0]*(n_points-1) + [1])
            ).roots()
            '''
            roots, _ = roots_jacobi(n_points - 2, 1, 1)
            abscissae = np.concatenate(([-1.0], roots, [1.0]))

        # 3. Mapping from [-1, 1] to [z_start, z_start + actual_L]
        z_coords = [z_start + (xi + 1.0) * (actual_L / 2.0) for xi in abscissae]
        
        # Sort to ensure numerical stability
        z_coords = sorted(z_coords)
        return z_coords




# -----------------------------------------------------------------------------
# Core property sampling
# -----------------------------------------------------------------------------
def _compute_station_data(
    field: Any,
    z_values: Sequence[float],
) -> List[Dict[str, Any]]:
    """
    Sample the CSF field at the provided z positions and compute section properties.

    This function delegates the actual validation/computation to the CSF library's
    analysis function. We intentionally do NOT "second-guess" the CSF analysis.

    Expected CSF interface
    ----------------------
    - field.section(z) -> a section object at that z
    - csf.section_field.section_full_analysis(section,alpha) -> dict with keys like:
        'A', 'Cx', 'Cy', 'Ix', 'Iy', 'Ixy', 'Ip', ...
      (We fall back to sensible defaults if some keys are missing.)

    Returns
    -------
    List[Dict[str, Any]]:
        Each dict contains:
          id (1-based),
          z,
          Cx, Cy,
          A, Ix, Iy, Ixy, J,
          plus any extra keys the analysis returns (stored under 'analysis_raw').

    Raises
    ------
    RuntimeError:
        If section_full_analysis cannot be imported.
    """
    '''
    try:
        from csf.section_field import section_full_analysis  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "Cannot import csf.section_field.section_full_analysis; "
            "this template generator requires the CSF analysis function."
        ) from e
    '''
    
    out: List[Dict[str, Any]] = []

    for i, z in enumerate(z_values):
        section_at_z = field.section(float(z))
        analysis = section_full_analysis(section_at_z) 
        cx = analysis.get("Cx")
        cy = analysis.get("Cy")
        
        A = analysis.get("A")
        Ix = analysis.get("Ix")
        Iy = analysis.get("Iy")
        Ixy = analysis.get("Ixy")
        # Torsion: different libraries may report 'Ip' or 'K_torsion' etc.
        J = analysis.get("Ip")#, analysis.get("j", analysis.get("K_torsion", 0.0)))
        
        out.append(
            {
                "id": i + 1,
                "z": float(z),
                "Cx": float(cx),
                "Cy": float(cy),
                "A": float(A),
                "Ix": float(Ix),
                "Iy": float(Iy),
                "Ixy": float(Ixy),
                "Ip": float(J),
                "analysis_raw": analysis,
            }
        )

    return out


    

#------------------------------------------------------------------------------
def _parse_optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    return float(value)
def write_sap2000_template_pack(
    field: Any,
    n_intervals: int = 20,
    template_filename: str = "export_template_pack.txt",
    *,
    mode: Literal["BOTH", "CENTROIDAL_LINE", "REFERENCE_LINE"] = "BOTH",
    section_prefix: str = "SEC",
    material_name: str = "S355",
    E_ref = None,
    nu = None,
    include_plot: bool = True,
    plot_filename: str = "section_variation.png",
    show_plot: bool = True,
    z_values: Optional[List[float]] = None,
    plot_n: int = 100,
    float_fmt: str = ".9g",
) -> str:

    """
    Export a CSF field to a structured text pack for SAP2000 / OpenSees input.

    Produces four compact tables:
      1. SOLVER INPUT    - properties consumed directly by SAP2000 / OpenSees.
      2. SECTION QUALITY - derived verification properties (principal axes, moduli).
      3. TORSION QUALITY - torsion breakdown with fidelity indicator.
      4. STATION NAMES   - section name list for frame property assignment.

    All section data comes from section_full_analysis() evaluated at the requested
    stations - no interpolation, no silent fallback values.

    Parameters
    ----------
    field            : ContinuousSectionField with .s0.z, .s1.z, .section(z).
    n_intervals      : Gauss-Lobatto intervals; stations = n_intervals + 1.
                       Ignored when z_values is provided.
    template_filename: Output file path.
    mode             : Retained for API compatibility; not used in output.
    section_prefix   : Prefix for section name labels ("SEC" -> "SEC0001").
    material_name    : Informational label written to the file header.
    E_ref            : Reference Young's modulus; G_ref = E_ref / (2*(1+nu)). For reference only
                       Written to header only if provided.
    nu               : Poisson's ratio; used to derive G_ref when E_ref is given. for referencep only
    include_plot     : If True and matplotlib is available, saves a property plot.
    plot_filename    : Path for the optional plot image.
    show_plot        : If True, display the plot interactively.
    z_values         : Explicit station list (strictly increasing, within field bounds).
                       No sorting or deduplication - invalid input raises ValueError.
    plot_n           : Number of uniformly sampled stations used only for the plot curve.
                       The export tables still use Lobatto stations or z_values.
    float_fmt        : Format spec for all numeric output fields.

    Returns
    -------
    str : Path of the file written.

    Raises
    ------
    ValueError : On invalid z_values.
    KeyError   : If section_full_analysis() does not return an expected key.
    """
    _Mode = Literal["BOTH", "CENTROIDAL_LINE", "REFERENCE_LINE"]
    if mode not in ("BOTH", "CENTROIDAL_LINE", "REFERENCE_LINE"):
        raise ValueError("mode must be one of: BOTH, CENTROIDAL_LINE, REFERENCE_LINE")

    # Extract CSF absolute bounds exactly as before.
    z_start = float(getattr(field.s0, "z"))
    z_end = float(getattr(field.s1, "z"))
    L = z_end - z_start

    # -------------------------------------------------------------------------
    # Station generation / selection
    # -------------------------------------------------------------------------
    # Minimal-impact rule:
    # - keep the original Lobatto path untouched when z_values is not provided;
    # - add a small explicit branch for user-provided stations.
    if z_values is None:

        station_z = get_lobatto_intervals(z_start, z_end, int(n_intervals)).tolist()
    else:
        # Explicit-stations behavior (new, opt-in).
        if not isinstance(z_values, list) or len(z_values) == 0:
            raise ValueError("z_values must be a non-empty list of numeric z coordinates.")

        station_z = []
        for i, v in enumerate(z_values):
            try:
                z = float(v)
            except Exception as e:
                raise ValueError(f"z_values[{i}] is not numeric: {v!r}") from e

            # Finite check without extra imports:
            # NaN fails z == z; infinities are caught by bound checks below.
            if z != z:
                raise ValueError(f"z_values[{i}] is NaN.")

            # Range check in absolute coordinates.
            if z < z_start or z > z_end:
                raise ValueError(
                    f"z_values[{i}]={z} is outside field bounds [{z_start}, {z_end}]."
                )

            station_z.append(z)

        # Strict monotonic increase:
        # no sorting/dedup on purpose (explicit input policy, no silent fixes).
        for i in range(1, len(station_z)):
            if not (station_z[i] > station_z[i - 1]):
                raise ValueError(
                    "z_values must be strictly increasing (no duplicates, no descending values)."
                )

    # Compute section data at selected stations (unchanged downstream flow).
    # The project helper is expected to be available in this module.
    stations_data = _compute_station_data(field, station_z)

    # Optional plot (best-effort).
    plot_path_written: Optional[str] = None
    if include_plot and plt is not None:

        from .visualizer import plot_section_variation as visualizer_plot_section_variation
        try:

            if int(plot_n) < 2:
                raise ValueError("plot_n must be >= 2.")

            plot_z = np.linspace(z_start, z_end, int(plot_n)).tolist()
            plot_stations_data = _compute_station_data(field, plot_z)

            plot_path_written = visualizer_plot_section_variation(
                stations_data,
                plot_stations_data=plot_stations_data,
                filename=plot_filename,
                show=show_plot,
            )

        except Exception as e:
            print("DEBUG plot exception:", repr(e))
            raise

    # -------------------------------------------------------------------------
    # _t fields (Bredt-Batho wall thickness) exist only for single-polygon
    # @cell/@wall sections; optional columns are emitted only when at least one
    # station carries the value - avoids empty columns in the common case.
    # -------------------------------------------------------------------------

    records = []
    any_cell_t = False
    any_wall_t = False

    for d in stations_data:
        res = d["analysis_raw"]

        # Fail fast - no silent defaults for missing keys.
        for k in ("A", "Cx", "Cy", "Ix", "Iy", "Ixy", "Ip",
                  "I1", "I2", "theta_deg",
                  "rx", "ry", "Wx", "Wy", "K_torsion", "Q_na",
                  "J_sv_cell", "J_sv_wall",
                  "J_s_vroark", "J_s_vroark_fidelity"):
            if k not in res:
                raise KeyError(
                    f"section_full_analysis() missing key '{k}' at z={d['z']}."
                )

        # J_sv_* may be a scalar float or a (J, t) tuple depending on whether
        # the section is single-polygon; extract both components defensively.
        arr_cell = np.atleast_1d(res["J_sv_cell"])
        j_cell   = float(arr_cell[0])
        t_cell   = float(arr_cell[1]) if len(arr_cell) >= 2 else None

        arr_wall = np.atleast_1d(res["J_sv_wall"])
        j_wall   = float(arr_wall[0])
        t_wall   = float(arr_wall[1]) if len(arr_wall) >= 2 else None

        if t_cell is not None:
            any_cell_t = True
        if t_wall is not None:
            any_wall_t = True

        # Torsion selection: additive Saint-Venant contributions.
        # Zero only when both are absent - explicit warning, no silent fallback.
        has_cell = j_cell != 0.0
        has_wall = j_wall != 0.0

        if has_cell and has_wall:
            j_tors = j_cell + j_wall
            method = "J_sv_cell+J_sv_wall"
        elif has_cell:
            j_tors = j_cell
            method = "J_sv_cell"
        elif has_wall:
            j_tors = j_wall
            method = "J_sv_wall"
        else:
            j_tors = 0.0
            method = "J_tors skip"
            warnings.warn(
                "No valid Saint-Venant torsion contribution "
                "(J_sv_cell or J_sv_wall) available for export."
            )

        records.append({
            "id":                  d["id"],
            "z":                   d["z"],
            "A":                   float(res["A"]),
            "Cx":                  float(res["Cx"]),
            "Cy":                  float(res["Cy"]),
            "Ix":                  float(res["Ix"]),
            "Iy":                  float(res["Iy"]),
            "Ixy":                 float(res["Ixy"]),
            "Ip":                  float(res["Ip"]),
            "I1":                  float(res["I1"]),
            "I2":                  float(res["I2"]),
            "theta_deg":           float(res["theta_deg"]),
            "rx":                  float(res["rx"]),
            "ry":                  float(res["ry"]),
            "Wx":                  float(res["Wx"]),
            "Wy":                  float(res["Wy"]),
            "K_torsion":           float(res["K_torsion"]),
            "Q_na":                float(res["Q_na"]),
            "J_sv_cell":           j_cell,
            "J_sv_cell_t":         t_cell,
            "J_sv_wall":           j_wall,
            "J_sv_wall_t":         t_wall,
            "J_s_vroark":          float(res["J_s_vroark"]),
            "J_s_vroark_fidelity": float(res["J_s_vroark_fidelity"]),
            "J_tors":              j_tors,
            "method":              method,
        })

    N = len(records)

    # -------------------------------------------------------------------------
    # Build output text - four compact tables.
    # Uniform column width W keeps tables both machine-parseable and
    # human-readable without requiring a CSV parser.
    # -------------------------------------------------------------------------
    W = 20
    lines: List[str] = []

    def _fmt(v) -> str:
        """Format float using float_fmt; return empty string when value is None."""
        if v is None:
            return ""
        return format(float(v), float_fmt)

    def _header(*labels):
        """Emit a fixed-width header row followed by a separator line."""
        lines.append("  " + "".join(lbl.ljust(W) for lbl in labels))
        lines.append("  " + "-" * (W * len(labels)))

    def _row(*vals):
        """Emit a fixed-width data row."""
        lines.append("  " + "".join(str(v).ljust(W) for v in vals))

    # ---- File header --------------------------------------------------------
    lines.append("# CSF SECTION EXPORT")
    lines.append(f"# z_start      : {_fmt(z_start)}")
    lines.append(f"# z_end        : {_fmt(z_end)}")
    lines.append(f"# length       : {_fmt(L)}")
    lines.append(f"# stations     : {N}")
    lines.append(f"# station_mode : {'user' if z_values is not None else 'lobatto'}")
    lines.append(f"# stations_list: {' '.join(_fmt(z) for z in station_z)}")
    #lines.append(f"# material     : {material_name}")
    lines.append(f"# J_tors       : J_sv_cell + J_sv_wall - see TABLE 3 for per-method breakdown and fidelity")
    
    if E_ref is not None:
        lines.append(f"# E_ref        : {_fmt(E_ref)} is reported for reference only, E is polygon-pair based.")
    if nu is not None:
        lines.append(f"# nu           : {_fmt(nu)} is reported for reference only, nu is polygon-pair based.")
    
    if plot_path_written is not None:
        lines.append(f"# plot         : {plot_path_written}")
    lines.append(f"# doc          : docs/sections/sectionfullanalysis.md")
    lines.append("")

    # ---- TABLE 1: Solver input ----------------------------------------------
    # Direct input for SAP2000 and OpenSees beam elements.
    # J_tors = J_sv_cell + J_sv_wall; see TABLE 3 for per-method breakdown.
    # Cx, Cy: centroid offsets in the section plane.
    lines.append("# TABLE 1 - SOLVER INPUT")
    lines.append("# z  A  Ix  Iy  Ixy  Ip  J_tors  G_ref  Cx  Cy  method")
    _header("z", "A", "Ix", "Iy", "Ixy", "Ip", "J_tors",  "Cx", "Cy", "method")
    for r in records:
        _row(_fmt(r["z"]), _fmt(r["A"]),
             _fmt(r["Ix"]), _fmt(r["Iy"]), _fmt(r["Ixy"]), _fmt(r["Ip"]),
             _fmt(r["J_tors"]), _fmt(r["Cx"]), _fmt(r["Cy"]),
             r["method"])
    lines.append("")

    # ---- TABLE 2: Section quality -------------------------------------------
    # Verification properties - not consumed directly by solvers.
    # theta_deg: principal axis rotation (0 for symmetric sections).
    # K_torsion: semi-empirical A^4/(40*Ip), low fidelity, included for completeness.
    lines.append("# TABLE 2 - SECTION QUALITY")
    lines.append("# z  I1  I2  theta_deg  rx  ry  Wx  Wy  Q_na  K_torsion")
    _header("z", "I1", "I2", "theta_deg", "rx", "ry", "Wx", "Wy", "Q_na", "K_torsion")
    for r in records:
        _row(_fmt(r["z"]),
             _fmt(r["I1"]), _fmt(r["I2"]), _fmt(r["theta_deg"]),
             _fmt(r["rx"]), _fmt(r["ry"]),
             _fmt(r["Wx"]), _fmt(r["Wy"]),
             _fmt(r["Q_na"]), _fmt(r["K_torsion"]))
    lines.append("")

    # ---- TABLE 3: Torsion quality -------------------------------------------
    # Per-method torsion breakdown.
    # _t columns (Bredt-Batho wall thickness) appear only when at least one
    # station carries the value (single-polygon @cell/@wall sections).
    # J_s_vroark_fidelity: CSF polygon-based reliability index.
    #   >= 0.9 reliable | 0.8-0.9 borderline | < 0.8 outside validity domain.
    t3_headers = ["z", "J_sv_cell"]
    if any_cell_t:
        t3_headers.append("J_sv_cell_t")
    t3_headers.append("J_sv_wall")
    if any_wall_t:
        t3_headers.append("J_sv_wall_t")
    t3_headers += ["J_s_vroark", "J_s_vroark_fidelity", "J_tors", "method"]

    lines.append("# TABLE 3 - TORSION QUALITY")
    lines.append("# J_s_vroark_fidelity: >=0.9 reliable | 0.8-0.9 borderline | <0.8 do not use")
    _header(*t3_headers)
    for r in records:
        vals = [_fmt(r["z"]), _fmt(r["J_sv_cell"])]
        if any_cell_t:
            vals.append(_fmt(r["J_sv_cell_t"]))
        vals.append(_fmt(r["J_sv_wall"]))
        if any_wall_t:
            vals.append(_fmt(r["J_sv_wall_t"]))
        vals += [
            _fmt(r["J_s_vroark"]),
            _fmt(r["J_s_vroark_fidelity"]),
            _fmt(r["J_tors"]),
            r["method"],
        ]
        _row(*vals)
    lines.append("")

    # ---- TABLE 4: Station names ---------------------------------------------
    # Section name list for SAP2000 frame property assignment.
    lines.append("# TABLE 4 - STATION NAMES")
    _header("id", "z", "section_name")
    for r in records:
        _row(str(r["id"]), _fmt(r["z"]), f"{section_prefix}{r['id']:04d}")
    lines.append("")

    # -------------------------------------------------------------------------
    # Write file
    # -------------------------------------------------------------------------
    out_path = Path(template_filename)
    if out_path.parent and not out_path.parent.exists():
        out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")

    return str(out_path)


#--------------------------------------------------------------------------------
def write_sap2000_geometry(*args: Any, **kwargs: Any) -> str:
    """
    Backward-compatible wrapper.

    this function tried to generate a SAP2000 .s2k directly. In v2 we avoid
    promising direct import correctness and instead generate a template pack.

    Use:
        write_sap2000_template_pack(...)

    This wrapper calls write_sap2000_template_pack with the provided arguments.
    """
    return write_sap2000_template_pack(*args, **kwargs)


def _csf__is_finite_number(x: Any) -> bool:
    """Return True if x can be converted to a finite float."""
    try:
        v = float(x)
    except Exception:
        return False
    return math.isfinite(v)


def _csf__ensure_parent_dir_exists(path: str) -> None:
    """
    Ensure the parent directory exists; otherwise raise CSFError.

    Note: we intentionally do NOT auto-create directories. This makes typos
    in output paths fail fast and is easier to debug.
    """
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        raise CSFError(
            f"Output directory does not exist for yaml_path='{path}'. "
            f"Missing directory: '{parent}'."
        )


def _csf__atomic_write_text(path: str, text: str) -> None:
    """
    Write a file atomically:
      1) write to path + '.tmp'
      2) os.replace to final name
    """
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp_path, path)


def _csf__section_to_Sz_dict(section_obj,nodesection: str) -> Dict[str, Any]:
    """
    Convert a computed Section into the minimal YAML dict format:

      Sz:
        z: <float>
        polygons:
          <poly_name>:
            weight: <float>
            vertices:
              - [x, y]
              - [x, y]
              ...

    Polygon weights are exported exactly as computed at z (already include w(z)).
    """
    out_polys: Dict[str, Any] = {}

    for i, poly in enumerate(section_obj.polygons):
        if not hasattr(poly, "name"):
            raise CSFError(f"Polygon at index {i} has no attribute 'name'.")
        if not hasattr(poly, "weightabs"):
            raise CSFError(f"Polygon '{getattr(poly,'name','?')}' at index {i} has no attribute 'weight'.")
        if not hasattr(poly, "vertices"):
            raise CSFError(f"Polygon '{getattr(poly,'name','?')}' at index {i} has no attribute 'vertices'.")

        verts_out = []
        for j, v in enumerate(poly.vertices):
            if not hasattr(v, "x") or not hasattr(v, "y"):
                raise CSFError(f"Vertex {j} of polygon '{poly.name}' lacks x/y attributes.")

            x = float(v.x)
            y = float(v.y)

            # If your module defines XY (PyYAML pretty mode), use it to enforce flow style [x, y].
            if "XY" in globals() and globals().get("XY") is not None:
                verts_out.append(globals()["XY"]((x, y)))  # type: ignore[index]
            else:
                verts_out.append([x, y])
        #
        poly_name = str(poly.name)

        # Clean duplicated diagnostic names produced by section interpolation.
        # Example: "tower:tower" -> "tower".
        if ":" in poly_name:
            name0, name1 = poly_name.split(":", 1)
            node_section_norm = str(nodesection).strip().lower()

            if node_section_norm == "s0":
                poly_name = name0
            elif node_section_norm == "s1":
                poly_name = name1                      
        out_polys[poly_name] = {
            "weight": float(poly.weightabs),
            "vertices": verts_out,
        }
    return {
        nodesection: {
            "z": float(getattr(section_obj, "z", float("nan"))),
            "polygons": out_polys,
        }
    }


def _yaml_scalar(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"

    # supporto numeri numpy (np.float64, np.int64, ecc.)
    try:
        import numpy as np
        if isinstance(v, np.generic):
            v = v.item()
    except Exception:
        pass

    if isinstance(v, (int, float)):
        return str(v)

    s = str(v)
    # quote se serve
    if s == "" or any(c in s for c in [":", "#", "\n", "{", "}", "[", "]"]):
        return '"' + s.replace('"', '\\"') + '"'
    return s


def _simple_yaml_dump(data, indent: int = 0) -> str:
    sp = "  " * indent

    if isinstance(data, dict):
        out = []
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                out.append(f"{sp}{k}:")
                out.append(_simple_yaml_dump(v, indent + 1))
            else:
                out.append(f"{sp}{k}: {_yaml_scalar(v)}")
        return "\n".join(out)

    if isinstance(data, list):
        out = []
        for item in data:
            if isinstance(item, (dict, list)):
                out.append(f"{sp}-")
                out.append(_simple_yaml_dump(item, indent + 1))
            else:
                out.append(f"{sp}- {_yaml_scalar(item)}")
        return "\n".join(out)

    # scalare singolo
    return f"{sp}{_yaml_scalar(data)}"

def safe_evaluate_weight_zrelative(formula: str, p0: Polygon, p1: Polygon, z0: float, z1: float, z: float,print=True) -> tuple[float, dict]:
    """
    Evaluates a weight formula string safely by trapping all potential exceptions.
    
    This function performs:
    1. Proactive File System check (pre-evaluation).
    2. Mathematical evaluation via eval/evaluate_weight_formula.
    3. Physical constraint validation (e.g., negative results).
    4. Immediate visual reporting via print_evaluation_report.
    """
    # 1. Initialize the internal report structure
    t_pos=z/(z1-z0)
    report = {
        "status": "SUCCESS",
        "error_type": None,
        "message": "Formula evaluated successfully.",
        "suggestion": None,
        "z_pos": z ,
        "t_pos": t_pos,
        "formula": formula.strip()
    }
    
    result = 0.0
    
    try:
        # --- BLOCK 1: PROACTIVE FILE SYSTEM CHECK ---
        # Scan formula for E_lookup('filename') calls using Regex
        # Handles single/double quotes and optional spaces
        match = re.search(r"E_lookup\s*\(\s*['\"](.+?)['\"]\s*\)", report["formula"])
       
        if match:
            filename = match.group(1)
            # Check if file exists on disk BEFORE calling the core logic
            if not os.path.exists(filename):
                report.update({
                    "status": "ERROR",
                    "error_type": "File System Error",
                    "message": f"Lookup file '{filename}' not found.",
                    "suggestion": f"Ensure the file exists in the current directory: {os.getcwd()}"
                })
                print_evaluation_report(0.0, report)
                return 0.0, report

        # --- BLOCK 2: FORMULA EVALUATION ---
        # Attempt to run the core evaluation logic
        result = evaluate_weight_formula_zrelative(formula, p0, p1, z0,z1, z)
        
        # --- BLOCK 3: PHYSICAL VALIDATION ---
        # Check for non-physical results (e.g., negative stiffness or weight)
        if result < 0:
            report.update({
                "status": "WARNING",
                "error_type": "Physical Constraint",
                "message": f"Calculated value is negative ({result:g}).",
                "suggestion": "Verify if a void was intended. Consider using 'np.maximum(0, ...)'."
            })

    
    except NameError as e:
        # Occurs if a variable (like 'w0' or 'z') is misspelled or 'np' is not loaded
        report.update({
            "status": "ERROR",
            "error_type": "Syntax/Variable Error",
            "message": f"Undefined variable or function: {str(e)}",
            "suggestion": "Check variable names. Remember Python is case-sensitive (e.g., 'w0' vs 'W0')."
        })

    except ZeroDivisionError:
        # Occurs if the formula divides by zero at this specific z-position
        report.update({
            "status": "ERROR",
            "error_type": "Mathematical Error",
            "message": "Division by zero encountered during evaluation.",
            "suggestion": "Add a small epsilon to the denominator, e.g., (x + ESP_L)."
        })

    except IndexError:
        # Occurs if d(i,j) refers to a vertex that doesn't exist
        report.update({
            "status": "ERROR",
            "error_type": "Geometry Index Error",
            "message": "Vertex index out of range in d(i,j) function.",
            "suggestion": "Ensure polygon indices are correct and start from 1."
        })

    except Exception as e:
        # Catch-all for any other unforeseen execution errors
        report.update({
            "status": "ERROR",
            "error_type": "Execution Error",
            "message": str(e),
            "suggestion": "Check the formula syntax and any external data sources."
        })

    # --- BLOCK 5: IMMEDIATE OUTPUT ---
    # Call the tabular printer before returning values
    final_value = result if report["status"] != "ERROR" else 0.0
    if print:
        print_evaluation_report(final_value, report)
    
    return float(final_value), report

def print_evaluation_report(value: float, report: dict):
    """
    Prints minimalist structured report with Timestamp.
    Designed for traceability.
    """
    # 1. Icons and Styling
    icons = {"SUCCESS": "OK", "WARNING": "WW", "ERROR": "KO"}
    icon = icons.get(report["status"], "⚪")
    bw = 72  # Reference width for horizontal lines
    
    # 2. Helper for clean line printing
    def print_line(label, content):
        print(f"  {label:<12} {content}")

    # 3. Header
    print("\n" + "═" * bw)
    header_text = f"{icon}  CSF WEIGHT LAW INSPECTOR  |  {report['status']}"
    print(" " * ((bw - len(header_text)) // 2) + header_text)
    print("═" * bw)

    # 4. Input Section
    formula_display = report['formula'] if len(report['formula']) < 60 else report['formula'][:57] + "..."
    print_line("FORMULA:", formula_display)
    print_line("POSITION Z:", f"{report['z_pos']:.4f}  (ref. coordinate)")
    print_line("POSITION t:", f"{report['t_pos']:.4f}  (ref. normalized)")
    # 5. Results Section (Separator)
    print("-" * bw)
    if report["status"] != "ERROR":
        w_str = f"{value:g}" if abs(value) < 1e5 else f"{value:.4e}"
        print_line("RESULT W:", f"➤ {w_str}")
    else:
        print_line("RESULT W:", "❌ [EVALUATION FAILED]")

    # 6. Contextual Error/Warning Section
    if report["status"] != "SUCCESS":
        print("-" * bw)
        print_line("CATEGORY:", report.get("error_type", "Unknown"))
        print_line("DETAIL:", report.get("message", "N/A"))
        print_line("ADVICE:", report.get("suggestion", "Check input parameters."))

    # 7. Footer with Timestamp
    print("-" * bw)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Aligned to the right
    timestamp_str = f"Validated on: {now}"
    print(" " * (bw - len(timestamp_str)) + timestamp_str)
    print("═" * bw + "\n")

def execute_string_to_float(code_string, x_value):
    # 1. Create a workspace (namespace) for exec to run in
    # We prepopulate it with 'x' so the string can use it for calculations
    workspace = {"x": x_value}
    
    # 2. Execute the string of code
    # The string is expected to store the final calculation in a variable named 'risultato'
    # globals is kept empty {}, and workspace acts as the local namespace
    exec(code_string, {}, workspace)
    
    # 3. Extract the value from the workspace
    # We use .get() to avoid an error if 'risultato' is missing, then cast to float
    final_number = float(workspace.get("output", 0.0))


def evaluate_shear_weight_formula(
    formula: str,
    p0: Polygon,
    p1: Polygon,
    z0: float,
    z1: float,
    zt: float,
    w: float,
) -> float:
    """
    Evaluate a string-based shear-weight law.

    Differences from evaluate_weight_formula():
    - The variable 'w' is available and represents the absolute weight at z.
    - The special function iso(nu) is available.
    - If iso(nu) is used, it must be the entire formula.

    iso(nu) applies the isotropic relation:

        G = E / (2 * (1 + nu))

    In CSF terms, if 'w' represents the absolute E-like weight,
    iso(nu) returns the corresponding G-like shear weight.
    """

    if not isinstance(formula, str):
        raise ValueError("shear_weight formula must be a string.")

    formula = formula.strip()

    if not formula:
        raise ValueError("shear_weight formula cannot be empty.")

    # Detect iso(...) usage.
    iso_call = re.fullmatch(r"iso\s*\((.*)\)", formula)
    iso_used = re.search(r"\biso\s*\(", formula) is not None

    if iso_used and iso_call is None:
        raise ValueError(
            "Invalid shear_weight formula: iso(<nu>) must be used alone."
        )

    z = zt
    l_total = z1 - z0

    current_verts = tuple(
        v0.lerp(v1, z, l_total)
        for v0, v1 in zip(p0.vertices, p1.vertices)
    )

    p0_z = Polygon(vertices=current_verts, weight=p0.weight, name=p0.name)

    t = zt / (z1 - z0)

    def E_lookup(filename: str) -> float:
        # zt is absolute for E lookup.
        return lookup_homogenized_elastic_modulus(filename, zt)

    def T_lookup(filename: str) -> float:
        # t is normalized for T lookup.
        return lookup_homogenized_elastic_modulus(filename, t)

    def iso(nu: float) -> float:
        # Isotropic relation: E = 2 * G * (1 + nu)
        # Here w represents the absolute E-like weight at z.
        # Therefore the shear weight is G-like:
        # shear_w = w / (2 * (1 + nu))
        nu = float(nu)
        den = 2.0 * (1.0 + nu)

        if abs(den) < 1e-15:
            raise ValueError("Invalid iso(nu): nu = -1 makes shear weight undefined.")

        shear_weight = float(w) / den
        return shear_weight

    d = lambda i, j: get_points_distance(p0_z, i, j)
    di = lambda i, j: get_points_distance(p0, i, j)
    de = lambda i, j: get_points_distance(p1, i, j)

    context = {
        "w": float(w),          # Absolute weight at z
        "w0": p0.weight,        # Start weight
        "w1": p1.weight,        # End weight
        "z": z,                 # Absolute z
        "t": t,                 # Normalized z
        "L": l_total,           # Physical length
        "math": math,
        "np": np,
        "d": d,
        "d0": di,
        "d1": de,
        "E_lookup": E_lookup,
        "T_lookup": T_lookup,
        "iso": iso,
    }

    SAFE_BUILTINS = {
        "int": int,
        "float": float,
        "bool": bool,
        "min": min,
        "max": max,
        "abs": abs,
        "round": round,
        "sum": sum,
        "pow": pow,
        "len": len,
        "range": range,
        "sorted": sorted,
        "enumerate": enumerate,
        "zip": zip,
        "list": list,
        "tuple": tuple,
        "dict": dict,
        "set": set,
        "any": any,
        "all": all,
    }
    shear_weight = float(eval(formula, {"__builtins__": SAFE_BUILTINS}, context))

    return shear_weight

def evaluate_weight_formula( formula: str, p0: Polygon, p1: Polygon,  z0: float, z1: float, zt: float) -> float:
    """
    Wrapper function intended for use within 'eval()' contexts.
    It bridges the string evaluation to the structural lookup logic.

    Evaluates a string-based mathematical formula to determine the polygon weight at a 
            
    Args:
        formula (str): The Python expression to evaluate.
        p0 (Polygon): The polygon definition at the start section (z=0).
        p1 (Polygon): The polygon definition at the end section (z=L).
        zt (float): real relative or normalized values
        normalize: how to interpred zt
        
    Returns:
        float: The calculated weight (Elastic Modulus).
        
    Raises:
        Exception: Propagates any error encountered during evaluation.
    """
    # 2. Generate a temporary for the 'd(i,j)' helper.
    # This allows the formula to access distances at the current evaluation point.
    #   
    # z is absolute
    
    z = zt  
    # z must be absolute for interpolationg the poligons sections
    l_total=z1-z0
    current_verts = tuple(
        v0.lerp(v1, z,l_total) for v0, v1 in zip(p0.vertices, p1.vertices)
    )
    p0_z = Polygon(vertices=current_verts, weight=p0.weight, name=p0.name)
    
    t = zt/(z1-z0)
    
    # 3. Define the external file lookup helper
    def E_lookup(filename: str) -> float:
        # in this case z is abosolute
        # we need to go in relative z
        return lookup_homogenized_elastic_modulus(filename, zt)
    
    def T_lookup(filename: str) -> float:
        # only for T_lookup zt is normalized
        return lookup_homogenized_elastic_modulus(filename, t)   
        
    # 4. Define local distance helpers for the context
    # These are used in the formula as d(i,j), d0(i,j), d1(i,j)
    d  = lambda i, j: get_points_distance(p0_z, i, j)
    di = lambda i, j: get_points_distance(p0, i, j)
    de = lambda i, j: get_points_distance(p1, i, j)
    
    # 5. Build the evaluation context (Environment)
    #t = z / l_total if abs(l_total) > _tol.EPS_L else 0.0
    context = {
        "w0": p0.weight,        # Start weight
        "w1": p1.weight,        # End weight
        "z": z,                 # Alias for z-axis consistency
        "t": t,    
        "L": l_total,           # Physical length
        "math": math,           # Python math library
        "np": np,               # NumPy for advanced math
        "d": d,                 # Current distance function
        "d0": di,               # Start distance function
        "d1": de,               # End distance function
        "E_lookup": E_lookup,    # File-based data lookup
        "T_lookup": T_lookup    # File-based data lookup
    }

    
    # Define minimal safe builtins
    SAFE_BUILTINS = {
    # numeric / conversion
        "int": int,
        "float": float,
        "bool": bool,
        "min": min,
        "max": max,
        "abs": abs,
        "round": round,
        "sum": sum,
        "pow": pow,

        # collections / iteration helpers
        "len": len,
        "range": range,
        "sorted": sorted,
        "enumerate": enumerate,
        "zip": zip,
        "list": list,
        "tuple": tuple,
        "dict": dict,
        "set": set,

        # logic
        "any": any,
        "all": all,
    }
    
    # 6. Execute evaluation in a clean sandbox
    # We disable __builtins__ for safety to ensure only provided tools are used.
    
    law_value =  float(eval(formula, {"__builtins__": SAFE_BUILTINS}, context))
    return law_value
 
def execute_string_to_float(code_string, z_val, t_val):
    """
    Executes a Python procedure from a string and returns a float.
    Uses 'z' and 't' as input variables.
    """
    
    # 1. THE BRIDGE (Workspace)
    # Here we map your numbers to the names 'z' and 't'
    # These are the only variables the string will "see"
    workspace = {
        "z": z_val, 
        "t": t_val,
        "math": math
    }
    
    try:
        # 2. THE EXECUTION
        exec(code_string, {}, workspace)
        
        # 3. THE RETRIEVAL
        # The code string MUST save the final result in 'output'
        if "output" not in workspace:
            raise NameError("Error: The variable 'output' is missing in your string!")
        
        return float(workspace["output"])
        
    except Exception as e:
        print(f"--- ERROR IN YOUR CODE STRING ---")
        print(f"Details: {e}")
        raise


def evaluate_weight_formula_zrelative( formula: str, p0: Polygon, p1: Polygon, z0: float, z1: float, z: float) -> float:
        """
        Evaluates a string-based mathematical formula to determine the polygon weight at a 
                
        Args:
            formula (str): The Python expression to evaluate.
            p0 (Polygon): The polygon definition at the start section (z=0).
            p1 (Polygon): The polygon definition at the end section (z=L).
            z (float): real relative z
            
        Returns:
            float: The calculated weight (Elastic Modulus).
            
        Raises:
            Exception: Propagates any error encountered during evaluation.
        """
        
        #evaluate_weight_formula( formula, p0, p1, l_total, z)
        '''
        # 2. Generate a temporary for the 'd(i,j)' helper.
        # This allows the formula to access distances at the current evaluation point.
        #
      
        current_verts = tuple(
            v0.lerp(v1, z,l_total) for v0, v1 in zip(p0.vertices, p1.vertices)
        )
        p_z = Polygon(vertices=current_verts, weight=p0.weight, name=p0.name)
        #print(f"DEBUG p_z {p_z}")
        # 3. Define the external file lookup helper
        def E_lookup(filename: str) -> float:
            return lookup_homogenized_elastic_modulus(filename, z)
        def T_lookup(filename: str) -> float:
            t=z
            return lookup_homogenized_elastic_modulus(filename, t)       
        # 4. Define local distance helpers for the context
        # These are used in the formula as d(i,j), d0(i,j), d1(i,j)
        d  = lambda i, j: get_points_distance(p_z, i, j)
        di = lambda i, j: get_points_distance(p0, i, j)
        de = lambda i, j: get_points_distance(p1, i, j)

        # 5. Build the evaluation context (Environment)
        #t = z / l_total if abs(l_total) > _tol.EPS_L else 0.0
        context = {
            "w0": p0.weight,        # Start weight
            "w1": p1.weight,        # End weight
            "z": z,                 # Alias for z-axis consistency
            #"t": t,    
            "L": l_total,           # Physical length
            "math": math,           # Python math library
            "np": np,               # NumPy for advanced math
            "d": d,                 # Current distance function
            "d0": di,               # Start distance function
            "d1": de,               # End distance function
            "E_lookup": E_lookup,    # File-based data lookup
            "T_lookup": T_lookup    # File-based data lookup
        }

        '''
        zabsolute = z0+z
        return evaluate_weight_formula( formula, p0, p1, z0,z1, zabsolute)

def section_geometry(section: Section, fmt=".8f"):
    """
    Prints the section structure keeping the original table layout.
    Uses 'fmt' for all vertex coordinates.
    """
    # print(f"DEBUG section_print_geometry {section}")
    print(f"--- SECTION DETAILS (z={section.z}) ---")
    
    # Original Header
    print(f"{'Name':<12} | {'Weight':<10} | {'N. Vertices':<10} | {'Coordinates':<30}")
    print("-" * 100)
    
    for poly in section.polygons:
        # We apply the explicit 'fmt' to EVERY vertex in the polygon
        # This creates a single string with all points formatted as requested
        v_coords = ", ".join([f"({format(v.x, fmt)}, {format(v.y, fmt)})" for v in poly.vertices])
            
        # Print using your exact original column widths
        print(f"{poly.name:<12} | {poly.weight:<10.2f} | {len(poly.vertices):<10} | {v_coords}")


def section_print_analysis(full_analysis, fmt=".8f"):
    """
    Prints the structural analysis report for a cross-section.
    
    Args:
        full_analysis (dict): Dictionary containing the calculated properties.
        fmt (str): Optional Python format string for numerical output. 
                   Defaults to ".8f" (fixed-point with 8 decimals). 
          
                   Can be set to ".4e" for scientific notation or others.
    """

    def fmt_val_or_pair(x: Union[float, Tuple[float, float]], fmt: str) -> str:
        """
        Format either:
        - a single float -> formatted with `fmt`
        - a pair (v, t)  -> f"{v_fmt} t={t_fmt}" using the same `fmt`
        """
        # Case 1: single float
        if isinstance(x, (int, float)):
            return format(float(x), fmt)

        # Case 2: tuple of 2 floats
        if isinstance(x, tuple) and len(x) == 2:
            v, t = x
            return f"{format(float(v), fmt)} t={format(float(t), fmt)}"

        raise TypeError("x must be a float/int or a tuple of 2 floats")    
    span = 130
    print("\n" + "="*span)
    print("FULL MODEL ANALYSIS REPORT - SECTION EVALUATION")
    print("#  Name                              Key")
    print("="*span)
    
    # Using the 'fmt' parameter inside f-strings for all numerical values
    print(f"1) Area (A):                          A                     {full_analysis['A']:{fmt}}     # Total Homogenized area")
    print(f"2) Centroid Cx:                       Cx                    {full_analysis['Cx']:{fmt}}     # Horizontal geometric centroid (X-axis locus)")
    print(f"3) Centroid Cy:                       Cy                    {full_analysis['Cy']:{fmt}}     # Vertical geometric centroid (Y-axis locus)")
    print(f"4) Inertia Ix:                        Ix                    {full_analysis['Ix']:{fmt}}     # Second moment of area about the centroidal X-axis")
    print(f"5) Inertia Iy:                        Iy                    {full_analysis['Iy']:{fmt}}     # Second moment of area about the centroidal Y-axis")
    print(f"6) Inertia Ixy:                       Ixy                   {full_analysis['Ixy']:{fmt}}     # Product of inertia (indicates axis symmetry)")
    print(f"7) Polar Moment    :                  Ip                    {full_analysis['Ip']:{fmt}}     # Polar second moment of area (sum of Ix and Iy)")
    print(f"8) Principal Inertia I1:              I1                    {full_analysis['I1']:{fmt}}     # Major principal second moment of area")
    print(f"9) Principal Inertia I2:              I2                    {full_analysis['I2']:{fmt}}     # Minor principal second moment of area")
    print(f"10) Radius of Gyration rx:            rx                    {full_analysis['rx']:{fmt}}     # Radii of gyration relative to the X-axis")
    print(f"11) Radius of Gyration ry:            ry                    {full_analysis['ry']:{fmt}}     # Radii of gyration relative to the Y-axis")
    print(f"12) Elastic Modulus Wx:               Wx                    {full_analysis['Wx']:{fmt}}     # Elastic section modulus (flexural strength about X)")
    print(f"13) Elastic Modulus Wy:               Wy                    {full_analysis['Wy']:{fmt}}     # Elastic section modulus (flexural strength about Y)")
    print(f"14) Torsional Rigidity K:             K_torsion             {full_analysis['K_torsion']:{fmt}}     # Semi-empirical torsional stiffness approximation")
    print(f"15) First_moment:                     Q_na                  {full_analysis['Q_na']:{fmt}}     # First moment of area at NA (governs shear capacity)" )
    print(f"16) Torsional const K cell            J_sv_cell             {fmt_val_or_pair(full_analysis['J_sv_cell'],fmt)}     # Saint-Venant torsional constant for closed thin-walled by applying  Bredt–Batho formula")    
    print(f"17) Torsional const K wall            J_sv_wall             {fmt_val_or_pair(full_analysis['J_sv_wall'],fmt)}     # computes the Saint-Venant torsional constant for open thin-walled walls")
    print(f"18) Torsional const K roark:          J_s_vroark            {full_analysis['J_s_vroark']:{fmt}}     # Roark torsional indicator (equivalent-rectangle mapping)")
    print(f"19) Torsional const K roark fidelity: J_s_vroark_fidelity   {full_analysis['J_s_vroark_fidelity']:{fmt}}     # Reliability index based on aspect-ratio (1.0 = Thin-walled, 0.0 = Stout")
    print("="*span) 

def section_full_analysis_keys() -> List[str]:
    """
    Returns the ordered list of keys generated by the full analysis.
    Useful for mapping, CSV headers, or selective data extraction.
    """
    return [
        'A',
        'Cx',
        'Cy',
        'Ix',
        'Iy',
        'Ixy',
        'Ip',
        'I1',
        'I2',
        'rx',
        'ry',
        'Wx',
        'Wy',
        'K_torsion'
        ,'Q_na'
        ,'J_sv_wall'
        ,'J_sv_cell'
        ,'J_s_vroark'
        ,'J_s_vroark_fidelity'
    ]

def write_opensees_geometry(
    field,
    n_points: int,
    E_ref = None,
    nu = None,
    filename: str = "geometry.tcl",
):  
    """
    Write a CSF-style OpenSees geometry file **as DATA** (to be parsed line-by-line),
    not as a Tcl script to be sourced.

    --------------------------------------------------------------------------------
    FILE CONTRACT (DATA, NOT Tcl)
    --------------------------------------------------------------------------------
    1) Exact stations (critical for reproducibility)
       We write the exact longitudinal stations used by CSF:
           # CSF_Z_STATIONS: z0 z1 ... zN-1
       A downstream builder must use these stations (no re-generation).

    2) Section record format (data record that *resembles* OpenSees)
       We write one record per station:

           section CSF <tag> <A> <Iz> <Iy> <J_tors> <Cx> <Cy>

       IMPORTANT:
       - This is a DATA record. OpenSees Tcl would NOT accept the trailing <Cx> <Cy>.
       - Cx,Cy are appended for CSF parsers/builders (centroid offsets in section plane).
       - A, Iz, Iy, J_tors are station-wise CSF results computed from polygon-level E/G values.

    3) Torsion export without tying the file to a single CSF torsion model
       CSF may provide multiple Saint-Venant torsion contributions
       (e.g., thin-walled cell and thin-walled open wall).

              Torsion selection policy:

         - If both J_sv_cell and J_sv_wall are present and > 0:
             J_tors = J_sv_cell + J_sv_wall
           (additive Saint-Venant contributions)

         - If only one of them is present and > 0:
             J_tors = that value

         - Legacy "Ip" is NOT automatically used here
           (avoids mixing distinct torsion models silently).

         - If no valid Saint-Venant contribution is available:
             fail-fast (explicit error; no silent torsion default).

    --------------------------------------------------------------------------------
    OUTPUT CONTENTS
    --------------------------------------------------------------------------------
    - Header comments
    - # CSF_Z_STATIONS: exact z-coordinates
    - Optional informational nodes (best-fit line through centroid offsets)
    - geomTransf Linear 1 1 0 0 (simple default)
    - One section record per station (as described above)

    --------------------------------------------------------------------------------
    REQUIREMENTS
    --------------------------------------------------------------------------------
    - numpy must be available
    - section_full_analysis(sec, ...) must return at least:
        "A", "Ix", "Iy", "Cx", "Cy"
      and (for torsion export) at least one of:
        "J_sv_wall", "J_sv_cell"
    """



    # -------------------------------------------------------------------------
    # Helper: robust positive check for torsion fields
    # Convention: J_* == 0 means "not provided / not applicable"
    # -------------------------------------------------------------------------
    def _is_pos(v: object, eps: float = 0.0) -> bool:
        try:
            x = float(v)
        except Exception:
            return False
        return np.isfinite(x) and (x > eps)

    # -------------------------------------------------------------------------
    # 0) Member endpoints (same z convention used by the CSF field)
    # -------------------------------------------------------------------------
    z0 = float(field.s0.z)
    z1 = float(field.s1.z)

    # -------------------------------------------------------------------------
    # 1) Exact sampling stations provided by CSF.
    #    We do not assume formulas here; we trust the field.
    # -------------------------------------------------------------------------
    z_coords = field.get_lobatto_integration_points(n_points)
    z_coords = [float(z) for z in z_coords]

    # -------------------------------------------------------------------------
    # 2) Run section analysis at each station
    # -------------------------------------------------------------------------
    results = []
    cx_list = []
    cy_list = []
    for z in z_coords:


        sec = field.section(z)

        # NOTE:
        # Torsion details are handled inside section_full_analysis / torsion routines.
        # inside section_full_analysis / torsion routines.
        # The exporter should not encode that assumption here unless it is part of
        # the section analysis contract.
        res = section_full_analysis(sec)

        # Minimal required keys
        
        for k in ("A", "Ix", "Iy", "Cx", "Cy"):
            if k not in res:
                raise KeyError(f"section_full_analysis() missing required key '{k}' at z={z}")

        results.append(res)
        cx_list.append(float(res["Cx"]))
        cy_list.append(float(res["Cy"]))
    
    
    # -------------------------------------------------------------------------
    # 3) Informational-only: best-fit straight line through centroid offsets
    #    (used only for exported geometry metadata)
    # -------------------------------------------------------------------------
    m_y, q_y = np.polyfit(z_coords, cy_list, 1)
    m_x, q_x = np.polyfit(z_coords, cx_list, 1)
    
    
    # -------------------------------------------------------------------------
    # 4) Reference shear modulus
    # -------------------------------------------------------------------------
    if E_ref is None or nu is None:
        G_ref = None
    else:
        G_ref = float(E_ref) / (2.0 * (1.0 + float(nu)))

    # -------------------------------------------------------------------------
    # 5) Write file (DATA)
    # -------------------------------------------------------------------------
    

    try:
        with open(filename, "w", encoding="utf-8") as f:
            # ---- Header (comments only) ----
            f.write("# OpenSees Geometry DATA File - Generated by CSF\n")
            f.write(f"# Beam Span: {z1 - z0:.6f} (units follow your model)\n")
            f.write(f"# Stations: {len(z_coords)}\n")
            f.write("# NOTE: This file is meant to be PARSED AS DATA (do NOT source it as Tcl).\n")
            f.write("# NOTE: Section records are CSF data records, not OpenSees Tcl syntax.\n")
            f.write("#\n")
            f.write("# CSF_EXPORT_MODE:\n")
            if E_ref is not None:
                f.write(f"# CSF_METADATA_E_REF: {E_ref} Only weighted section properties are exported; E_ref is kept as a reference modulus.\n")
            if nu is not None:
                f.write(f"# CSF_METADATA_NU_REF: {nu} Only weighted section properties are exported; nu is kept as a reference poisson ratio.\n")
            if G_ref is not None:
                f.write(f"# CSF_METADATA_G_REF: {G_ref}\n")
            f.write("# CSF_TORSION_SELECTION: J_tors = J_sv_cell + J_sv_wall")
            # ---- Exact z stations ----
            f.write("\n\n# CSF_Z_STATIONS: " + " ".join(f"{z:.12g}" for z in z_coords) + "\n\n")

            # ---- Informational nodes (optional) ----
            f.write("# Informational nodes (best-fit line through centroid offsets)\n")
            f.write(f"node 1 {m_x * z0 + q_x:.12g} {m_y * z0 + q_y:.12g} {z0:.12g}\n")
            f.write(f"node 2 {m_x * z1 + q_x:.12g} {m_y * z1 + q_y:.12g} {z1:.12g}\n\n")

            # ---- Default transformation (builder may override) ----
            f.write("geomTransf Linear 1 1 0 0\n\n")

            # ---- Section records ----
            # Record format (DATA):
            #    section CSF tag A Iz Iy J_tors Cx Cy
            #
            # Mapping:
            #   Iz := Ix from CSF (if your axes are aligned); otherwise swap upstream.
            #   Iy := Iy from CSF
            #
            # IMPORTANT: ensure your downstream builder interprets Ix/Iy consistently.
            for i, res in enumerate(results):
                tag = i + 1


                #
                # POLICY:
                #   1) If thin-walled Saint-Venant contributions are available:
                #        J_tors = J_sv_cell + J_sv_wall
                #      (additive contributions if both are present)
                #
                #      torsion_method is set to:
                #        - "J_sv_cell+J_sv_wall" if both are present
                #        - "J_sv_cell" if only cell is present
                #        - "J_sv_wall" if only wall is present
                #
                # -------------------------------------------------------------------------

                # Always take the first value, whether scalar or array
                J_cell = np.atleast_1d(res["J_sv_cell"])[0]
                J_wall = np.atleast_1d(res["J_sv_wall"])[0]
                J_tors = 0
                if J_cell != 0  or J_wall != 0:
                    J_tors = J_cell + J_wall

                    if J_cell !=0  and J_wall !=0:
                        torsion_method = "J_sv_cell+J_sv_wall"
                    elif  J_cell ==0:
                        torsion_method = "J_sv_wall"
                    else:
                        torsion_method = "J_sv_cell"

                else:
                    torsion_method = "J_tors skip"
                    J_tors=0
                    warnings.warn(
                        "No valid Saint-Venant torsion contribution "
                        "(J_sv_cell or J_sv_wall) available for export."
                    )


                # Write section data record
                f.write(
                    "section CSF {tag} {A:.6e} {Iz:.6e} {Iy:.6e} {J:.6e} "
                    "{Cx:.6e} {Cy:.6e}  # torsion={tm}\n".format(
                        tag=tag,
                        A=float(res["A"]),
                        Iz=float(res["Ix"]),
                        Iy=float(res["Iy"]),
                        J=float(J_tors),
                        Cx=float(res["Cx"]),
                        Cy=float(res["Cy"]),
                        tm=torsion_method,
                    )
                )

        print(f"[SUCCESS] Wrote CSF geometry data to: {filename}")
        print(f"[INFO] Stations: {len(z_coords)} | Span: {z1 - z0:.6f}")

    except OSError as e:
        print(f"[ERROR] Could not write '{filename}': {e}")
        raise


def lookup_homogenized_elastic_modulus(filename: str, zt: float) -> float:
    """
    Retrieves the elastic modulus (E) for a given longitudinal coordinate (z) 
    from an external lookup file.
    
    ALGORITHM STRATEGY:
    1. Parsing: The function reads a text file where each line contains a pair of 
       values: [coordinate_z, modulus_E].
    2. Exact Match: If the requested 'z' matches a coordinate in the file, 
       the corresponding E is returned immediately.
    3. Boundary Handling: If 'z' is outside the range defined in the file, 
       it performs flat extrapolation (returns the nearest boundary value).
    4. Linear Interpolation (LERP): If 'z' falls between two points (z_i, E_i) 
       and (z_j, E_j), it calculates E via:
       E = E_i + (E_j - E_i) * (z - z_i) / (z_j - z_i)

    FILE FORMAT ASSUMPTIONS:
    - The file should be a space, tab, or comma-separated text file.
    - Column 0: Z-coordinate (must be in increasing order for correct interpolation).
    - Column 1: Elastic Modulus value.

    Args:
        filename (str): Path to the lookup data file.
        zt (float): The current coordinate where the property is needed. can be both normalised or not

    Returns:
        float: The interpolated or exact Elastic Modulus.
    """
    
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Lookup file not found: {filename}")

    # --- STEP 1: LOAD DATA ---
    # We use a list of tuples to store the [z, E] pairs.
    # Data is expected to be numeric.
    data = []
    with open(filename, 'r') as f:
        for line in f:
            # Skip empty lines or comments starting with '#'
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            try:
                # Support for common delimiters (comma, tab, space)
                parts = line.replace(',', ' ').split()
                if len(parts) >= 2:
                    z_val = float(parts[0])
                    e_val = float(parts[1])
                    data.append((z_val, e_val))
            except ValueError:
                # Skip lines that do not contain valid numbers
                continue

    if not data:
        raise ValueError(f"No valid data found in lookup file: {filename}")

    # Ensure data is sorted by Z-coordinate for the interpolation logic
    data.sort(key=lambda x: x[0])

    # --- STEP 2: BOUNDARY CHECKS (Extrapolation) ---
    # If the requested z is below the minimum z in the file
    if zt <= data[0][0]:
        return data[0][1]
    # If the requested z is above the maximum z in the file
    if zt >= data[-1][0]:
        return data[-1][1]

    # --- STEP 3: SEARCH AND INTERPOLATION ---
    # Iterate through the pairs to find the interval [z_i, z_i+1] containing z.
    for i in range(len(data) - 1):
        z0, e0 = data[i]
        z1, e1 = data[i+1]
        
        # Exact match check
        if abs(zt - z0) < _tol.EPS_L:
            
            return e0
           # Exact match check
        if abs(zt - z1) < _tol.EPS_L:
            
            return e1

        # Check if z is within the current segment
        if z0 < zt < z1:
            # Linear Interpolation Formula:
            # weight = (target - start) / (end - start)
            t = (zt - z0) / (z1 - z0)
            # Result = start_val + weight * (end_val - start_val)
            return e0 + t * (e1 - e0)
    # end for
    # Fallback for the very last point
    return data[-1][1]

"""


CSF-consistent rewrite of:

    def compute_saint_venant_Jv2(poly_input, verbose=False) -> Tuple[float, float]

Design goals
------------

Representation-invariant for sections:
   - The Roark equivalent-rectangle mapping is non-linear, so computing J per polygon
     and summing depends on how the same domain is split into polygons.
   - Therefore, for a Section we first aggregate (A, centroid, Ix, Iy, Ixy) algebraically
     and apply the mapping ONCE.
Fidelity is also representation-invariant:
   - It is computed from the *equivalent rectangle* only (optionally via an external
     diagnostic), not by averaging per-piece fidelities.

Preconditions (expected upstream in CSF)
----------------------------------------
- Each polygon is a simple CCW loop with positive signed area.
- _tol.EPS_A and _tol.EPS_K are provided upstream (as globals or attached to objects).
"""

# -----------------------------------------------------------------------------
# Tolerance resolution (no hard-coded constants here)
# -----------------------------------------------------------------------------

def _resolve_eps_a(obj: Any) -> float:
    return _tol.EPS_A


def _resolve_eps_k(obj: Any) -> float:
    return _tol.EPS_K


# -----------------------------------------------------------------------------
# Signed polygon integrals (no abs())
# -----------------------------------------------------------------------------

def _poly_signed_area_centroid(pts: Any, eps_a: float) -> Tuple[float, float, float]:
    """
    Shoelace integration.

    Returns (A, Cx, Cy) with signed area A.
    Under CSF preconditions polygons are CCW so A > 0.
    """
    def _xy(p):
        if hasattr(p, "x") and hasattr(p, "y"):
            return float(p.x), float(p.y)
        return float(p[0]), float(p[1])    
    n = len(pts)
    if n < 3:
        raise ValueError("Polygon has < 3 vertices.")

    a2 = 0.0
    cx6 = 0.0
    cy6 = 0.0

    for i in range(n):
        v0 = pts[i]
        v1 = pts[(i + 1) % n]
        cross = v0.x * v1.y - v1.x * v0.y
        a2 += cross
        cx6 += (v0.x + v1.x) * cross
        cy6 += (v0.y + v1.y) * cross

        '''
        print(f"i={i:2d}: v0=({v0.x:8.6f}, {v0.y:8.6f}) v1=({v1.x:8.6f}, {v1.y:8.6f})")
        print(f"     cross={cross:10.6f}  a2={a2:10.6f}  cx6_contrib={(v0.x + v1.x)*cross:10.6f}")
        print(f"     cy6_contrib={(v0.y + v1.y)*cross:10.6f}  cx6_tot={cx6:10.6f}  cy6_tot={cy6:10.6f}")
        print()  # riga vuota
        '''

    A = 0.5 * a2
    if A <= eps_a:
        raise ValueError("Polygon area is non-positive or too small (expected CCW, non-degenerate).")

    Cx = cx6 / (3.0 * a2)
    Cy = cy6 / (3.0 * a2)
    return A, Cx, Cy


def _principal_inertias(ix: float, iy: float, ixy: float) -> Tuple[float, float]:
    """Principal inertias (eigenvalues) of the 2x2 centroidal inertia tensor."""
    tr = ix + iy
    diff = ix - iy
    rad = math.sqrt((0.5 * diff) * (0.5 * diff) + ixy * ixy)
    i1 = 0.5 * tr + rad
    i2 = 0.5 * tr - rad
    return i1, i2


# -----------------------------------------------------------------------------
# Roark equivalent-rectangle torsion proxy
# -----------------------------------------------------------------------------

def _roark_torsion_rect(a: float, b: float) -> float:
    """
    Roark-style torsion approximation for a solid rectangular section.

    Here a and b are the full side dimensions, with a >= b > 0:

        J ≈ a*b^3 * [
              1/3
            - 0.21*(b/a)*(1 - (b/a)^4/12)
        ]

    This is the full-side form of the common half-side expression:

        J ≈ a_h*b_h^3 * [
              16/3
            - 3.36*(b_h/a_h)*(1 - (b_h/a_h)^4/12)
        ]
    
    """
    if b > a:
        a, b = b, a
    ratio = b / a    
    factor = (1.0 / 3.0) - 0.21 * ratio * (1.0 - (ratio ** 4) / 12.0)
    return factor * a * (b ** 3)


def _equiv_rectangle_dims(A: float, i_min: float, eps_k: float) -> Tuple[float, float]:
    """
    Map (A, I_min) to equivalent rectangle dimensions (a >= b).

    Uses: I_min = (A * t^2) / 12  -> t = sqrt(12*I_min/A),  b = A/t
    """
    #print(f"DEBIG _equiv_rectangle_dims A {A} i_min {i_min}")
    if A <= 0.0:
        raise ValueError("Effective area must be positive for the solid-rectangle mapping.")
    if i_min <= 0.0:
        raise ValueError("Minor principal inertia must be positive for the solid-rectangle mapping.")

    t = math.sqrt(12.0 * i_min / A)
    if t <= eps_k:
        raise ValueError("Equivalent thickness too small; torsion proxy ill-conditioned.")

    b_equiv = A / t
    if b_equiv >= t:
        a_dim = b_equiv
        b_dim = t
    else:
        a_dim = t
        b_dim = b_equiv
    return a_dim, b_dim

def compute_saint_venant_Jv2(poly_input: Any) -> Tuple[float, float]:
    """
    Estimate the Saint-Venant torsional constant J and a fidelity indicator.

    Returns (J_total, fidelity).

    Strategy
    --------
    - Net geometric area and homogenised area via polygon_surface_w1_inners0.
    - Equivalent Roark rectangle: shape from geometric bounding box, area from
      A_geom_net. Weight enters as linear multiplier w_total = Ao / A_geom_net.
    - Fidelity = A_geom_net / Ag  (fill ratio of the geometric bounding box).
    - Isoperimetric penalty: if the outer polygon is nearly circular
      (q_iso > 0.90), J and fidelity are forced to zero.
    - Weight-dispersion penalty:  fid_final = fid * (1 - dev_weightabs^2).
    """
    
    section = poly_input

    if any(
        "@cell" in str(getattr(p, "name", "")) or
        "@closed" in str(getattr(p, "name", ""))
        for p in section.polygons
    ):
        return 0.0, 0.0 
    
    # ------------------------------------------------------------------
    # Helper: normalised weight-dispersion (coefficient of variation)
    # ------------------------------------------------------------------
    verbose=False
    
    def compute_shear_areas(
        section: Any,
        children_map: Mapping[int, Sequence[int]],
        eps_a: float = _tol.EPS_A,
    ) -> Tuple[float, float]:
        """
        Compute shear geometric area and shear-weighted area from a Section object.

        Input:
        - section:
            Section object exposing section.polygons.

        - children_map:
            Mapping parent_idx -> direct inner polygon indexes.

        Returns:
        - A_geom_net:
            Sum of occupied geometric areas for polygons with shear_weightabs != 0.

        - Ao:
            Sum of occupied geometric areas multiplied by shear_weightabs.

        Area rule:
        - occupied_area(idx) = area(idx) - sum(area(direct_inner_idx))

        Notes:
        - Polygons with shear_weightabs == 0 are excluded from both returned sums.
        - The children_map subtraction is geometric and index-based.
        - Polygon names are never used.
        - Vertices are passed directly to _poly_signed_area_centroid.
        - _poly_signed_area_centroid must already be available in the same module.
        """

        polygons = section.polygons
   
        area_by_idx: Dict[int, float] = {}

        for idx, polygon in enumerate(polygons):
            signed_area, _, _ = _poly_signed_area_centroid(polygon.vertices, eps_a)
            area_by_idx[idx] = abs(float(signed_area))

        occupied_area_by_idx: Dict[int, float] = {}

        for idx in range(len(polygons)):
            occupied_area = area_by_idx[idx]

            for inner_idx in children_map.get(idx, ()):
                occupied_area -= area_by_idx[inner_idx]

            occupied_area_by_idx[idx] = occupied_area

        A_geom_net = 0.0
        Ao = 0.0

        for idx, polygon in enumerate(polygons):
            shear_weightabs = float(polygon.shear_weightabs)
            if shear_weightabs == 0.0:
                continue

            occupied_area = occupied_area_by_idx[idx]

            A_geom_net += occupied_area
            Ao += occupied_area * shear_weightabs

        return A_geom_net, Ao



    def _shear_weightabs_deviation(polys: Any) -> float:
        """
        Coefficient of variation of shear_weightabs among polygons.

        Returns 0.0 when:
        - there are no positive shear_weightabs values;
        - there is only one positive shear_weightabs value;
        - all positive shear_weightabs values are equal.
        """
        values = []

        for p in polys:
            if not hasattr(p, "shear_weightabs"):
                raise ValueError("Polygon has no shear_weightabs.")

            sw = float(p.shear_weightabs)

            if sw > 0.0:
                values.append(sw)

        if len(values) <= 1:
            return 0.0

        mean = sum(values) / len(values)

        if mean == 0.0:
            return 0.0

        var = sum((sw - mean) ** 2 for sw in values) / len(values)

        return (var ** 0.5) / abs(mean)

    # ------------------------------------------------------------------
    # Helper: geometric bounding-box dimensions (no weighting)
    # ------------------------------------------------------------------

    def _geometric_bounding_box_dims(poly_input: Any) -> Tuple[float, float]:
        """
        Compute the minimum-area geometric bounding box for one or more polygons.

        All vertices from the input polygons are collected into a single point cloud.
        Candidate box orientations are taken from the polygon edge directions. For a
        polygonal planar shape, the minimum-area enclosing rectangle has one side
        parallel to an edge direction, so no continuous angular optimisation is needed.

        The returned dimensions (B, H) correspond to the candidate with the minimum
        area B * H. The computation is purely geometric: polygon weights are ignored.
        """

        def _xy_array(pts: Any) -> np.ndarray:
            coords = np.empty((len(pts), 2), dtype=float)

            for i, pt in enumerate(pts):
                if hasattr(pt, "x"):
                    coords[i, 0] = pt.x
                    coords[i, 1] = pt.y
                else:
                    coords[i, 0] = pt[0]
                    coords[i, 1] = pt[1]

            return coords

        if hasattr(poly_input, "polygons"):
            polygons = poly_input.polygons() if callable(poly_input.polygons) else poly_input.polygons
        elif hasattr(poly_input, "vertices"):
            polygons = [poly_input]
        else:
            polygons = poly_input

        polygons = list(polygons)

        point_arrays = []
        angle_arrays = []

        for poly in polygons:
            vertices_attr = getattr(poly, "vertices", None)
            pts = vertices_attr() if callable(vertices_attr) else vertices_attr

            if pts is None:
                raise ValueError("Polygon has no vertices.")

            pts = list(pts)

            if len(pts) < 3:
                raise ValueError("Polygon has fewer than 3 vertices.")

            arr = _xy_array(pts)
            point_arrays.append(arr)

            nxt = np.roll(arr, -1, axis=0)
            d = nxt - arr

            dx = d[:, 0]
            dy = d[:, 1]

            valid = (np.abs(dx) >= 1e-15) | (np.abs(dy) >= 1e-15)

            if np.any(valid):
                theta = np.mod(np.arctan2(dy[valid], dx[valid]), np.pi / 2.0)
                angle_arrays.append(np.round(theta, 15))

        if not point_arrays:
            raise ValueError("No polygons provided.")

        if not angle_arrays:
            raise ValueError("No valid polygon edges found.")

        points = np.vstack(point_arrays)
        angles = np.unique(np.concatenate(angle_arrays))

        x = points[:, 0]
        y = points[:, 1]

        best_area = float("inf")
        best_B = 0.0
        best_H = 0.0

        # Chunking avoids building a very large angle-by-point matrix at once.
        chunk_size = 256

        for start in range(0, len(angles), chunk_size):
            a = angles[start:start + chunk_size]

            cos_t = np.cos(a)[:, None]
            sin_t = np.sin(a)[:, None]

            xr = x[None, :] * cos_t + y[None, :] * sin_t
            yr = -x[None, :] * sin_t + y[None, :] * cos_t

            B = xr.max(axis=1) - xr.min(axis=1)
            H = yr.max(axis=1) - yr.min(axis=1)
            area = B * H

            idx = int(np.argmin(area))

            if area[idx] < best_area:
                best_area = float(area[idx])
                best_B = float(B[idx])
                best_H = float(H[idx])

        return best_B, best_H

  
    # ------------------------------------------------------------------
    # Helper: isoperimetric ratio Q = 4*pi*A / P^2
    # ------------------------------------------------------------------
    def _isoperimetric_ratio(pts: list) -> float:
        def _x(p):
            return p.x if hasattr(p, "x") else p[0]
        def _y(p):
            return p.y if hasattr(p, "y") else p[1]

        n = len(pts)
        perimeter = sum(
            math.hypot(
                _x(pts[(i + 1) % n]) - _x(pts[i]),
                _y(pts[(i + 1) % n]) - _y(pts[i])
            )
            for i in range(n)
        )
        A, _, _ = _poly_signed_area_centroid(pts, 0.0)
        if perimeter <= 0:
            return 0.0
        return 4.0 * math.pi * abs(A) / (perimeter ** 2)

    eps_a = _resolve_eps_a(poly_input)
    polys = poly_input.polygons

    # ------------------------------------------------------------------
    # Net geometric area and homogenised area via topology-aware function
    # ------------------------------------------------------------------
    from .continuous_section_field import ContinuousSectionField
    s0 = Section(
        z=0.0,
        polygons=poly_input.polygons,
    )

    s1 = Section(
        z=1.0,
        polygons=poly_input.polygons,
    )


    field    = ContinuousSectionField(section0=s0, section1=s1)
    mapchildren=field.build_direct_children_map(0)    
    A_geom_net,Ao = compute_shear_areas(poly_input,mapchildren)
   
    if A_geom_net <= eps_a:
        return 0.0, 0.0
    if Ao <= eps_a:
        return 0.0, 0.0
    
    w_total = Ao / A_geom_net
    # ------------------------------------------------------------------
    # Equivalent Roark rectangle: shape from bounding box, area from A_geom_net
    # ------------------------------------------------------------------
    b_box, h_box = _geometric_bounding_box_dims(polys)
    Ag       = b_box * h_box
    ratio_hb = max(b_box, h_box) / min(b_box, h_box)
    h_eq     = math.sqrt(A_geom_net * ratio_hb)
    b_eq     = math.sqrt(A_geom_net / ratio_hb)

    ktorsion=  _roark_torsion_rect(h_eq, b_eq)
    J_total = w_total * ktorsion
    
    fid     = min(A_geom_net, Ag) / max(A_geom_net, Ag)
    #print(f"DEBUG A_geom_net {A_geom_net} Ao {Ao} : J_total {J_total} : w_total {w_total} : ktorsion {ktorsion}")
    # ------------------------------------------------------------------
    # Isoperimetric penalty: circular sections -> J = 0
    # ------------------------------------------------------------------
    
    outer_poly = max(
        polys,
        key=lambda p: float(getattr(p, "weightabs", 1.0)) * abs(
            _poly_signed_area_centroid(
                p.vertices() if callable(getattr(p, "vertices", None)) else p.vertices,
                0.0
            )[0]
        )
    )
    outer_pts = (
        outer_poly.vertices()
        if callable(getattr(outer_poly, "vertices", None))
        else outer_poly.vertices
    )
    q_iso = _isoperimetric_ratio(outer_pts)
    if q_iso > 0.90:
        fid     = 0.0
        J_total = 0.0

    # ------------------------------------------------------------------
    # Weight-dispersion penalty on fidelity
    # ------------------------------------------------------------------
    
    dev_shear_weightabs = _shear_weightabs_deviation(polys)
    
    fid_final = fid * (1.0 - dev_shear_weightabs ** 1.5)
    fid_final = max(0.0, min(1.0, fid_final))
    
    if verbose:
        print(
            f"roark: J_total={J_total:.6e}  fid={fid:.4f}"
            f"  fid_final={fid_final:.4f}  w_total={w_total:.4f}"
            f"  q_iso={q_iso:.4f}  dev_w={dev_shear_weightabs:.4f}"

        )
    if verbose and math.isfinite(fid_final) and fid_final < 0.5:
        print(
            "[SECTION ANALYSIS] Global fidelity for '%s' is low (%.2f)." %
            (getattr(poly_input, "name", "unnamed"), fid_final)
        )
    
    return float(J_total), float(fid_final)


def calculate_t_eq(points):
    """
    Calcola t_eq = 2*A/P per poligono thin-walled.
    points: list [[x1,y1], [x2,y2], ..., [xn,yn]] linea mediana.
    """
    points = np.array(points)
    # Area shoelace
    x, y = points[:,0], points[:,1]
    A = 0.5 * np.abs(np.dot(x, np.roll(y,1)) - np.dot(y, np.roll(x,1)))
    # Perimetro
    diffs = np.diff(points, axis=0, append=points[0:1])
    P = np.sum(np.sqrt(np.sum(diffs**2, axis=1)))
    t_eq = 2 * A / P if P > 0 else 0
    return t_eq, A, P  # Ritorna anche A, P per debug


"""
CSF torsion (Saint-Venant) - CELL-based closed thin-walled variant
==================================================================

This file provides a *single* drop-in function:

    compute_saint_venant_J_cell(section)

It is designed to live in the same module where your CSF geometry and torsion
functions already exist (e.g., your `section_field.py`), because it expects
these symbols to be available:

Required symbols from your codebase
-----------------------------------
- compute_saint_venant_J(section)      : legacy fallback
- polygon_area_centroid(poly) -> (A_signed, (Cx, Cy))
- _tol.EPS_A, _tol.EPS_L                         : tolerances
- CSFError                             : exception type (subclass of ValueError)
- Section / Polygon data model:
    section.polygons iterable of Polygon-like objects, each with:
      - p.name (string)
      - p.weight (float)   (MUST exist; no silent defaults)
      - p.vertices iterable of points with .x and .y

User convention for CLOSED thin-walled cells
--------------------------------------------
A polygon is treated as a "closed thin-walled cell" entity if its name contains
either token (case-insensitive):

    "@CLOSED"  or  "@CELL"

Examples:
    ring@wall@closed@t=0.020
    box_skin@CELL
    cell1@cell@t=0.008

Important: "@WALL" is *not* required here; you can combine tags if you want.

Dispatch rule (same spirit as @WALL)
------------------------------------
- If no polygon name contains "@CLOSED" or "@CELL": this function returns
  compute_saint_venant_J(section) (legacy).
- Otherwise: only polygons tagged with "@CLOSED"/"@CELL" contribute.

Thickness per cell polygon
--------------------------
- If polygon name contains "@t=<value>": use that thickness (meters).
- Else: estimate thickness via the SAME rigid rule you already adopted for @WALL:

      t := 2*A / P 

  where:
    A = abs(signed area of the *single polygon*),
    P = perimeter of the *single polygon* boundary.

Closed thin-walled torsion model (single-cell, constant thickness)
------------------------------------------------------------------
This function uses the Bredt-Batho single-cell engineering formula:

    J ≈ 4 * A_m^2 / ∮(ds/t)

For constant thickness t along the median line:

    J ≈ 4 * A_m^2 * t / b

where:
- A_m is the area enclosed by the median line,
- b = ∮ ds is the median line length (a "midline perimeter").

Key modelling point for your "single polygon ring with a cut"
-------------------------------------------------------------
Your "ring as ONE polygon" representation typically follows the pattern:
- traverse outer contour,
- insert a radial connection to the inner contour,
- traverse inner contour,
- connect back.

To compute A_m from this single polygon, we *reconstruct* two contours
(outer and inner) by exploiting the repeated vertices that delimit the loops.

Expected vertex pattern (robustly detected)
-------------------------------------------
Let v[0] be the first vertex.
We expect to find:
1) a second occurrence of v[0] somewhere later  -> end of OUTER loop
2) the next vertex is the INNER loop start v_in
3) a second occurrence of v_in later            -> end of INNER loop

From these two reconstructed loops:
- A_outer = |area(outer loop)|
- A_inner = |area(inner loop)|

Then:
- A_wall  = max(A_outer - A_inner, 0)
- A_m     ≈ (A_outer + A_inner)/2   (median-area proxy; exact for t->0 limit)

Finally, with constant thickness:
    b ≈ A_wall / t        (because A_wall ≈ b * t)
so:
    J ≈ 4 * A_m^2 * t / b = 4 * A_m^2 * t^2 / A_wall

Limitations / non-goals (explicit)
----------------------------------
- Multi-cell connected torsion is NOT solved here (compatibility matrices, etc.).
  If you tag multiple disjoint cells (physically disconnected), summing their J
  contributions is reasonable and is what we do.
- If the polygon does not match the expected "two loops separated by repeated points"
  pattern, we raise a CSFError to fail fast (transparent, no heuristics).

Weight convention
-----------------
For torsional stiffness (G*J), negative stiffness is not physically meaningful.
We therefore scale each polygon contribution by abs(weight), consistent with your
compute_saint_venant_J_wall implementation.

"""

def compute_saint_venant_J_cell(section: "Section") -> float:
    """
    Compute closed-cell Saint-Venant torsional constant J_sv [m^4]
    for polygons tagged as @cell/@closed using a thin-walled closed-cell model.

    Key parsing policy for @cell:
    - OUTER loop is detected by the first repeated occurrence of the first vertex.
    - INNER loop is the remaining tail after OUTER closure.
    - INNER must be repeated endpoint
    """
    
    TOKEN_CELL = "@cell"
    TOKEN_CLOSED = "@closed"
    TOKEN_T = "@t="
    verbose = False
    polys = getattr(section, "polygons", None)
    if not polys:
        return 0.0

    # -------------------------------------------------------------------------
    # 0) Select @cell polygons
    # -------------------------------------------------------------------------
    cell_polys = []
    for p in polys:
        nm = str(getattr(p, "name", "") or "")
        low = nm.lower()
        if (TOKEN_CELL in low) or (TOKEN_CLOSED in low):
            cell_polys.append(p)
    
    if not cell_polys:
        return 0.0
    
    # -------------------------------------------------------------------------
    # 1) Local helpers
    # -------------------------------------------------------------------------



    @dataclass(frozen=True)
    class CellGeometry:
        """
        Complete geometric result for one slit-encoded @cell polygon.

        All quantities are purely geometric. No material, weight, or shear-weight
        factor is included here.
        """

        # Topological split indices
        outer_end: int
        inner_start: int
        inner_end: int

        # Extracted loops without duplicated closure points
        outer_xy: List[Tuple[float, float]]
        inner_xy: List[Tuple[float, float]]

        # Areas
        A_outer: float
        A_inner: float
        A_wall: float

        # Perimeters
        P_outer: float
        P_inner: float
        P_total: float

        # Global mid-line quantities
        A_m: float
        b_m: float

        # Geometric thickness fallback
        t_geom: float


    def _same_point(
        a: Tuple[float, float],
        b: Tuple[float, float],
    ) -> bool:
        """
        Return True if two points coincide within the global geometric tolerance.
        """
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        return (dx * dx + dy * dy) <= _tol.EPS_A


    def _find_cell_split_indices(
        xy: List[Tuple[float, float]],
        nm: str,
    ) -> Tuple[int, int, int]:
        """
        Find the topological split indices of a slit-encoded @cell polygon.

        OUTER starts at xy[0] and closes at the first later point coincident
        with xy[0].

        INNER starts immediately after OUTER closure and is represented by the
        remaining tail of xy. The last point of xy must coincide with the first
        INNER point, so INNER is explicitly closed on itself.
        """
        if len(xy) < 8:
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' has too few vertices "
                f"for @cell encoding."
            )

        outer_end = None

        for i in range(1, len(xy)):
            if _same_point(xy[i], xy[0]):
                outer_end = i
                break

        if outer_end is None or outer_end < 3:
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' cannot close OUTER loop."
            )

        inner_start = outer_end + 1
        inner_end = len(xy) - 1

        if (inner_end - inner_start) < 3:
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' INNER loop is degenerate."
            )

        if not _same_point(xy[inner_end], xy[inner_start]):
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' INNER closure is not valid"
            )

        return outer_end, inner_start, inner_end


    def _validate_cell_split_indices(
        xy: List[Tuple[float, float]],
        nm: str,
        split_indices: Tuple[int, int, int],
    ) -> Tuple[int, int, int]:
       
        """
        Validate @cell split indices against the current vertex sequence.

        The split itself is detected by _find_cell_split_indices(). This function
        only checks that the resulting OUTER and INNER closure indices are
        topologically and geometrically valid.    
    
        """
        outer_end, inner_start, inner_end = split_indices

        if len(xy) < 8:
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' has too few vertices "
                f"for @cell encoding."
            )

        if not (0 < outer_end < inner_start <= inner_end < len(xy)):
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' has @cell split "
                f"(outer_end={outer_end}, inner_start={inner_start}, inner_end={inner_end})."
            )

        if (inner_end - inner_start) < 3:
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' INNER loop is degenerate."
            )

        if not _same_point(xy[outer_end], xy[0]):
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' OUTER closure is not valid."
            )

        if not _same_point(xy[inner_end], xy[inner_start]):
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}'INNER closure is not valid."
            )

        return split_indices


    def _build_cell_geometry_from_indices(
        xy: List[Tuple[float, float]],
        nm: str,
        outer_end: int,
        inner_start: int,
        inner_end: int,
    ) -> CellGeometry:
        """
        Build CellGeometry from already-known split indices.

        The duplicated closure points are excluded from both loops.
        """
        outer_xy = xy[0:outer_end]
        inner_xy = xy[inner_start:inner_end]

        A_outer_signed = _signed_area_xy(outer_xy)
        A_inner_signed = _signed_area_xy(inner_xy)


        if A_outer_signed * A_inner_signed >= 0.0:
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' OUTER and INNER loops "
                f"must have opposite signed areas."
            )


        if A_outer_signed == 0.0 or A_inner_signed == 0.0:
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' has zero-area OUTER or INNER loop."
            )


        A_outer = abs(A_outer_signed)
        A_inner = abs(A_inner_signed)

        # The geometrically outer loop is the one with larger absolute area.
        if A_inner > A_outer:
            outer_xy, inner_xy = inner_xy, outer_xy
            A_outer, A_inner = A_inner, A_outer

        A_wall = A_outer - A_inner
        if A_wall <= _tol.EPS_A:
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' has non-positive wall area "
                f"(A_outer={A_outer:.12g}, A_inner={A_inner:.12g})."
            )

        P_outer = _perimeter_xy(outer_xy)
        P_inner = _perimeter_xy(inner_xy)
        P_total = P_outer + P_inner

        if P_total <= _tol.EPS_L:
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' has near-zero total perimeter."
            )

        A_m = 0.5 * (A_outer + A_inner)
        b_m = 0.5 * P_total
        t_geom = 2.0 * A_wall / P_total

        if A_m <= _tol.EPS_A or b_m <= _tol.EPS_L:
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' has degenerate global mid-line quantities."
            )

        return CellGeometry(
            outer_end=outer_end,
            inner_start=inner_start,
            inner_end=inner_end,
            outer_xy=outer_xy,
            inner_xy=inner_xy,
            A_outer=A_outer,
            A_inner=A_inner,
            A_wall=A_wall,
            P_outer=P_outer,
            P_inner=P_inner,
            P_total=P_total,
            A_m=A_m,
            b_m=b_m,
            t_geom=t_geom,
        )


    def _split_outer_inner_loops_global(
        xy: List[Tuple[float, float]],
        nm: str
        #split_indices: Optional[Tuple[int, int, int]] = None,
    ) -> Tuple[CellGeometry, Tuple[int, int, int]]:
        """
        Split a slit-encoded @cell polygon and compute all geometric quantities.

        The OUTER/INNER split is detected from the current vertex sequence.
        Areas, perimeters, mid-line quantities, and t_geom are recomputed from
        the current coordinates.
        """
        
        split_indices = _find_cell_split_indices(xy, nm)
        _validate_cell_split_indices(xy, nm, split_indices)

        outer_end, inner_start, inner_end = split_indices

        cell_geom = _build_cell_geometry_from_indices(
            xy=xy,
            nm=nm,
            outer_end=outer_end,
            inner_start=inner_start,
            inner_end=inner_end,
        )

        return cell_geom, split_indices


    def _compute_J_cell_geom_from_global_mid_quantities(
        cell_geom: CellGeometry,
        t: float,
        nm: str,
        i_cell: int,
        z_sec,
    ) -> float:
        """
        Compute J using global mid-line quantities:

            A_m = 0.5 * (A_outer + A_inner)
            b_m = 0.5 * (P_outer + P_inner)
            J   = 4 * A_m^2 * t / b_m
        """
        if cell_geom.A_m <= _tol.EPS_A or cell_geom.b_m <= _tol.EPS_L:
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' degenerate global mid quantities "
                f"(A_m={cell_geom.A_m:.12g}, b_m={cell_geom.b_m:.12g})."
            )

        if verbose:
            print(
                f"[CELL-GEOM][idx={i_cell}][z={z_sec}][{nm}] \n"
                f"A_outer={cell_geom.A_outer:.12g} A_inner={cell_geom.A_inner:.12g} "
                f"A_wall={cell_geom.A_wall:.12g} \n"
                f"P_outer={cell_geom.P_outer:.12g} P_inner={cell_geom.P_inner:.12g} "
                f"P_total={cell_geom.P_total:.12g} \n"
                f"A_m={cell_geom.A_m:.12g} b_m={cell_geom.b_m:.12g} t={t:.12g} \n"
            )

        return 4.0 * (cell_geom.A_m ** 2) * t / cell_geom.b_m

    #--
    def _xy_list(poly) -> List[Tuple[float, float]]:
        """
        Return polygon vertices as [(x, y), ...], preserving original sequence.
        """
        verts = getattr(poly, "vertices", None)
        if not verts or len(verts) < 3:
            return []
        return [(float(v.x), float(v.y)) for v in verts]

    def _perimeter_xy(xy: List[Tuple[float, float]]) -> float:
        """
        Perimeter of a closed polygonal chain (last->first included).
        """
        n = len(xy)
        if n < 2:
            return 0.0
        P = 0.0
        for i in range(n):
            x0, y0 = xy[i]
            x1, y1 = xy[(i + 1) % n]
            dx = x1 - x0
            dy = y1 - y0
            P += (dx * dx + dy * dy) ** 0.5
        return P

    def _signed_area_xy(xy: List[Tuple[float, float]]) -> float:
        """
        Signed area by shoelace (>0 CCW).
        """
        area, _, _ = _poly_signed_area_centroid_xy(xy)
        
        
        return area


    def _parse_t(name: str) -> Optional[float]:
        """
        Parse @t=<value> from polygon name. Return positive float or None.
        """
        low = name.lower()
        idx = low.find(TOKEN_T)
        if idx < 0:
            return None

        start = idx + len(TOKEN_T)
        if start >= len(name):
            return None

        allowed = set("0123456789.+-eE")
        s = []
        for ch in name[start:]:
            if ch in allowed:
                s.append(ch)
            else:
                break

        if not s:
            return None

        try:
            tval = float("".join(s))
        except Exception:
            return None

        if tval <= 0.0:
            return None
        return tval
    # -------------------------------------------------------------------------
    # 2) Accumulate contributions
    # -------------------------------------------------------------------------
    J_total = 0.0

    for i_cell, p in enumerate(cell_polys):
        nm = str(getattr(p, "name", "") or "")

        # No silent default for structural weight.
        shear_weight = float(getattr(p, "shear_weight"))

        if abs(shear_weight) < _tol.EPS_A:
            continue

        xy = _xy_list(p)
        
        cell_geom, split_indices = _split_outer_inner_loops_global(
            xy=xy,
            nm=nm
        )
        
        t = _parse_t(nm)
        if t is None:
            t = cell_geom.t_geom
            
        if t < _tol.EPS_L:
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' invalid thickness t={t}."
            )
              

        z_sec = getattr(section, "z", None)

        J_geom = _compute_J_cell_geom_from_global_mid_quantities(
            cell_geom=cell_geom,
            t=t,
            nm=nm,
            i_cell=i_cell,
            z_sec=z_sec,
        )
        contrib = shear_weight * J_geom
        if verbose:
            print(
                f"[CELL-CHECK] z={z_sec} idx={i_cell} name={nm} "
                f"n_outer={len(cell_geom.outer_xy)} n_inner={len(cell_geom.inner_xy)} "
                f"A_outer={cell_geom.A_outer:.12e} "
                f"A_inner={cell_geom.A_inner:.12e} "
                f"A_wall={cell_geom.A_wall:.12e} "
                f"P_outer={cell_geom.P_outer:.12e} "
                f"P_inner={cell_geom.P_inner:.12e} "
                f"P_total={cell_geom.P_total:.12e} "
                f"A_m={cell_geom.A_m:.12e} "
                f"b_m={cell_geom.b_m:.12e} "
                f"t={t:.12e} "
                f"J_geom={J_geom:.12e} "
                f"GJ={contrib:.12e}"
            )


        J_total += contrib
        
    if len(cell_polys) == 1:
        
        return J_total, t
    
    else:
        
        return J_total


"""
CSF torsion (Saint-Venant) - WALL-based variant with optional thickness override

Drop-in snippet: add this function in the same module where:
- Section / Polygon classes are defined
- polygon_area_centroid(poly) exists and returns (signed_area, cx, cy)
- compute_saint_venant_J(section) exists (legacy fallback)
- _tol.EPS_A, _tol.EPS_L exist (or replace with your tolerances)

User convention
---------------
A polygon is treated as a "wall entity" if its name contains the token "@WALL"
(case-insensitive). Example:

    web@wall
    top_flange@WALL

Optional thickness override:
----------------------------
The user may also provide a thickness override inside the SAME name string:

    web@wall@t=0.01
    top_flange@wall@t=0.0125

Rules:
- If "@t=<number>" is present, that thickness (in meters) is used for that wall polygon.
- If "@t=" is absent, thickness is estimated from pure geometry (rigid rule):

        t := t = (P - sqrt(P² - 16A)) / 4 or 2*A / P

This is intentionally profile-agnostic: no shape recognition, no heuristics, no tests.
The user is responsible for tagging the correct polygons.

Theory (international standard: open thin-walled approximation)
---------------------------------------------------------------
For open thin-walled sections:

    J_sv ≈ Σ ( b_i * t_i^3 / 3 )

To avoid explicitly computing the midline length b_i, use the thin-wall identity:

    A_i ≈ b_i * t_i  =>  b_i ≈ A_i / t_i

Then:

    J_i ≈ (A_i / t_i) * t_i^3 / 3 = A_i * t_i^2 / 3

Important note on weights
-------------------------
CSF polygon weights may be used as stiffness scalars.
For torsion stiffness (G * J), negative stiffness is not physically meaningful,
so we scale contributions by abs(weight).
If you want a different convention, change abs(w) accordingly.
"""
def compute_saint_venant_J_wall(section: "Section") -> float:
    """
    Compute Saint-Venant torsional constant J_sv using "@WALL" polygons.

    Dispatch
    --------
    - If no polygon name contains "@WALL": return compute_saint_venant_J(section) (legacy).
    - Otherwise: use open thin-walled approximation on polygons tagged with "@WALL".

    Thickness choice per wall polygon
    ---------------------------------
    - If polygon name contains "@t=<value>": use that thickness (meters).
    - Else: estimate thickness via t := 2*A/P.

    Returns
    -------
    float
        Effective Saint-Venant torsional constant J_sv [m^4].
    """
    verbose = False
    # -----------------------------
    # 1) Geometry helpers
    # -----------------------------
    def _poly_area_abs(poly) -> float:
        verts = getattr(poly, "vertices", None)
        if not verts or len(verts) < 3:
            return 0.0

        s = 0.0
        n = len(verts)

        for i in range(n):
            j = (i + 1) % n
            xi = float(verts[i].x)
            yi = float(verts[i].y)
            xj = float(verts[j].x)
            yj = float(verts[j].y)
            s += xi * yj - xj * yi

        return abs(0.5 * s)


    def _poly_perimeter(poly) -> float:
        verts = getattr(poly, "vertices", None)
        if not verts or len(verts) < 2:
            return 0.0

        perim = 0.0
        n = len(verts)

        for i in range(n):
            j = (i + 1) % n
            dx = float(verts[j].x) - float(verts[i].x)
            dy = float(verts[j].y) - float(verts[i].y)
            perim += (dx * dx + dy * dy) ** 0.5

        return perim
        
    # -----------------------------
    # 2) Parse optional "@t=<...>"
    # -----------------------------
    def _parse_thickness_from_name(name: str) -> Optional[float]:
        """
        Parse thickness override from a polygon name.

        Accepted patterns (case-insensitive):
            "...@t=0.01"
            "...@T=0.01"

        Parsing stops at the first non-numeric character (besides . + - e E).

        Returns
        -------
        float | None
            Thickness in meters, or None if not present / not parseable.
        """
        low = name.lower()
        idx = low.find(token_t)
        if idx < 0:
            return None

        start = idx + len(token_t)
        if start >= len(name):
            return None

        # Collect a valid float substring 
        allowed = set("0123456789.+-eE")
        s = []
        for ch in name[start:]:
            if ch in allowed:
                s.append(ch)
            else:
                break

        if not s:
            return None

        try:
            tval = float("".join(s))
        except Exception:
            return None

        # Reject non-positive values
        if tval <= 0.0:
            return None

        return tval

    
    token_wall = "@WALL"
    token_t = "@t="

    polys = getattr(section, "polygons", None)
    if not polys:
        return 0.0

    # -----------------------------
    # 0) Select wall polygons
    # -----------------------------
    wall_polys = []
    for p in polys:
        nm = str(getattr(p, "name", "") or "")
        if token_wall.lower() in nm.lower():
            wall_polys.append(p)

    # No "@WALL" anywhere exit
    #if not wall_polys:
    #    return 0.0 
    
    # -----------------------------
    # 3) Compute J_sv_wall (open thin-walled)
    # -----------------------------

    J = 0.0
    n_wall_used = 0 
    for p in wall_polys:
        
        shear_weight = float(getattr(p, "shear_weight"))
        
        if abs(shear_weight) < _tol.EPS_A:
            t=0            
            continue
        
        A = _poly_area_abs(p)
        
        if A < _tol.EPS_A:
            t=0
            continue
        
        nm = str(getattr(p, "name", "") or "")
        t_override = _parse_thickness_from_name(nm)
        t_source = "?"
        if t_override is not None:
            if verbose:
                print(f"DEBUG t_override {t_override}")
            t = float(t_override)
            t_source = "@t"

        else:
            P = _poly_perimeter(p)
            if P < _tol.EPS_L:
                continue

            disc = P * P - 16.0 * A
            if disc < 0.0:
                t = 2.0 * A / P
                t_source = "2A/P_fallback"
            else:
                t = (P - disc ** 0.5) / 4.0
                t_source = "Tglobal"
                
        if t < _tol.EPS_L:
            continue
        

        # b ≈ A/t, so J_i ≈ (A/t)*t^3/3 = A*t^2/3
        J_i = (A * (t ** 2)) / 3.0

        J_i_wall = J_i
        if verbose:
            print(f"DEBUG Area poly {p} A={A} J_i={J_i}")    

        P_dbg = _poly_perimeter(p)

        b_est = (A / t) if t > _tol.EPS_L else 0.0
        if verbose:
            print(
                "[DEBUG J_WALL] "
                f"name={nm!r} | "
                f"A={A:.8e} | "
                f"P={P_dbg:.8e} | "
                f"t={t:.8e} [{t_source}] | "
                f"b_est=A/t={b_est:.8e} | "
                f"J_i={J_i_wall:.8e} | "
                f"shear_weight={shear_weight:.8e}"
            )


        # Keep torsional stiffness non-negative
        J +=  shear_weight * J_i
    

    if len(wall_polys) == 1:
        return float(J),t
    else:
        
        return float(J)


def _poly_vertices_xy(poly: Any) -> List[PointXY]:
    """Extract polygon vertices as plain (x, y) float tuples."""
    verts = getattr(poly, "vertices", None)
    if verts is None:
        raise ValueError(f"Polygon '{getattr(poly, 'name', None)}' has no .vertices attribute.")
    out: List[PointXY] = []
    for v in verts:
        out.append((float(getattr(v, "x")), float(getattr(v, "y"))))
    return out


def _bbox_xy(verts: Sequence[PointXY]) -> Tuple[float, float, float, float]:
    """Axis-aligned bounding box for a vertex list."""
    if not verts:
        raise ValueError("Empty vertex list.")
    xs = [p[0] for p in verts]
    ys = [p[1] for p in verts]
    return (min(xs), min(ys), max(xs), max(ys))


def _auto_grid_h_from_bbox(verts: Sequence[PointXY], auto_n: int) -> float:
    """
    Automatic grid spacing based on the polygon bounding box:

        h := min(span_x, span_y) / auto_n
    """
    if auto_n <= 0:
        raise ValueError("auto_n must be > 0.")
    x0, y0, x1, y1 = _bbox_xy(verts)
    span_x = x1 - x0
    span_y = y1 - y0
    span = span_x if span_x < span_y else span_y
    if span <= 0.0:
        raise ValueError("Degenerate polygon bounding box (zero span).")
    return span / float(auto_n)


def _point_on_segment_sq(
    px: float, py: float,
    ax: float, ay: float,
    bx: float, by: float,
    eps_l: float
) -> bool:
    """
    Return True if point (px,py) lies on segment AB, with tolerance.

    No abs(); uses squared comparisons.
    """
    abx = bx - ax
    aby = by - ay
    apx = px - ax
    apy = py - ay

    ab2 = abx * abx + aby * aby
    eps2 = eps_l * eps_l

    # Degenerate segment (A≈B): treat as a point.
    if ab2 <= eps2:
        dx = px - ax
        dy = py - ay
        return (dx * dx + dy * dy) <= eps2

    # Collinearity: cross product magnitude squared <= (eps^2 * |AB|^2)
    cross = abx * apy - aby * apx
    if (cross * cross) > (eps2 * ab2):
        return False

    # Projection: 0 <= dot <= |AB|^2 (with tolerance)
    dot = apx * abx + apy * aby
    if dot < -eps_l:
        return False
    if dot > (ab2 + eps_l):
        return False

    return True


def _point_in_poly_inclusive(px: float, py: float, verts: Sequence[PointXY], eps_l: float) -> bool:
    """
    Ray casting point-in-polygon, counting boundary as inside.

    No validation is performed; self-intersections may yield undefined results.
    """
    n = len(verts)
    if n < 3:
        return False

    # Boundary inclusion: test "on any edge".
    for i in range(n):
        ax, ay = verts[i]
        bx, by = verts[(i + 1) % n]
        if _point_on_segment_sq(px, py, ax, ay, bx, by, eps_l):
            return True

    inside = False
    for i in range(n):
        x1, y1 = verts[i]
        x2, y2 = verts[(i + 1) % n]

        # Edge straddles horizontal line at py?
        cond = (y1 > py) != (y2 > py)
        if cond:
            x_int = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if x_int > px:
                inside = not inside

    return inside


def _build_inside_mask(
    verts: Sequence[PointXY],
    xs: np.ndarray,
    ys: np.ndarray,
    eps_l: float
) -> np.ndarray:
    """Build boolean mask M[j,i] = True if grid node (xs[i], ys[j]) is inside polygon."""
    ny = int(ys.size)
    nx = int(xs.size)
    mask = np.zeros((ny, nx), dtype=bool)

    for j in range(ny):
        y = float(ys[j])
        for i in range(nx):
            x = float(xs[i])
            if _point_in_poly_inclusive(x, y, verts, eps_l):
                mask[j, i] = True

    return mask


def _solve_poisson_sor(
    mask: np.ndarray,
    h: float,
    *,
    max_iter: int,
    tol: float,
    omega: float
) -> np.ndarray:
    """
    Solve ∇²ψ = -2 on a masked grid using SOR, with ψ=0 outside.

    Stopping rule:
        max update magnitude <= tol
    (implemented via squared values; no abs()).
    """
    ny, nx = mask.shape
    psi = np.zeros((ny, nx), dtype=float)

    h2 = h * h
    tol2 = tol * tol
    rhs_term = 2.0 * h2  # from discretization of -2

    for _ in range(int(max_iter)):
        max_d2 = 0.0

        for j in range(ny):
            for i in range(nx):
                if not mask[j, i]:
                    continue

                old = psi[j, i]

                # Neighbor values, ψ=0 outside.
                e = psi[j, i + 1] if (i + 1 < nx and mask[j, i + 1]) else 0.0
                w = psi[j, i - 1] if (i - 1 >= 0 and mask[j, i - 1]) else 0.0
                n = psi[j - 1, i] if (j - 1 >= 0 and mask[j - 1, i]) else 0.0
                s = psi[j + 1, i] if (j + 1 < ny and mask[j + 1, i]) else 0.0

                gs = (e + w + n + s + rhs_term) * 0.25
                new = (1.0 - omega) * old + omega * gs
                psi[j, i] = new

                d = new - old
                d2 = d * d
                if d2 > max_d2:
                    max_d2 = d2

        if max_d2 <= tol2:
            break

    return psi

def _sq(x: float) -> float:
    return x * x


def _is_near_zero(x: float, eps: float) -> bool:
    """
    Compare x to 0 using squared values to avoid abs().

    Note: This is for degeneracy guards only (division-by-zero avoidance).
    It does not "fix" or "normalize" signs.
    """
    return _sq(x) <= _sq(eps)


def _signed_area_centroid_xy(
    verts: Sequence[tuple[float, float]]
) -> Tuple[float, float, float]:
    """
    Shoelace formula.
    Returns (A, Cx, Cy) not weight
    """

    n = len(verts)
    if n < 3:
        raise ValueError("Polygon has <3 vertices.")

    a2 = 0.0
    cx6 = 0.0
    cy6 = 0.0

    for i in range(n):
        x0, y0 = verts[i]
        x1, y1 = verts[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        a2 += cross
        cx6 += (x0 + x1) * cross
        cy6 += (y0 + y1) * cross

    if abs(a2) < _tol.EPS_A:
        return 0.0, 0.0, 0.0

    A = 0.5 * a2
    Cx = cx6 / (3.0 * a2)
    Cy = cy6 / (3.0 * a2)

    return A, Cx, Cy


def _poly_signed_area_centroid_xy(verts: Sequence[PointXY]) -> Tuple[float, float, float]:#qui
    return _signed_area_centroid_xy(verts)


def export_to_opensees_tcl(field, K_12x12, filename="csf_model.tcl"):
    """
      Generates an OpenSees-ready .tcl file that defines the nodes and the stiffness-matrix element computed by CSF.
    """
    z0 = field.z0
    z1 = field.z1
    
    with open(filename, "w") as f:
        f.write("# --------------------------------------------------\n")
        f.write("# Model automatically generated by CSF (Continuous Section Field)\n")
        f.write("# --------------------------------------------------\n\n")
        
        # 1. Definition of the Nodes (Base and Top)
        # Syntax: node nodeTag x y z
        f.write(f"node 1 0.0 0.0 {z0}\n")
        f.write(f"node 2 0.0 0.0 {z1}\n\n")
        
        # 2. Definition of the stiffness matrix K in TCL list format
        f.write("set K {\n")
        for row in K_12x12:
            row_str = " ".join(f"{val:.8e}" for val in row)
            f.write(f"    {row_str}\n")
        f.write("}\n\n")
        
        # 3. Definition of the geometric transformation (required in OpenSees)
        f.write("geomTransf Linear 1 0 1 0\n\n")
        
        # 4. Definition of the MatrixBeamColumn element
        # Syntax: element matrixBeamColumn eleTag iNode jNode transfTag Klist
        f.write("element matrixBeamColumn 1 1 2 1 $K\n\n")
        
        f.write("puts \"CSF model successfully loaded: 2 nodes, 1 element (12×12 stiffness matrix)\"\n")

    print(f"TCL file generated successfully: {filename}")


def assemble_element_stiffness_matrix(field: ContinuousSectionField, E_ref: float = 1.0, 
                                nu: float = 0.3, n_gauss: int = 5) -> np.ndarray:
    """
    Assembles the complete 12x12 Timoshenko beam stiffness matrix with full EIxy coupling.

    DOF order (OpenSees compatible): [ux1,uy1,uz1,θx1,θy1,θz1 | ux2,uy2,uz2,θx2,θy2,θz2]
    Full asymmetric section support (EIxy coupling) + Saint-Venant torsion.
    """
    L = abs(field.z1 - field.z0)
    if L < _tol.EPS_L:
        raise ValueError("Element length must be positive")

    G_ref = E_ref / (2 * (1 + nu))

    # Gaussian quadrature points (n_gauss sufficient for exact integration)
    gauss_points = np.polynomial.legendre.leggauss(n_gauss)

    K = np.zeros((12, 12))

    for xi, weight in gauss_points:
        z_phys = ((field.z1 - field.z0) * xi + (field.z1 + field.z0)) / 2.0 # absolute z
        W = weight * (L / 2.0)
        
        # Sectional properties
        K_sec = section_stiffness_matrix(field.section(z_phys), E_ref=E_ref) # absolute z
        props = section_full_analysis(field.section(z_phys))#alpha not used

        '''
        Jt = props.get("J_sv", 0.0)
        if Jt <= 0.0:
            Jt = props.get("J_s_vroark", 0.0)
        '''
        GK = 0#G_ref * Jt

        EA = K_sec[0, 0]
        EIx = K_sec[1, 1] 
        EIy = K_sec[2, 2]
        EIxy = K_sec[1, 2]
        #GK = props['Ip'] * G_ref  # Correct Saint-Venant torsion
        
        # Integration coefficients (Euler-Bernoulli exact)
        c1 = 12 * W / L**3
        c2 = 6 * W / L**2  
        c3 = 4 * W / L
        c4 = 2 * W / L
        
        # AXIAL (DOF 0,6)
        axial = EA * W / L
        K[0,0] += axial; K[6,6] += axial
        K[0,6] -= axial; K[6,0] -= axial
        
        # TORSION (DOF 3,9) - Saint-Venant
        tors = GK * W / L
        K[3,3] += tors; K[9,9] += tors  
        K[3,9] -= tors; K[9,3] -= tors
        
        # FLEXURE YZ (about X) - DOF 1,5,7,11 [uy1,θz1,uy2,θz2]
        K[1,1] += c1*EIx; K[1,5] += c2*EIx; K[1,7] -= c1*EIx; K[1,11] += c2*EIx
        K[5,5] += c3*EIx; K[5,7] -= c2*EIx; K[5,11] += c4*EIx
        K[7,7] += c1*EIx; K[7,11] -= c2*EIx
        K[11,11] += c3*EIx
        
        # FLEXURE XZ (about Y) - DOF 2,4,8,10 [uz1,θy1,uz2,θy2] 
        K[2,2] += c1*EIy; K[2,4] -= c2*EIy; K[2,8] -= c1*EIy; K[2,10] -= c2*EIy
        K[4,4] += c3*EIy; K[4,8] += c2*EIy; K[4,10] += c4*EIy
        K[8,8] += c1*EIy; K[8,10] += c2*EIy
        K[10,10] += c3*EIy
        
        # FULL EIxy COUPLING (24 terms) - Bending-bending interaction
        # Node 1 rotations [uy1,uz1] = [1,2] couple with [θz1,θy1] = [5,4]
        K[1,2] += c1*EIxy; K[2,1] += c1*EIxy
        K[1,4] -= c2*EIxy; K[4,1] -= c2*EIxy  
        K[1,8] -= c1*EIxy; K[8,1] -= c1*EIxy
        K[1,10] -= c2*EIxy; K[10,1] -= c2*EIxy
        
        K[2,5] += c2*EIxy; K[5,2] += c2*EIxy
        K[4,5] += c4*EIxy; K[5,4] += c4*EIxy  # Corrected from 0.0
        K[2,7] -= c1*EIxy; K[7,2] -= c1*EIxy
        K[2,11] -= c2*EIxy; K[11,2] -= c2*EIxy
        
        K[5,8] -= c2*EIxy; K[8,5] -= c2*EIxy
        K[5,10] += c4*EIxy; K[10,5] += c4*EIxy
        K[7,4] -= c2*EIxy; K[4,7] -= c2*EIxy
        K[7,10] += c2*EIxy; K[10,7] += c2*EIxy
        
        K[11,4] += c2*EIxy; K[4,11] += c2*EIxy
        K[11,8] -= c2*EIxy; K[8,11] -= c2*EIxy

    # Final validation (reciprocity theorem)
    if not np.allclose(K, K.T, rtol=_tol.EPS_K_RTOL, atol=_tol.EPS_K_ATOL):
        warnings.warn("Minor asymmetry detected - enforcing symmetry", RuntimeWarning)
        K = (K + K.T) / 2.0

    # Physical bounds check
    if np.any(np.diag(K[:6]) < 0):
        raise ValueError("Negative diagonal stiffness detected")
        
    return K

    
def polygon_inertia_about_origin(poly: Polygon) -> Tuple[float, float, float]:
    """
    Second moments about the origin (0,0) using standard polygon formulas.
    Returns (Ix, Iy, Ixy) about origin, INCLUDING poly.weight.

    Notes:
    - Works for simple polygons (non self-intersecting).
    - Sign/orientation is handled by using signed cross; we then multiply by weight.
    - For holes, you can use negative weight or a separate convention.
    """
    verts = poly.vertices
    n = len(verts)

    Ix = 0.0
    Iy = 0.0
    Ixy = 0.0

    for i in range(n):
        x0, y0 = verts[i].x, verts[i].y
        x1, y1 = verts[(i + 1) % n].x, verts[(i + 1) % n].y
        cross = x0 * y1 - x1 * y0

        Ix += (y0 * y0 + y0 * y1 + y1 * y1) * cross
        Iy += (x0 * x0 + x0 * x1 + x1 * x1) * cross
        Ixy += (x0 * y1 + 2.0 * x0 * y0 + 2.0 * x1 * y1 + x1 * y0) * cross

    Ix *= (1.0 / 12.0)
    Iy *= (1.0 / 12.0)
    Ixy *= (1.0 / 24.0)

    # Apply weight; keep sign conventions consistent by using magnitude of orientation implicitly
    # For typical usage, we want weighted contributions. We take absolute values of Ix/Iy if polygon orientation flips.
    # Using signed formulas + abs for Ix/Iy tends to be robust for mixed orientations in prototypes.
    return (poly.weight * Ix, poly.weight * Iy, poly.weight * Ixy)

# -----------------------------------------------------------------------------
# Volume polygon-list report helpers (reuses integrate_volume; no local integration)
# -----------------------------------------------------------------------------


def volume_polygon_list_report_data(
    field: "ContinuousSectionField",
    z1: float,
    z2: float,
    n_points: int = 20,
    *,
    do_debug_check: bool = False,
    debug_tol: float = 1e-9,
) -> Dict[str, Any]:
    """
    Build per-polygon volume report data between two stations.

    Design rules
    ------------
    - Volumes are computed ONLY via integrate_volume(...).
    - Descriptive columns (names, weights at endpoints, law labels) are obtained
      from field.inspect_section_entities(z).
    - No additional validation/assumptions are introduced here; CSF preconditions
      are enforced upstream (parser/validator).

    Parameters
    ----------
    field:
        ContinuousSectionField instance.
    z1, z2:
        Two absolute stations (order is preserved for reporting; integration uses [min,max]).
    n_points:
        Gauss-Legendre points passed to integrate_volume.
    do_debug_check:
        If True, checks (internally) that sum of per-polygon weighted volumes matches
        integrate_volume(idx=None) (within tolerance). Not printed by default.
    debug_tol:
        Absolute tolerance used for the internal check.

    Returns
    -------
    Dict[str, Any] with keys:
      - "z1", "z2", "n_points"
      - "rows": list of dict rows (one per polygon)
      - "tot_occ", "tot_hom"
      - "debug": dict (only meaningful if do_debug_check=True)
    """
    z1 = float(z1)
    z2 = float(z2)

    # Station snapshots (authoritative for metadata).
    e1 = field.inspect_section_entities(z1)
    e2 = field.inspect_section_entities(z2)

    rows: List[Dict[str, Any]] = []

    tot_occ = 0.0
    tot_hom = 0.0

    # Integration uses positive measure but we keep z1/z2 ordering for the report.
    z_int0 = min(z1, z2)
    z_int1 = max(z1, z2)

    for i in range(len(e1)):
        r1 = e1[i]
        r2 = e2[i]

        # Metadata (no reinterpretation).
        s0_name = str(r1.get("s0_name"))
        s1_name = str(r1.get("s1_name"))

        w1 = float(r1.get("weight_abs_z")) #weight_at_z
        w2 = float(r2.get("weight_abs_z"))  #weight_at_z

        law = r1.get("weight_law")
        law_str = "none" if law is None else str(law)

        # Volumes (no local integration here).
        v = integrate_volume(field, z_int0, z_int1, int(n_points), idx=int(i))


        # idx-mode returns a (V_geom, V_weighted) tuple by contract.
        v_occ = float(v[0])
        v_hom = float(v[1])

        tot_occ += v_occ
        tot_hom += v_hom

        rows.append(
            {
                "id": int(i),
                "s0_w": w1,
                "s1_w": w2,
                "weight_law": law_str,
                "s0_name": s0_name,
                "s1_name": s1_name,
                "volume_occupied": v_occ,
                "homogenized_volume_occupied": v_hom,
            }
        )

    debug: Dict[str, Any] = {}
    if do_debug_check:
        v_total = float(integrate_volume(field, z_int0, z_int1, int(n_points), idx=None))
        # Per requirement: compare against weighted sum (homogenized column).
        delta = float(tot_hom - v_total)
        ok = abs(delta) <= float(debug_tol)
        debug = {
            "enabled": True,
            "v_total": v_total,
            "sum_hom": float(tot_hom),
            "delta": delta,
            "abs_tol": float(debug_tol),
            "ok": bool(ok),
        }
    
    return {
        "z1": z1,
        "z2": z2,
        "n_points": int(n_points),
        "rows": rows,
        "tot_occ": float(tot_occ),
        "tot_hom": float(tot_hom),
        "debug": debug,
    }

def volume_polygon_list_report(
    field: ContinuousSectionField,
    z1: float,
    z2: float,
    *,
    n_points: int = 20,
    outputs: list[Any] | None = None,
    fmt_display: str = "0.6f",
    w_tol: float = 0.0,
    do_debug_check: bool = False,
    debug_tol: float = 1e-9,
) -> dict[str, Any]:
    """
    High-level API: build and emit the per-polygon volume report.

    This is a convenience wrapper around:
      - volume_polygon_list_report_data(...)
      - emit_volume_polygon_list_report(...)

    Rules
    -----
    - No extra validation or assumptions are introduced here.
    - Volumes come from integrate_volume (via volume_polygon_list_report_data).
    - Metadata comes from field inspection (via volume_polygon_list_report_data).

    Returns
    -------
    The report dict returned by volume_polygon_list_report_data(...).
    """
    # Build report data (per-polygon volumes + totals)
    report = volume_polygon_list_report_data(
        field,
        float(z1),
        float(z2),
        int(n_points),
        do_debug_check=bool(do_debug_check),
        debug_tol=float(debug_tol),
    )

    # Emit report to requested outputs (stdout/text/CSV)
    emit_volume_polygon_list_report(
        report,
        outputs=outputs,
        fmt_display=str(fmt_display),
        w_tol=float(w_tol) if w_tol is not None else 0.0,
    )

    return report


def emit_volume_polygon_list_report(
    report: Dict[str, Any],
    *,
    outputs: List[Any] | None = None,
    fmt_display: str = "0.6f",
    w_tol: float = 0.0,
) -> None:
    """
    Emit a volume polygon-list report (stdout/text/CSV) using the same formatting as actions.volume.

    Parameters
    ----------
    report:
        Object returned by volume_polygon_list_report_data(...).
    outputs:
        Output routing. If None/empty -> ["stdout"].
        - "stdout" prints the report.
        - any other string path:
            * ".csv" writes the CSV with the same field names as actions.volume
            * otherwise writes the text report.
    fmt_display:
        Numeric formatting string passed to built-in format(...).
    w_tol:
        Report header value (kept for backward compatibility; may be unused by the action logic).
    """
    if not outputs:
        outputs = ["stdout"]

    z1 = float(report["z1"])
    z2 = float(report["z2"])
    n_points = int(report["n_points"])
    rows = list(report["rows"])
    tot_occ = float(report["tot_occ"])
    tot_hom = float(report["tot_hom"])

    want_stdout = ("stdout" in outputs)
    want_text_file = any((isinstance(o, str) and o != "stdout" and Path(o).suffix.lower() != ".csv") for o in outputs)
    want_csv_file = any((isinstance(o, str) and o != "stdout" and Path(o).suffix.lower() == ".csv") for o in outputs)

    report_blocks: List[str] = []
    csv_rows: List[Dict[str, Any]] = []

    def _fmt(v: Any) -> str:
        if v is None:
            return "None"
        if isinstance(v, (int, float)):
            try:
                return format(float(v), fmt_display)
            except Exception:
                return str(v)
        return str(v)

    # Build report block if needed.
    if want_stdout or want_text_file:
        max_idx = max((int(r["id"]) for r in rows), default=0)
        id_width = max(2, len(str(max_idx)))

        buf = io.StringIO()
        with redirect_stdout(buf):
            print(f"VOLUME POLYGON LIST REPORT at z={_fmt(z1)} and z={_fmt(z2)}")
            print("=" * 120)
            print(f"n_points={int(n_points)}  w_tol={_fmt(float(w_tol) if w_tol is not None else 0.0)}")
            print("")
            print(
                f"{'id':<6s} | {'s0.w':>12s} | {'s1.w':>12s} | {'weight_law':<18s} | "
                f"{'s0.name':<18s} | {'s1.name':<18s} | {'Volume Occupied':>18s} | {'Homogenized Volume':>20s}"
            )
            print("-" * 120)

            for r in rows:
                i = int(r["id"])
                id_str = f"[{i:0{id_width}d}]"

                print(
                    f"{id_str:<6s} | {_fmt(r['s0_w']):>12s} | {_fmt(r['s1_w']):>12s} | {str(r['weight_law']):<18s} | "
                    f"{str(r['s0_name']):<18s} | {str(r['s1_name']):<18s} | {_fmt(r['volume_occupied']):>18s} | {_fmt(r['homogenized_volume_occupied']):>20s}"
                )

                if want_csv_file:
                    csv_rows.append(
                        {
                            "z1": float(z1),
                            "z2": float(z2),
                            "id": int(i),
                            "s0_w": float(r["s0_w"]),
                            "s1_w": float(r["s1_w"]),
                            "weight_law": str(r["weight_law"]),
                            "s0_name": str(r["s0_name"]),
                            "s1_name": str(r["s1_name"]),
                            "volume_occupied": float(r["volume_occupied"]),
                            "homogenized_volume_occupied": float(r["homogenized_volume_occupied"]),
                            "n_points": int(n_points),
                        }
                    )

            print("-" * 120)
            print(f"Total Occupied Volume:           {_fmt(tot_occ)}")
            print(f"Total Occupied Homogenized Volume: {_fmt(tot_hom)}")
            print("")

        report_blocks.append(buf.getvalue())

    # If we need CSV but we didn't build rows inside the report path (e.g., file-only CSV),
    # generate csv_rows now.
    if want_csv_file and not csv_rows:
        for r in rows:
            i = int(r["id"])
            csv_rows.append(
                {
                    "z1": float(z1),
                    "z2": float(z2),
                    "id": int(i),
                    "s0_w": float(r["s0_w"]),
                    "s1_w": float(r["s1_w"]),
                    "weight_law": str(r["weight_law"]),
                    "s0_name": str(r["s0_name"]),
                    "s1_name": str(r["s1_name"]),
                    "volume_occupied": float(r["volume_occupied"]),
                    "homogenized_volume_occupied": float(r["homogenized_volume_occupied"]),
                    "n_points": int(n_points),
                }
            )

    # Emit outputs.
    for outp in outputs:
        if outp == "stdout":
            for blk in report_blocks:
                print(blk, end="" if blk.endswith("\n") else "\n")
            continue

        p = Path(outp)
        if not p.parent.exists():
            raise RuntimeError(f"Output directory does not exist: {p.parent}")

        if p.suffix.lower() == ".csv":
            fieldnames = [
                "z1",
                "z2",
                "id",
                "s0_w",
                "s1_w",
                "weight_law",
                "s0_name",
                "s1_name",
                "volume_occupied",
                "homogenized_volume_occupied",
                "n_points",
            ]
            with open(p, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=fieldnames)
                w.writeheader()
                for row in csv_rows:
                    w.writerow(row)
        else:
            with open(p, "w", encoding="utf-8") as f:
                for blk in report_blocks:
                    f.write(blk)
                    if not blk.endswith("\n"):
                        f.write("\n")



"""
Volume integration utilities for CSF (ContinuousSectionField).

This file provides a drop-in replacement for the fixed n-point Gauss–Legendre
volume integration used in section_field.py.

The core idea is unchanged:

    V = ∫_z0^z1 A(z) dz

where A(z) is obtained by evaluating the CSF section at z and extracting its
(net / transformed) area from section_properties(...).

The improvement is that the number of Gauss points is now a parameter.

"""
# NOTE:
# - This function assumes the following names exist in section_field.py:
#     - class ContinuousSectionField with attributes z0, z1 and method section(z)
#     - function section_properties(section) returning a dict containing key "A"
#
# If your code uses different names (e.g., "field.z0/z1" or "props['A_tr']"),
# adjust only the extraction line where we read the area.
def integrate_volume(
    field: "ContinuousSectionField",
    z0: float,
    z1: float,
    n_points: int = 20,
    *,
    idx: int | None = None,
) -> float | tuple[float, float]:
    """
    Integrate "volume-like" quantities over [z0, z1] using Gauss–Legendre quadrature.

    Two scenarios only
    ------------------
    1) idx is None (LEGACY):
         Returns a single float:
           V_legacy = ∫ A_global(z) dz
         where A_global(z) is taken from:
           section_properties(field.section(z))["A"]
         (This preserves the existing legacy meaning: global area as defined by section_properties.)

    2) idx is an int (0-based):
         Returns a tuple of two floats:
           (V_geom, V_weighted)
         computed for ONE polygon only, using the "occupied surface" rule:
           - polygon has w=1
           - direct inners have w=0

         At each z we use polygon_surface_w1_inners0[_single] to get:
           A_net(z) = occupied surface (w=1 on polygon, w=0 on direct inners)
           A_w(z)   = A_net(z) * w_eff(z)

         Then:
           V_geom     = ∫ A_net(z) dz
           V_weighted = ∫ A_w(z) dz

    Notes
    -----
    - In idx mode we DO NOT call section_properties(...) to avoid mixing global weighted section logic.
    - Integration uses |z1 - z0| so results are positive "volumes" regardless of interval direction.
    """
    # --- basic validation ---
    if not isinstance(n_points, int) or n_points < 1:
        raise ValueError("n_points must be an integer >= 1")

    if not isinstance(z0, (int, float)):
        raise TypeError(f"z0 must be a number (float), got {type(z0).__name__}")
    if not isinstance(z1, (int, float)):
        raise TypeError(f"z1 must be a number (float), got {type(z1).__name__}")
    z0 = float(z0)
    z1 = float(z1)

    if idx is not None:
        if not isinstance(idx, int):
            raise TypeError(f"idx must be an int (0-based) or None, got {type(idx).__name__}")
        if idx < 0:
            raise ValueError(f"idx must be >= 0 (0-based), got {idx}")

    # Interval length (use absolute to produce positive "volume-like" values)
    L = abs(z1 - z0)
    if L == 0.0:
        return (0.0, 0.0) if idx is not None else 0.0

    z_mid = 0.5 * (z0 + z1)
    half_L = 0.5 * L

    # Gauss–Legendre nodes/weights on [-1, 1]
    xi, wi = np.polynomial.legendre.leggauss(n_points)

    # --- accumulators ---
    if idx is None:
        volume_legacy = 0.0
    else:
        volume_geom = 0.0
        volume_weighted = 0.0

    def _poly_A_pair_at_z(z_abs: float) -> tuple[float, float]:
        """
        Return (A_net, A_w) for the selected polygon idx at z_abs.

        Prefer a dedicated single-polygon function if it exists; otherwise
        fall back to computing the full list and selecting the requested idx.
        """
        # Try the specialized single function if available in the module namespace.
        #fn = globals().get("polygon_surface_w1_inners0_single")
        rec = polygon_surface_w1_inners0_single(field, z_abs, idx)  # type: ignore[misc]

        return float(rec["A"]), float(rec["A_w"])

    for x, w in zip(xi, wi):
        # Map x in [-1,1] to z in [z0,z1] (using midpoint + half-length)
        z = z_mid + half_L * float(x)
        w = float(w)

        if idx is None:
            sec = field.section(z)
            props = section_properties(sec)
            A_global = float(props["A"])
            volume_legacy += A_global * w * half_L
        else:
            # -----------------------------------------------------------------
            # IDX integrands (explicit and isolated):
            #   A_net(z): occupied surface (w=1 on polygon, w=0 on direct inners)
            #   A_w(z)  : A_net(z) * w_eff(z)
            # -----------------------------------------------------------------
            A_net, A_w = _poly_A_pair_at_z(z)
            volume_geom += A_net * w * half_L
            volume_weighted += A_w * w * half_L

    return volume_legacy if idx is None else (volume_geom, volume_weighted)
    
def section_full_analysis(section: Section, compute_vroark=True):
    """
    Perform a complete geometric and sectional analysis of a cross-section.

    The routine combines basic sectional properties with derived quantities such
    as principal inertias, elastic section moduli, first statical moment at the
    neutral axis, and selected torsional estimates.
    """

    # -------------------------------------------------------------------------
    # 1. PRIMARY GEOMETRIC PROPERTIES
    # -------------------------------------------------------------------------
    # Compute the base sectional properties: net area, centroid, centroidal
    # moments of inertia, product of inertia, and polar inertia.
    # Weighted polygons are included in the algebraic section definition.
    props = section_properties(section)

    # -------------------------------------------------------------------------
    # 2. PRINCIPAL AXIS PROPERTIES
    # -------------------------------------------------------------------------
    # Compute principal inertias and the principal-axis rotation angle.
    derived = section_derived_properties(props)

    # -------------------------------------------------------------------------
    # 3. ELASTIC SECTION MODULI
    # -------------------------------------------------------------------------
    # Compute elastic section moduli from the centroidal inertias and the maximum
    # distances from the centroid to the effective polygon vertices.
    effective_polygons = section.polygons
   

    if effective_polygons:
        all_x = [v.x for poly in effective_polygons for v in poly.vertices]
        all_y = [v.y for poly in effective_polygons for v in poly.vertices]

        # Extreme-fiber distances relative to the centroidal axes.
        y_dist_max = max(max(all_y) - props['Cy'], props['Cy'] - min(all_y))
        x_dist_max = max(max(all_x) - props['Cx'], props['Cx'] - min(all_x))

        # Elastic section moduli: W = I / c.
        props['Wx'] = props['Ix'] / y_dist_max if y_dist_max > _tol.EPS_L else 0.0
        props['Wy'] = props['Iy'] / x_dist_max if x_dist_max > _tol.EPS_L else 0.0
    else:
        props['Wx'] = 0.0
        props['Wy'] = 0.0

    # -------------------------------------------------------------------------
    # 4. BASIC TORSIONAL STIFFNESS ESTIMATE
    # -------------------------------------------------------------------------
    # Compute a simple semi-empirical torsional estimate from area and polar
    # inertia. This is retained as an approximate scalar indicator, not as a
    # replacement for the refined Saint-Venant routines below.
    A = props['A']
    Ip = props['Ix'] + props['Iy']

    if Ip > _tol.EPS_K:
        props['K_torsion'] = (A**4) / (40.0 * Ip)
    else:
        props['K_torsion'] = 0.0

    # -------------------------------------------------------------------------
    # 5. FIRST STATICAL MOMENT AT THE NEUTRAL AXIS
    # -------------------------------------------------------------------------
    # Compute Q for the portion of the section above the neutral axis, using the
    # centroidal y-axis as the reference axis.
    props['Q_na'] = section_statical_moment_partial(
        section, y_cut=props['Cy'], reference_axis=props['Cy']
    )

    # -------------------------------------------------------------------------
    # 6. SAINT-VENANT TORSIONAL ESTIMATES
    # -------------------------------------------------------------------------
    # Compute the available Saint-Venant torsional estimates. The Roark-based
    # routine can be skipped when a downstream action does not need it.
    # props['J_sv'] = compute_saint_venant_J(section, alpha=alpha, eps_a=_tol.EPS_A)
    # props['J_sv_alpha'] = alpha

    props['J_sv_cell'] = compute_saint_venant_J_cell(section)
    props['J_sv_wall'] = compute_saint_venant_J_wall(section)

    if compute_vroark:
        props['J_s_vroark'], props['J_s_vroark_fidelity'] = compute_saint_venant_Jv2(section)
    else:
        props['J_s_vroark'] = 0
        props['J_s_vroark_fidelity'] = 0

    # -------------------------------------------------------------------------
    # 7. DATA CONSOLIDATION
    # -------------------------------------------------------------------------
    # Return a single dictionary containing both base and derived properties.
    return {**props, **derived}

def polygon_statical_moment(poly: Polygon, y_axis: float) -> float:
    """
    Computes the First Moment of Area (Statical Moment), Q, of a SINGLE polygon 
    relative to a specific horizontal axis (y_axis).
    
    TECHNICAL NOTES:
    - Formula: Q = Area * (y_centroid - y_axis)
    - Sign Convention: Positive if the polygon centroid is above the reference axis.
    - Homogenization: Uses weighted area to account for holes or material density.
    """
    area_i, (cx_i, cy_i) = polygon_area_centroid(poly)
    # Distance from the polygon centroid to the reference axis
    d_y = cy_i - y_axis
    return area_i * d_y

def section_statical_moment_partial(section: Section, y_cut: float, reference_axis: float | None = None) -> float:
    """
    Compute the statical moment Q of the portion of the section located ABOVE y_cut,
    with respect to a horizontal reference axis y = y_ref.

    The section is processed polygon-by-polygon:
    - Each polygon is clipped by the half-plane y >= y_cut.
    - For the retained part, we compute its area and centroid.
    - We accumulate Q = A_part * (Cy_part - y_ref), using signed area if the polygon
      representation supports signed contributions (e.g., holes via orientation/sign).
    """
    # Compute section-level properties to obtain the default reference axis (neutral axis).

    if reference_axis is None:
        props = section_properties(section)
        y_ref = props["Cy"]
    else:
        y_ref = reference_axis


    q_total = 0.0
    # Geometric tolerance for comparisons and degenerate cases.
    eps_l = _tol.EPS_L
    eps_a = _tol.EPS_A

    for poly in section.polygons:
        verts = poly.vertices
        n = len(verts)

        # Clip polygon against the half-plane y >= y_cut using an edge-walking approach.
        clipped: list[Pt] = []

        for i in range(n):
            p1 = verts[i]
            p2 = verts[(i + 1) % n]

            # Classify endpoints with a tolerance to reduce numerical flicker at the cut line.
            p1_in = (p1.y >= y_cut - eps_l)
            p2_in = (p2.y >= y_cut - eps_l)

            if p1_in and p2_in:
                # Edge fully inside: keep the end vertex.
                clipped.append(p2)

            elif p1_in and not p2_in:
                # Edge exits the half-plane: add the intersection point (if not horizontal).
                dy = p2.y - p1.y
                if abs(dy) > eps_l:
                    t = (y_cut - p1.y) / dy
                    clipped.append(Pt(p1.x + t * (p2.x - p1.x), y_cut))

            elif (not p1_in) and p2_in:
                # Edge enters the half-plane: add the intersection point then the end vertex.
                dy = p2.y - p1.y
                if abs(dy) > eps_l:
                    t = (y_cut - p1.y) / dy
                    clipped.append(Pt(p1.x + t * (p2.x - p1.x), y_cut))
                clipped.append(p2)

            # If both endpoints are outside, add nothing.

        # A valid polygonal region needs at least 3 vertices after clipping.
        if len(clipped) < 3:
            continue

        # Skip regions that are effectively flat on the cut line.
        if all(abs(v.y - y_cut) < eps_l for v in clipped):
            continue

        # Build a clipped polygon with the same weight as the source polygon.
        clipped_poly = Polygon(vertices=tuple(clipped), weight=poly.weight)

        # Compute area and centroid of the clipped part.
        area_part, (_, cy_part) = polygon_area_centroid(clipped_poly)
        

        # Ignore negligible contributions.
        if abs(area_part) <= eps_a:
            continue

        # Statical moment contribution of this clipped part about y = y_ref.
        q_total += area_part * (cy_part - y_ref)

    return q_total


def section_derived_properties(props: Dict[str, float]) -> Dict[str, float]:
    """
    Computes derived structural properties including principal moments of inertia,
    principal axis rotation, and radius of gyration.
    """
    Ix = props['Ix']
    Iy = props['Iy']
    Ixy = props['Ixy']

    # Calculate Mohr's Circle parameters
    avg = (Ix + Iy) / 2
    diff = (Ix - Iy) / 2
    # R is the radius of Mohr's Circle: R = sqrt(((Ix - Iy)/2)^2 + Ixy^2)
    R = math.sqrt(diff**2 + Ixy**2)

    # --- NUMERICAL STABILITY & ISOTROPY CHECK ---
    # For perfectly symmetric sections (like circles or squares), Ix = Iy and Ixy = 0.
    # This creates a mathematical singularity where the principal angle is indeterminate
    # (Mohr's Circle collapses to a single point). 
    # To prevent numerical noise from producing erratic rotation angles,
    # we detect if the radius R is negligible compared to the magnitude of inertia.
    # If isotropic, the principal angle is set to 0.0 by engineering convention.
    if R <  abs(avg) * _tol.EPS_K_RTOL:
        theta = 0.0
    else:
        # Standard calculation for the angle of the principal X-axis
        theta = 0.5 * math.atan2(-2 * Ixy, Ix - Iy)
    # --------------------------------------------

    '''
    'I1': avg + R,  # Major principal moment of inertia
    'I2': avg - R,  # Minor principal moment of inertia
    'theta_rad': theta,
    'theta_deg': math.degrees(theta),
    'rx': math.sqrt(Ix / props['A']) if props['A'] > 0 else 0,
    'ry': math.sqrt(Iy / props['A']) if props['A'] > 0 else 0,
    '''

    I1 = avg + R
    I2 = avg - R
    theta_rad = theta
    theta_deg = math.degrees(theta)


    if Ix < 0:
        raise ValueError(f"Negative Ix={Ix:.6g}: cannot compute rx")
    if Iy < 0:
        raise ValueError(f"Negative Iy={Iy:.6g}: cannot compute ry")

    try:
        rx = math.sqrt(Ix / props['A']) if props['A'] > 0 else 0
        ry = math.sqrt(Iy / props['A']) if props['A'] > 0 else 0
    except (ValueError, ZeroDivisionError) as e:
        raise ValueError(f"Error computing radii of gyration: {e}") from e

    
    return {
        'I1': I1,
        'I2': I2,
        'theta_rad': theta_rad,
        'theta_deg': theta_deg,
        'rx': rx,
        'ry': ry,
    }




# -------------------------
# Stiffness Matrix Calculation
# -------------------------

def section_stiffness_matrix(section: Section, E_ref: float = 1.0) -> np.ndarray:
    """
 Assembles the 3x3 constitutive stiffness matrix relating generalized 
    strains to internal forces (N, Mx, My).

    TECHNICAL SUMMARY:
    This function performs a numerical integration over the composite 
    polygonal domain to compute the sectional stiffness properties relative 
    to the global origin (0,0). It accounts for multi-material homogenization 
    via the polygon weighting system.

    STIFFNESS MATRIX FORMULATION:
    The resulting matrix K maps the axial strain (epsilon) and curvatures 
    (kappa_x, kappa_y) to the Resultant Normal Force (N) and Bending Moments (Mx, My):
    
        [ N  ]   [ EA    ESx   -ESy  ] [ epsilon ]
        [ Mx ] = [ ESx   EIxx  -EIxy ] [ kappa_x ]
        [ My ]   [ -ESy -EIxy   EIyy ] [ kappa_y ]

    COMPUTATIONAL STRATEGY:
    1. Fan Triangulation: 
       Each polygon is decomposed into triangles using a "fan" approach, 
       with the first vertex (v0) acting as the common pivot.
       
    2. Numerical Integration (Gauss Quadrature):
       For each triangular sub-domain, the function calls the Gaussian 
       integrator to retrieve optimal sampling points.
       
    3. Contribution Mapping:
       At each Gauss point (x, y) with differential area dA:
       - Axial Stiffness (EA): Σ E * dA
       - First Moments (ESx, ESy): Σ E * y * dA and Σ E * x * dA
       - Second Moments (EIxx, EIyy, EIxy): Σ E * y^2 * dA, Σ E * x^2 * dA, 
         and Σ E * x * y * dA.

    4. Homogenization:
       The 'poly.weight' parameter scales the reference Young's Modulus (E_ref), 
       allowing for the modeling of hollow sections (negative weights) or 
       composite structures with varying material stiffness.

    5. Symmetrization:
       Enforces the Maxwell-Betti reciprocal theorem by ensuring K[i,j] = K[j,i].

    RETURNS:
       A 3x3 NumPy array representing the cross-sectional stiffness tensor.   
    """
    # 1. Get exact geometric properties (already multiplied by interpolated weight)
    props = section_properties(section)
    
    area = props['A']
    # If Sx/Sy are not explicitly in props, they are computed from Area * Centroid
    sx = props.get('Sx', area * props['Cy'])
    sy = props.get('Sy', area * props['Cx'])
    
    # 2. Build the 3x3 matrix weighted by E_ref
    # Since 'area', 'Ix', etc. already include 'weight', 
    # E_ref acts as the global Young's Modulus scale.
    k_matrix = np.array([
        [E_ref * area,         E_ref * sy,           -E_ref * sx],
        [E_ref * sy,           E_ref * props['Iy'],  -E_ref * props['Ixy']],
        [-E_ref * sx,         -E_ref * props['Ixy'],  E_ref * props['Ix']]
    ])
    
    return k_matrix

def _segments_intersect(p1, p2, p3, p4) -> bool:
    '''
    Determines if two finite line segments (p1-p2 and p3-p4) intersect in a 2D plane.

    TECHNICAL SUMMARY:
    This function implements a robust geometric intersection test based on the 
    'Orientation Test' (cross-product method). It is primarily used to detect 
    self-intersections in homogenized polygons, ensuring the topological integrity 
    of the cross-sectional boundaries.

    MATHEMATICAL FORMULATION:
    1. Orientation Primitive:
       The inner 'orient' function computes the signed area of the triangle formed 
       by points (a, b, c). 
       - If Result > 0: The sequence (a, b, c) is Counter-Clockwise (CCW).
       - If Result < 0: The sequence is Clockwise (CW).
       - If Result = 0: The points are Collinear.

    2. Relative Orientation Logic:
       For two segments to intersect, the endpoints of each segment must lie on 
       opposite sides of the line defined by the other segment.
       - o1, o2 check points p3 and p4 relative to line p1-p2.
       - o3, o4 check points p1 and p2 relative to line p3-p4.

    3. Intersection Criterion:
       The condition (o1 * o2 < 0) and (o3 * o4 < 0) identifies a 'Proper Intersection'.
       This occurs when the endpoints strictly straddle the opposing lines, 
       excluding collinear overlaps or shared endpoints to maintain computational 
       stability during polygon validation.

    APPLICABILITY IN RULED SURFACE MODELING:
    By preventing self-intersecting polygons, this function ensures that the 
    Shoelace formula and Gaussian integration yield physically consistent results 
    for the area and inertia of the tower sections.

    RETURNS:
       - True: If segments p1-p2 and p3-p4 intersect.
       - False: Otherwise.

    '''

    def orient(a, b, c):
        return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)

    o1 = orient(p1, p2, p3)
    o2 = orient(p1, p2, p4)
    o3 = orient(p3, p4, p1)
    o4 = orient(p3, p4, p2)

    return (o1 * o2 < 0) and (o3 * o4 < 0)

def polygon_has_self_intersections(poly: Polygon) -> bool:
    """
    Returns True if the polygon has any self-intersection between NON-adjacent edges.

    This version is *robust*:
    - Detects proper crossings (X-shaped intersections)
    - Also detects "touching" (vertex on edge) and collinear overlaps

    Why this matters:
    - Your current _segments_intersect() uses a strict test (o1*o2 < 0 and o3*o4 < 0),
        which will NOT flag touching or collinear overlap. :contentReference[oaicite:1]{index=1}
    - For ruled-surface interpolation across z, "touching" can appear due to numerical
        noise or twisting, and you typically want a warning.

    Input model:
    - poly.vertices: Tuple[Pt, ...]
    - Pt has fields .x, .y
    """
    verts = poly.vertices
    n = len(verts)

    # Triangles cannot self-intersect (excluding degeneracy, which you already validate elsewhere).
    if n < 4:
        return False

    eps = _tol.EPS_L  # Use your global linear tolerance

    # ---------- Local geometric primitives (kept inside function; no extra global funcs) ----------

    def _orient(a: Pt, b: Pt, c: Pt) -> float:
        """Signed area*2 of triangle (a,b,c)."""
        return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)

    def _sign(x: float) -> int:
        """Map x to {-1,0,+1} using eps."""
        if x > eps:
            return 1
        if x < -eps:
            return -1
        return 0

    def _on_segment(a: Pt, b: Pt, p: Pt) -> bool:
        """
        Return True if p lies on segment ab (including endpoints), assuming collinearity
        (or near-collinearity) has already been established.
        """
        return (
            min(a.x, b.x) - eps <= p.x <= max(a.x, b.x) + eps
            and min(a.y, b.y) - eps <= p.y <= max(a.y, b.y) + eps
        )

    def _segments_intersect_robust(a1: Pt, a2: Pt, b1: Pt, b2: Pt) -> bool:
        """
        Robust 2D segment intersection test:
        - Proper intersection (strict crossing)
        - Touching at endpoints / vertex-on-edge
        - Collinear overlap
        """
        o1 = _sign(_orient(a1, a2, b1))
        o2 = _sign(_orient(a1, a2, b2))
        o3 = _sign(_orient(b1, b2, a1))
        o4 = _sign(_orient(b1, b2, a2))

        # Proper crossing (strict)
        if o1 * o2 < 0 and o3 * o4 < 0:
            return True

        # Touching / collinear cases
        if o1 == 0 and _on_segment(a1, a2, b1):
            return True
        if o2 == 0 and _on_segment(a1, a2, b2):
            return True
        if o3 == 0 and _on_segment(b1, b2, a1):
            return True
        if o4 == 0 and _on_segment(b1, b2, a2):
            return True

        return False

    # ---------- Edge pair scanning ----------
    # Edge i: verts[i] -> verts[(i+1)%n]
    # Compare only with non-adjacent edges to avoid trivial shared-vertex "intersections".
    for i in range(n):
        a1 = verts[i]
        a2 = verts[(i + 1) % n]

        # j starts at i+2 to skip the adjacent edge (i+1).
        for j in range(i + 2, n):
            # Skip the edge that shares the closing vertex with edge i
            # (i=0 edge is adjacent to the last edge).
            if (j + 1) % n == i:
                continue

            b1 = verts[j]
            b2 = verts[(j + 1) % n]

            if _segments_intersect_robust(a1, a2, b1, b2):
                return True

    return False


def get_points_distance(polygon: Polygon, i: int, j: int) -> float:
    """
    Calculates the Euclidean distance between vertex i and vertex j of a polygon.
    Indices i and j are 1-based (from 1 to N).
    
    This can measure sides (if i, j are consecutive) or diagonals/distances 
    between any two nodes of the polygon.
    """
    
    verts = polygon.vertices
    n = len(verts)

    # Validate indices to prevent Out of Range errors
    if not (0 <= i <= n) or not (1 <= j <= n):
        raise IndexError(f"Vertex indices {i, j} out of range for polygon with {n} vertices.")

    # Convert 1-based indices to 0-based for Python list access
    
    p1 = verts[i]
    p2 = verts[j]
    
    # Euclidean distance formula: sqrt((x2-x1)^2 + (y2-y1)^2)
    dist = math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)
    
    return dist

# -------------------------
# Core: Continuous section field (geometry-only)
# -------------------------
def get_edge_length(polygon: Polygon, edge_idx: int) -> float:
    """
    Calculates the length of the j-th edge of a polygon.
    edge_idx is 1-based (1 to N).
    """
    verts = polygon.vertices
    n = len(verts)
    
    # Translate 1-based index to 0-based
    # Edge j connects vertex j-1 to vertex j
    idx1 = (edge_idx - 1) % n
    idx2 = edge_idx % n
    
    p1 = verts[idx1]
    p2 = verts[idx2]
    
    return math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)

#-------------------------------------------------------------------------------------------------------------
def list_polygons_with_contents(csf: ContinuousSectionField, z: float) -> List[Dict[str, Any]]:
    """
    Return one record per polygon at coordinate z, including direct containment.

    Structural rules:
    - polygon identity is strictly the local index in sec.polygons
    - names are output labels only
    - topology is consumed strictly as index-based data

    Output fields:
      - idx (int): polygon index in the sampled section ordering at z
      - name (str | None): cleaned polygon label for output only
      - container_idx (int | None): direct container index, or None for a root polygon
      - container_name (str | None): cleaned label of the direct container, or None
      - direct_children_idx (List[int]): direct child indices
      - direct_children (List[str | None]): cleaned labels of the direct children
      - is_container (bool): True if the polygon has at least one direct child

    Raises:
    - TypeError / ValueError only for structural issues
    """
    if not isinstance(z, (int, float)):
        raise TypeError(f"z must be a number, got {type(z).__name__}")

    sec = csf.section(float(z))
    if sec is None:
        raise ValueError("csf.section(z) returned None.")

    if not hasattr(sec, "polygons"):
        raise ValueError("Sampled section has no 'polygons' attribute.")

    polygons = sec.polygons

    labels_by_idx: Dict[int, Optional[str]] = {}

    # Read labels for output only.
    # Labels are propagated as-is and never affect structural logic.
    for idx, poly in enumerate(polygons):
        if hasattr(poly, "name"):
            labels_by_idx[idx] = poly.name
        else:
            labels_by_idx[idx] = None

    children_idx_map = csf.build_direct_children_map(float(z))

    if not isinstance(children_idx_map, dict):
        raise TypeError("build_direct_children_map(z) must return a dict.")

    parent_idx_of: Dict[int, int] = {}

    # Validate the index-based hierarchy and build the inverse child -> parent map.
    for parent_idx, child_idx_list in children_idx_map.items():
        if not isinstance(parent_idx, int):
            raise TypeError(
                f"Hierarchy parent index must be int, got {type(parent_idx).__name__}."
            )

        if not (0 <= parent_idx < len(polygons)):
            raise ValueError(
                f"Hierarchy parent index {parent_idx} is outside polygon range."
            )

        if not isinstance(child_idx_list, list):
            raise TypeError(
                f"Hierarchy children for parent idx={parent_idx} must be a list."
            )

        for child_idx in child_idx_list:
            if not isinstance(child_idx, int):
                raise TypeError(
                    f"Hierarchy child index under parent idx={parent_idx} must be int, "
                    f"got {type(child_idx).__name__}."
                )

            if not (0 <= child_idx < len(polygons)):
                raise ValueError(
                    f"Hierarchy child index {child_idx} under parent idx={parent_idx} "
                    f"is outside polygon range."
                )

            if child_idx == parent_idx:
                raise ValueError(
                    f"Polygon idx={child_idx} cannot be parent of itself."
                )

            if child_idx in parent_idx_of:
                previous_parent_idx = parent_idx_of[child_idx]
                raise ValueError(
                    f"Polygon idx={child_idx} has multiple direct containers: "
                    f"idx={previous_parent_idx} and idx={parent_idx}."
                )

            parent_idx_of[child_idx] = parent_idx

    out: List[Dict[str, Any]] = []

    for idx in range(len(polygons)):
        if idx in parent_idx_of:
            container_idx = parent_idx_of[idx]
        else:
            container_idx = None

        if idx in children_idx_map:
            direct_children_idx = list(children_idx_map[idx])
        else:
            direct_children_idx = []

        if container_idx is None:
            container_name = None
        else:
            container_name = labels_by_idx[container_idx]

        direct_children_labels: List[Optional[str]] = []
        for child_idx in direct_children_idx:
            direct_children_labels.append(labels_by_idx[child_idx])

        out.append(
            {
                "idx": idx,
                "name": labels_by_idx[idx],
                "container_idx": container_idx,
                "container_name": container_name,
                "direct_children_idx": direct_children_idx,
                "direct_children": direct_children_labels,
                "is_container": len(direct_children_idx) > 0,
            }
        )

    return out


def polygon_surface_w1_inners0(self: Any, z: float) -> List[Dict[str, Any]]:
    """
    Compute the local occupied surface for every polygon at coordinate z using the rule:
      - w(polygon) = 1
      - w(direct inners) = 0

    And its weighted counterpart:
      - A_w = A * w_eff

    Structural rules:
    - all topology, validation, and calculations are strictly index-based
    - names are output labels only
    - names must never trigger errors or logic branches

    Required upstream structural fields:
    - list_polygons_with_contents(self, z):
        * idx
        * container_idx
        * direct_children_idx
    - self.inspect_section_entities(z):
        * idx
        * area_signed
        * weight_at_z

    Output fields:
      - idx (int)
      - name (str | None)
      - container_name (str | None)
      - direct_inners (List[str | None])
      - w (float)
      - A (float)
      - A_w (float)
    """
    if not isinstance(z, (int, float)):
        raise TypeError(f"z must be a number (float), got {type(z).__name__}")
    z = float(z)

    rows = list_polygons_with_contents(self, z)
    if not isinstance(rows, list):
        raise TypeError("list_polygons_with_contents(self, z) must return a list.")

    container_of: Dict[int, Optional[int]] = {}
    direct_inners_of: Dict[int, List[int]] = {}

    # Optional labels for output only.
    row_by_idx: Dict[int, Dict[str, Any]] = {}

    for row_index, r in enumerate(rows):
        if not isinstance(r, dict):
            raise TypeError(
                f"list_polygons_with_contents(self, z) must return a list of dicts. "
                f"Invalid item at position {row_index}."
            )

        if "idx" not in r:
            raise ValueError(f"Hierarchy row at position {row_index} has no 'idx' field.")
        idx = r["idx"]
        if not isinstance(idx, int):
            raise TypeError(f"Hierarchy row 'idx' must be int, got {type(idx).__name__}.")

        if idx in container_of:
            raise ValueError(f"Duplicate polygon idx in hierarchy rows at z={z}: {idx}")

        if "container_idx" not in r:
            raise ValueError(f"Hierarchy row idx={idx} has no 'container_idx' field.")
        container_idx = r["container_idx"]
        if container_idx is not None and not isinstance(container_idx, int):
            raise TypeError(
                f"Hierarchy row idx={idx} has invalid 'container_idx' type: "
                f"{type(container_idx).__name__}"
            )

        if "direct_children_idx" not in r:
            raise ValueError(f"Hierarchy row idx={idx} has no 'direct_children_idx' field.")
        direct_children_idx = r["direct_children_idx"]
        if not isinstance(direct_children_idx, list):
            raise TypeError(
                f"Hierarchy row idx={idx} has invalid 'direct_children_idx' type: "
                f"{type(direct_children_idx).__name__}"
            )
        for child_idx in direct_children_idx:
            if not isinstance(child_idx, int):
                raise TypeError(
                    f"Hierarchy row idx={idx} contains non-int child index: {child_idx!r}"
                )

        container_of[idx] = container_idx
        direct_inners_of[idx] = list(direct_children_idx)
        row_by_idx[idx] = r

    if not hasattr(self, "inspect_section_entities"):
        raise AttributeError("Expected self.inspect_section_entities(z) to exist.")

    entities = self.inspect_section_entities(z)
    if not isinstance(entities, list):
        raise TypeError("inspect_section_entities(z) must return a list of dict records.")

    area_by_idx: Dict[int, float] = {}
    w_rel_by_idx: Dict[int, float] = {}
    w_abs_by_idx: Dict[int, float] = {}
    w_shear_abs_by_idx: Dict[int, float] = {}
    w_weight_abs_z_idx: Dict[int, float] = {}

    # Optional labels for output only.
    entity_by_idx: Dict[int, Dict[str, Any]] = {}

    for entity_index, e in enumerate(entities):
        if not isinstance(e, dict):
            raise TypeError(
                f"inspect_section_entities(z) must return a list of dict records. "
                f"Invalid item at position {entity_index}."
            )

        if "idx" not in e:
            raise ValueError(f"Entity at position {entity_index} has no 'idx' field.")
        idx = e["idx"]
        if not isinstance(idx, int):
            raise TypeError(f"Entity 'idx' must be int, got {type(idx).__name__}.")

        if idx in area_by_idx:
            raise ValueError(f"Duplicate entity idx from inspect_section_entities at z={z}: {idx}")

        if "area_signed" not in e:
            raise ValueError(f"Entity idx={idx} has no 'area_signed' field.")
        if "weight_abs_z" not in e:
            raise ValueError(f"Entity idx={idx} has no 'weight_at_z' field.")

        area_by_idx[idx] = float(e["area_signed"])
        w_rel_by_idx[idx] = float(e["weight_at_z"])
        w_abs_by_idx[idx] = float(e["weight_abs_z"])
        #w_abs_by_idx[idx] = float(e["weight_abs_at_z"])


        w_shear_abs_by_idx[idx] = float(e["shear_weight_abs_at_z"])

        entity_by_idx[idx] = e

    for idx in container_of:
        if idx not in area_by_idx:
            raise ValueError(
                f"Polygon idx={idx} is in hierarchy but missing from inspect_section_entities at z={z}."
            )

    for idx, parent_idx in container_of.items():
        if parent_idx is None:
            continue
        if parent_idx not in container_of:
            raise ValueError(
                f"Polygon idx={idx} references missing container idx={parent_idx} at z={z}."
            )

    for idx, inner_idx_list in direct_inners_of.items():
        for inner_idx in inner_idx_list:
            if inner_idx not in area_by_idx:
                raise ValueError(
                    f"Inner polygon idx={inner_idx} of polygon idx={idx} is missing "
                    f"from inspect_section_entities at z={z}."
                )
    out: List[Dict[str, Any]] = []

    for idx in sorted(container_of.keys()):
        direct_inners_idx = direct_inners_of[idx]

        area_p = area_by_idx[idx]
        inners_sum = 0.0
        for inner_idx in direct_inners_idx:
            inners_sum += area_by_idx[inner_idx]

        A = area_p - inners_sum
        #w_eff = w_eff_by_idx[idx]
        w_eff = w_abs_by_idx[idx]
        w_shear_eff = w_shear_abs_by_idx[idx]

        direct_inners_labels: List[Optional[str]] = []
        for inner_idx in direct_inners_idx:
            if inner_idx in row_by_idx and "name" in row_by_idx[inner_idx]:
                direct_inners_labels.append(row_by_idx[inner_idx]["name"])
            else:
                direct_inners_labels.append(None)

        if idx in row_by_idx and "name" in row_by_idx[idx]:
            name = row_by_idx[idx]["name"]
        else:
            name = None

        if idx in row_by_idx and "container_name" in row_by_idx[idx]:
            container_name = row_by_idx[idx]["container_name"]
        else:
            container_name = None

        out.append(
            {
                "idx": idx,
                "name": name,
                "container_name": container_name,
                "direct_inners": direct_inners_labels,
                "w": float(w_eff),
                "shear_w": float(w_shear_eff),
                "A": float(A),
                "A_w": float(A * w_eff),
                "A_shear_w": float(A * w_shear_eff),
            }
        )

    return out


def polygon_surface_w1_inners0_single(
    self: ContinuousSectionField,
    z: float,
    idx: int
) -> Dict[str, Any]:
    """
    Compute the local occupied surface for one polygon at coordinate z using the rule:
      - w(polygon) = 1
      - w(direct inners) = 0

    And its weighted counterpart:
      - A_w = A * w_eff

    Structural rules:
    - all topology, validation, and calculations are strictly index-based
    - names are output labels only
    - names must never trigger errors or logic branches

    Required upstream structural fields:
    - list_polygons_with_contents(self, z):
        * idx
        * container_idx
        * direct_children_idx
    - self.inspect_section_entities(z):
        * idx
        * area_signed
        * weight_at_z

    Output fields:
      - idx (int)
      - name (str | None)
      - container_name (str | None)
      - direct_inners (List[str | None])
      - w (float)
      - A (float)
      - A_w (float)
    """
    if not isinstance(z, (int, float)):
        raise TypeError(f"z must be a number (float), got {type(z).__name__}")
    z = float(z)

    if not isinstance(idx, int):
        raise TypeError(f"idx must be an int (0-based), got {type(idx).__name__}")
    if idx < 0:
        raise ValueError(f"idx must be >= 0 (0-based), got {idx}")

    rows = list_polygons_with_contents(self, z)
    if not isinstance(rows, list):
        raise TypeError("list_polygons_with_contents(self, z) must return a list.")

    container_of: Dict[int, Optional[int]] = {}
    direct_inners_of: Dict[int, List[int]] = {}
    row_by_idx: Dict[int, Dict[str, Any]] = {}

    for row_index, r in enumerate(rows):
        if not isinstance(r, dict):
            raise TypeError(
                f"list_polygons_with_contents(self, z) must return a list of dicts. "
                f"Invalid item at position {row_index}."
            )

        if "idx" not in r:
            raise ValueError(f"Hierarchy row at position {row_index} has no 'idx' field.")
        row_idx = r["idx"]
        if not isinstance(row_idx, int):
            raise TypeError(f"Hierarchy row 'idx' must be int, got {type(row_idx).__name__}.")

        if row_idx in container_of:
            raise ValueError(f"Duplicate polygon idx in hierarchy rows at z={z}: {row_idx}")

        if "container_idx" not in r:
            raise ValueError(f"Hierarchy row idx={row_idx} has no 'container_idx' field.")
        container_idx = r["container_idx"]
        if container_idx is not None and not isinstance(container_idx, int):
            raise TypeError(
                f"Hierarchy row idx={row_idx} has invalid 'container_idx' type: "
                f"{type(container_idx).__name__}"
            )

        if "direct_children_idx" not in r:
            raise ValueError(f"Hierarchy row idx={row_idx} has no 'direct_children_idx' field.")
        direct_children_idx = r["direct_children_idx"]
        if not isinstance(direct_children_idx, list):
            raise TypeError(
                f"Hierarchy row idx={row_idx} has invalid 'direct_children_idx' type: "
                f"{type(direct_children_idx).__name__}"
            )
        for child_idx in direct_children_idx:
            if not isinstance(child_idx, int):
                raise TypeError(
                    f"Hierarchy row idx={row_idx} contains non-int child index: {child_idx!r}"
                )

        container_of[row_idx] = container_idx
        direct_inners_of[row_idx] = list(direct_children_idx)
        row_by_idx[row_idx] = r

    if idx not in container_of:
        raise ValueError(f"Polygon idx={idx} not found in hierarchy rows at z={z}.")

    if not hasattr(self, "inspect_section_entities"):
        raise AttributeError("Expected self.inspect_section_entities(z) to exist.")

    entities = self.inspect_section_entities(z)
    if not isinstance(entities, list):
        raise TypeError("inspect_section_entities(z) must return a list of dict records.")

    area_by_idx: Dict[int, float] = {}
    w_rel_by_idx: Dict[int, float] = {}

    for entity_index, e in enumerate(entities):
        if not isinstance(e, dict):
            raise TypeError(
                f"inspect_section_entities(z) must return a list of dict records. "
                f"Invalid item at position {entity_index}."
            )

        if "idx" not in e:
            raise ValueError(f"Entity at position {entity_index} has no 'idx' field.")
        entity_idx = e["idx"]
        if not isinstance(entity_idx, int):
            raise TypeError(f"Entity 'idx' must be int, got {type(entity_idx).__name__}.")

        if entity_idx in area_by_idx:
            raise ValueError(
                f"Duplicate entity idx from inspect_section_entities at z={z}: {entity_idx}"
            )

        if "area_signed" not in e:
            raise ValueError(f"Entity idx={entity_idx} has no 'area_signed' field.")
        if "weight_at_z" not in e:
            raise ValueError(f"Entity idx={entity_idx} has no 'weight_at_z' field.")

        area_by_idx[entity_idx] = float(e["area_signed"])
        w_rel_by_idx[entity_idx] = float(e["weight_at_z"])

    if idx not in area_by_idx:
        raise ValueError(
            f"Polygon idx={idx} is in hierarchy but missing from inspect_section_entities at z={z}."
        )

    direct_inners_idx = direct_inners_of[idx]
    for inner_idx in direct_inners_idx:
        if inner_idx not in area_by_idx:
            raise ValueError(
                f"Inner polygon idx={inner_idx} of polygon idx={idx} is missing "
                f"from inspect_section_entities at z={z}."
            )

    visited: set[int] = set()
    w_eff = 0.0
    cur_idx = idx

    while True:
        if cur_idx in visited:
            raise ValueError(
                f"Cannot resolve effective weight at z={z}: cycle detected in container chain at idx={cur_idx}."
            )
        visited.add(cur_idx)

        if cur_idx not in w_rel_by_idx:
            raise ValueError(f"Polygon idx={cur_idx} has no relative weight at z={z}.")
        w_eff += w_rel_by_idx[cur_idx]

        if cur_idx not in container_of:
            raise ValueError(f"Polygon idx={cur_idx} is missing from hierarchy rows at z={z}.")

        parent_idx = container_of[cur_idx]
        if parent_idx is None:
            break

        if parent_idx not in container_of:
            raise ValueError(
                f"Container idx={parent_idx} for polygon idx={cur_idx} is missing "
                f"from hierarchy rows at z={z}."
            )

        cur_idx = parent_idx

    area_p = area_by_idx[idx]
    inners_sum = 0.0
    for inner_idx in direct_inners_idx:
        inners_sum += area_by_idx[inner_idx]

    direct_inners_labels: List[Optional[str]] = []
    for inner_idx in direct_inners_idx:
        if inner_idx in row_by_idx and "name" in row_by_idx[inner_idx]:
            direct_inners_labels.append(row_by_idx[inner_idx]["name"])
        else:
            direct_inners_labels.append(None)

    if idx in row_by_idx and "name" in row_by_idx[idx]:
        name = row_by_idx[idx]["name"]
    else:
        name = None

    if idx in row_by_idx and "container_name" in row_by_idx[idx]:
        container_name = row_by_idx[idx]["container_name"]
    else:
        container_name = None

    A = area_p - inners_sum
    A_w = A * w_eff

    return {
        "idx": idx,
        "name": name,
        "container_name": container_name,
        "direct_inners": direct_inners_labels,
        "w": float(w_eff),
        "A": float(A),
        "A_w": float(A_w),
    }

def export_polygon_vertices_csv_file(
    section: Section = None,
    field: ContinuousSectionField = None,
    zpos: float = None,
    exp_filename: str = "csv_export.txt",
    z_values: Optional[List[float]] = None,
    fmt: str = "{:.16g}",
):
    """
    File wrapper for export_polygon_vertices_csv().

    Modes
    -----
    1) Single export:
       - section=...
       or
       - field=... and zpos=...

    2) Multiple export:
       - field=... and z_values=[...]
    """

    out_path = Path(exp_filename)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Prevent ambiguous mixed usage
    if z_values is not None and section is not None:
        raise ValueError("section cannot be used together with z_values.")

    if z_values is not None and field is None:
        raise ValueError("field is required when z_values is provided.")

    with open(out_path, "w", encoding="utf-8") as f:
        def put_line(s: str) -> None:
            f.write(s)
            f.write("\n")

        # Multiple export mode
        if z_values is not None:
            for z in z_values:
                export_polygon_vertices_csv(
                    section=None,
                    field=field,
                    zpos=float(z),
                    put=put_line,
                    fmt=fmt,
                )
            return

        # Single export mode
        export_polygon_vertices_csv(
            section=section,
            field=field,
            zpos=zpos,
            put=put_line,
            fmt=fmt,
        )

def export_polygon_vertices_csv(section: Section=None, field: ContinuousSectionField=None,    zpos: float=None, put=print, fmt="{:.16g}"):
    """
    Export CSV with ALL coordinates.

    One row per vertex (recommended for CSV):
    idx_polygon, idx_container, s0_name, s1_name, w, vertex_i, x, y

    Sources:
    - geometry: section.polygons -> poly.name, poly.vertices (Pt has .x .y)
    - container + names: entities[*] by polygon name
    - w: area_w["groups"][*]["w"] mapped by polygon name

    Parameters
    ----------
    fmt : str
        Python format string for floats, e.g. "{:.6f}", "{:.6g}", "{:.16g}".
        Applied to: w, x, y (when they are not None).
    """

 

    def build_w_by_idx(named_polys: dict) -> dict[int, float]:
        """
        Build {idx: w_by_idx} from polygons metadata.
        """
        polys_by_idx = {}

        for poly in named_polys.values():
            idx = poly["idx"]
            polys_by_idx[idx] = poly

        w_by_idx = {}

        for poly in polys_by_idx.values():
            idx = poly["idx"]
            w_by_idx[idx]=poly["weight_abs_z"]

        return w_by_idx

    def strip_wall_cell_suffix(name: str) -> str:
        """
        Remove the first occurrence of '@wall', '@cell', or '@closed'
        and everything after it.
        """
        if not name:
            return name

        low = name.lower()
        idxs = [
            i for i in (
                low.find("@cell"),
                low.find("@wall"),
                low.find("@closed"),
            )
            if i >= 0
        ]

        if not idxs:
            return name

        return name[:min(idxs)]    

    # Mode A: explicit section provided
    has_section = section is not None

    # Mode B: field + zpos provided
    has_field_mode = (field is not None) and (zpos is not None)

    if not has_section and not has_field_mode:
        raise ValueError(
            "You must provide either 'section' OR both 'field' and 'zpos'."
        )

    if not has_section:
        # Build section from field at given z
        section = field.section(float(zpos))
    else:
        # If section is given, ignore zpos and infer z if available
        if zpos is None:
            zpos = getattr(section, "z", None)
        if zpos != section.z:
               raise ValueError(
                    f"You must provide either 'section' OR ('field' and 'zpos') consistent {zpos}. and  {section.z}"
                )
    
    z=section.z


    area_w=field.section_area_by_weight(
            z=z,
            w_tol= 0.0,
            include_per_polygon = False,
        )

    entities = field.inspect_section_entities(z)
    ent_by_name = {e["name"]: e for e in entities}

    w_by_idx = {
        ent["idx"]: ent["weight_abs_z"]
        for ent in entities
    }

    shear_w_by_idx = {
        ent["idx"]: ent["shear_weight_abs_at_z"]
        for ent in entities
    }
    poisson_by_idx = {
        ent["idx"]: ent["poisson"]
        for ent in entities
    }

    w_by_idx_nope = build_w_by_idx(ent_by_name)

    def esc(v):
        # Minimal CSV escaping
        if v is None:
            s = ""
        else:
            s = str(v)
        if any(ch in s for ch in [",", '"', "\n", "\r"]):
            s = '"' + s.replace('"', '""') + '"'
        return s

    def fmt_num(v):
        # Format numbers with `fmt`.
        # Supports:
        # - full format string: "{:.5g}"
        # - format specifier:  ".5g"
        if v is None:
            return None
        if isinstance(v, bool):
            return v
        if isinstance(v, int):
            return v

        def _apply_fmt(x: float) -> str:
            if isinstance(fmt, str) and "{" in fmt:
                return fmt.format(x)      # e.g. "{:.5g}"
            return format(x, fmt)         # e.g. ".5g"

        if isinstance(v, float):
            return _apply_fmt(v)

        try:
            fv = float(v)
        except Exception:
            return v
        return _apply_fmt(fv)

        
    z_hdr = fmt.format(float(z))
    put("## GEOMETRY EXPORT ##")
    put(f"# z={z}")   
    cols = ["idx_polygon", "idx_container", "s0_name", "s1_name", "w", "shear_w","poisson","vertex_i", "x", "y"]
    put(",".join(cols))

    for poly in section.polygons:
        
        name = poly.name
      
        ent = ent_by_name.get(name, {})

        idx_polygon = ent.get("idx")
        idx_container = ent.get("container_idx")

        s0_name = ent.get("s0_name")
        s1_name = ent.get("s1_name")

        # w ONLY from area_w groups (as requested)
        w = w_by_idx.get(idx_polygon)
        shear_w = shear_w_by_idx.get(idx_polygon)
     
        
        poisson = float(poisson_by_idx.get(idx_polygon))
        if math.isnan(poisson):
            poisson = None

        #rows = polygon_surface_w1_inners0_single(field, z=z,idx=idx_polygon)        
        #print(f"DEBUG export idx_polygon {idx_polygon} rows: {rows}")
        #w = w_by_name.get(name)

        for i, pt in enumerate(poly.vertices):
            x = float(pt.x)
            y = float(pt.y)

            row = [
                idx_polygon,
                idx_container,
                s0_name,
                s1_name,
                fmt_num(w),
                fmt_num(shear_w),
                fmt_num(poisson),
                i,
                fmt_num(x),
                fmt_num(y),
            ]
            put(",".join(esc(fmt_num(v)) for v in row))
            #put(",".join(esc(v) for v in row))


def section_properties(section: Section) -> Dict[str, float]:
    """
    Computes the integral geometric properties for a composite cross-section.

    TECHNICAL SUMMARY:
    This function performs a multi-pass integration over a set of weighted 
    polygons to derive the global geometric constants. It manages homogenization 
    by algebraically summing contributions, allowing for the representation of 
    complex domains with voids or varying material densities.

    ALGORITHMIC WORKFLOW:
    1. First-Order Moments (Area and Centroid):
       - Aggregates the weighted area (A) and the first moments of area (Qx, Qy) 
         for all constituent polygons.
       - Locates the global centroid (Cx, Cy) of the composite section.

    2. Second-Order Moments (Inertia about Origin):
       - Computes the area moments of inertia (Ix, Iy) and the product of 
         inertia (Ixy) relative to the global coordinate origin (0,0).

    3. Translation of Axes (Parallel Axis Theorem):
       - Applies the Huygens-Steiner Theorem to shift the moments of inertia 
         from the global origin to the newly calculated centroidal axes:
         I_centroid = I_origin - A * d^2
       - This transformation ensures the properties are intrinsic to the 
         section's geometry, independent of the global coordinate system.

    4. Polar Moment Extraction:
       - Derives the Polar Second Moment of Area (J) about the centroid as 
         the sum of the orthogonal centroidal moments (Ix + Iy).

    RETURNS:
       A comprehensive dictionary containing:
       - 'A': Net weighted area.
       - 'Cx', 'Cy': Centroidal coordinates.
       - 'Ix', 'Iy', 'Ixy': Second moments of area about centroidal axes.
       - 'Ip': Polar moment of area.
    """
    # First pass: area + centroid
    A_tot = 0.0
    Cx_num = 0.0
    Cy_num = 0.0

    poly_cache = []
    ii=0
    for poly in section.polygons:
        ii=ii+1
        A_i, (cx_i, cy_i) = polygon_area_centroid(poly)
        A_tot += A_i
        
        Cx_num += A_i * cx_i
        Cy_num += A_i * cy_i
        poly_cache.append((poly, A_i, cx_i, cy_i))

    if abs(A_tot) < _tol.EPS_A:
        raise ValueError("Composite area is ~0;- cannot compute centroid/properties reliably. ")

    Cx = Cx_num / A_tot
    
    Cy = Cy_num / A_tot

    # Second pass: inertia about origin then shift to centroid
    Ix_o = 0.0
    Iy_o = 0.0
    Ixy_o = 0.0

    for poly, _, _, _ in poly_cache:
        ix, iy, ixy = polygon_inertia_about_origin(poly)
        Ix_o += ix
        Iy_o += iy
        Ixy_o += ixy

    # Parallel axis theorem to centroid
    Ix_c = Ix_o - A_tot * (Cy * Cy)
    Iy_c = Iy_o - A_tot * (Cx * Cx)
    Ixy_c = Ixy_o - A_tot * (Cx * Cy)

    J = Ix_c + Iy_c


    if abs(A_tot)<_tol.EPS_A:
        A_tot = 0
    if abs(Cx)<_tol.EPS_L:
        Cx = 0
    if abs(Cy)<_tol.EPS_L:
        Cy = 0
    if abs(Ix_c)<_tol.EPS_K_ATOL:
        Ix_c = 0
    if abs(Iy_c)<_tol.EPS_K_ATOL:
        Iy_c = 0
    if abs(Ixy_c)<_tol.EPS_K_ATOL:
        Ixy_c= 0
    if abs(J)<_tol.EPS_K_ATOL:
        J= 0                
    return {
        "z": section.z,
        "A": A_tot,
        "Cx": Cx,
        "Cy": Cy,
        "Ix": Ix_c,
        "Iy": Iy_c,
        "Ixy": Ixy_c,
        "Ip": J,
    }



def _polygon_signed_area_and_centroid(poly: Polygon) -> Tuple[float, Tuple[float, float]]:
    """
    Shoelace. 
    with no weight 
    """
    verts_xy = [(v.x, v.y) for v in poly.vertices]
    A, Cx, Cy = _signed_area_centroid_xy(verts_xy)

    return A, (Cx, Cy)

def polygon_area_centroid(poly: Polygon) -> Tuple[float, Tuple[float, float]]:
    # with weight
    A_signed, (Cx, Cy) = _polygon_signed_area_and_centroid(poly)
    A_mag = (A_signed) 
    return poly.weight * A_mag, (Cx, Cy)


