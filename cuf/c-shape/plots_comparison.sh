#!/bin/sh
python3 -m csf.cuf.tools.plot_strain_stress_boundary_v10 \
  --csf-yaml models/c_section_chapter9_5_3_9L9_csf.yaml \
  --checkpoint output/c_section_table_9_13_lagrangeL9_v4_E10/c_section_table_9_13_lagrangeL9_v4_E10_eq1.cuf.npz \
  --fem3d fem3d/c_section_table_9_13_a.npz \
  --fem-stress-from-csf
