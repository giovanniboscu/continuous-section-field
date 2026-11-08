#!/usr/bin/env bash
# Generate CSF-CUF maps and all available longitudinal/perimeter FEM3D H20 overlays.
# Run from cuf/I-Shape_L. No structural solver is invoked.
set -Eeuo pipefail

MODEL="${MODEL:-models/carrera_i_shaped_taper80_l9_web3.yaml}"
CUF="${CUF:-output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1.cuf.npz}"
FEM="${FEM:-fem3d/output/h20_convergence/T4_h20.npz}"
OUT="${OUT:-plot_results/all_H20_CUF}"
MODULE="${MODULE:-csf.cuf.tools.plot_strain_stress_boundary_v10}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
DPI="${DPI:-220}"
POINTS="${POINTS:-201}"
PERIMETER_POINTS="${PERIMETER_POINTS:-201}"
TRANSVERSE_GRID="${TRANSVERSE_GRID:-120}"
VECTOR_GRID="${VECTOR_GRID:-60}"
INWARD="${INWARD:-0.1}"
# Space-separated physical x stations, e.g. STATIONS='250 500 750'.
STATIONS="${STATIONS:-250 500 750}"

for file in "$MODEL" "$CUF" "$FEM"; do
  if [[ ! -f "$file" ]]; then
    printf 'ERROR: missing input file: %s\n' "$file" >&2
    printf 'Run this script from cuf/I-Shape_L or override MODEL/CUF/FEM.\n' >&2
    exit 2
  fi
done
# Refuse to label a non-H20 FEM checkpoint as H20, even if its filename looks correct.
if ! "$PYTHON_BIN" - "$FEM" <<'PY_H20'
import sys
import numpy as np
path = sys.argv[1]
with np.load(path, allow_pickle=False) as data:
    required = ('nodes', 'elements', 'displacement', 'element_E', 'element_G', 'element_nu')
    missing = [k for k in required if k not in data]
    if missing:
        raise SystemExit(f"ERROR: H20 checkpoint is missing {missing}: {path}")
    nodes, elements, disp = data['nodes'], data['elements'], data['displacement']
    if elements.ndim != 2 or elements.shape[1] != 20:
        raise SystemExit(f"ERROR: expected H20 connectivity (N,20), found {elements.shape}: {path}")
    if nodes.ndim != 2 or nodes.shape[1] != 3 or disp.shape != nodes.shape:
        raise SystemExit(f"ERROR: invalid H20 node/displacement shapes: {path}")
    print(f"[input] FEM3D H20 confirmed: {len(elements)} elements, {len(nodes)} nodes; {path}")
PY_H20
then
  exit 2
fi
if ! "$PYTHON_BIN" -c 'import importlib, sys; importlib.import_module(sys.argv[1])' "$MODULE"; then
  printf 'ERROR: plotting module not importable: %s\n' "$MODULE" >&2
  exit 2
fi
mkdir -p "$OUT"
LOG="$OUT/run.log"
exec > >(tee -a "$LOG") 2>&1
printf '=== H20 vs CSF-CUF plotting ===\n'
printf 'MODEL=%s\nCUF=%s\nFEM=%s\nOUT=%s\n' "$MODEL" "$CUF" "$FEM" "$OUT"

common=(--csf-yaml "$MODEL" --checkpoint "$CUF" --fem3d "$FEM" \
        --stress-mode boundary --fem-stress-from-element --dpi "$DPI")

printf '\n[1] Longitudinal displacements, strains and stresses (boundary + inward)\n'
"$PYTHON_BIN" -m "$MODULE" "${common[@]}" \
  --points "$POINTS" --vertices all --inward-offset "$INWARD" \
  --output-dir "$OUT/longitudinal"

printf '\n[2] Transverse CUF maps and FEM3D H20 perimeter overlays\n'
for station in $STATIONS; do
  # Avoid shell path surprises when a station contains decimal points.
  tag="${station//./p}"
  printf '\n  x=%s mm\n' "$station"
  "$PYTHON_BIN" -m "$MODULE" "${common[@]}" \
    --transverse-x "$station" \
    --transverse-grid "$TRANSVERSE_GRID" \
    --transverse-vector-grid "$VECTOR_GRID" \
    --transverse-perimeter \
    --transverse-perimeter-points "$PERIMETER_POINTS" \
    --transverse-inward-offset "$INWARD" \
    --output-dir "$OUT/transverse_x${tag}"
done

printf '\n=== Completed ===\n'
printf 'Output root: %s\n' "$OUT"
printf 'PNG files: %s\n' "$(find "$OUT" -type f -name '*.png' | wc -l)"
printf 'Figure CSV files: %s\n' "$(find "$OUT" -type f -path '*/figure_csv/*.csv' | wc -l)"
printf 'Run log: %s\n' "$LOG"
printf 'Note: transverse color maps are CUF-only; FEM H20 is overlaid on perimeter/longitudinal plots.\n'
