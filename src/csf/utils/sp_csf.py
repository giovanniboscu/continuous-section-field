"""
Bridge between CSF and sectionproperties.

This tool uses sectionproperties as the finite-element-based section analysis
backend where applicable.

sectionproperties:
https://github.com/robbievanleeuwen/section-properties
License: MIT

sp_to_csf.py
============

Convert one or two sectionproperties sections to a CSF YAML file.

Supports:
- Prismatic sections (S0 = S1, same section type and dimensions)
- Tapered sections  (S0 != S1, same section type, different dimensions)
- Morphing          (S0 and S1 of different section types)
- Offset            (independent dx/dy translation of S0 and S1)
- Twist             (rotation of S0 and S1 around their centroid)
- Generic section pre-processing via sectionproperties' alignment/shift/rotate tools

Centroid alignment
------------------
When --morph is used (or S0 and S1 are of different types/sizes), the two
sections will in general have different centroid positions in the SP coordinate
system. By default (auto-align mode), sp_to_csf computes the centroid of each
section and applies the offset needed to align them in the CSF coordinate
system. The reference point is the centroid of S0.

Auto-alignment can be disabled with --no-align. In that case the raw SP
coordinates are used, and you can supply explicit offsets with --dx0/dy0/dx1/dy1.

If explicit --dx1/dy1 are provided, auto-alignment is skipped for S1.
Same for --dx0/dy0 and S0.

Usage (CLI)
-----------
  # Prismatic RHS
  python sp_to_csf.py rectangular_hollow_section \\
    --s0 d=200,b=150,t=10,r_out=15,n_r=8,z=0 \\
    --s1 d=200,b=150,t=10,r_out=15,n_r=8,z=10

  # Tapered RHS
  python sp_to_csf.py rectangular_hollow_section \\
    --s0 d=300,b=200,t=12,r_out=20,n_r=8,z=0 \\
    --s1 d=200,b=150,t=8,r_out=15,n_r=8,z=10

  # Morph RHS -> CHS (centroids auto-aligned)
  python sp_to_csf.py rectangular_hollow_section \\
    --morph circular_hollow_section \\
    --s0 d=4000,b=4000,t=30,r_out=300,n_r=16,z=0 \\
    --s1 d=2500,t=18,n=48,z=70000 \\
    --n=96 --name=tower --out=wind_tower.yaml

  # Morph with twist
  python sp_to_csf.py rectangular_hollow_section \\
    --morph circular_hollow_section \\
    --s0 d=200,b=150,t=10,r_out=15,n_r=8,z=0 \\
    --s1 d=180,t=8,n=32,z=10 \\
    --twist1=45

  # Disable auto-align, supply manual offsets
  python sp_to_csf.py rectangular_hollow_section \\
    --morph circular_hollow_section \\
    --s0 d=200,b=200,t=10,r_out=20,n_r=8,z=0 \\
    --s1 d=150,t=8,n=32,z=10 \\
    --no-align --dx1=25 --dy1=25

Usage (library)
---------------
  from sp_to_csf import sp_to_csf_yaml, sp_sections_to_csf_yaml
  from sectionproperties.pre.library import rectangular_hollow_section, circular_hollow_section

  sp_to_csf_yaml(
      rectangular_hollow_section(d=4000, b=4000, t=30, r_out=300, n_r=16),
      circular_hollow_section(d=2500, t=18, n=48),
      z0=0.0, z1=70000.0,
      n=96, name="tower",
      output_path="wind_tower.yaml",
  )

  sp_sections_to_csf_yaml(
      "rectangular_section",
      {"d": 200, "b": 150, "z": 0.0, "align_center": True},
      "rectangular_section",
      {"d": 200, "b": 150, "z": 10.0, "x_offset": 25.0, "angle": 15.0},
      output_path="rectangles.yaml",
      auto_align=False,
  )
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple

Point = Tuple[float, float]


# ---------------------------------------------------------------------------
# Basic polygon helpers
# ---------------------------------------------------------------------------

def _signed_area(pts: Sequence[Point]) -> float:
    """Signed area of a closed polygon. Positive = CCW, Negative = CW."""
    area = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        area += x0 * y1 - x1 * y0
    return 0.5 * area


# ---------------------------------------------------------------------------
# YAML formatting helpers
# ---------------------------------------------------------------------------

def _fmt_float(value: float, precision: int = 6) -> str:
    """Format a float compactly for YAML output."""
    text = f"{float(value):.{precision}f}".rstrip("0").rstrip(".")
    if text in {"-0", "-0.0", ""}:
        return "0"
    return text


def _poly_block(
    name: str,
    weight: float,
    vertices: Sequence[Point],
    indent: int = 8,
    precision: int = 6,
) -> str:
    """Return one CSF polygon block in YAML format.

    CSF requires the polygon name as a mapping key:
        tower:
          weight: 1.0
          vertices:
            - [x, y]
    """
    sp0 = " " * indent
    sp1 = " " * (indent + 2)
    sp2 = " " * (indent + 4)
    lines = [
        f"{sp0}{name}:",
        f"{sp1}weight: {_fmt_float(weight, precision)}",
        f"{sp1}vertices:",
    ]
    for x, y in vertices:
        lines.append(
            f"{sp2}- [{_fmt_float(x, precision)}, {_fmt_float(y, precision)}]"
        )
    return "\n".join(lines)


def _translate_points(
    pts: Sequence[Point],
    dx: float = 0.0,
    dy: float = 0.0,
    precision: int = 6,
) -> List[Point]:
    """Translate a point list by (dx, dy)."""
    return [
        (round(x + dx, precision), round(y + dy, precision))
        for x, y in pts
    ]


# ---------------------------------------------------------------------------
# Rotation helper
# ---------------------------------------------------------------------------

def _rotate_points(
    pts: Sequence[Point],
    angle_deg: float,
    cx: float = 0.0,
    cy: float = 0.0,
    precision: int = 6,
) -> List[Point]:
    """Rotate a point list by angle_deg degrees (CCW) around (cx, cy).

    Applied after resampling and translation so it does not affect
    vertex-to-vertex correspondence.
    """
    import math
    if abs(angle_deg) < 1e-12:
        return list(pts)
    rad = math.radians(angle_deg)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    result = []
    for x, y in pts:
        dx = x - cx
        dy = y - cy
        result.append((
            round(cx + dx * cos_a - dy * sin_a, precision),
            round(cy + dx * sin_a + dy * cos_a, precision),
        ))
    return result


# ---------------------------------------------------------------------------
# Morphing helpers
# ---------------------------------------------------------------------------

def _same_point(p0: Point, p1: Point, tol: float = 1e-12) -> bool:
    return abs(p0[0] - p1[0]) <= tol and abs(p0[1] - p1[1]) <= tol


def _find_axis_start_on_edge(
    pts: Sequence[Point],
    cx: float,
    cy: float,
    tol: float = 1e-12,
) -> Tuple[int, float]:
    """Find the exact start position on the positive local x semi-axis.

    Translates the contour to centroid, then finds the first intersection
    of the contour with the ray y=0, x>=0. Returns (edge_index, edge_t).
    """
    local = [(x - cx, y - cy) for x, y in pts]
    n = len(local)
    candidates: List[Tuple[float, int, float]] = []

    for i in range(n):
        x0, y0 = local[i]
        x1, y1 = local[(i + 1) % n]

        if abs(y0) <= tol and abs(y1) <= tol:
            xs = [x for x in (x0, x1) if x >= -tol]
            if xs:
                x_hit = min(max(x, 0.0) for x in xs)
                seg_dx = x1 - x0
                t_hit = 0.0 if abs(seg_dx) <= tol else (x_hit - x0) / seg_dx
                candidates.append((x_hit, i, max(0.0, min(1.0, t_hit))))
            continue

        if (y0 <= tol and y1 >= -tol) or (y1 <= tol and y0 >= -tol):
            dy = y1 - y0
            if abs(dy) <= tol:
                continue
            t_hit = -y0 / dy
            if -tol <= t_hit <= 1.0 + tol:
                x_hit = x0 + t_hit * (x1 - x0)
                if x_hit >= -tol:
                    candidates.append((max(x_hit, 0.0), i, max(0.0, min(1.0, t_hit))))

    if candidates:
        _, edge_idx, edge_t = min(candidates, key=lambda item: item[0])
        return edge_idx, edge_t

    # Fallback: rightmost vertex
    right_idx = max(range(n), key=lambda i: local[i][0])
    return right_idx, 0.0


def _rotate_contour_to_axis_start(
    pts: Sequence[Point],
    cx: float,
    cy: float,
    tol: float = 1e-12,
) -> List[Point]:
    """Rotate a ring so the first point is on the positive x semi-axis."""
    n = len(pts)
    if n < 3:
        raise ValueError("A polygon ring must contain at least 3 vertices")

    edge_idx, edge_t = _find_axis_start_on_edge(pts, cx, cy, tol)
    p0 = pts[edge_idx]
    p1 = pts[(edge_idx + 1) % n]
    start = (
        p0[0] + edge_t * (p1[0] - p0[0]),
        p0[1] + edge_t * (p1[1] - p0[1]),
    )

    rotated: List[Point] = [start]
    next_idx = (edge_idx + 1) % n
    if not _same_point(start, pts[next_idx], tol):
        rotated.append(pts[next_idx])

    j = (next_idx + 1) % n
    while j != next_idx:
        rotated.append(pts[j])
        j = (j + 1) % n

    if not _same_point(start, pts[edge_idx], tol):
        rotated.append(pts[edge_idx])

    cleaned: List[Point] = []
    for point in rotated:
        if not cleaned or not _same_point(cleaned[-1], point, tol):
            cleaned.append(point)

    if len(cleaned) < 3:
        raise ValueError("Degenerate contour after start-point rotation")

    return cleaned


def _resample_contour(pts: Sequence[Point], n: int) -> List[Point]:
    """Resample a closed polygon to exactly n equidistant points."""
    if n < 3:
        raise ValueError("n must be >= 3")
    m = len(pts)
    if m < 3:
        raise ValueError("A polygon ring must contain at least 3 vertices")

    arc = [0.0]
    for i in range(m):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % m]
        arc.append(arc[-1] + ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5)

    total = arc[-1]
    if total <= 0.0:
        raise ValueError("Degenerate contour with zero perimeter")

    result: List[Point] = []
    edge = 0
    for k in range(n):
        s = total * k / n
        while edge < m - 1 and s > arc[edge + 1]:
            edge += 1
        x0, y0 = pts[edge]
        x1, y1 = pts[(edge + 1) % m]
        seg_len = arc[edge + 1] - arc[edge]
        t = 0.0 if seg_len <= 1e-12 else (s - arc[edge]) / seg_len
        result.append((x0 + t * (x1 - x0), y0 + t * (y1 - y0)))

    return result


def _morph_ring_to_vertices(
    coords: Any,
    n: int,
    cx: float,
    cy: float,
    precision: int = 6,
) -> List[Point]:
    """Convert a Shapely ring to n equidistant CCW vertices aligned to
    the positive x semi-axis of the local (centroid-centered) frame.

    Used for morph mode (different section types) where resampling is needed
    to match vertex count between S0 and S1.
    """
    pts = [(float(x), float(y)) for x, y in coords]
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    if len(pts) < 3:
        raise ValueError("A ring must contain at least 3 distinct points")
    if _signed_area(pts) < 0.0:
        pts = list(reversed(pts))
    rotated = _rotate_contour_to_axis_start(pts, cx, cy)
    resampled = _resample_contour(rotated, n)
    return [(round(x, precision), round(y, precision)) for x, y in resampled]


def _native_ring_to_vertices(
    coords: Any,
    cx: float,
    cy: float,
    precision: int = 6,
) -> List[Point]:
    """Convert a Shapely ring to CCW vertices using the native SP order.

    Native mode is meant for prismatic/tapered sections generated by the same
    sectionproperties constructor. In that case sectionproperties already emits
    corresponding vertices in a consistent parametric order. Therefore this
    function must not insert points and must not cyclically shift the ring: both
    operations can break the native correspondence for tapered sections.
    """
    pts = [(float(x), float(y)) for x, y in coords]
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    if len(pts) < 3:
        raise ValueError("A ring must contain at least 3 distinct points")
    if _signed_area(pts) < 0.0:
        pts = list(reversed(pts))
    return [(round(x, precision), round(y, precision)) for x, y in pts]
# ---------------------------------------------------------------------------
# Feature-aware morph helpers
# ---------------------------------------------------------------------------

def _draw_radius_points(
    pt: Point,
    r: float,
    theta: float,
    n: int,
    ccw: bool = True,
    phi: float = 1.5707963267948966,
) -> List[Point]:
    """Generate radius points using sectionproperties' draw_radius convention."""
    import math

    if r <= 0.0:
        return [pt, pt]

    mult = 1.0 if ccw else -1.0
    count = max(2, n)
    result: List[Point] = []
    for i in range(count):
        t = theta + mult * i / max(1, count - 1) * phi
        result.append((pt[0] + r * math.cos(t), pt[1] + r * math.sin(t)))
    return result


