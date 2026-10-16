#!/bin/sh

python3 fem3d/run_c_section_table_9_13_fem3d.py   models/c_section_chapter9_5_3_csf.yaml   problems/c_section_table_9_13.yaml   fem3d/c_section_table_9_13_a.npz  --nx 200   --ny-top-free 18   --ny-bottom-free 18   --ny-web 10   --nz-flange 10   --nz-web 18
