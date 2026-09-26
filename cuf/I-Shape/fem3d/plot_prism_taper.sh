#!/bin/sh
python3  compare_prism_taper.py ../output/prism/lagrange/table9_N18_E1/cuf_scaled_lagrange_taper_table9_N18.cuf.npz ../output/taper/lagrange/table9_N18_E1/cuf_scaled_lagrange_taper_table9_N18.cuf.npz --prism-fem3d output/fem3d_prism.npz --taper-fem3d output/fem3d_tapper.npz --output-dir prism_vs_taper
