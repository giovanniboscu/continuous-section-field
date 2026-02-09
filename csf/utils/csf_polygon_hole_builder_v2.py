"""
csf_polygon_hole_builder_v1.py

Generates a CSF geometry YAML with two stations (S0, S1) for a ring-like shape.

Two modeling modes
------------------
SINGLE_POLE = False
    Writes ONE polygon per station using a single flattened vertex stream that encodes
    two closed loops:
      - outer loop: CCW
      - inner loop: CW  (hole encoding via signed-area convention)
    Each loop is explicitly closed by repeating its first vertex.

SINGLE_POLE = True
    Writes TWO polygons per station:
      - outer polygon with weight = 1.0
      - inner polygon (void) with weight = 0.0
    Both polygons are emitted CCW (CSF precondition).

YAML format emitted
-------------------
CSF:
  sections:
    S0:
      z: <z0>
      polygons:
        <outer_name>: ...
        [<void_name>: ...]   # only if SINGLE_POLE=True
    S1:
      z: <z1>
      polygons:
        <outer_name>: ...
        [<void_name>: ...]   # only if SINGLE_POLE=True
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import List


# -----------------------------------------------------------------------------
# Geometry primitives
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class Pt:
    x: float
    y: float


def make_tagged_name(base: str = "poly") -> str:
    """Return a polygon name tagged for the thin-wall path (name only)."""
    return f"{base}"


def make_void_name(base: str = "void") -> str:
    """Return a conventional name for the void polygon."""
    return base


def regular_ngon_on_bbox_ccw(center: Pt, lx: float, ly: float, n_sides: int, start_angle: float) -> List[Pt]:
    """
    Build a CCW n-gon sampled on an axis-aligned ellipse that fits the given bounding box.

    The loop is returned *not closed* (no repeated first point).
    """
    if n_sides <= 3:
        raise ValueError("n_sides must be > 3")
    if lx <= 0.0 or ly <= 0.0:
        raise ValueError("lx and ly must be > 0")

    a = 0.5 * lx
    b = 0.5 * ly
    cx, cy = center.x, center.y

    pts: List[Pt] = []
    dtheta = 2.0 * math.pi / n_sides
    for k in range(n_sides):
        theta = start_angle + k * dtheta
        pts.append(Pt(cx + a * math.cos(theta), cy + b * math.sin(theta)))
    return pts


def reverse_loop(loop: List[Pt]) -> List[Pt]:
    """
    Reverse loop traversal while keeping the same start vertex.

    If loop = [p0, p1, ..., p_{n-1}] (CCW), the returned loop is:
      [p0, p_{n-1}, ..., p1] (CW)
    """
    if len(loop) < 3:
        raise ValueError("loop must have at least 3 vertices")
    return [loop[0]] + list(reversed(loop[1:]))


def build_multi_loop_stream(inner_loop: List[Pt], outer_loop: List[Pt]) -> List[Pt]:
    """
    Encode two loops into one flattened vertex stream with explicit loop closures.

    Encoding:
      inner + [inner[0]] + outer + [outer[0]]
    """
    if len(inner_loop) < 3 or len(outer_loop) < 3:
        raise ValueError("loops must have at least 3 vertices")
    return inner_loop + [inner_loop[0]] + outer_loop + [outer_loop[0]]


def _fmt_float(x: float) -> str:
    """Deterministic float formatting for YAML."""
    return f"{x:.12g}"


def _write_yaml_with_header(path: str, header_lines: List[str], body_lines: List[str]) -> None:
    """Write YAML by prepending a comment header."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(header_lines) + "\n" + "\n".join(body_lines) + "\n")


def build_yaml_body_singlepoly(
    outer_name: str,
    z0: float,
    z1: float,
    w0: float,
    w1: float,
    stream0: List[Pt],
    stream1: List[Pt],
) -> List[str]:
    """Build YAML body for one polygon per station (multi-loop stream)."""
    lines: List[str] = []
    lines.append("CSF:")
    lines.append("  sections:")
    lines.append("    S0:")
    lines.append(f"      z: {_fmt_float(z0)}")
    lines.append("      polygons:")
    lines.append(f"        {outer_name}:")
    lines.append(f"          weight: {_fmt_float(w0)}")
    lines.append("          vertices:")
    for p in stream0:
        lines.append(f"            - [{_fmt_float(p.x)}, {_fmt_float(p.y)}]")
    lines.append("    S1:")
    lines.append(f"      z: {_fmt_float(z1)}")
    lines.append("      polygons:")
    lines.append(f"        {outer_name}:")
    lines.append(f"          weight: {_fmt_float(w1)}")
    lines.append("          vertices:")
    for p in stream1:
        lines.append(f"            - [{_fmt_float(p.x)}, {_fmt_float(p.y)}]")
    return lines


