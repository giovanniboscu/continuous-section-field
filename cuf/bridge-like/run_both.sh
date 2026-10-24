#!/usr/bin/env bash
set -uo pipefail

# Run every YAML case in the cases/ directory.
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CASE_DIR="$ROOT/cases"

if ! command -v csf-cuf >/dev/null 2>&1; then
  echo 'Error: csf-cuf not found. Activate the project virtual environment.' >&2
  exit 127
fi

shopt -s nullglob
cases=("$CASE_DIR"/*.yaml "$CASE_DIR"/*.yml)
if (( ${#cases[@]} == 0 )); then
  echo "Error: no YAML files found in $CASE_DIR" >&2
  exit 1
fi

failed=0
for case_file in "${cases[@]}"; do
  echo "===== Running $(basename "$case_file") ====="
  if ! csf-cuf "$case_file"; then
    echo "FAILED: $(basename "$case_file")" >&2
    ((failed+=1))
  fi
done

echo "Completed: ${#cases[@]} cases, $failed failed."
(( failed == 0 ))


