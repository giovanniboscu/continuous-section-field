#!/usr/bin/env python3
# =============================================================================
# create_yaml_tapered_pole_lookup.py
#
# Generates:
#   - tapered_pole_lookup.yaml
#
# Purpose:
#   Build a CSF input case for a tapered circular hollow prestressed concrete
#   pole idealized as concentric regions and prestressing steel components,
#   with independent participation laws for axial/bending and shear/torsion.
#
# Modelling rule for this version:
#   - No analytical degradation law is written in the YAML.
#   - Every axial/bending participation law is referenced through T_lookup(...).
#   - Every shear/torsion participation law is referenced through T_lookup(...).
#   - Axial/bending and shear/torsion participation fields are independent.
#   - The case therefore defines a non-isotropic participation scenario.
#   - Plasticity is not introduced.
#   - Lookup-table contents are external model data, kept outside the YAML.
#
# Literature basis:
#   - The structural family is a tapered prestressed circular hollow-cored pole.
#   - The 16 equally spaced 1/2 in strand ring follows the example arrangement
#     shown in the PCI/ASCE Guide for the Design of Prestressed Concrete Poles.
#
# Modelling scope:
#   - The base and top diameters are CSF case parameters, not copied from a
#     single table in the guide.
#   - The concentric split is a CSF zonal idealization of the annular wall.
#   - The lookup-table contents define the prescribed longitudinal participation
#     fields for this case.
# =============================================================================
from __future__ import annotations
import importlib.util
from pathlib import Path
import subprocess
import sys
# =============================================================================
# CASE PARAMETERS
# =============================================================================
# Longitudinal coordinates.
z0 = "0.0"
z1 = "20.0"
# Section centre.
cx = "0.0"
cy = "0.0"
# Tapered onion radii in metres.
# S0: base section, D_ext = 0.600 m, D_inner = 0.400 m.
# S1: top section,  D_ext = 0.440 m, D_inner = 0.280 m.
# The wall is split into four annular concrete participation zones outside the
# central hollow core.
radii0 = "0.200,0.225,0.250,0.275,0.300"
radii1 = "0.140,0.160,0.180,0.200,0.220"
# Polygon names for annular concrete cells.
layer_names = "core_inner,pcbar_host_layer,cover_inner,cover_outer"
# Base weights. Concrete zones are normalized to 1.0. PC strands are assigned a
# separate relative stiffness through bar_weight below.
layer_weights = "1,1,1,1"
# Circular discretization.
N = "256"
# Prestressing strand ring.
# 1/2 in = 0.0127 m. Sixteen strands are used as the documented example count.
n_bars = "16"
bar_diameter = "0.0127"
bar_sides = "16"
bar_host_layer_index = "1"
bar_prefix = "pcbar"
bar_weight = "6.0"
theta0_deg = "0.0"
# Guide radii place the strand polygons inside the pcbar_host_layer at both ends.
bar_guide_radius0 = "0.24365"
bar_guide_radius1 = "0.17365"
# Lookup-table law references.
# The YAML receives T_lookup(...) only. The law data are stored in ./laws/.
law_dir = "laws"
core_law = f'T_lookup("{law_dir}/weight_law_core_inner.dat")'
pcbar_host_law = f'T_lookup("{law_dir}/weight_law_pcbar_host_layer.dat")'
cover_inner_law = f'T_lookup("{law_dir}/weight_law_cover_inner.dat")'
cover_outer_law = f'T_lookup("{law_dir}/weight_law_cover_outer.dat")'
bar_law = f'T_lookup("{law_dir}/weight_law_pcbar.dat")'
# Shear/torsion lookup-table law references.
# These laws are independent from the axial/bending participation laws.
# The case does not use iso(<nu>) for shear/torsion participation.
core_shear_law = f'T_lookup("{law_dir}/shear_weight_law_core_inner.dat")'
pcbar_host_shear_law = f'T_lookup("{law_dir}/shear_weight_law_pcbar_host_layer.dat")'
cover_inner_shear_law = f'T_lookup("{law_dir}/shear_weight_law_cover_inner.dat")'
cover_outer_shear_law = f'T_lookup("{law_dir}/shear_weight_law_cover_outer.dat")'
bar_shear_law = f'T_lookup("{law_dir}/shear_weight_law_pcbar.dat")'
# Output.
out_yaml = Path("tapered_pole_lookup.yaml")
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
# MAIN
# =============================================================================
def main() -> None:
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
        "--layer-shear-law", f"0:{core_shear_law}",
        "--layer-shear-law", f"1:{pcbar_host_shear_law}",
        "--layer-shear-law", f"2:{cover_inner_shear_law}",
        "--layer-shear-law", f"3:{cover_outer_shear_law}",
        "--all-bars-shear-law", bar_shear_law,
        "--out", str(out_yaml),
    ]
    subprocess.run(cmd, check=True)
    print("")
    print("Generated:")
    print(f"  - {out_yaml}")
    print("")
    print("Geometry summary:")
    print("  L                         = 20.0 m")
    print("  base outer diameter       = 0.600 m")
    print("  base inner diameter       = 0.400 m")
    print("  top outer diameter        = 0.440 m")
    print("  top inner diameter        = 0.280 m")
    print("  prestressing components   = 16")
    print("  component diameter        = 0.0127 m")
    print("  axial/bending laws        = T_lookup(...), files in ./laws/")
    print("  shear/torsion laws        = T_lookup(...), files in ./laws/")
    print("  participation scenario    = non-isotropic")
if __name__ == "__main__":
    main()