def build_yaml_body_twopoly(
    outer_name: str,
    void_name: str,
    z0: float,
    z1: float,
    w_outer0: float,
    w_outer1: float,
    outer0: List[Pt],
    outer1: List[Pt],
    void0: List[Pt],
    void1: List[Pt],
) -> List[str]:
    """Build YAML body for two polygons per station: outer (w=1) and void (w=0)."""
    lines: List[str] = []
    lines.append("CSF:")
    lines.append("  sections:")
    lines.append("    S0:")
    lines.append(f"      z: {_fmt_float(z0)}")
    lines.append("      polygons:")
    lines.append(f"        {outer_name}:")
    lines.append(f"          weight: {_fmt_float(w_outer0)}")
    lines.append("          vertices:")
    for p in outer0:
        lines.append(f"            - [{_fmt_float(p.x)}, {_fmt_float(p.y)}]")
    lines.append(f"        {void_name}:")
    lines.append("          weight: 0")
    lines.append("          vertices:")
    for p in void0:
        lines.append(f"            - [{_fmt_float(p.x)}, {_fmt_float(p.y)}]")
    lines.append("    S1:")
    lines.append(f"      z: {_fmt_float(z1)}")
    lines.append("      polygons:")
    lines.append(f"        {outer_name}:")
    lines.append(f"          weight: {_fmt_float(w_outer1)}")
    lines.append("          vertices:")
    for p in outer1:
        lines.append(f"            - [{_fmt_float(p.x)}, {_fmt_float(p.y)}]")
    lines.append(f"        {void_name}:")
    lines.append("          weight: 0")
    lines.append("          vertices:")
    for p in void1:
        lines.append(f"            - [{_fmt_float(p.x)}, {_fmt_float(p.y)}]")
    return lines


