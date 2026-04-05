#!/usr/bin/env bash
# =============================================================================
# run_csf_to_elastodyn.sh
# Complete CSF -> BModes -> ElastoDyn tower pipeline launcher.
#
# Usage:
#   chmod +x run_csf_to_elastodyn.sh
#   ./run_csf_to_elastodyn.sh <geometry.yaml>
#
# Outputs:
#   <geometry>_ElastoDyn_Tower.dat
#   <geometry>_BModes_tower.bmt
#   <geometry>_BModes_tower.bmi      (only if RNA parameters are set)
#   <geometry>_BModes_tower.out      (only if BModes executable is configured)
# =============================================================================

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <geometry.yaml>"
    exit 1
fi

YAML="$1"

if [[ ! -f "$YAML" ]]; then
    echo "ERROR: file not found: $YAML"
    exit 1
fi

# --- Material parameters ----------------------------------------------------
E=210e9
G=80.8e9
RHO=8500
N=100
DAMP=1.0

# --- RNA tip-mass parameters ------------------------------------------------
# Placeholder values for pipeline testing only.
# Replace them with machine-specific data for physical runs.
MASS_TIP="350000"
IXX_TIP="2607890"
IYY_TIP="43784227"
IZZ_TIP="2607890"
CM_LOC="-1.9"
CM_AXIAL="1.75"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- BModes executable ------------------------------------------------------
# Priority:
#   1) environment variable BMODES_EXE if already set
#   2) local default at ./BModes/build/bmodes/bmodes if present
#   3) no automatic BModes execution
if [[ -z "${BMODES_EXE:-}" ]]; then
    if [[ -x "$SCRIPT_DIR/BModes/build/bmodes/bmodes" ]]; then
        BMODES_EXE="$SCRIPT_DIR/BModes/build/bmodes/bmodes"
    else
        BMODES_EXE=""
    fi
fi

ARGS=(
    "$SCRIPT_DIR/csf_to_elastodyn.py" "$YAML"
    --E "$E"
    --G "$G"
    --rho "$RHO"
    --n "$N"
    --damp "$DAMP"
)

if [[ -n "$MASS_TIP" && -n "$IXX_TIP" && -n "$IYY_TIP" && -n "$IZZ_TIP" && -n "$CM_LOC" && -n "$CM_AXIAL" ]]; then
    ARGS+=(
        --mass-tip "$MASS_TIP"
        --ixx-tip  "$IXX_TIP"
        --iyy-tip  "$IYY_TIP"
        --izz-tip  "$IZZ_TIP"
        --cm-loc   "$CM_LOC"
        --cm-axial "$CM_AXIAL"
    )
else
    echo "INFO: RNA parameters not set — .bmi file will not be generated."
    echo ""
fi

if [[ -n "$BMODES_EXE" ]]; then
    echo "INFO: BModes executable found — full pipeline will run automatically."
    echo "      $BMODES_EXE"
    echo ""
    ARGS+=(--bmodes-exe "$BMODES_EXE")
else
    echo "INFO: BMODES_EXE not set and local BModes executable not found."
    echo "      The script will stop after writing .dat/.bmt/.bmi."
    echo ""
fi

python3 "${ARGS[@]}"
