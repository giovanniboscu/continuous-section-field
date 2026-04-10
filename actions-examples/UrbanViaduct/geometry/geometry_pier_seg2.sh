#!/usr/bin/env bash
# =============================================================================
# Project : Pier50 — Urban Viaduct, Seismic Zone 2 (NTC2018)
# Segment : 2 — Main shaft  (z = 8 → 38 m)
# =============================================================================
# The shaft carries combined axial load (self-weight + deck) and the dominant
# seismic bending moment (first mode, T ≈ 1.8–2.2 s for a 50 m pier).
# Section tapers linearly — reduces self-weight and optimises stiffness
# distribution.  Wall thickness held ≥ H_clear/15 per EC8-2 §5.4.1.
#
# Geometry
# --------
#   S0  z =  8 m :  5.20 × 3.20 m,  tg = 0.60 m   (must match S1 of Seg 1)
#   S1  z = 38 m :  4.00 × 2.60 m,  tg = 0.45 m
#   Corner radius R = 0.30 m
#
# Reinforcement  (reduced relative to base — outside plastic-hinge zone)
# ---------------
#   Outer row : 40 bars Ø25 mm   cover = 75 mm
#   Inner row : 28 bars Ø20 mm   cover = 75 mm (inner face)
# =============================================================================
set -euo pipefail

PY_MODULE="csf.utils.writegeometry_rio_v2"

z0=8.0
z1=38.0

# --- Base section S0  (z = 8 m) — must match S1 of Segment 1 ---
s0_x=0.0;  s0_y=0.0
s0_dx=5.20; s0_dy=3.20; s0_R=0.30; s0_tg=0.60; s0_t_cell=0.0

# --- Head section S1  (z = 38 m) — must match S0 of Segment 3 ---
s1_x=0.0;  s1_y=0.0
s1_dx=4.00; s1_dy=2.60; s1_R=0.30; s1_tg=0.45; s1_t_cell=0.0

twist_deg=0
N=128
singlepolygon=true

# Outer row : 40 bars Ø25 mm   area = pi/4 * 0.025^2 = 4.91e-4 m²
# Inner row : 28 bars Ø20 mm   area = pi/4 * 0.020^2 = 3.14e-4 m²
# dist_row1_outer = cover(75) + radius(12.5) = 87.5 mm  → 0.088 m
# dist_row2_inner = cover(75) + radius(10)   = 85.0 mm  → 0.085 m
n_bars_row1=40;      n_bars_row2=28
area_bar_row1=0.000491;  area_bar_row2=0.000314
dist_row1_outer=0.088;   dist_row2_inner=0.085
rebar_weight=1.0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
out="${SCRIPT_DIR}/../yaml/pier_seg2.yaml"

python3 -m "$PY_MODULE" \
    --z0            "$z0"            --z1            "$z1"            \
    --s0-t-cell     "$s0_t_cell"     --s0-tg         "$s0_tg"         \
    --s0-x          "$s0_x"          --s0-y          "$s0_y"          \
    --s0-dx         "$s0_dx"         --s0-dy         "$s0_dy"         \
    --s0-R          "$s0_R"                                           \
    --s1-t-cell     "$s1_t_cell"     --s1-tg         "$s1_tg"         \
    --s1-x          "$s1_x"          --s1-y          "$s1_y"          \
    --s1-dx         "$s1_dx"         --s1-dy         "$s1_dy"         \
    --s1-R          "$s1_R"                                           \
    --twist-deg     "$twist_deg"     --N             "$N"             \
    --singlepolygon "$singlepolygon"                                  \
    --n-bars-row1   "$n_bars_row1"   --n-bars-row2   "$n_bars_row2"   \
    --area-bar-row1 "$area_bar_row1" --area-bar-row2 "$area_bar_row2" \
    --dist-row1-outer "$dist_row1_outer"                              \
    --dist-row2-inner "$dist_row2_inner"                              \
    --rebar-weight  "$rebar_weight"  --out           "$out"