def _polyline_length(pts: Sequence[Point]) -> float:
    """Return the open-polyline length."""
    length = 0.0
    for p0, p1 in zip(pts, pts[1:]):
        length += ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2) ** 0.5
    return length


def _resample_open_polyline(pts: Sequence[Point], n: int) -> List[Point]:
    """Sample n points along an open polyline, including start but excluding end."""
    if n < 1:
        return []
    if len(pts) < 2:
        raise ValueError("An open polyline must contain at least 2 points")

    arc = [0.0]
    for p0, p1 in zip(pts, pts[1:]):
        arc.append(arc[-1] + ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2) ** 0.5)

    total = arc[-1]
    if total <= 0.0:
        return [pts[0] for _ in range(n)]

    result: List[Point] = []
    edge = 0
    for k in range(n):
        s_pos = total * k / n
        while edge < len(pts) - 2 and s_pos > arc[edge + 1]:
            edge += 1
        x0, y0 = pts[edge]
        x1, y1 = pts[edge + 1]
        seg_len = arc[edge + 1] - arc[edge]
        t = 0.0 if seg_len <= 1e-12 else (s_pos - arc[edge]) / seg_len
        result.append((x0 + t * (x1 - x0), y0 + t * (y1 - y0)))

    return result


def _allocate_feature_counts(
    features: Sequence[Tuple[str, Sequence[Point], Sequence[Point]]],
    n: int,
) -> List[int]:
    """Allocate the total vertex count over independent geometric features."""
    if n < len(features):
        raise ValueError(
            f"Feature morph requires at least {len(features)} vertices"
        )

    weights = [
        max(_polyline_length(s0), _polyline_length(s1), 1e-12)
        for _, s0, s1 in features
    ]
    total_weight = sum(weights)

    counts = [max(1, int(n * w / total_weight)) for w in weights]
    while sum(counts) < n:
        errors = [
            n * weights[i] / total_weight - counts[i]
            for i in range(len(features))
        ]
        idx = max(range(len(errors)), key=lambda i: errors[i])
        counts[idx] += 1
    while sum(counts) > n:
        idx = max(range(len(counts)), key=lambda i: counts[i])
        if counts[idx] <= 1:
            break
        counts[idx] -= 1

    return counts


def _polygon_centroid(pts: Sequence[Point]) -> Point:
    """Return the centroid of a non-self-intersecting polygon ring."""
    area2 = 0.0
    cx_num = 0.0
    cy_num = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        area2 += cross
        cx_num += (x0 + x1) * cross
        cy_num += (y0 + y1) * cross

    if abs(area2) <= 1e-12:
        raise ValueError("Cannot compute centroid of a zero-area polygon")

    return cx_num / (3.0 * area2), cy_num / (3.0 * area2)


def _require_section_param(params: dict, key: str, section_name: str) -> Any:
    """Read a required section parameter with a clear error message."""
    if key not in params:
        raise ValueError(f"Missing '{key}' parameter for {section_name}")
    return params[key]


def _scaled_reference_y(params: dict, reference_params: Optional[dict]) -> float:
    """Return a stable lower split height for rectangle-compatible features."""
    d = float(_require_section_param(params, "d", "rectangular_section"))
    if reference_params and "t_f" in reference_params and "d" in reference_params:
        ref_d = float(reference_params["d"])
        if ref_d > 0.0:
            y = float(reference_params["t_f"]) / ref_d * d
        else:
            y = 0.25 * d
    else:
        y = 0.25 * d
    return max(1e-9, min(0.49 * d, y))


def _i_like_feature_blocks(
    params: dict,
    section_name: str,
) -> List[Tuple[str, List[Point]]]:
    """Return a fixed feature sequence for an I-like section outline."""
    import math

    d = float(_require_section_param(params, "d", section_name))
    b = float(_require_section_param(params, "b", section_name))
    tf = float(_require_section_param(params, "t_f", section_name))
    tw = float(_require_section_param(params, "t_w", section_name))
    r = float(_require_section_param(params, "r", section_name))
    nr = int(_require_section_param(params, "n_r", section_name))

    lw = b * 0.5 - tw * 0.5
    rw = b * 0.5 + tw * 0.5

    lrr = _draw_radius_points(
        pt=(rw + r, tf + r),
        r=r,
        theta=1.5 * math.pi,
        n=nr,
        ccw=False,
    )
    urr = _draw_radius_points(
        pt=(rw + r, d - tf - r),
        r=r,
        theta=math.pi,
        n=nr,
        ccw=False,
    )
    ulr = _draw_radius_points(
        pt=(lw - r, d - tf - r),
        r=r,
        theta=0.5 * math.pi,
        n=nr,
        ccw=False,
    )
    llr = _draw_radius_points(
        pt=(lw - r, tf + r),
        r=r,
        theta=0.0,
        n=nr,
        ccw=False,
    )

    return [
        ("bottom_edge", [(0.0, 0.0), (b, 0.0)]),
        ("right_bottom_end", [(b, 0.0), (b, tf)]),
        ("bottom_inner_right", [(b, tf), (rw + r, tf)]),
        ("lower_right_radius", lrr),
        ("right_web", [(rw, tf + r), (rw, d - tf - r)]),
        ("upper_right_radius", urr),
        ("top_inner_right", [(rw + r, d - tf), (b, d - tf)]),
        ("right_top_end", [(b, d - tf), (b, d)]),
        ("top_edge", [(b, d), (0.0, d)]),
        ("left_top_end", [(0.0, d), (0.0, d - tf)]),
        ("top_inner_left", [(0.0, d - tf), (lw - r, d - tf)]),
        ("upper_left_radius", ulr),
        ("left_web", [(lw, d - tf - r), (lw, tf + r)]),
        ("lower_left_radius", llr),
        ("bottom_inner_left", [(lw - r, tf), (0.0, tf)]),
        ("left_bottom_end", [(0.0, tf), (0.0, 0.0)]),
    ]


