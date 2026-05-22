#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# Automatic @wall / thin-wall verification runner.
#
# For each geometry YAML in this directory, the script:
#   1. runs CSF actions with the common actions.yaml file;
#   2. stores the CSF report in out/<case>/section_selected_analysis.txt;
#   3. runs sectionproperties through csf-sp at z = 0.0 with an explicit mesh;
#   4. optionally runs csf-sp with --plot when PLOT_MESH=1;
#   5. extracts:
#        - J_sv_wall from the CSF report;
#        - the optional wall thickness t, when J_sv_wall is printed as (J, t);
#        - e.j from the sectionproperties report;
#   6. compares J_sv_wall against sectionproperties e.j;
#   7. writes both:
#        - out/thinwall_summary.csv  machine-readable summary;
#        - out/thinwall_summary.txt  human-readable summary.
#
# Usage:
#   ./run_thinwall_tests.sh
#
# Optional plot:
#   PLOT_MESH=1 ./run_thinwall_tests.sh
#
# Optional overrides:
#   REL_TOL=0.15 ./run_thinwall_tests.sh
#   DEFAULT_MESH=0.5 ./run_thinwall_tests.sh
#   ACTION_FILE=actions.yaml ./run_thinwall_tests.sh
# -----------------------------------------------------------------------------

ACTION_FILE="${ACTION_FILE:-actions.yaml}"
OUT_DIR="${OUT_DIR:-out}"
Z_STATION="${Z_STATION:-0.0}"
DEFAULT_MESH="${DEFAULT_MESH:-1.0}"
REL_TOL="${REL_TOL:-0.12}"
PLOT_MESH="${PLOT_MESH:-0}"

CSF_ACTIONS_CMD="${CSF_ACTIONS_CMD:-csf-actions}"
CSF_SP_CMD="${CSF_SP_CMD:-csf-sp}"

# Optional per-case mesh overrides.
declare -A CASE_MESH=(
  ["c-shape.yaml"]="0.0001"
  ["e-shape.yaml"]="0.0001"
  ["f-shape.yaml"]="0.0001"
  ["h1-shaped.yaml"]="0.0001"
  ["h-rot-shaped.yaml"]="0.0001"
  ["i-shaped.yaml"]="0.0001"
  ["l-shape.yaml"]="0.0001"
  ["m-shape.yaml"]="0.0001"
  ["t-shapep.yaml"]="0.0001"
  ["t-uniqshape.yaml"]="0.0001"
)

mkdir -p "$OUT_DIR"

SUMMARY_CSV="$OUT_DIR/thinwall_summary.csv"
SUMMARY_TXT="$OUT_DIR/thinwall_summary.txt"

printf 'case,mesh,z,J_sv_wall,t_wall,J_sectionproperties,rel_error,status\n' > "$SUMMARY_CSV"

{
  printf '%-18s %-8s %-18s %-12s %-18s %-14s %-8s\n' \
    "CASE" "MESH" "J_sv_wall" "t_wall" "SP e.j" "REL_ERROR" "STATUS"
  printf '%0.s-' {1..110}
  echo
} > "$SUMMARY_TXT"

extract_j_sv_wall() {
  local file="$1"
  python3 - "$file" <<'PY'
import re
import sys

text = open(sys.argv[1], encoding="utf-8", errors="replace").read()

mt = re.search(
    r"J_sv_wall\s*:\s*\(\s*([-+0-9.eE]+)\s*,\s*([-+0-9.eE]+)\s*\)",
    text,
)
if mt:
    print(mt.group(1), mt.group(2))
    raise SystemExit(0)

ms = re.search(
    r"J_sv_wall\s*:\s*([-+0-9.eE]+)",
    text,
)
if ms:
    print(ms.group(1), "nan")
    raise SystemExit(0)

lines = [line for line in text.splitlines() if "J_sv_wall" in line or "wall" in line.lower()]
print("Could not extract J_sv_wall. Relevant lines:", file=sys.stderr)
for line in lines[:20]:
    print(line, file=sys.stderr)
raise SystemExit(1)
PY
}

extract_sp_ej() {
  local file="$1"
  python3 - "$file" <<'PY'
import re
import sys

text = open(sys.argv[1], encoding="utf-8", errors="replace").read()

patterns = [
    r"sectionproperties native e\.j \[E_i carrier\]\s*=\s*([-+0-9.eE]+)",
    r"\be\.j\s*[│| ]+\s*([-+0-9.eE]+)",
    r"\be\.j\s*[:=]\s*([-+0-9.eE]+)",
]

for pat in patterns:
    m = re.search(pat, text)
    if m:
        print(m.group(1))
        raise SystemExit(0)

print("Could not extract sectionpropertiecsf-sp s e.j", file=sys.stderr)
raise SystemExit(1)
PY
}

compare_values() {
  local j_csf="$1"
  local j_sp="$2"
  local rel_tol="$3"
  python3 - "$j_csf" "$j_sp" "$rel_tol" <<'PY'
import sys

j_csf = float(sys.argv[1])
j_sp = float(sys.argv[2])
rel_tol = float(sys.argv[3])

rel = abs(j_csf - j_sp) / max(abs(j_sp), 1e-300)
status = "PASS" if rel <= rel_tol else "FAIL"

print(f"{rel:.12g} {status}")
PY
}

format_percent() {
  local rel="$1"
  python3 - "$rel" <<'PY'
import sys
rel = float(sys.argv[1])
print(f"{100.0 * rel:.2f}%")
PY
}

format_t_wall() {
  local t="$1"
  python3 - "$t" <<'PY'
import math
import sys

value = sys.argv[1]

try:
    x = float(value)
except ValueError:
    print(value)
    raise SystemExit(0)

if math.isnan(x):
    print("nan")
else:
    print(f"{x:.6g}")
PY
}

