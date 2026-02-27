#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# User parameters (edit here)
# -----------------------------
AIRFOIL_S0="Cylinder1_coords.txt"
AIRFOIL_S1="NACA64_A17_coords.txt"
OUT_YAML="geometry.yaml"

# Stations (z)
S0_Z=0.0
S1_Z=61.5

# Required geometry params
S0_CHORD=1.0
S1_CHORD=1.0

# Twist angles [deg]
S0_TWIST_DEG=0.0
S1_TWIST_DEG=13.3

# Optional params
PITCH_AXIS_XC=0.25
POLYGON_BASE="blade_section"
WEIGHT=1.0

# -----------------------------
# Run
# -----------------------------
python3 make_csf_blade_yaml.py   --airfoil-s0 "${AIRFOIL_S0}"   --airfoil-s1 "${AIRFOIL_S1}"   --out "${OUT_YAML}"   --s0-z "${S0_Z}"   --s1-z "${S1_Z}"   --s0-chord "${S0_CHORD}"   --s1-chord "${S1_CHORD}"   --s0-twist "${S0_TWIST_DEG}"   --s1-twist "${S1_TWIST_DEG}"   --pitch-axis-xc "${PITCH_AXIS_XC}"   --polygon-base "${POLYGON_BASE}"   --weight "${WEIGHT}"   --force-ccw
