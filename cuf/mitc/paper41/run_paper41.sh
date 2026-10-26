#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p logs
for beam in B2 B3 B4; do
  for mode in off on; do
    case="mitc_paper41_L9_${beam}_${mode}"
    echo "Running ${case}"
    csf-cuf "cases/${case}.yaml" 2>&1 | tee "logs/${case}.log"
  done
done
