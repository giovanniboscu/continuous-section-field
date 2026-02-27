#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate a CSF geometry YAML from a given base polygon (S0),
creating S1 by rotating S0 by a user-defined angle.

- Input polygon is hard-coded from user data.
- Output format matches the requested CSF YAML structure.
- Comments are in English.
"""

import math
from typing import List, Tuple

Point = Tuple[float, float]


# ============================================================
# USER PARAMETERS (easy to read / edit)
# ============================================================

# Rotation from S0 to S1 [rad]
# Example: -pi/2 = clockwise 90 deg
ROTATION_ANGLE_RAD = -math.pi / 4

# Section Z coordinates
Z_S0 = 0.0
Z_S1 = 18.5

# Polygon names in YAML
POLY_NAME_S0 = "start"
POLY_NAME_S1 = "end"

# Polygon weights
WEIGHT_S0 = 1.0
WEIGHT_S1 = 1.0

# Output file path
OUTPUT_YAML_PATH = "geometry.yaml"

# Decimal formatting for coordinates
COORD_DECIMALS = 6


# ============================================================
# INPUT DATA (S0 polygon vertices provided by user)
# ============================================================

S0_VERTICES: List[Point] = [
    ( 0.933333, -0.033333 ),
    ( 0.933333,  0.033333 ),
    ( 0.400000,  0.300000 ),
    ( 0.311111,  0.922222 ),
    ( 0.244444,  0.944444 ),
    (-0.200000,  0.500000 ),
    (-0.733333,  0.588889 ),
    (-0.766667,  0.533333 ),
    (-0.500000,  0.000000 ),
    (-0.766667, -0.533333 ),
    (-0.733333, -0.588889 ),
    (-0.200000, -0.500000 ),
    ( 0.244444, -0.944444 ),
    ( 0.311111, -0.922222 ),
    ( 0.400000, -0.300000 ),
]


# ============================================================
# GEOMETRY FUNCTIONS
# ============================================================

def rotate_point(point: Point, angle_rad: float) -> Point:
    """Rotate one point around origin (0,0). Positive angle = CCW."""
    x, y = point
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    xr = c * x - s * y
    yr = s * x + c * y
    return (xr, yr)


def rotate_polygon(vertices: List[Point], angle_rad: float) -> List[Point]:
    """Rotate all vertices by the same angle."""
    return [rotate_point(p, angle_rad) for p in vertices]


# ============================================================
# YAML WRITER
# ============================================================

def fmt(v: float) -> str:
    """Format float with fixed decimals."""
    return f"{v:.{COORD_DECIMALS}f}"


def build_vertices_yaml(vertices: List[Point], indent: str = " " * 12) -> str:
    """Build YAML lines for vertex list."""
    lines = []
    for x, y in vertices:
        lines.append(f"{indent}- [ {fmt(x)}, {fmt(y)} ]")
    return "\n".join(lines)


def build_csf_yaml(
    s0_vertices: List[Point],
    s1_vertices: List[Point],
) -> str:
    """Build full CSF YAML content."""
    s0_vertices_yaml = build_vertices_yaml(s0_vertices, indent=" " * 12)
    s1_vertices_yaml = build_vertices_yaml(s1_vertices, indent=" " * 12)

    yaml_text = f"""# ver 1.0 - untit [m]
CSF:
  sections:
    S0:
      z: {Z_S0}
      polygons:
        {POLY_NAME_S0}:
          weight: {WEIGHT_S0}
          vertices:
{s0_vertices_yaml}

    S1:
      z: {Z_S1}
      polygons:
        {POLY_NAME_S1}:
          weight: {WEIGHT_S1}
          vertices:
{s1_vertices_yaml}
"""
    return yaml_text


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    # S0 = input polygon
    s0 = S0_VERTICES

    # S1 = rotated S0
    s1 = rotate_polygon(s0, ROTATION_ANGLE_RAD)

    # Build YAML text
    yaml_text = build_csf_yaml(s0, s1)

    # Save file
    with open(OUTPUT_YAML_PATH, "w", encoding="utf-8") as f:
        f.write(yaml_text)

    # Print to terminal too
    print(yaml_text)
    print(f"Written: {OUTPUT_YAML_PATH}")


if __name__ == "__main__":
    main()