def _channel_like_feature_blocks(
    params: dict,
    section_name: str,
) -> List[Tuple[str, List[Point]]]:
    """Return an I-compatible feature sequence for a channel outline."""
    import math

    d = float(_require_section_param(params, "d", section_name))
    b = float(_require_section_param(params, "b", section_name))
    tf = float(_require_section_param(params, "t_f", section_name))
    tw = float(_require_section_param(params, "t_w", section_name))
    r = float(_require_section_param(params, "r", section_name))
    nr = int(_require_section_param(params, "n_r", section_name))

    lrr = _draw_radius_points(
        pt=(tw + r, tf + r),
        r=r,
        theta=1.5 * math.pi,
        n=nr,
        ccw=False,
    )
    urr = _draw_radius_points(
        pt=(tw + r, d - tf - r),
        r=r,
        theta=math.pi,
        n=nr,
        ccw=False,
    )

    return [
        ("bottom_edge", [(0.0, 0.0), (b, 0.0)]),
        ("right_bottom_end", [(b, 0.0), (b, tf)]),
        ("bottom_inner_right", [(b, tf), (tw + r, tf)]),
        ("lower_right_radius", lrr),
        ("right_web", [(tw, tf + r), (tw, d - tf - r)]),
        ("upper_right_radius", urr),
        ("top_inner_right", [(tw + r, d - tf), (b, d - tf)]),
        ("right_top_end", [(b, d - tf), (b, d)]),
        ("top_edge", [(b, d), (0.0, d)]),
        ("left_top_end", [(0.0, d), (0.0, d - tf)]),
        ("top_inner_left", [(0.0, d - tf), (0.0, d - tf - r)]),
        ("upper_left_radius", [(0.0, d - tf - r), (0.0, d - tf - r)]),
        ("left_web", [(0.0, d - tf - r), (0.0, tf + r)]),
        ("lower_left_radius", [(0.0, tf + r), (0.0, tf + r)]),
        ("bottom_inner_left", [(0.0, tf + r), (0.0, tf)]),
        ("left_bottom_end", [(0.0, tf), (0.0, 0.0)]),
    ]


def _angle_like_feature_blocks(
    params: dict,
    section_name: str,
) -> List[Tuple[str, List[Point]]]:
    """Return a fixed feature sequence for an L-section outline.

    The sequence is anchored on the geometric features that must remain matched
    during morphing: the two outer toe regions, the inner root radius, and the
    three straight branches linking them.
    """
    import math

    d = float(_require_section_param(params, "d", section_name))
    b = float(_require_section_param(params, "b", section_name))
    t = float(_require_section_param(params, "t", section_name))
    rr = float(_require_section_param(params, "r_r", section_name))
    rt = float(_require_section_param(params, "r_t", section_name))
    nr = int(_require_section_param(params, "n_r", section_name))

    brt = _draw_radius_points(
        pt=(b - rt, rt),
        r=rt,
        theta=1.5 * math.pi,
        n=nr,
        ccw=False,
    )
    root = _draw_radius_points(
        pt=(t + rr, t + rr),
        r=rr,
        theta=1.5 * math.pi,
        n=nr,
        ccw=False,
    )
    trt = _draw_radius_points(
        pt=(t - rt, d - rt),
        r=rt,
        theta=0.5 * math.pi,
        n=nr,
        ccw=False,
    )

    return [
        ("bottom_edge", [(0.0, 0.0), (b - rt, 0.0)]),
        ("bottom_right_toe_radius", brt),
        ("right_bottom_end", [(b, rt), (b, t)]),
        ("bottom_inner_edge", [(b, t), (t + rr, t)]),
        ("inner_root_radius", root),
        ("inner_vertical", [(t, t + rr), (t, d - rt)]),
        ("top_right_toe_radius", trt),
        ("top_edge", [(t - rt, d), (0.0, d)]),
        ("left_edge", [(0.0, d), (0.0, 0.0)]),
    ]


def _tee_like_feature_blocks(
    params: dict,
    section_name: str,
) -> List[Tuple[str, List[Point]]]:
    """Return an I-compatible feature sequence for a tee outline.

    Missing lower-flange features are collapsed to zero-length polylines so the
    generic feature matcher can reuse the same label sequence.
    """
    import math

    d = float(_require_section_param(params, "d", section_name))
    b = float(_require_section_param(params, "b", section_name))
    tf = float(_require_section_param(params, "t_f", section_name))
    tw = float(_require_section_param(params, "t_w", section_name))
    r = float(_require_section_param(params, "r", section_name))
    nr = int(_require_section_param(params, "n_r", section_name))

    rw = b * 0.5 + tw * 0.5
    lw = b * 0.5 - tw * 0.5

    urr = _draw_radius_points(
        pt=(rw + r, d - tf - r),
        r=r,
        theta=math.pi,
        n=nr,
        ccw=False,
    )
    ulr = _draw_radius_points(
        pt=(lw - r, d - tf - r),
        r=r,
        theta=0.5 * math.pi,
        n=nr,
        ccw=False,
    )

    return [
        ("bottom_edge", [(lw, 0.0), (rw, 0.0)]),
        ("right_bottom_end", [(rw, 0.0), (rw, 0.0)]),
        ("bottom_inner_right", [(rw, 0.0), (rw, 0.0)]),
        ("lower_right_radius", [(rw, 0.0), (rw, 0.0)]),
        ("right_web", [(rw, 0.0), (rw, d - tf - r)]),
        ("upper_right_radius", urr),
        ("top_inner_right", [(rw + r, d - tf), (b, d - tf)]),
        ("right_top_end", [(b, d - tf), (b, d)]),
        ("top_edge", [(b, d), (0.0, d)]),
        ("left_top_end", [(0.0, d), (0.0, d - tf)]),
        ("top_inner_left", [(0.0, d - tf), (lw - r, d - tf)]),
        ("upper_left_radius", ulr),
        ("left_web", [(lw, d - tf - r), (lw, 0.0)]),
        ("lower_left_radius", [(lw, 0.0), (lw, 0.0)]),
        ("bottom_inner_left", [(lw, 0.0), (lw, 0.0)]),
        ("left_bottom_end", [(lw, 0.0), (lw, 0.0)]),
    ]


def _rectangle_feature_blocks(
    params: dict,
    reference_params: Optional[dict],
) -> List[Tuple[str, List[Point]]]:
    """Return an I-compatible feature sequence collapsed onto a rectangle."""
    d = float(_require_section_param(params, "d", "rectangular_section"))
    b = float(_require_section_param(params, "b", "rectangular_section"))
    yb = _scaled_reference_y(params, reference_params)
    yt = d - yb

    return [
        ("bottom_edge", [(0.0, 0.0), (b, 0.0)]),
        ("right_bottom_end", [(b, 0.0), (b, yb)]),
        ("bottom_inner_right", [(b, yb), (b, yb)]),
        ("lower_right_radius", [(b, yb), (b, yb)]),
        ("right_web", [(b, yb), (b, yt)]),
        ("upper_right_radius", [(b, yt), (b, yt)]),
        ("top_inner_right", [(b, yt), (b, yt)]),
        ("right_top_end", [(b, yt), (b, d)]),
        ("top_edge", [(b, d), (0.0, d)]),
        ("left_top_end", [(0.0, d), (0.0, yt)]),
        ("top_inner_left", [(0.0, yt), (0.0, yt)]),
        ("upper_left_radius", [(0.0, yt), (0.0, yt)]),
        ("left_web", [(0.0, yt), (0.0, yb)]),
        ("lower_left_radius", [(0.0, yb), (0.0, yb)]),
        ("bottom_inner_left", [(0.0, yb), (0.0, yb)]),
        ("left_bottom_end", [(0.0, yb), (0.0, 0.0)]),
    ]


def _section_feature_blocks(
    section_name: str,
    params: dict,
    reference_params: Optional[dict] = None,
) -> List[Tuple[str, List[Point]]]:
    """Return a fixed feature sequence for supported feature morph families."""
    if section_name == "i_section":
        return _i_like_feature_blocks(params, section_name)
    if section_name == "channel_section":
        return _channel_like_feature_blocks(params, section_name)
    if section_name == "rectangular_section":
        return _rectangle_feature_blocks(params, reference_params)
    if section_name == "angle_section":
        return _angle_like_feature_blocks(params, section_name)
    if section_name == "tee_section":
        return _tee_like_feature_blocks(params, section_name)
    raise ValueError(
        "Feature morph currently supports i_section, channel_section, "
        "rectangular_section, angle_section, tee_section, and the dedicated "
        "i_section <-> tee_section pair"
    )


