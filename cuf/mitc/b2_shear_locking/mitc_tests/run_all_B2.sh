#!/usr/bin/env bash
# Version: 2.0 - 2026-10-11
# Execute eight paired B2 convergence cases without altering solver sources.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "${script_dir}/.."

if ! command -v csf-cuf >/dev/null 2>&1; then
  echo "ERROR: csf-cuf not found in PATH (activate the project venv first)." >&2
  exit 1
fi
if [[ ! -f expansions/lagrangeL9_v4.py ]]; then
  echo "ERROR: expected existing expansions/lagrangeL9_v4.py under cuf/c-shape." >&2
  exit 1
fi
mkdir -p mitc_tests/logs

for ne in 01 02 04 08; do
  for mode in off on; do
    name="mitc_locking_rect_B2_N${ne}_${mode}"
    echo "===== ${name} ====="
    csf-cuf "cases/${name}.yaml" 2>&1 | tee "mitc_tests/logs/${name}.log"
  done
done

python3 mitc_tests/compare_results.py
