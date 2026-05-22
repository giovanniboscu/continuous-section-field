#!/usr/bin/env bash
# =============================================================================
# create_yaml_nrel.sh
#
# Generates:
#   - NREL-5-MW.yaml
#   - NREL-5-MW-degr.yaml
#
# The degraded model differs only in weight_laws.
# =============================================================================

set -euo pipefail

# =============================================================================
# PARAMETERS
# =============================================================================

z0="0.0"
z1="87.6"

# Base section
s0_dx="6.0"
s0_dy="6.0"
s0_R="3.0"
s0_tg="0.0351"

# Top section
s1_dx="3.87"
s1_dy="3.87"
s1_R="1.935"
s1_tg="0.0247"

# Discretization
N="2048"
twist_deg="0"

# Output files
out_normal="NREL-5-MW.yaml"
out_degr="NREL-5-MW-degr.yaml"

# =============================================================================
# GENERATE BASE GEOMETRY
# =============================================================================

python3 -m csf.utils.writegeometry_rio_v2 \
    --z0 "$z0" \
    --z1 "$z1" \
    --s0-x 0.0 \
    --s0-y 0.0 \
    --s0-dx "$s0_dx" \
    --s0-dy "$s0_dy" \
    --s0-R "$s0_R" \
    --s0-tg "$s0_tg" \
    --s0-t-cell 0.0 \
    --s1-x 0.0 \
    --s1-y 0.0 \
    --s1-dx "$s1_dx" \
    --s1-dy "$s1_dy" \
    --s1-R "$s1_R" \
    --s1-tg "$s1_tg" \
    --s1-t-cell 0.0 \
    --twist-deg "$twist_deg" \
    --N "$N" \
    --singlepolygon True \
    --n-bars-row1 0 \
    --n-bars-row2 0 \
    --area-bar-row1 1 \
    --area-bar-row2 1 \
    --dist-row1-outer 1 \
    --dist-row2-inner 1 \
    --rebar-weight 1 \
    --out "$out_normal"

# =============================================================================
# NORMAL YAML
# =============================================================================

cat >> "$out_normal" <<'YAML_EOF'

  weight_laws:
    - 'cell_base@cell,cell_head@cell: 210000000000'

  shear_weight_laws:
    - 'cell_base@cell,cell_head@cell:iso(0.3)'

YAML_EOF

# =============================================================================
# DEGRADED YAML
# =============================================================================

cp "$out_normal" "$out_degr"

python3 - <<'PY'
from pathlib import Path

path = Path("NREL-5-MW-degr.yaml")

text = path.read_text()

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

text = text.replace(old, new)

path.write_text(text)

print("OK -- degraded YAML generated")
PY

echo ""
echo "Generated:"
echo "  - $out_normal"
echo "  - $out_degr"
mkdir -p out
mkdir -p out-degr

echo "created out,out-degr dirs"
