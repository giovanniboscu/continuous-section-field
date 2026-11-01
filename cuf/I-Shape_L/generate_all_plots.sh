#!/usr/bin/env bash

set -euo pipefail

# ============================================================
# CSF-CUF plot generation
#   1) Transverse maps only
#   2) Transverse perimeter plots only
#   3) Longitudinal boundary plots
# ============================================================

MODULE="csf.cuf.tools.plot_strain_stress_boundary_v10"

CSF_YAML="models/carrera_i_shaped_taper80_l9_web3.yaml"

CHECKPOINT="output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1.cuf.npz"

FEM3D="fem3d/output/fem3d_taper.npz"

# Transverse section
TRANSVERSE_X="500.0"

# Perimeter sampling
PERIMETER_POINTS="201"
INWARD_OFFSET="0.1"

# Longitudinal sampling
LONGITUDINAL_POINTS="201"

# Output root
OUTPUT_ROOT="${OUTPUT_ROOT:-plot_results}"

MAPS_OUTPUT="${OUTPUT_ROOT}/maps"
PERIMETER_OUTPUT="${OUTPUT_ROOT}/perimeters"
LONGITUDINAL_OUTPUT="${OUTPUT_ROOT}/longitudinal"


echo "============================================================"
echo "CSF-CUF plot generation"
echo "============================================================"
echo "CSF model      : ${CSF_YAML}"
echo "CUF checkpoint : ${CHECKPOINT}"
echo "FEM3D          : ${FEM3D}"
echo "Transverse x   : ${TRANSVERSE_X}"
echo "Output root    : ${OUTPUT_ROOT}"
echo "============================================================"


mkdir -p "${MAPS_OUTPUT}"
mkdir -p "${PERIMETER_OUTPUT}"
mkdir -p "${LONGITUDINAL_OUTPUT}"


# ============================================================
# 1. TRANSVERSE MAPS ONLY
# ============================================================

echo
echo "------------------------------------------------------------"
echo "[1/3] Generating transverse maps"
echo "------------------------------------------------------------"

python -m "${MODULE}" \
  --csf-yaml "${CSF_YAML}" \
  --checkpoint "${CHECKPOINT}" \
  --transverse-x "${TRANSVERSE_X}" \
  --output-dir "${MAPS_OUTPUT}"

echo "[OK] Transverse maps completed"


# ============================================================
# 2. TRANSVERSE PERIMETER ONLY
#    CUF + FEM3D
#    Boundary + inward perimeter
# ============================================================

echo
echo "------------------------------------------------------------"
echo "[2/3] Generating transverse perimeter plots"
echo "------------------------------------------------------------"

python -m "${MODULE}" \
  --csf-yaml "${CSF_YAML}" \
  --checkpoint "${CHECKPOINT}" \
  --fem3d "${FEM3D}" \
  --transverse-x "${TRANSVERSE_X}" \
  --transverse-perimeter-only \
  --transverse-perimeter-points "${PERIMETER_POINTS}" \
  --transverse-inward-offset "${INWARD_OFFSET}" \
  --output-dir "${PERIMETER_OUTPUT}" \
  --fem-stress-from-element

echo "[OK] Transverse perimeter plots completed"


# ============================================================
# 3. LONGITUDINAL BOUNDARY
#    CUF + FEM3D
# ============================================================

echo
echo "------------------------------------------------------------"
echo "[3/3] Generating longitudinal boundary plots"
echo "------------------------------------------------------------"

python -m "${MODULE}" \
  --csf-yaml "${CSF_YAML}" \
  --checkpoint "${CHECKPOINT}" \
  --fem3d "${FEM3D}" \
  --stress-mode boundary \
  --points "${LONGITUDINAL_POINTS}" \
  --output-dir "${LONGITUDINAL_OUTPUT}" \
  --fem-stress-from-element

echo "[OK] Longitudinal plots completed"


echo
echo "============================================================"
echo "ALL GENERATIONS COMPLETED"
echo "============================================================"
echo "Maps        : ${MAPS_OUTPUT}"
echo "Perimeters  : ${PERIMETER_OUTPUT}"
echo "Longitudinal: ${LONGITUDINAL_OUTPUT}"
echo "============================================================"