def _i_section_to_tee_feature_vertices(
    params_s0: dict,
    params_s1: dict,
    n: int,
    precision: int,
) -> Tuple[List[Point], List[Point]]:
    """Build matched I-section and tee-section rings feature by feature."""
    import math

    d0 = float(_require_section_param(params_s0, "d", "i_section"))
    b0 = float(_require_section_param(params_s0, "b", "i_section"))
    tf0 = float(_require_section_param(params_s0, "t_f", "i_section"))
    tw0 = float(_require_section_param(params_s0, "t_w", "i_section"))
    r0 = float(_require_section_param(params_s0, "r", "i_section"))
    nr0 = int(_require_section_param(params_s0, "n_r", "i_section"))

    d1 = float(_require_section_param(params_s1, "d", "tee_section"))
    b1 = float(_require_section_param(params_s1, "b", "tee_section"))
    tf1 = float(_require_section_param(params_s1, "t_f", "tee_section"))
    tw1 = float(_require_section_param(params_s1, "t_w", "tee_section"))
    r1 = float(_require_section_param(params_s1, "r", "tee_section"))
    nr1 = int(_require_section_param(params_s1, "n_r", "tee_section"))

    rw0 = b0 * 0.5 + tw0 * 0.5
    lw0 = b0 * 0.5 - tw0 * 0.5
    rw1 = b1 * 0.5 + tw1 * 0.5
    lw1 = b1 * 0.5 - tw1 * 0.5

    br0 = _draw_radius_points(
        pt=(rw0 + r0, tf0 + r0),
        r=r0,
        theta=1.5 * math.pi,
        n=nr0,
        ccw=False,
    )
    tr0 = _draw_radius_points(
        pt=(rw0 + r0, d0 - tf0 - r0),
        r=r0,
        theta=math.pi,
        n=nr0,
        ccw=False,
    )
    tl0 = _draw_radius_points(
        pt=(lw0 - r0, d0 - tf0 - r0),
        r=r0,
        theta=0.5 * math.pi,
        n=nr0,
        ccw=False,
    )
    bl0 = _draw_radius_points(
        pt=(lw0 - r0, tf0 + r0),
        r=r0,
        theta=0.0,
        n=nr0,
        ccw=False,
    )

    tr1 = _draw_radius_points(
        pt=(rw1 + r1, d1 - tf1 - r1),
        r=r1,
        theta=math.pi,
        n=nr1,
        ccw=False,
    )
    tl1 = _draw_radius_points(
        pt=(lw1 - r1, d1 - tf1 - r1),
        r=r1,
        theta=0.5 * math.pi,
        n=nr1,
        ccw=False,
    )

    features: List[Tuple[str, List[Point], List[Point]]] = [
        (
            "bottom_edge",
            [(0.0, 0.0), (b0, 0.0)],
            [(lw1, 0.0), (rw1, 0.0)],
        ),
        (
            "right_lower_web_and_disappearing_flange",
            [(b0, 0.0), (b0, tf0), *br0, (rw0, d0 - tf0 - r0)],
            [(rw1, 0.0), (rw1, d1 - tf1 - r1)],
        ),
        ("top_right_root_radius", tr0, tr1),
        (
            "top_flange",
            [tr0[-1], (b0, d0 - tf0), (b0, d0), (0.0, d0), (0.0, d0 - tf0), tl0[0]],
            [tr1[-1], (b1, d1 - tf1), (b1, d1), (0.0, d1), (0.0, d1 - tf1), tl1[0]],
        ),
        ("top_left_root_radius", tl0, tl1),
        (
            "left_lower_web_and_disappearing_flange",
            [tl0[-1], (lw0, tf0 + r0), *bl0, (0.0, tf0), (0.0, 0.0)],
            [(lw1, d1 - tf1 - r1), (lw1, 0.0)],
        ),
    ]

    return _features_to_vertices(features, n=n, precision=precision)


def _features_to_vertices(
    features: Sequence[Tuple[str, Sequence[Point], Sequence[Point]]],
    n: int,
    precision: int,
) -> Tuple[List[Point], List[Point]]:
    """Convert paired feature polylines into matched closed-ring vertices."""
    counts = _allocate_feature_counts(features, n)
    vertices_s0: List[Point] = []
    vertices_s1: List[Point] = []

    for count, (_, feature_s0, feature_s1) in zip(counts, features):
        vertices_s0.extend(_resample_open_polyline(feature_s0, count))
        vertices_s1.extend(_resample_open_polyline(feature_s1, count))

    if len(vertices_s0) != n or len(vertices_s1) != n:
        raise ValueError("Feature morph produced an inconsistent vertex count")

    if _signed_area(vertices_s0) < 0.0:
        vertices_s0 = list(reversed(vertices_s0))
        vertices_s1 = list(reversed(vertices_s1))
    if _signed_area(vertices_s1) < 0.0:
        vertices_s1 = list(reversed(vertices_s1))

    if _signed_area(vertices_s0) <= 0.0 or _signed_area(vertices_s1) <= 0.0:
        raise ValueError("Feature morph produced a non-CCW or degenerate ring")

    return (
        [(round(x, precision), round(y, precision)) for x, y in vertices_s0],
        [(round(x, precision), round(y, precision)) for x, y in vertices_s1],
    )


def _feature_vertices_for_pair(
    section_s0: str,
    section_s1: str,
    params_s0: dict,
    params_s1: dict,
    n: int,
    precision: int,
) -> Tuple[List[Point], List[Point]]:
    """Return matched vertices for supported feature morph pairs."""
    if section_s0 == "i_section" and section_s1 == "tee_section":
        return _i_section_to_tee_feature_vertices(params_s0, params_s1, n, precision)
    if section_s0 == "tee_section" and section_s1 == "i_section":
        raw_i, raw_tee = _i_section_to_tee_feature_vertices(params_s1, params_s0, n, precision)
        return raw_tee, raw_i

    supported = {"i_section", "channel_section", "rectangular_section", "angle_section", "tee_section"}
    if section_s0 not in supported or section_s1 not in supported:
        raise ValueError(
            f"Feature morph is not implemented for {section_s0} -> {section_s1}. "
            "Use --morph-mode perimeter or implement a dedicated feature map."
        )

    blocks0 = _section_feature_blocks(section_s0, params_s0, params_s1)
    blocks1 = _section_feature_blocks(section_s1, params_s1, params_s0)
    labels0 = [label for label, _ in blocks0]
    labels1 = [label for label, _ in blocks1]
    if labels0 != labels1:
        raise ValueError("Internal feature labels are inconsistent")

    features = [
        (label0, pts0, pts1)
        for (label0, pts0), (_, pts1) in zip(blocks0, blocks1)
    ]
    return _features_to_vertices(features, n=n, precision=precision)


def _write_feature_morph_yaml(
    section_s0: str,
    section_s1: str,
    params_s0: dict,
    params_s1: dict,
    z0: float,
    z1: float,
    output_path: "str | Path",
    n: int,
    name: str,
    comment: Optional[str],
    solid_weight: float,
    indent: int,
    precision: int,
    dx0: Optional[float],
    dy0: Optional[float],
    dx1: Optional[float],
    dy1: Optional[float],
    twist0_deg: float,
    twist1_deg: float,
    auto_align: bool,
) -> Tuple[Path, Point, Point]:
    """Write a CSF YAML file using a feature-aware morph map."""
    output_path = Path(output_path)

    raw_s0, raw_s1 = _feature_vertices_for_pair(
        section_s0=section_s0,
        section_s1=section_s1,
        params_s0=params_s0,
        params_s1=params_s1,
        n=n,
        precision=precision,
    )
    cx0_geom, cy0_geom = _polygon_centroid(raw_s0)
    cx1_geom, cy1_geom = _polygon_centroid(raw_s1)

    if auto_align:
        _dx0 = -cx0_geom if dx0 is None else dx0
        _dy0 = -cy0_geom if dy0 is None else dy0
        _dx1 = -cx1_geom if dx1 is None else dx1
        _dy1 = -cy1_geom if dy1 is None else dy1
    else:
        _dx0 = dx0 if dx0 is not None else 0.0
        _dy0 = dy0 if dy0 is not None else 0.0
        _dx1 = dx1 if dx1 is not None else 0.0
        _dy1 = dy1 if dy1 is not None else 0.0

    ext0 = _translate_points(raw_s0, dx=_dx0, dy=_dy0, precision=precision)
    ext1 = _translate_points(raw_s1, dx=_dx1, dy=_dy1, precision=precision)
    ext0 = _rotate_points(
        ext0,
        twist0_deg,
        cx=cx0_geom + _dx0,
        cy=cy0_geom + _dy0,
        precision=precision,
    )
    ext1 = _rotate_points(
        ext1,
        twist1_deg,
        cx=cx1_geom + _dx1,
        cy=cy1_geom + _dy1,
        precision=precision,
    )

    align_note = (
        f"# Centroid S0 (feature): ({_fmt_float(cx0_geom, precision)}, {_fmt_float(cy0_geom, precision)})"
        f"  offset applied: ({_fmt_float(_dx0, precision)}, {_fmt_float(_dy0, precision)})\n"
        f"# Centroid S1 (feature): ({_fmt_float(cx1_geom, precision)}, {_fmt_float(cy1_geom, precision)})"
        f"  offset applied: ({_fmt_float(_dx1, precision)}, {_fmt_float(_dy1, precision)})"
    )

    header_lines = ["# Generated by sp_to_csf.py"]
    if comment:
        header_lines.append(f"# {comment}")
    header_lines += [
        f"# S0 at z={_fmt_float(z0, precision)}",
        f"# S1 at z={_fmt_float(z1, precision)}",
        f"# Feature morph: {section_s0} -> {section_s1}, n={n} vertices",
        f"# auto_align={'ON' if auto_align else 'OFF'}",
        align_note,
        f"# Twist S0: {_fmt_float(twist0_deg, precision)} deg CCW",
        f"# Twist S1: {_fmt_float(twist1_deg, precision)} deg CCW",
        "# Ring orientation: CCW | Hole weight: 0.0",
    ]

    yaml_text = "\n".join([
        *header_lines, "",
        "CSF:", "  sections:", "    S0:",
        f"      z: {_fmt_float(z0, precision)}",
        "      polygons:",
        _poly_block(name, solid_weight, ext0, indent, precision),
        "    S1:",
        f"      z: {_fmt_float(z1, precision)}",
        "      polygons:",
        _poly_block(name, solid_weight, ext1, indent, precision), "",
    ])

    output_path.write_text(yaml_text, encoding="utf-8")
    return output_path, (cx0_geom, cy0_geom), (cx1_geom, cy1_geom)

