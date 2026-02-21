"""
csf_crete_cone_v3.py

CSF YAML generator for a tapered circular member with:
  - Outer concrete ring
  - Middle steel ring
  - Inner concrete ring
  - Central hole (void)

This version writes the rings *explicitly* in the YAML so you can SEE them.
Each ring is defined by two polygons:
  (outer boundary, weight +W) and (inner boundary, weight -W)

Radial layout (outside -> inside)
---------------------------------
R0 > R1 > R2 > R3 >= 0

  Outer concrete ring: r in [R1, R0] with weight Wc_outer
  Steel ring         : r in [R2, R1] with weight Ws
  Inner concrete ring: r in [R3, R2] with weight Wc_inner
  Hole (void)        : r in [0,  R3] with weight 0

Transformed-section weights
---------------------------
W = E_material / E_ref (dimensionless)

Typical choice:
  E_ref = E_concrete
  -> concrete weight = 1.0
  -> steel weight    ~ E_steel / E_concrete (e.g., 200/30 ≈ 6.67)

YAML formatting
--------------
- Vertices as:  - [x, y]
- Floats with 6 decimals.

Dependencies
------------
- PyYAML:  python -m pip install pyyaml
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

import yaml

Point = Tuple[float, float]


# =============================================================================
# YAML Dumper: fixed float format + points as [x, y]
# =============================================================================

class CSFDumper(yaml.SafeDumper):
    """Safe dumper with CSF-friendly float/vertex formatting."""
    pass


def _repr_float(dumper: yaml.Dumper, value: float):
    return dumper.represent_scalar("tag:yaml.org,2002:float", f"{value:.6f}")


def _repr_point(dumper: yaml.Dumper, value: tuple):
    return dumper.represent_sequence("tag:yaml.org,2002:seq", list(value), flow_style=True)


CSFDumper.add_representer(float, _repr_float)
CSFDumper.add_representer(tuple, _repr_point)


# =============================================================================
# Geometry
# =============================================================================

def circle_polygon(
    radius_m: float,
    n_sides: int,
    phase_rad: float = 0.0,
    center_xy_m: Point = (0.0, 0.0),
) -> List[tuple]:
    """CCW polygon approximation of a circle. Returns (x, y) tuples."""
    if radius_m < 0.0:
        raise ValueError("radius_m must be >= 0")
    if n_sides < 3:
        raise ValueError("n_sides must be >= 3")

    cx, cy = center_xy_m
    verts: List[tuple] = []
    for i in range(n_sides):
        theta = phase_rad + 2.0 * math.pi * i / n_sides
        x = cx + radius_m * math.cos(theta)
        y = cy + radius_m * math.sin(theta)
        verts.append((x, y))
    return verts


# =============================================================================
# Parameters
# =============================================================================

@dataclass(frozen=True)
class RingRadii4:
    """R0 > R1 > R2 > R3 >= 0"""
    R0: float  # outer radius (external boundary)
    R1: float  # interface: outer concrete -> steel
    R2: float  # interface: steel -> inner concrete
    R3: float  # hole radius (void)

    def validate(self) -> None:
        if not (self.R0 > self.R1 > self.R2 > self.R3 >= 0.0):
            raise ValueError(f"Require R0 > R1 > R2 > R3 >= 0, got {self}")


@dataclass(frozen=True)
class Weights3:
    """Transformed-section weights: W = E/E_ref"""
    Wc_outer: float
    Ws: float
    Wc_inner: float

    def validate(self) -> None:
        if self.Wc_outer < 0.0 or self.Ws < 0.0 or self.Wc_inner < 0.0:
            raise ValueError("Weights must be >= 0")


# =============================================================================
# CSF section builder (EXPLICIT rings)
# =============================================================================

def build_section_explicit_3rings_hole(
    z_m: float,
    radii: RingRadii4,
    weights: Weights3,
    n_sides: int,
    phase_rad: float = 0.0,
) -> Dict:
    """
    Explicit rings (each ring = outer(+W) + inner(-W)):

      Outer concrete ring: [R1, R0]
      Steel ring         : [R2, R1]
      Inner concrete ring: [R3, R2]
      Hole               : [0,  R3] (weight 0) produced by the last minus.
    """
    radii.validate()
    weights.validate()

    Wc0 = float(weights.Wc_outer)
    Ws  = float(weights.Ws)
    Wc2 = float(weights.Wc_inner)

    polys = {
        # Outer concrete ring (R1..R0)
        "conc_outer_plus_R0": {
            "weight": Wc0,
            "vertices": circle_polygon(radii.R0, n_sides, phase_rad=phase_rad),
        },
        "conc_outer_minus_R1": {
            "weight": -Wc0,
            "vertices": circle_polygon(radii.R1, n_sides, phase_rad=phase_rad),
        },

        # Steel ring (R2..R1)
        "steel_plus_R1": {
            "weight": Ws,
            "vertices": circle_polygon(radii.R1, n_sides, phase_rad=phase_rad),
        },
        "steel_minus_R2": {
            "weight": -Ws,
            "vertices": circle_polygon(radii.R2, n_sides, phase_rad=phase_rad),
        },

        # Inner concrete ring (R3..R2)
        "conc_inner_plus_R2": {
            "weight": Wc2,
            "vertices": circle_polygon(radii.R2, n_sides, phase_rad=phase_rad),
        },
        "conc_inner_minus_R3": {
            "weight": -Wc2,
            "vertices": circle_polygon(radii.R3, n_sides, phase_rad=phase_rad),
        },
    }

    return {"z": float(z_m), "polygons": polys}


# =============================================================================
# Main
# =============================================================================

# patch_main.py
import math
import yaml

# NOTE:
# This patch assumes these symbols already exist in your project and are importable:
#   - RingRadii4
#   - Weights3
#   - build_section_explicit_3rings_hole
#   - CSFDumper
#
# If they are in a module (e.g. pole_utils.py), add:
# from pole_utils import RingRadii4, Weights3, build_section_explicit_3rings_hole, CSFDumper


def main() -> None:
    # Output file (change if you want)
    output_yaml_path = "pole_cone_3rings.yaml"

    # Polygon resolution (thin steel ring -> use high values)
    requested_polygon_sides = 100
    minimum_polygon_sides = 4
    polygon_sides = max(requested_polygon_sides, minimum_polygon_sides)

    phase_rad = 0.0

    # Stations
    z_base_m = 0.0
    z_top_m = 120.0

    # -------------------------------------------------------------------------
    # BASE (0 m)  - COHERENT WITH TABLE
    #   Dext = 13.00 m
    #   Concrete ring thickness = 800 mm = 0.80 m  -> R3 = R0 - t_conc
    #   Total steel area = 0.40 m^2 (equivalent thin ring)
    #   Steel ring centered in concrete thickness
    # -------------------------------------------------------------------------
    Dext_base_m = 13.00
    t_conc_base_m = 0.80
    Asteel_tot_base_m2 = 0.40

    R0_base_outer_radius_m = Dext_base_m / 2.0  # 6.50
    R3_base_hole_radius_m = R0_base_outer_radius_m - t_conc_base_m  # 5.70

    Rc_base_m = 0.5 * (R0_base_outer_radius_m + R3_base_hole_radius_m)  # 6.10
    tsteel_base_m = Asteel_tot_base_m2 / (2.0 * math.pi * Rc_base_m)  # ~0.01044 m

    R1_base_conc_to_steel_radius_m = Rc_base_m + 0.5 * tsteel_base_m  # ~6.10522
    R2_base_steel_to_conc_radius_m = Rc_base_m - 0.5 * tsteel_base_m  # ~6.09478

    # Sanity: R0 > R1 > R2 > R3
    if not (R0_base_outer_radius_m > R1_base_conc_to_steel_radius_m > R2_base_steel_to_conc_radius_m > R3_base_hole_radius_m >= 0.0):
        raise ValueError("BASE radii do not satisfy R0 > R1 > R2 > R3 >= 0")

    S0 = RingRadii4(
        R0=R0_base_outer_radius_m,
        R1=R1_base_conc_to_steel_radius_m,
        R2=R2_base_steel_to_conc_radius_m,
        R3=R3_base_hole_radius_m,
    )

    # -------------------------------------------------------------------------
    # TOP (120 m) - COHERENT WITH TABLE
    #   Dext = 4.00 m
    #   Concrete ring thickness = 250 mm = 0.25 m
    #   Total steel area = 0.16 m^2 (equivalent thin ring)
    #   Steel ring centered in concrete thickness
    # -------------------------------------------------------------------------
    Dext_top_m = 4.00
    t_conc_top_m = 0.25
    Asteel_tot_top_m2 = 0.16

    R0_top_outer_radius_m = Dext_top_m / 2.0  # 2.00
    R3_top_hole_radius_m = R0_top_outer_radius_m - t_conc_top_m  # 1.75

    Rc_top_m = 0.5 * (R0_top_outer_radius_m + R3_top_hole_radius_m)  # 1.875
    tsteel_top_m = Asteel_tot_top_m2 / (2.0 * math.pi * Rc_top_m)  # ~0.01359 m

    R1_top_conc_to_steel_radius_m = Rc_top_m + 0.5 * tsteel_top_m  # ~1.88179
    R2_top_steel_to_conc_radius_m = Rc_top_m - 0.5 * tsteel_top_m  # ~1.86820

    # Sanity: R0 > R1 > R2 > R3
    if not (R0_top_outer_radius_m > R1_top_conc_to_steel_radius_m > R2_top_steel_to_conc_radius_m > R3_top_hole_radius_m >= 0.0):
        raise ValueError("TOP radii do not satisfy R0 > R1 > R2 > R3 >= 0")

    S1 = RingRadii4(
        R0=R0_top_outer_radius_m,
        R1=R1_top_conc_to_steel_radius_m,
        R2=R2_top_steel_to_conc_radius_m,
        R3=R3_top_hole_radius_m,
    )

    # -------------------------------------------------------------------------
    # Material weights (E/E_ref)
    # Common choice: E_ref = E_concrete -> concrete = 1.0
    # -------------------------------------------------------------------------
    W_concrete_outer = 1.00
    W_steel = 6.67
    W_concrete_inner = 1.00

    W = Weights3(Wc_outer=W_concrete_outer, Ws=W_steel, Wc_inner=W_concrete_inner)

    # Build sections (EXPLICIT rings)
    sec_S0 = build_section_explicit_3rings_hole(z_base_m, S0, W, polygon_sides, phase_rad=phase_rad)
    sec_S1 = build_section_explicit_3rings_hole(z_top_m, S1, W, polygon_sides, phase_rad=phase_rad)

    data = {"CSF": {"sections": {"S0": sec_S0, "S1": sec_S1}}}

    # Write YAML
    with open(output_yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, Dumper=CSFDumper, sort_keys=False, default_flow_style=False)

    # Sanity prints (names you should SEE in YAML)
    print(f"Wrote: {output_yaml_path}")
    print(f"polygon_sides={polygon_sides}")

    print("S0 polygon keys:")
    for k in data["CSF"]["sections"]["S0"]["polygons"].keys():
        print(f"  - {k}")

    print("S1 polygon keys:")
    for k in data["CSF"]["sections"]["S1"]["polygons"].keys():
        print(f"  - {k}")


if __name__ == "__main__":
    main()
