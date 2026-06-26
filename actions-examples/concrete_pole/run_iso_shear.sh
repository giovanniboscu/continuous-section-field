#!/usr/bin/env bash
set -euo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 writegeometry_tapered_rebars.py \
  --z0 0.0 --z1 20.0 \
  --cx 0.0 --cy 0.0 \
  --radii0 0.200,0.225,0.250,0.275,0.300 \
  --radii1 0.140,0.160,0.180,0.200,0.220 \
  --layer-names core_inner,pcbar_host_layer,cover_inner,cover_outer \
  --layer-weights 1,1,1,1 \
  --N 256 \
  --n-bars 16 \
  --bar-guide-radius0 0.24365 \
  --bar-guide-radius1 0.17365 \
  --bar-host-layer-index 1 \
  --bar-diameter 0.0127 \
  --bar-sides 16 \
  --bar-weight 6.0 \
  --bar-prefix pcbar \
  --theta0-deg 0.0 \
  --layer-law '0:T_lookup("laws/weight_law_core_inner.dat")' \
  --layer-law '1:T_lookup("laws/weight_law_pcbar_host_layer.dat")' \
  --layer-law '2:T_lookup("laws/weight_law_cover_inner.dat")' \
  --layer-law '3:T_lookup("laws/weight_law_cover_outer.dat")' \
  --all-bars-law 'T_lookup("laws/weight_law_pcbar.dat")' \
  --layer-shear-law '0:iso(0.20)' \
  --layer-shear-law '1:iso(0.20)' \
  --layer-shear-law '2:iso(0.20)' \
  --layer-shear-law '3:iso(0.20)' \
  --all-bars-shear-law 'iso(0.30)' \
  --out tapered_pc_pole_iso_lookup.yaml