# ---------------------------------------------------------------------------
# sectionproperties extraction helpers
# ---------------------------------------------------------------------------

def _import_sp_geometry_types() -> Tuple[Any, Any]:
    """Import Geometry and CompoundGeometry from sectionproperties."""
    try:
        from sectionproperties.pre.geometry import CompoundGeometry, Geometry
        return Geometry, CompoundGeometry
    except ImportError:
        try:
            from sectionproperties.pre import CompoundGeometry, Geometry
            return Geometry, CompoundGeometry
        except ImportError as exc:
            raise ImportError(
                "sectionproperties is required: pip install sectionproperties"
            ) from exc


def _flatten_geometry_to_polygons(geometry: Any) -> List[Any]:
    """Return the Shapely polygons contained in a sectionproperties geometry."""
    Geometry, CompoundGeometry = _import_sp_geometry_types()
    try:
        from shapely.geometry import MultiPolygon
    except ImportError as exc:
        raise ImportError("shapely is required") from exc

    polygons: List[Any] = []
    if isinstance(geometry, CompoundGeometry):
        geoms = list(geometry.geoms)
    elif isinstance(geometry, Geometry):
        geoms = [geometry]
    else:
        raise TypeError(
            f"Expected Geometry or CompoundGeometry, got {type(geometry).__name__}"
        )
    for g in geoms:
        shp = g.geom
        if isinstance(shp, MultiPolygon):
            polygons.extend(list(shp.geoms))
        else:
            polygons.append(shp)
    return polygons


def geometry_centroid(geometry: Any) -> Tuple[float, float]:
    """Return the centroid (cx, cy) of the union of all polygons in a
    sectionproperties geometry object."""
    return _geometry_centroid(geometry)

def _geometry_centroid(geometry: Any) -> Tuple[float, float]:
    """Return the centroid (cx, cy) of the union of all polygons in a
    sectionproperties geometry object."""
    polys = _flatten_geometry_to_polygons(geometry)
    try:
        from shapely.ops import unary_union
    except ImportError as exc:
        raise ImportError("shapely is required") from exc
    union = unary_union(polys)
    return union.centroid.x, union.centroid.y


# ---------------------------------------------------------------------------
# Pairwise block builder
# ---------------------------------------------------------------------------

def _pair_to_blocks(
    poly_s0: Any,
    poly_s1: Any,
    base_name: str,
    n: Optional[int],
    solid_weight: float,
    void_weight: float,
    indent: int,
    precision: int,
    dx0: float,
    dy0: float,
    dx1: float,
    dy1: float,
    twist0_deg: float,
    twist1_deg: float,
    morph_mode: str = "perimeter",
) -> Tuple[List[str], List[str]]:
    """Convert one polygon pair (exterior + holes) into matching CSF YAML blocks.

    Both sections must have the same number of holes.
    Offset and twist are applied after resampling/alignment.

    n=None (native mode): use SP native vertices without resampling.
        Correct for tapered sections of the same type — SP generates
        vertices in the same parametric order for both sections.
    n=int (resample mode): resample both rings to n equidistant points.
        Required for morph mode where section types differ.
    """
    holes_s0 = list(poly_s0.interiors)
    holes_s1 = list(poly_s1.interiors)

    if len(holes_s0) != len(holes_s1):
        raise ValueError(
            f"Polygon '{base_name}': different hole count in S0 ({len(holes_s0)}) "
            f"and S1 ({len(holes_s1)})"
        )

    cx0, cy0 = poly_s0.centroid.x, poly_s0.centroid.y
    cx1, cy1 = poly_s1.centroid.x, poly_s1.centroid.y

    def _process(ring_coords, cx, cy, dx, dy, twist_deg, is_s0):
        if morph_mode == "native" or n is None:
            # Native mode: preserve SP vertex order and native vertex count.
            pts = _native_ring_to_vertices(ring_coords, cx, cy, precision)
        elif morph_mode == "perimeter":
            # Perimeter mode: current global arc-length resampling.
            pts = _morph_ring_to_vertices(ring_coords, n, cx, cy, precision)
        else:
            raise ValueError(
                "Feature mode is handled before generic polygon extraction"
            )
        pts = _translate_points(pts, dx=dx, dy=dy, precision=precision)
        pts = _rotate_points(pts, twist_deg, cx=cx + dx, cy=cy + dy, precision=precision)
        return pts

    ext0 = _process(poly_s0.exterior.coords, cx0, cy0, dx0, dy0, twist0_deg, True)
    ext1 = _process(poly_s1.exterior.coords, cx1, cy1, dx1, dy1, twist1_deg, False)

    # In native mode, verify vertex counts match after alignment
    if n is None and len(ext0) != len(ext1):
        raise ValueError(
            f"Polygon '{base_name}': native vertex count mismatch — "
            f"S0 has {len(ext0)}, S1 has {len(ext1)}.\n"
            "Ensure n_r (and n for circular sections) are identical in --s0 and --s1."
        )

    blocks_s0 = [_poly_block(base_name, solid_weight, ext0, indent, precision)]
    blocks_s1 = [_poly_block(base_name, solid_weight, ext1, indent, precision)]

    for i, (ring0, ring1) in enumerate(zip(holes_s0, holes_s1)):
        hname = f"{base_name}_hole" if i == 0 else f"{base_name}_hole{i}"
        h0 = _process(ring0.coords, cx0, cy0, dx0, dy0, twist0_deg, True)
        h1 = _process(ring1.coords, cx1, cy1, dx1, dy1, twist1_deg, False)
        blocks_s0.append(_poly_block(hname, void_weight, h0, indent, precision))
        blocks_s1.append(_poly_block(hname, void_weight, h1, indent, precision))

    return blocks_s0, blocks_s1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def sp_to_csf_yaml(
    geometry_s0: Any,
    geometry_s1: Any,
    z0: float,
    z1: float,
    output_path: "str | Path",
    n: Optional[int] = None,
    name: Optional[str] = None,
    comment: Optional[str] = None,
    solid_weight: float = 1.0,
    void_weight: float = 0.0,
    indent: int = 8,
    precision: int = 6,
    dx0: Optional[float] = None,
    dy0: Optional[float] = None,
    dx1: Optional[float] = None,
    dy1: Optional[float] = None,
    twist0_deg: float = 0.0,
    twist1_deg: float = 0.0,
    auto_align: bool = True,
    morph_mode: str = "perimeter",
) -> Path:
    """Convert two sectionproperties geometries to a CSF YAML file.

    Parameters
    ----------
    geometry_s0, geometry_s1 : Geometry or CompoundGeometry
        Start and end sections. May be of different types (morphing).
    z0, z1 : float
        z-coordinates of S0 and S1.
    output_path : str or Path
        Output YAML file path.
    n : int or None
        Number of vertices per ring after resampling.
        None (default): native mode — use SP vertices without resampling.
            Correct for tapered sections of the same type (same n_r).
        int: resample mode — equidistant arc-length resampling.
            Required for morph mode (different section types).
            Use higher values for sections with sharp corners (>= 64).
    name : str, optional
        Polygon base name (default: "section").
    comment : str, optional
        Comment added to the YAML header.
    solid_weight : float
        Weight of exterior polygons (default 1.0).
    void_weight : float
        Weight of interior rings / holes (default 0.0).
    dx0, dy0 : float, optional
        Explicit offset for S0. If None and auto_align=True, computed
        automatically so that the S0 centroid maps to the origin.
    dx1, dy1 : float, optional
        Explicit offset for S1. If None and auto_align=True, computed
        automatically so that the S1 centroid aligns with the S0 centroid.
    twist0_deg, twist1_deg : float
        Rotation of S0 and S1 around their centroid in degrees CCW (default 0).
    auto_align : bool
        If True (default), automatically offset S0 and S1 so their centroids
        coincide in the CSF coordinate frame. Explicit dx/dy values override
        auto-alignment for the respective section.

    Returns
    -------
    Path
    """
    output_path = Path(output_path)
    poly_name = name or "section"
    if morph_mode not in {"perimeter", "native"}:
        raise ValueError(
            "sp_to_csf_yaml supports only 'perimeter' and 'native'. "
            "Feature mode is available through the CLI writer."
        )

    polygons_s0 = _flatten_geometry_to_polygons(geometry_s0)
    polygons_s1 = _flatten_geometry_to_polygons(geometry_s1)

    if len(polygons_s0) != len(polygons_s1):
        raise ValueError(
            f"S0 has {len(polygons_s0)} polygon(s), S1 has {len(polygons_s1)}. "
            "Both must have the same number of polygons (same hole layout)."
        )

    # --- Centroid auto-alignment ---
    # Compute the global centroid of each geometry (union of all polygons).
    # S0 centroid is mapped to the origin; S1 centroid is aligned to it.
    # Explicit dx/dy values override auto-alignment for that section.
    cx0_geom, cy0_geom = _geometry_centroid(geometry_s0)
    cx1_geom, cy1_geom = _geometry_centroid(geometry_s1)

    if auto_align:
        # S0 offset: move S0 centroid to origin (unless explicit offset given)
        _dx0 = (-cx0_geom if dx0 is None else dx0)
        _dy0 = (-cy0_geom if dy0 is None else dy0)
        # S1 offset: move S1 centroid to the S0 centroid after S0 offset
        # S0 centroid in CSF frame = (0, 0) after auto-align
        _dx1 = (-cx1_geom if dx1 is None else dx1)
        _dy1 = (-cy1_geom if dy1 is None else dy1)
    else:
        _dx0 = dx0 if dx0 is not None else 0.0
        _dy0 = dy0 if dy0 is not None else 0.0
        _dx1 = dx1 if dx1 is not None else 0.0
        _dy1 = dy1 if dy1 is not None else 0.0

    align_note = (
        f"# Centroid S0 (SP): ({_fmt_float(cx0_geom, precision)}, {_fmt_float(cy0_geom, precision)})"
        f"  offset applied: ({_fmt_float(_dx0, precision)}, {_fmt_float(_dy0, precision)})\n"
        f"# Centroid S1 (SP): ({_fmt_float(cx1_geom, precision)}, {_fmt_float(cy1_geom, precision)})"
        f"  offset applied: ({_fmt_float(_dx1, precision)}, {_fmt_float(_dy1, precision)})"
    )

    blocks_s0: List[str] = []
    blocks_s1: List[str] = []

    for idx, (poly0, poly1) in enumerate(zip(polygons_s0, polygons_s1)):
        bname = poly_name if len(polygons_s0) == 1 else f"{poly_name}_{idx}"

        # The morph strategy is explicit. Perimeter mode keeps global resampling;
        # native mode preserves the sectionproperties vertex order.
        n_eff = None if morph_mode == "native" else n

        local_s0, local_s1 = _pair_to_blocks(
            poly_s0=poly0, poly_s1=poly1,
            base_name=bname, n=n_eff,
            solid_weight=solid_weight, void_weight=void_weight,
            indent=indent, precision=precision,
            dx0=_dx0, dy0=_dy0, dx1=_dx1, dy1=_dy1,
            twist0_deg=twist0_deg, twist1_deg=twist1_deg,
            morph_mode=morph_mode,
        )
        blocks_s0.extend(local_s0)
        blocks_s1.extend(local_s1)

    header_lines = ["# Generated by sp_to_csf.py"]
    if comment:
        header_lines.append(f"# {comment}")
    header_lines += [
        f"# S0 at z={_fmt_float(z0, precision)}",
        f"# S1 at z={_fmt_float(z1, precision)}",
        f"# morph_mode={morph_mode}",
        f"# Each ring resampled to n={n} equidistant vertices",
        f"# auto_align={'ON' if auto_align else 'OFF'}",
        align_note,
        f"# Twist S0: {_fmt_float(twist0_deg, precision)} deg CCW",
        f"# Twist S1: {_fmt_float(twist1_deg, precision)} deg CCW",
        "# Ring orientation: CCW | Hole weight: 0.0",
    ]

    yaml_text = "\n".join([
        *header_lines, "",
        "CSF:", "  sections:", "    S0:",
        f"      z: {_fmt_float(z0, precision)}",
        "      polygons:", *blocks_s0,
        "    S1:",
        f"      z: {_fmt_float(z1, precision)}",
        "      polygons:", *blocks_s1, "",
    ])

    output_path.write_text(yaml_text, encoding="utf-8")
    return output_path


