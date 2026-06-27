# =============================================================================
# create_yaml_tapered_pole_lookup.py
#
# Generates a tapered circular hollow prestressed concrete pole CSF YAML.
#
# Usage:
#   python3 create_yaml_tapered_pole_lookup.py iso tapered_pc_pole_iso_lookup.yaml
#   python3 create_yaml_tapered_pole_lookup.py non-iso tapered_pole_lookup.yaml
#
# Geometry basis:
#   Example 1, self-supporting single pole,
#   PCI/ASCE Guide for the Design of Prestressed Concrete Poles.
#
# Model:
#   - Above-ground cantilever length is used.
#   - S0 is the groundline section.
#   - S1 is the top section.
#   - The embedded portion is not included in this CSF field.
# =============================================================================

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import subprocess
import sys


# =============================================================================
# CASE PARAMETERS
# =============================================================================

# Longitudinal coordinates.
z0 = "0.0"
z1 = "22.86"

# Section centre.
cx = "0.0"
cy = "0.0"

# Tapered onion radii in metres.
#
# S0: groundline section
#     Do = 27.2 in = 0.69088 m -> ro = 0.34544 m
#     Di = 20.3 in = 0.51562 m -> ri = 0.25781 m
#
# S1: top section
#     Do = 11.0 in = 0.27940 m -> ro = 0.13970 m
#     Di = 6.0 in  = 0.15240 m -> ri = 0.07620 m
#
# Four annular concrete participation zones are used outside the central void.
radii0 = "0.25781,0.27972,0.30163,0.32353,0.34544"
radii1 = "0.07620,0.09208,0.10795,0.12383,0.13970"

# Polygon names for annular concrete cells.
layer_names = "core_inner,pcbar_host_layer,cover_inner,cover_outer"

# Base weights.
layer_weights = "1,1,1,1"

# Circular discretization.
N = "256"

# Prestressing strand ring.
n_bars = "16"
bar_diameter = "0.0127"
bar_sides = "16"
bar_host_layer_index = "1"
bar_prefix = "pcbar"
bar_weight = "6.0"
theta0_deg = "0.0"

# Guide radii place the strand polygons inside pcbar_host_layer.
# bar radius = 0.0127 / 2 = 0.00635 m.
bar_guide_radius0 = "0.29"
bar_guide_radius1 = "0.10"

# Lookup-table law references.
law_dir = "laws"

core_law = f'T_lookup("{law_dir}/weight_law_core_inner.dat")'
pcbar_host_law = f'T_lookup("{law_dir}/weight_law_pcbar_host_layer.dat")'
cover_inner_law = f'T_lookup("{law_dir}/weight_law_cover_inner.dat")'
cover_outer_law = f'T_lookup("{law_dir}/weight_law_cover_outer.dat")'
bar_law = f'T_lookup("{law_dir}/weight_law_pcbar.dat")'

core_shear_law = f'T_lookup("{law_dir}/shear_weight_law_core_inner.dat")'
pcbar_host_shear_law = f'T_lookup("{law_dir}/shear_weight_law_pcbar_host_layer.dat")'
cover_inner_shear_law = f'T_lookup("{law_dir}/shear_weight_law_cover_inner.dat")'
cover_outer_shear_law = f'T_lookup("{law_dir}/shear_weight_law_cover_outer.dat")'
bar_shear_law = f'T_lookup("{law_dir}/shear_weight_law_pcbar.dat")'


# =============================================================================
# ARGUMENTS
# =============================================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "model",
        choices=["iso", "non-iso"],
        help="Participation model for shear/torsion laws.",
    )
    parser.add_argument(
        "out_yaml",
        type=Path,
        help="Output YAML file.",
    )
    return parser.parse_args()


# =============================================================================
# GENERATOR RESOLUTION
# =============================================================================

def generator_command() -> list[str]:
    """Return the command prefix for the tapered-pole geometry generator."""
    module_name = "csf.utils.writegeometry_tapered_onion_rebars"

    try:
        module_available = importlib.util.find_spec(module_name) is not None
    except ModuleNotFoundError:
        module_available = False

    if module_available:
        return [sys.executable, "-m", module_name]

    local_script = Path(__file__).with_name("writegeometry_tapered_rebars.py")
    if local_script.exists():
        return [sys.executable, str(local_script)]

    raise RuntimeError(
        "writegeometry_tapered_onion_rebars was not found. "
        "Install CSF with the tapered geometry generator or place "
        "writegeometry_tapered_rebars.py next to this launcher."
    )


# =============================================================================
# MODEL-SPECIFIC LAW ARGUMENTS
# =============================================================================

def shear_law_arguments(model: str) -> tuple[list[str], str, str]:
    if model == "iso":
        return (
            [
                "--layer-shear-law", "0:iso(0.20)",
                "--layer-shear-law", "1:iso(0.20)",
                "--layer-shear-law", "2:iso(0.20)",
                "--layer-shear-law", "3:iso(0.20)",
                "--all-bars-shear-law", "iso(0.30)",
            ],
            "iso(0.20/0.30)",
            "isotropic",
        )

    return (
        [
            "--layer-shear-law", f"0:{core_shear_law}",
            "--layer-shear-law", f"1:{pcbar_host_shear_law}",
            "--layer-shear-law", f"2:{cover_inner_shear_law}",
            "--layer-shear-law", f"3:{cover_outer_shear_law}",
            "--all-bars-shear-law", bar_shear_law,
        ],
        "T_lookup(...), files in ./laws/",
        "non-isotropic",
    )


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    args = parse_args()

    shear_args, shear_summary, participation_scenario = shear_law_arguments(args.model)

    cmd = generator_command() + [
        "--z0", z0,
        "--z1", z1,
        "--cx", cx,
        "--cy", cy,
        "--radii0", radii0,
        "--radii1", radii1,
        "--layer-names", layer_names,
        "--layer-weights", layer_weights,
        "--N", N,
        "--n-bars", n_bars,
        "--bar-guide-radius0", bar_guide_radius0,
        "--bar-guide-radius1", bar_guide_radius1,
        "--bar-host-layer-index", bar_host_layer_index,
        "--bar-diameter", bar_diameter,
        "--bar-sides", bar_sides,
        "--bar-weight", bar_weight,
        "--bar-prefix", bar_prefix,
        "--theta0-deg", theta0_deg,
        "--layer-law", f"0:{core_law}",
        "--layer-law", f"1:{pcbar_host_law}",
        "--layer-law", f"2:{cover_inner_law}",
        "--layer-law", f"3:{cover_outer_law}",
        "--all-bars-law", bar_law,
    ]

    cmd += shear_args
    cmd += ["--out", str(args.out_yaml)]

    subprocess.run(cmd, check=True)

    print("")
    print("Generated:")
    print(f"  - {args.out_yaml}")
    print("")
    print("Geometry summary:")
    print("  L                         = 22.86 m")
    print("  base outer diameter       = 0.69088 m")
    print("  base inner diameter       = 0.51562 m")
    print("  top outer diameter        = 0.27940 m")
    print("  top inner diameter        = 0.15240 m")
    print("  prestressing components   = 16")
    print("  component diameter        = 0.0127 m")
    print("  axial/bending laws        = T_lookup(...), files in ./laws/")
    print(f"  shear/torsion laws        = {shear_summary}")
    print(f"  participation scenario    = {participation_scenario}")


if __name__ == "__main__":
    main()
