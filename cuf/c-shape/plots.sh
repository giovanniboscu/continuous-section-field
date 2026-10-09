#!/bin/sh
python3 -m csf.cuf.tools.plot_strain_stress_boundary_v10 --csf-yaml models/c_section_chapter9_5_3_csf.yaml  --checkpoint output/c_section_table_9_13_lagrange_N08_1el/c_section_table_9_13_lagrange_N08_1el_eq2.cuf.npz --fem3d fem3d/c_section_table_9_13.fem.npz --fem-stress-from-csf --output-dir plots