__all__ = ["sp_to_csf_yaml", "sp_sections_to_csf_yaml"]


# ---------------------------------------------------------------------------
# CLI helpers and section-level transforms
# ---------------------------------------------------------------------------

_SECTION_TRANSFORM_KEYS = {
    "align_center",
    "align_to",
    "x_offset",
    "y_offset",
    "angle",
}
_ALIGN_TO_VALUES = {"top", "bottom", "left", "right"}


def _coerce(value: str) -> Any:
    """Coerce a CLI token to bool, int, float, or leave it as string."""
    low = value.strip().lower()
    if low == "true":
        return True
    if low == "false":
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def _parse_section_params(raw: str) -> dict:
    result = {}
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        if "=" not in token:
            raise ValueError(f"Invalid token '{token}' — expected key=value")
        k, v = token.split("=", 1)
        result[k.strip()] = _coerce(v.strip())
    return result


def _extract_required_z(params: dict, section_label: str) -> float:
    """Read the required z coordinate for one endpoint section."""
    if "z" not in params:
        raise ValueError(f"Missing 'z' parameter for {section_label}")
    value = params["z"]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Parameter 'z' for {section_label} must be numeric")
    return float(value)


def _parse_bool_param(value: Any, key: str, section_name: str) -> bool:
    """Validate a boolean section-level transform parameter."""
    if isinstance(value, bool):
        return value
    raise ValueError(
        f"Parameter '{key}' for {section_name} must be true or false"
    )



