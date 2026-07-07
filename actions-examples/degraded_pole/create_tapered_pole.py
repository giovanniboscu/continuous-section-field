# =============================================================================
# create_yaml_tapered_pole_lookup_sectorgrid_centered_polygonid.py
#
# Generates a tapered circular hollow prestressed-concrete utility pole CSF YAML
# using a concrete sector grid:
#
#   radial levels × angular sectors
#
# Polygon naming convention:
#   <sector>_<level>_<type>
#
# where type is:
#   C  = concrete
#   CH = concrete host level for bars
#   S  = steel bar
#
# Sector 0 starts from 12 o'clock when theta0_deg = 90.0 and proceeds
# counter-clockwise.
# =============================================================================

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


# =============================================================================
# STIFFNESS SCALES
# =============================================================================

E0_CONCRETE = 35.0e9
E0_PCBAR = 6.0 * E0_CONCRETE

G0_CONCRETE = 14.0e9
G0_PCBAR = 84.0e9


# =============================================================================
# CASE PARAMETERS
# =============================================================================

z0 = "0.0"
z1 = "15.0"

cx = "0.0"
cy = "0.0"

# Four annular concrete levels outside the central void.
radii0 = "0.1100,0.1325,0.1550,0.1775,0.2000"
radii1 = "0.0500,0.0650,0.0800,0.0950,0.1100"

layer_weights = ",".join([f"{E0_CONCRETE:.12e}"] * 4)

# Sector grid.
N = "16"
arc_steps = "16"

# Prestressing strand ring.
n_bars = "16"
bar_diameter = "0.0100"
bar_sides = "16"
bar_host_layer_index = "1"
bar_weight = f"{E0_PCBAR:.12e}"

# Sector 0 starts from 12 o'clock and proceeds counter-clockwise.
theta0_deg = "90.0"

# The generator uses half-sector offset by default.
# With N = 16, the offset is 11.25 degrees.
# It can be made explicit by adding:
#   "--bar-center-offset-deg", "11.25"
bar_guide_radius0 = "0.1440"
bar_guide_radius1 = "0.0720"

law_dir = "laws"


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
    return [
        sys.executable,
        "-m",
        "csf.utils.writegeometry_tappered_pole",
    ]

# =============================================================================
# POLYGON ID AND LAW ARGUMENTS
# =============================================================================

def concrete_polygon_id(sector_idx: int, layer_idx: int, host_layer_idx: int) -> str:
    level = layer_idx + 1
    polygon_type = "CH" if layer_idx == host_layer_idx else "C"
    return f"{sector_idx}_{level}_{polygon_type}"


def bar_polygon_id(bar_idx: int, host_layer_idx: int) -> str:
    level = host_layer_idx + 1
    return f"{bar_idx}_{level}_S"


def polygon_law_arguments(model: str) -> tuple[list[str], str, str]:
    args: list[str] = []
    n_sectors = int(N)
    n_layers = len([part for part in radii0.split(",") if part.strip()]) - 1
    n_steel = int(n_bars)
    host_layer_idx = int(bar_host_layer_index)

    for layer_idx in range(n_layers):
        for sector_idx in range(n_sectors):
            polygon_id = concrete_polygon_id(sector_idx, layer_idx, host_layer_idx)
            args += [
                "--sector-law",
                f'{layer_idx}:{sector_idx}:w0*T_lookup("{law_dir}/weight_law_{polygon_id}.dat")',
            ]
            if model == "iso":
                shear_law = "iso(0.20)"
            else:
                shear_law = f'{G0_CONCRETE:.12e}*T_lookup("{law_dir}/shear_weight_law_{polygon_id}.dat")'
            args += ["--sector-shear-law", f"{layer_idx}:{sector_idx}:{shear_law}"]

    for bar_idx in range(n_steel):
        polygon_id = bar_polygon_id(bar_idx, host_layer_idx)
        args += [
            "--bar-law",
            f'{bar_idx}:w0*T_lookup("{law_dir}/weight_law_{polygon_id}.dat")',
        ]
        if model == "iso":
            shear_law = "iso(0.30)"
        else:
            shear_law = f'{G0_PCBAR:.12e}*T_lookup("{law_dir}/shear_weight_law_{polygon_id}.dat")'
        args += ["--bar-shear-law", f"{bar_idx}:{shear_law}"]

    if model == "iso":
        return args, "per-polygon iso(0.20/0.30)", "isotropic"

    return args, "per-polygon G0*T_lookup(...), files in ./laws/", "non-isotropic"


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    args = parse_args()
    law_args, shear_summary, participation_scenario = polygon_law_arguments(args.model)

    cmd = generator_command() + [
        "--z0", z0,
        "--z1", z1,
        "--cx", cx,
        "--cy", cy,
        "--radii0", radii0,
        "--radii1", radii1,
        "--layer-weights", layer_weights,
        "--N", N,
        "--arc-steps", arc_steps,
        "--n-bars", n_bars,
        "--bar-guide-radius0", bar_guide_radius0,
        "--bar-guide-radius1", bar_guide_radius1,
        "--bar-host-layer-index", bar_host_layer_index,
        "--bar-diameter", bar_diameter,
        "--bar-sides", bar_sides,
        "--bar-weight", bar_weight,
        "--theta0-deg", theta0_deg,
    ]

    cmd += law_args
    cmd += ["--out", str(args.out_yaml)]

    subprocess.run(cmd, check=True)

    print("")
    print("Generated:")
    print(f"  - {args.out_yaml}")
    print("")
    print("Geometry summary:")
    print("  L                         = 15.0 m")
    print("  radial concrete levels    = 4")
    print("  angular sectors           = 16")
    print("  concrete polygons/station = 64")
    print("  prestressing components   = 16")
    print("  polygon id format         = <sector>_<level>_<type>")
    print("  sector 0                  = 12 o'clock, counter-clockwise")
    print("  bar centre offset         = half sector")
    print("  base outer diameter       = 0.400 m")
    print("  base inner diameter       = 0.220 m")
    print("  top outer diameter        = 0.220 m")
    print("  top inner diameter        = 0.100 m")
    print("  component diameter        = 0.0100 m")
    print("  axial/bending laws        = per-polygon w0*T_lookup(...), files in ./laws/")
    print(f"  shear/torsion laws        = {shear_summary}")
    print(f"  participation scenario    = {participation_scenario}")


if __name__ == "__main__":
    main()
