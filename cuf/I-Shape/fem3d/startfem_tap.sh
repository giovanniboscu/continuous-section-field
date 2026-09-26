#!/bin/sh
python run_bending_fem3d_v2.py ../models/carrera_i_shaped_taper80.yaml output/fem3d_tapper.npz \
  --amplitude -1 \
  --nx 80 \
  --ny-left 3 \
  --ny-web 6 \
  --ny-right 3 \
  --nz-flange 4 \
  --nz-web 20
