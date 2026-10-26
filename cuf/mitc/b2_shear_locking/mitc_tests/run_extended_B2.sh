#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 mitc_tests/extend_B2.py --counts 16 32 64
command -v csf-cuf >/dev/null || { echo 'ERROR: csf-cuf not installed' >&2; exit 1; }
mkdir -p mitc_tests/logs
for ne in 16 32 64; do
  for mode in off on; do
    name="mitc_locking_rect_B2_N${ne}_${mode}"
    csf-cuf "cases/${name}.yaml" 2>&1 | tee "mitc_tests/logs/${name}.log"
  done
done
python3 mitc_tests/compare_extended.py
