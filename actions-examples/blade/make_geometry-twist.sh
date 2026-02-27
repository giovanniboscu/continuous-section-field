#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# User parameters (edit here)
# -----------------------------
S1_TWIST_DEG=45

# -----------------------------
# Run
# -----------------------------
python3 make_csf_blade_yaml.py \
  --airfoil-s0 Cylinder1_coords.txt \
  --airfoil-s1 NACA64_A17_coords.txt \
  --s1-twist "${S1_TWIST_DEG}" \
  --out geometry.yaml \
  --force-ccw