def _parse_float_param(value: Any, key: str, section_name: str) -> float:
    """Validate a numeric section-level transform parameter."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(
            f"Parameter '{key}' for {section_name} must be numeric"
        )
    return float(value)



def _split_section_params(
    section_name: str,
    params: dict,
) -> Tuple[dict, dict]:
    """Split raw section parameters into SP constructor args and transform args.

    The split is explicit on purpose. If a parameter belongs to the transform
    layer, it must not silently flow into the sectionproperties constructor.
    """
    sp_params = {}
    transform = {
        "align_center": False,
        "align_to": None,
        "x_offset": 0.0,
        "y_offset": 0.0,
        "angle": 0.0,
    }

    for key, value in params.items():
        if key == "z":
            continue
        if key == "align_center":
            transform["align_center"] = _parse_bool_param(
                value, key, section_name
            )
        elif key == "align_to":
            if not isinstance(value, str):
                raise ValueError(
                    f"Parameter 'align_to' for {section_name} must be one of: "
                    f"{', '.join(sorted(_ALIGN_TO_VALUES))}"
                )
            side = value.strip().lower()
            if side not in _ALIGN_TO_VALUES:
                raise ValueError(
                    f"Parameter 'align_to' for {section_name} must be one of: "
                    f"{', '.join(sorted(_ALIGN_TO_VALUES))}"
                )
            transform["align_to"] = side
        elif key in {"x_offset", "y_offset", "angle"}:
            transform[key] = _parse_float_param(value, key, section_name)
        else:
            sp_params[key] = value

    return sp_params, transform



def _transform_has_translation(transform: dict, tol: float = 1e-12) -> bool:
    """Return True if the transform contains any translation-like request."""
    return (
        transform["align_center"]
        or transform["align_to"] is not None
        or abs(transform["x_offset"]) > tol
        or abs(transform["y_offset"]) > tol
    )



def _transform_is_active(transform: dict, tol: float = 1e-12) -> bool:
    """Return True if any section-level transform is effectively requested."""
    return _transform_has_translation(transform, tol) or abs(transform["angle"]) > tol



def _validate_transform_pair(
    section_s0: str,
    section_s1: str,
    transform_s0: dict,
    transform_s1: dict,
    auto_align: bool,
) -> None:
    """Validate pairwise section-level transform semantics.

    The rules are intentionally strict. If the relative placement of S0 and S1
    is not fully determined by the explicit parameters, the function stops.
    """
    if transform_s0["align_center"] and transform_s0["align_to"] is not None:
        raise ValueError(
            f"Section {section_s0}: 'align_center' and 'align_to' cannot be "
            "used together"
        )
    if transform_s1["align_center"] and transform_s1["align_to"] is not None:
        raise ValueError(
            f"Section {section_s1}: 'align_center' and 'align_to' cannot be "
            "used together"
        )
    if transform_s0["align_to"] is not None and transform_s1["align_to"] is not None:
        raise ValueError(
            "Section-level 'align_to' cannot be specified for both S0 and S1"
        )
    if auto_align and (
        _transform_has_translation(transform_s0)
        or _transform_has_translation(transform_s1)
    ):
        raise ValueError(
            "Section-level align/shift parameters require auto_align=False "
            "because CSF auto-alignment would overwrite them"
        )



def _apply_standalone_section_transform(geometry: Any, transform: dict) -> Any:
    """Apply the transforms that do not depend on the other section."""
    result = geometry
    if transform["align_center"]:
        result = result.align_center()
    if abs(transform["x_offset"]) > 1e-12 or abs(transform["y_offset"]) > 1e-12:
        result = result.shift_section(
            x_offset=transform["x_offset"],
            y_offset=transform["y_offset"],
        )
    if abs(transform["angle"]) > 1e-12:
        result = result.rotate_section(angle=transform["angle"])
    return result



def _apply_dependent_section_transform(
    geometry: Any,
    reference_geometry: Any,
    transform: dict,
) -> Any:
    """Apply a transform that contains an explicit align_to dependency."""
    result = geometry.align_to(
        other=reference_geometry,
        on=transform["align_to"],
    )
    if abs(transform["x_offset"]) > 1e-12 or abs(transform["y_offset"]) > 1e-12:
        result = result.shift_section(
            x_offset=transform["x_offset"],
            y_offset=transform["y_offset"],
        )
    if abs(transform["angle"]) > 1e-12:
        result = result.rotate_section(angle=transform["angle"])
    return result



def _build_geometry(section_name: str, params: dict) -> Any:
    """Build one sectionproperties geometry from pure constructor parameters."""
    unexpected = sorted(set(params).intersection(_SECTION_TRANSFORM_KEYS))
    if unexpected:
        raise ValueError(
            "Internal error: section-level transform parameters must be split "
            f"before _build_geometry(): {unexpected}"
        )
    try:
        from sectionproperties.pre import library
    except ImportError:
        raise ImportError("pip install sectionproperties")
    fn = getattr(library, section_name, None)
    if fn is None:
        raise ValueError(
            f"'{section_name}' not found in sectionproperties.pre.library."
        )
    sp_params = {k: v for k, v in params.items() if k != "z"}
    return fn(**sp_params)



def _build_transformed_section_pair(
    section_s0: str,
    section_s1: str,
    params_s0: dict,
    params_s1: dict,
    auto_align: bool,
    morph_mode: str,
) -> Tuple[Any, Any, dict, dict]:
    """Build S0 and S1 and apply deterministic section-level SP transforms."""
    sp_params_s0, transform_s0 = _split_section_params(section_s0, params_s0)
    sp_params_s1, transform_s1 = _split_section_params(section_s1, params_s1)

    if morph_mode == "feature" and (
        _transform_is_active(transform_s0) or _transform_is_active(transform_s1)
    ):
        raise ValueError(
            "Section-level align/shift/rotate parameters are not supported "
            "with morph_mode='feature'"
        )

    _validate_transform_pair(
        section_s0=section_s0,
        section_s1=section_s1,
        transform_s0=transform_s0,
        transform_s1=transform_s1,
        auto_align=auto_align,
    )

    geom_s0 = _build_geometry(section_s0, sp_params_s0)
    geom_s1 = _build_geometry(section_s1, sp_params_s1)

    if transform_s0["align_to"] is not None:
        geom_s1 = _apply_standalone_section_transform(geom_s1, transform_s1)
        geom_s0 = _apply_dependent_section_transform(
            geom_s0,
            reference_geometry=geom_s1,
            transform=transform_s0,
        )
    elif transform_s1["align_to"] is not None:
        geom_s0 = _apply_standalone_section_transform(geom_s0, transform_s0)
        geom_s1 = _apply_dependent_section_transform(
            geom_s1,
            reference_geometry=geom_s0,
            transform=transform_s1,
        )
    else:
        geom_s0 = _apply_standalone_section_transform(geom_s0, transform_s0)
        geom_s1 = _apply_standalone_section_transform(geom_s1, transform_s1)

    return geom_s0, geom_s1, transform_s0, transform_s1



def sp_sections_to_csf_yaml(
    section_s0: str,
    params_s0: dict,
    section_s1: Optional[str],
    params_s1: dict,
    output_path: "str | Path",
    n: Optional[int] = None,
    name: Optional[str] = None,
    comment: Optional[str] = None,
    solid_weight: float = 1.0,
    void_weight: float = 0.0,
    indent: int = 8,
    precision: int = 6,
    dx0: Optional[float] = None,
    dy0: Optional[float] = None,
    dx1: Optional[float] = None,
    dy1: Optional[float] = None,
    twist0_deg: float = 0.0,
    twist1_deg: float = 0.0,
    auto_align: bool = True,
    morph_mode: str = "perimeter",
) -> Path:
    """High-level API using section names + parameter dictionaries.

    The dictionaries may contain both sectionproperties constructor parameters and
    the explicit section-level transform keys:
        - align_center : bool
        - align_to     : top | bottom | left | right
        - x_offset     : float
        - y_offset     : float
        - angle        : float (degrees CCW)

    The transform layer is applied before the existing CSF export layer. The two
    layers are kept separate on purpose so the current exporter semantics remain
    unchanged.
    """
    z0 = _extract_required_z(params_s0, "S0")
    z1 = _extract_required_z(params_s1, "S1")
    target_section_s1 = section_s1 or section_s0

    if morph_mode not in {"perimeter", "native", "feature"}:
        raise ValueError(
            "morph_mode must be one of: perimeter, native, feature"
        )

    if morph_mode == "feature":
        _, transform_s0 = _split_section_params(section_s0, params_s0)
        _, transform_s1 = _split_section_params(target_section_s1, params_s1)
        if _transform_is_active(transform_s0) or _transform_is_active(transform_s1):
            raise ValueError(
                "Section-level align/shift/rotate parameters are not supported "
                "with morph_mode='feature'"
            )
        n_feature = 64 if n is None else n
        result, _, _ = _write_feature_morph_yaml(
            section_s0=section_s0,
            section_s1=target_section_s1,
            params_s0=params_s0,
            params_s1=params_s1,
            z0=z0,
            z1=z1,
            output_path=output_path,
            n=n_feature,
            name=name or "section",
            comment=comment,
            solid_weight=solid_weight,
            indent=indent,
            precision=precision,
            dx0=dx0,
            dy0=dy0,
            dx1=dx1,
            dy1=dy1,
            twist0_deg=twist0_deg,
            twist1_deg=twist1_deg,
            auto_align=auto_align,
        )
        return result

    geometry_s0, geometry_s1, _, _ = _build_transformed_section_pair(
        section_s0=section_s0,
        section_s1=target_section_s1,
        params_s0=params_s0,
        params_s1=params_s1,
        auto_align=auto_align,
        morph_mode=morph_mode,
    )

    return sp_to_csf_yaml(
        geometry_s0=geometry_s0,
        geometry_s1=geometry_s1,
        z0=z0,
        z1=z1,
        output_path=output_path,
        n=n,
        name=name,
        comment=comment,
        solid_weight=solid_weight,
        void_weight=void_weight,
        indent=indent,
        precision=precision,
        dx0=dx0,
        dy0=dy0,
        dx1=dx1,
        dy1=dy1,
        twist0_deg=twist0_deg,
        twist1_deg=twist1_deg,
        auto_align=auto_align,
        morph_mode=morph_mode,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _generate_actions_yaml(
    output_path: Path,
    z0: float,
    z1: float,
    title: str = "CSF Tower",
    precision: int = 6,
) -> Path:
    """Generate a default CSF actions YAML file for quick exploration.

    Includes:
    - plot_volume_3d        — 3D ruled volume visualization
    - plot_properties       — continuous property variation along z
    - plot_section_2d       — 2D cross-section at 3 stations (base, mid, top)
    - section_selected_analysis — full property table at mid-height
    """
    z_mid = round((z0 + z1) / 2, precision)

    content = f"""# CSF actions file — generated by sp_to_csf.py
# Run with: csf-actions <geometry.yaml> <this_file>

CSF_ACTIONS:
  stations:
    station_mid:
      - {_fmt_float(z_mid, precision)}
    station_edge:
      - {_fmt_float(z0, precision)}
      - {_fmt_float(z1, precision)}
    station_3pt:
      - {_fmt_float(z0, precision)}
      - {_fmt_float(z_mid, precision)}
      - {_fmt_float(z1, precision)}

  actions:
    # 3D ruled volume visualization — shows the full geometry interpolation
    - plot_volume_3d:
        params:
          line_percent: 100.0
          title: "{title}"

    # Continuous property variation along z
    - plot_properties:
        properties: [A, Ix, Iy, Ip, I1, I2]
        params:
          num_points: 80

    # 2D cross-section outlines at base, mid, and top
    - plot_section_2d:
        stations:
          - station_3pt
        show_ids: False
        show_vertex_ids: False
    # Full section property table at mid-height
    - section_selected_analysis:
        stations:
          - station_3pt
        properties: [A, Cx, Cy, Ix, Iy, Ip, I1, I2, rx, ry, Wx, Wy,J_s_vroark, J_s_vroark_fidelity]