# -----------------------------------------------------------------------------
# __main__ variables snippet (edit here)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # If False: one polygon with two loops encoded in one vertex stream (inner loop CW).
    # If True : two polygons (outer + void) with weights (1.0, 0.0), both CCW.
    SINGLE_POLE = True

    # -----------------------------------------------------------------------------
    # Output filenames (CSF)
    # -----------------------------------------------------------------------------
    ACTIONS_YAML_FILENAME = "stell_degradated_model.yaml"
    if SINGLE_POLE:
        GEOMETRY_YAML_FILENAME = "stell_degradated_model_s.yaml"
    else:
        GEOMETRY_YAML_FILENAME = "stell_degradated_model_d.yaml"

    # Station coordinates (two sections)
    z0 = 0.0
    z1 = 85

    # Defaults
    W_DEFAULT = 1.0

    OUTER_POLY_NAME = make_tagged_name(base="poly")
    VOID_POLY_NAME = make_void_name(base="void")

    # Start vertex rule: leftmost point of each loop (angle = pi)
    START_ANGLE = math.pi

    # -----------------------
    # Section S0 parameters
    # -----------------------
    W0 = W_DEFAULT

    INNER_CENTER_0 = Pt(0.0, 0.0)
    INNER_LX_0 = 1.70
    INNER_LY_0 = 1.70
    INNER_N_0  = 128

    OUTER_CENTER_0 = Pt(0.0, 0.0)
    OUTER_LX_0 = 1.80
    OUTER_LY_0 = 1.80
    OUTER_N_0  = 128

    # -----------------------
    # Section S1 parameters
    # -----------------------
    W1 = W_DEFAULT

    INNER_CENTER_1 = Pt(0.0, 0.0)
    INNER_LX_1 = 1.70
    INNER_LY_1 = 1.70
    INNER_N_1  = 128

    OUTER_CENTER_1 = Pt(0.0, 0.0)
    OUTER_LX_1 = 1.80
    OUTER_LY_1 = 1.80
    OUTER_N_1  = 128

    # -----------------------------------------------------------------------------
    # Build loops for S0 and S1
    # -----------------------------------------------------------------------------
    inner0_ccw = regular_ngon_on_bbox_ccw(INNER_CENTER_0, INNER_LX_0, INNER_LY_0, INNER_N_0, start_angle=START_ANGLE)
    outer0_ccw = regular_ngon_on_bbox_ccw(OUTER_CENTER_0, OUTER_LX_0, OUTER_LY_0, OUTER_N_0, start_angle=START_ANGLE)

    inner1_ccw = regular_ngon_on_bbox_ccw(INNER_CENTER_1, INNER_LX_1, INNER_LY_1, INNER_N_1, start_angle=START_ANGLE)
    outer1_ccw = regular_ngon_on_bbox_ccw(OUTER_CENTER_1, OUTER_LX_1, OUTER_LY_1, OUTER_N_1, start_angle=START_ANGLE)

    # -----------------------------------------------------------------------------
    # Select loop orientations based on SINGLE_POLE
    # -----------------------------------------------------------------------------
    if not SINGLE_POLE:     
        # Two-polygon model: keep both CCW.
        print("TWO POL")
        inner0 = inner0_ccw
        outer0 = outer0_ccw
        inner1 = inner1_ccw
        outer1 = outer1_ccw
        
    else:
        print("SINGLE_POL")
        # Single-polygon multi-loop model: inner loop CW encodes a hole.
        inner0 = reverse_loop(inner0_ccw)
        outer0 = outer0_ccw
        inner1 = reverse_loop(inner1_ccw)
        outer1 = outer1_ccw

    # -----------------------------------------------------------------------------
    # Metadata header (records all geometric inputs used)
    # -----------------------------------------------------------------------------
    header: List[str] = []
    header.append("# -----------------------------------------------------------------------------")
    header.append("# GEOMETRY INPUTS (auto-recorded by generator)")
    header.append("# -----------------------------------------------------------------------------")
    header.append("# SCRIPT                : csf_polygon_hole_builder_v1.py")
    header.append(f"# SINGLE_POLE           : {SINGLE_POLE}")
    header.append(f"# GEOMETRY_YAML_FILENAME: {GEOMETRY_YAML_FILENAME}")
    header.append(f"# OUTER_POLY_NAME       : {OUTER_POLY_NAME}")
    header.append(f"# VOID_POLY_NAME        : {VOID_POLY_NAME}")
    header.append(f"# W_DEFAULT             : {W_DEFAULT}")
    header.append(f"# z0                    : {z0}")
    header.append(f"# z1                    : {z1}")
    header.append(f"# START_ANGLE           : {START_ANGLE}")
    header.append(f"# INNER_ORIENTATION     : {'CW' if not SINGLE_POLE else 'CCW'}")
    header.append(f"# OUTER_ORIENTATION     : CCW")
    header.append("#")
    header.append("# S0:")
    header.append(f"#   W0           : {W0}")
    header.append(f"#   INNER_CENTER : ({INNER_CENTER_0.x}, {INNER_CENTER_0.y})")
    header.append(f"#   INNER_LX     : {INNER_LX_0}")
    header.append(f"#   INNER_LY     : {INNER_LY_0}")
    header.append(f"#   INNER_N      : {INNER_N_0}")
    header.append(f"#   OUTER_CENTER : ({OUTER_CENTER_0.x}, {OUTER_CENTER_0.y})")
    header.append(f"#   OUTER_LX     : {OUTER_LX_0}")
    header.append(f"#   OUTER_LY     : {OUTER_LY_0}")
    header.append(f"#   OUTER_N      : {OUTER_N_0}")
    header.append("#")
    header.append("# S1:")
    header.append(f"#   W1           : {W1}")
    header.append(f"#   INNER_CENTER : ({INNER_CENTER_1.x}, {INNER_CENTER_1.y})")
    header.append(f"#   INNER_LX     : {INNER_LX_1}")
    header.append(f"#   INNER_LY     : {INNER_LY_1}")
    header.append(f"#   INNER_N      : {INNER_N_1}")
    header.append(f"#   OUTER_CENTER : ({OUTER_CENTER_1.x}, {OUTER_CENTER_1.y})")
    header.append(f"#   OUTER_LX     : {OUTER_LX_1}")
    header.append(f"#   OUTER_LY     : {OUTER_LY_1}")
    header.append(f"#   OUTER_N      : {OUTER_N_1}")
    header.append("# -----------------------------------------------------------------------------")

    # -----------------------------------------------------------------------------
    # Build YAML body according to SINGLE_POLE and write file
    # -----------------------------------------------------------------------------
    if not SINGLE_POLE:
        body = build_yaml_body_twopoly(
            outer_name=OUTER_POLY_NAME,
            void_name=VOID_POLY_NAME,
            z0=z0,
            z1=z1,
            w_outer0=W0,
            w_outer1=W1,
            outer0=outer0,
            outer1=outer1,
            void0=inner0,
            void1=inner1,
        )
    else:
        stream0 = build_multi_loop_stream(inner0, outer0)
        stream1 = build_multi_loop_stream(inner1, outer1)
        body = build_yaml_body_singlepoly(
            outer_name=OUTER_POLY_NAME,
            z0=z0,
            z1=z1,
            w0=W0,
            w1=W1,
            stream0=stream0,
            stream1=stream1,
        )

    _write_yaml_with_header(GEOMETRY_YAML_FILENAME, header, body)

    print(f"Wrote CSF geometry YAML: {GEOMETRY_YAML_FILENAME}")

