#!/bin/sh
# FEM3D baseline v02 (2026-10-12)
# Carrera Table 9.13 C-section: 20,480 nominal H8 elements.
# Run the existing CSF-CUF-based FEM3D driver without modifying it.
set -eu

cd "$(dirname "$0")"
mkdir -p fem3d

python3 fem3d/run_c_section_table_9_13_fem3d.py \
  models/c_section_chapter9_5_3_csf.yaml \
  problems/c_section_table_9_13.yaml \
  fem3d/c_section_table_9_13.fem.npz \
  --nx 80 \
  --ny-top-free 24 \
  --ny-bottom-free 16 \
  --ny-web 4 \
  --nz-flange 4 \
  --nz-web 16
