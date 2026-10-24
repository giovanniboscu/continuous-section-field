#!/bin/sh
python3 -m csf.cuf.tools.plot_strain_stress_boundary_v10 --csf-yaml models/bridge_geometry.yaml --checkpoint  output/bending_scaled_lagrange_N15/carrera_bridge_bending_scaled_lagrange_N15_eq1.cuf.npz --transverse-x 20   --transverse-grid 120   --transverse-vector-grid 50

python3 -m csf.cuf.tools.plot_strain_stress_boundary_v10 --csf-yaml models/bridge_geometry.yaml --checkpoint  output/bending_scaled_lagrange_N15/carrera_bridge_bending_scaled_lagrange_N15_eq1.cuf.npz 