"""
    output_path.write_text(content, encoding="utf-8")
    return output_path


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="sp_to_csf",
        description=(
            "Convert one or two sectionproperties sections to a CSF YAML file.\n"
            "Supports prismatic, tapered, morphing, offset, twist, and\n"
            "explicit section-level align/shift/rotate pre-processing.\n"
            "Centroids are auto-aligned by default when using --morph.\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
        allow_abbrev=False,
        epilog=(
            "Examples:\n\n"
            "  # Morph RHS -> CHS (wind tower), centroids auto-aligned\n"
            "  python sp_to_csf.py rectangular_hollow_section \\\n"
            "    --morph circular_hollow_section \\\n"
            "    --s0 d=4000,b=4000,t=30,r_out=300,n_r=16,z=0 \\\n"
            "    --s1 d=2500,t=18,n=48,z=70000 \\\n"
            "    --n=96 --name=tower --out=wind_tower.yaml\n\n"
            "  # Morph with twist\n"
            "  python sp_to_csf.py rectangular_hollow_section \\\n"
            "    --morph circular_hollow_section \\\n"
            "    --s0 d=200,b=150,t=10,r_out=15,n_r=8,z=0 \\\n"
            "    --s1 d=180,t=8,n=32,z=10 --twist1=45\n\n"
            "  # Disable auto-align, manual offset\n"
            "  python sp_to_csf.py rectangular_hollow_section \\\n"
            "    --morph circular_hollow_section \\\n"
            "    --s0 d=200,b=200,t=10,r_out=20,n_r=8,z=0 \\\n"
            "    --s1 d=150,t=8,n=32,z=10 \\\n"
            "    --no-align --dx1=25 --dy1=25\n"
        ),
    )
    parser.add_argument("section",
                        help="Section name for S0")
    parser.add_argument("--morph", type=str, default=None,
                        help="Section name for S1 if different from S0")
    parser.add_argument("--s0", type=str, required=True,
                        help="S0 params: key=value,... Must include z=<float>")
    parser.add_argument("--s1", type=str, required=True,
                        help="S1 params: key=value,... Must include z=<float>")
    parser.add_argument("--n", type=int, default=None,
                        help="Vertices per ring for morph mode (default: native SP vertices when omitted)")
    parser.add_argument("--morph-mode", choices=("perimeter", "native", "feature"),
                        default="perimeter",
                        help=(
                            "Morphing strategy. 'perimeter' keeps the current global "
                            "arc-length resampling; 'native' preserves the native SP "
                            "vertex order; 'feature' uses supported feature-block maps."
                        ))
    parser.add_argument("--name", type=str, default="section",
                        help="Polygon base name (default: section)")
    parser.add_argument("--out", type=str, default=None,
                        help="Output YAML path")
    parser.add_argument("--no-align", dest="no_align", action="store_true",
                        help="Disable centroid auto-alignment")
    parser.add_argument("--dx0", type=float, default=None,
                        help="Explicit X offset for S0 (overrides auto-align)")
    parser.add_argument("--dy0", type=float, default=None,
                        help="Explicit Y offset for S0 (overrides auto-align)")
    parser.add_argument("--dx1", type=float, default=None,
                        help="Explicit X offset for S1 (overrides auto-align)")
    parser.add_argument("--dy1", type=float, default=None,
                        help="Explicit Y offset for S1 (overrides auto-align)")
    parser.add_argument("--twist0", type=float, default=0.0,
                        help="Twist of S0 in degrees CCW (default 0)")
    parser.add_argument("--twist1", type=float, default=0.0,
                        help="Twist of S1 in degrees CCW (default 0)")
    parser.add_argument("--precision", type=int, default=6,
                        help="Decimal precision for coordinates (default 6)")
    parser.add_argument("--gen-actions", dest="gen_actions", action="store_true",
                        help="Also generate a default actions YAML alongside the geometry file")

    args = parser.parse_args()

    try:
        params_s0 = _parse_section_params(args.s0)
        params_s1 = _parse_section_params(args.s1)
    except ValueError as e:
        print(f"[ERROR] {e}")
        return 1

    try:
        z0 = _extract_required_z(params_s0, "S0")
        z1 = _extract_required_z(params_s1, "S1")
    except ValueError as e:
        print(f"[ERROR] {e}")
        return 1

    section_s0 = args.section
    section_s1 = args.morph or args.section

    try:
        geom_s0, geom_s1, transform_s0, transform_s1 = _build_transformed_section_pair(
            section_s0=section_s0,
            section_s1=section_s1,
            params_s0=params_s0,
            params_s1=params_s1,
            auto_align=not args.no_align,
            morph_mode=args.morph_mode,
        )
    except (ValueError, TypeError) as e:
        print(f"[ERROR] {e}")
        return 1

    out_path = args.out or f"{section_s0}_to_{section_s1}.yaml"

    # n=None means native SP vertices (tapered/prismatic mode)
    # For morph mode, default to 64 if not specified
    n_eff = args.n if args.n is not None else (64 if args.morph else None)
    mode_label = "morph" if args.morph else "tapered/prismatic"
    resample_label = f"n={n_eff}" if n_eff is not None else "native SP vertices"

    comment = (
        f"{section_s0}({args.s0}) -> {section_s1}({args.s1}) "
        f"{resample_label} morph_mode={args.morph_mode} "
        f"twist0={args.twist0} twist1={args.twist1}"
    )

    if args.morph_mode == "feature":
        if not args.morph:
            print("[ERROR] --morph-mode feature requires --morph")
            return 1
        try:
            result, (cx0, cy0), (cx1, cy1) = _write_feature_morph_yaml(
                section_s0=section_s0,
                section_s1=section_s1,
                params_s0=params_s0,
                params_s1=params_s1,
                z0=z0,
                z1=z1,
                output_path=out_path,
                n=n_eff,
                name=args.name,
                comment=comment,
                solid_weight=1.0,
                indent=8,
                precision=args.precision,
                dx0=args.dx0,
                dy0=args.dy0,
                dx1=args.dx1,
                dy1=args.dy1,
                twist0_deg=args.twist0,
                twist1_deg=args.twist1,
                auto_align=not args.no_align,
            )
        except ValueError as e:
            print(f"[ERROR] {e}")
            return 1

        print(f"Centroid S0 (feature frame): ({cx0:.3f}, {cy0:.3f})")
        print(f"Centroid S1 (feature frame): ({cx1:.3f}, {cy1:.3f})")
        if not args.no_align:
            print("Auto-align: ON — both feature centroids mapped to origin in CSF frame")
        print(
            f"Written: {result}  [feature morph, z={z0}→{z1}, "
            f"twist={args.twist0}°→{args.twist1}°]"
        )

        if args.gen_actions:
            actions_path = Path(out_path).with_suffix("").with_name(
                Path(out_path).stem + "_actions.yaml"
            )
            title = f"{section_s0} → {section_s1}"
            _generate_actions_yaml(actions_path, z0=z0, z1=z1,
                                   title=title, precision=args.precision)
            print(f"Written: {actions_path}  [actions]")
            print("\nRun with:")
            print(f"  csf-actions {out_path} {actions_path}")
        return 0

    try:
        result = sp_to_csf_yaml(
            geom_s0, geom_s1,
            z0=z0, z1=z1,
            output_path=out_path,
            n=n_eff,
            name=args.name,
            comment=comment,
            dx0=args.dx0, dy0=args.dy0,
            dx1=args.dx1, dy1=args.dy1,
            twist0_deg=args.twist0,
            twist1_deg=args.twist1,
            auto_align=not args.no_align,
            precision=args.precision,
            morph_mode=args.morph_mode,
        )
    except ValueError as e:
        print(f"[ERROR] {e}")
        return 1

    # Report centroid info
    cx0, cy0 = _geometry_centroid(geom_s0)
    cx1, cy1 = _geometry_centroid(geom_s1)
    print(f"Centroid S0 (SP frame): ({cx0:.3f}, {cy0:.3f})")
    print(f"Centroid S1 (SP frame): ({cx1:.3f}, {cy1:.3f})")
    if _transform_is_active(transform_s0) or _transform_is_active(transform_s1):
        print("Section-level SP transforms: ON")
    if not args.no_align:
        print(f"Auto-align: ON — both centroids mapped to origin in CSF frame")
    mode = f"{mode_label}/{args.morph_mode}"
    print(f"Written: {result}  [{mode}, z={z0}→{z1}, twist={args.twist0}°→{args.twist1}°]")

    # Generate companion actions YAML if requested
    if args.gen_actions:
        actions_path = Path(out_path).with_suffix("").with_name(
            Path(out_path).stem + "_actions.yaml"
        )
        title = f"{section_s0} → {section_s1}" if args.morph else section_s0
        _generate_actions_yaml(actions_path, z0=z0, z1=z1,
                               title=title, precision=args.precision)
        print(f"Written: {actions_path}  [actions]")
        print(f"\nRun with:")
        print(f"  csf-actions {out_path} {actions_path}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