append_table_row() {
  local case_name="$1"
  local mesh="$2"
  local j_wall="$3"
  local t_wall="$4"
  local j_sp="$5"
  local rel_error="$6"
  local status="$7"

  local rel_pct
  local t_fmt

  rel_pct="$(format_percent "$rel_error")"
  t_fmt="$(format_t_wall "$t_wall")"

  printf '%-18s %-8s %-18.6e %-12s %-18.6e %-14s %-8s\n' \
    "$case_name" \
    "$mesh" \
    "$j_wall" \
    "$t_fmt" \
    "$j_sp" \
    "$rel_pct" \
    "$status" \
    >> "$SUMMARY_TXT"
}

append_error_row() {
  local case_name="$1"
  local mesh="$2"
  local status="$3"

  printf '%-18s %-8s %-18s %-12s %-18s %-14s %-8s\n' \
    "$case_name" \
    "$mesh" \
    "-" \
    "-" \
    "-" \
    "-" \
    "$status" \
    >> "$SUMMARY_TXT"
}

shopt -s nullglob

cases=()
for yaml in *.yaml; do
  [[ "$yaml" == actions*.yaml ]] && continue
  cases+=("$yaml")
done

if (( ${#cases[@]} == 0 )); then
  echo "No geometry YAML files found."
  exit 1
fi

failures=0

for yaml in "${cases[@]}"; do
  case_name="${yaml%.yaml}"
  case_out="$OUT_DIR/$case_name"

  mkdir -p "$case_out"

  mesh="${CASE_MESH[$yaml]:-$DEFAULT_MESH}"
  csf_report="$case_out/section_selected_analysis.txt"
  sp_report="$case_out/sectionproperties.txt"
  plot_report="$case_out/plot.txt"

  echo "==> $yaml  mesh=$mesh"

  if ! "$CSF_ACTIONS_CMD" "$yaml" "$ACTION_FILE" > "$csf_report" 2>&1; then
    echo "    CSF actions failed. See: $csf_report"
    printf '%s,%s,%s,,,,,CSF_ACTIONS_ERROR\n' "$case_name" "$mesh" "$Z_STATION" >> "$SUMMARY_CSV"
    append_error_row "$case_name" "$mesh" "CSF_ACTIONS_ERROR"
    failures=$((failures + 1))
    continue
  fi

  if ! "$CSF_SP_CMD" --yaml="$yaml" --z="$Z_STATION" --plot --mesh="$mesh" > "$sp_report" 2>&1; then
    echo "    csf-sp failed. See: $sp_report"
    printf '%s,%s,%s,,,,,CSF_SP_ERROR\n' "$case_name" "$mesh" "$Z_STATION" >> "$SUMMARY_CSV"
    append_error_row "$case_name" "$mesh" "CSF_SP_ERROR"
    failures=$((failures + 1))
    continue
  fi

  if [[ "$PLOT_MESH" == "1" ]]; then
    if ! "$CSF_SP_CMD" --yaml="$yaml" --z="$Z_STATION" --mesh="$mesh" --plot > "$plot_report" 2>&1; then
      echo "    plot failed. See: $plot_report"
    else
      echo "    plot generated"
    fi
  fi

  if ! read -r j_wall t_wall < <(extract_j_sv_wall "$csf_report"); then
    echo "    Could not extract J_sv_wall. See: $csf_report"
    printf '%s,%s,%s,,,,,J_SV_WALL_PARSE_ERROR\n' "$case_name" "$mesh" "$Z_STATION" >> "$SUMMARY_CSV"
    append_error_row "$case_name" "$mesh" "J_SV_WALL_PARSE_ERROR"
    failures=$((failures + 1))
    continue
  fi

  if ! j_sp="$(extract_sp_ej "$sp_report")"; then
    echo "    Could not extract sectionproperties e.j. See: $sp_report"
    printf '%s,%s,%s,%s,%s,,,SP_EJ_PARSE_ERROR\n' \
      "$case_name" "$mesh" "$Z_STATION" "$j_wall" "$t_wall" \
      >> "$SUMMARY_CSV"
    append_error_row "$case_name" "$mesh" "SP_EJ_PARSE_ERROR"
    failures=$((failures + 1))
    continue
  fi

  read -r rel_error status < <(compare_values "$j_wall" "$j_sp" "$REL_TOL")

  printf '%s,%s,%s,%.17g,%s,%.17g,%s,%s\n' \
    "$case_name" \
    "$mesh" \
    "$Z_STATION" \
    "$j_wall" \
    "$t_wall" \
    "$j_sp" \
    "$rel_error" \
    "$status" \
    >> "$SUMMARY_CSV"

  append_table_row "$case_name" "$mesh" "$j_wall" "$t_wall" "$j_sp" "$rel_error" "$status"

  rel_pct="$(format_percent "$rel_error")"

  printf '    J_sv_wall=%s  t=%s  SP e.j=%s  rel_error=%s (%s)  %s\n' \
    "$j_wall" "$t_wall" "$j_sp" "$rel_error" "$rel_pct" "$status"

  if [[ "$status" != "PASS" ]]; then
    failures=$((failures + 1))
  fi
done

{
  printf '%0.s-' {1..110}
  echo
} >> "$SUMMARY_TXT"

echo
echo "CSV summary:   $SUMMARY_CSV"
echo "Text summary:  $SUMMARY_TXT"

if (( failures > 0 )); then
  echo "FAILED cases: $failures"
  exit 1
fi

echo "All thin-wall checks passed."
