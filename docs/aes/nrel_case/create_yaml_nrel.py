# =============================================================================
# create_yaml_nrel.py
#
# Generates:
#   - NREL-5-MW.yaml
#   - NREL-5-MW-degr.yaml
#
# The degraded model differs only in weight_laws.
# Cross-platform replacement for create_yaml_nrel.sh.
# =============================================================================

from pathlib import Path
import shutil
import subprocess
import sys


# =============================================================================
# PARAMETERS
# =============================================================================

z0 = "0.0"
z1 = "87.6"

# Base section
s0_dx = "6.0"
s0_dy = "6.0"
s0_R = "3.0"
s0_tg = "0.0351"

# Top section
s1_dx = "3.87"
s1_dy = "3.87"
s1_R = "1.935"
s1_tg = "0.0247"

# Discretization
N = "2048"
twist_deg = "0"

# Output files
out_normal = Path("NREL-5-MW.yaml")
out_degr = Path("NREL-5-MW-degr.yaml")


# =============================================================================
# GENERATE BASE GEOMETRY
# =============================================================================

cmd = [
    sys.executable,
    "-m",
    "csf.utils.writegeometry_rio_v2",
    "--z0", z0,
    "--z1", z1,
    "--s0-x", "0.0",
    "--s0-y", "0.0",
    "--s0-dx", s0_dx,
    "--s0-dy", s0_dy,
    "--s0-R", s0_R,
    "--s0-tg", s0_tg,
    "--s0-t-cell", "0.0",
    "--s1-x", "0.0",
    "--s1-y", "0.0",
    "--s1-dx", s1_dx,
    "--s1-dy", s1_dy,
    "--s1-R", s1_R,
    "--s1-tg", s1_tg,
    "--s1-t-cell", "0.0",
    "--twist-deg", twist_deg,
    "--N", N,
    "--singlepolygon", "True",
    "--n-bars-row1", "0",
    "--n-bars-row2", "0",
    "--area-bar-row1", "1",
    "--area-bar-row2", "1",
    "--dist-row1-outer", "1",
    "--dist-row2-inner", "1",
    "--rebar-weight", "1",
    "--out", str(out_normal),
]

subprocess.run(cmd, check=True)


# =============================================================================
# NORMAL YAML
# =============================================================================

normal_laws = """

  weight_laws:
    - 'cell_base@cell,cell_head@cell: 210000000000'

  shear_weight_laws:
    - 'cell_base@cell,cell_head@cell:iso(0.3)'

"""

with out_normal.open("a", encoding="utf-8") as f:
    f.write(normal_laws)


# =============================================================================
# DEGRADED YAML
# =============================================================================

shutil.copyfile(out_normal, out_degr)

text = out_degr.read_text(encoding="utf-8")

old = (
    "  weight_laws:\n"
    "    - 'cell_base@cell,cell_head@cell: 210000000000'"
)

new = (
    "  weight_laws:\n"
    "    - 'cell_base@cell,cell_head@cell: "
    "210000000000*np.maximum(0.84,"
    "1.0-0.10*np.exp(-((z-0.33*L)**2)/(2*(0.03*L)**2))"
    "-0.14*np.exp(-((z-0.67*L)**2)/(2*(0.03*L)**2)))'"
)

if old not in text:
    raise RuntimeError("Expected baseline weight_laws block not found.")

out_degr.write_text(text.replace(old, new), encoding="utf-8")

print("OK -- degraded YAML generated")


# =============================================================================
# OUTPUT DIRECTORIES
# =============================================================================

Path("out").mkdir(exist_ok=True)
Path("out-degr").mkdir(exist_ok=True)


print("")
print("Generated:")
print(f"  - {out_normal}")
print(f"  - {out_degr}")
print("created out,out-degr dirs")
