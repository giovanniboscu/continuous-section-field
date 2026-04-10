#!/usr/bin/env bash
# =============================================================================
# run_csf_sp_all.sh
# Run  python3 -m csf.utils.csf_sp  on every section CSV file
# produced by run_pier50.py  (stored in out/sections/).
#
# Usage (from the analysis/ directory):
#   bash run_csf_sp_all.sh                     # print to stdout
#   bash run_csf_sp_all.sh > ../result/sectionproperties_par.txt
# =============================================================================
set -euo pipefail

# Resolve the sections folder relative to this script's location,
# regardless of the working directory from which the script is called.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CSV_DIR="${SCRIPT_DIR}/../out/sections"

# --- Guard: sections folder must exist ---
if [ ! -d "$CSV_DIR" ]; then
    echo "ERROR: folder '$CSV_DIR' not found." >&2
    echo "       Run run_pier50.py first to generate the CSV section files." >&2
    exit 1
fi

# --- Collect and sort section files ---
mapfile -t FILES < <(find "$CSV_DIR" -maxdepth 1 -name "section_*.csv" | sort)

N_FILES=${#FILES[@]}

if [ "$N_FILES" -eq 0 ]; then
    echo "ERROR: no section_*.csv files found in '$CSV_DIR'." >&2
    exit 1
fi

echo "Found $N_FILES section files in '$CSV_DIR'"
echo ""
echo ""

# --- Process each section ---
idx=0
for f in "${FILES[@]}"; do
    idx=$(( idx + 1 ))
    fname="$(basename "$f")"
    echo "[$idx / $N_FILES]  $fname"
    python3 -m csf.utils.csf_sp "$f"
    echo ""
done

echo ""
echo "Done -- processed $N_FILES sections."
