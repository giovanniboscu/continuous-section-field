#!/usr/bin/env bash
# make_geometry.sh
#
# Parametric runner for make_csf_blade_yaml.py
# - All inputs are configured in one place
# - Fails fast on errors
#
# Usage:
#   chmod +x make_geometry.sh
#   ./make_geometry.sh
#
# Optional overrides:
#   S0_TWIST=13.0 S1_TWIST=0.0 OUT_YAML=out/geometry.yaml ./make_geometry.sh

set -euo pipefail

# -------------------------
# 1) Paths
# -------------------------
PYTHON_BIN="${PYTHON_BIN:-python3}"
SCRIPT_PY="${SCRIPT_PY:-make_csf_blade_yaml.py}"

AIRFOIL_S0="${AIRFOIL_S0:-Cylinder1_coords.txt}"
AIRFOIL_S1="${AIRFOIL_S1:-NACA64_A17_coords.txt}"

OUT_YAML="${OUT_YAML:-geometry.yaml}"

# -------------------------
# 2) Stations (z)
# -------------------------
S0_Z="${S0_Z:-0.0}"
S1_Z="${S1_Z:-61.5}"

# -------------------------
# 3) Geometry parameters
# -------------------------
S0_CHORD="${S0_CHORD:-3.542}"
S1_CHORD="${S1_CHORD:-1.419}"

# Twist in degrees (CCW positive in (x,y) plane as implemented in the Python script)
S0_TWIST="${S0_TWIST:-23.308}"
S1_TWIST="${S1_TWIST:-0.106}"

# Rotation axis location (x/c)
PITCH_AXIS_XC="${PITCH_AXIS_XC:-0.25}"

# -------------------------
# 4) CSF polygon metadata
# -------------------------
POLYGON_BASE="${POLYGON_BASE:-blade_shell}"
WEIGHT="${WEIGHT:-1.0}"

# -------------------------
# 5) Options
# -------------------------
FORCE_CCW="${FORCE_CCW:-1}"        # 1 = enable, 0 = disable
ALIGN_CYCLIC="${ALIGN_CYCLIC:-1}"  # 1 = enable, 0 = disable

# -------------------------
# 6) Pre-checks
# -------------------------
if [[ ! -f "$SCRIPT_PY" ]]; then
  echo "[ERROR] Python script not found: $SCRIPT_PY" >&2
  exit 2
fi

if [[ ! -f "$AIRFOIL_S0" ]]; then
  echo "[ERROR] Airfoil file not found (S0): $AIRFOIL_S0" >&2
  exit 2
fi

if [[ ! -f "$AIRFOIL_S1" ]]; then
  echo "[ERROR] Airfoil file not found (S1): $AIRFOIL_S1" >&2
  exit 2
fi

mkdir -p "$(dirname "$OUT_YAML")" 2>/dev/null || true

# -------------------------
# 7) Build flags
# -------------------------
FLAGS=(
  "--airfoil-s0" "$AIRFOIL_S0"
  "--airfoil-s1" "$AIRFOIL_S1"
  "--out" "$OUT_YAML"
  "--s0-z" "$S0_Z"
  "--s1-z" "$S1_Z"
  "--s0-chord" "$S0_CHORD"
  "--s1-chord" "$S1_CHORD"
  "--s0-twist" "$S0_TWIST"
  "--s1-twist" "$S1_TWIST"
  "--pitch-axis-xc" "$PITCH_AXIS_XC"
  "--polygon-base" "$POLYGON_BASE"
  "--weight" "$WEIGHT"
)

if [[ "$FORCE_CCW" == "1" ]]; then
  FLAGS+=("--force-ccw")
fi

if [[ "$ALIGN_CYCLIC" == "1" ]]; then
  FLAGS+=("--align-cyclic")
fi

# -------------------------
# 8) Run
# -------------------------
echo "[INFO] Running:"
echo "  $PYTHON_BIN $SCRIPT_PY ${FLAGS[*]}"
echo

"$PYTHON_BIN" "$SCRIPT_PY" "${FLAGS[@]}"

echo
echo "[OK] Wrote: $OUT_YAML"

