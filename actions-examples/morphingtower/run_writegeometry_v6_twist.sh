#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="${SCRIPT_DIR}/writegeometry_v6_twist.py"

# -------------------------
# Parameters
# -------------------------
z0=0.0
z1=40.0

# ===== Base circular annulus =====
tf_cell=0
tg_base=0.40
cx=0.0
cy=0.0
de=10.0

# ===== Head rounded-rectangle annulus =====
th_cell=0
tg_head=0.2
rcx=0.0
rcy=0.0
rdx=6.0
rdy=4.0
R=1.0

# ===== Twist between S0 and S1 [deg] =====
#twist_deg=43
twist_deg=45

# ===== Discretization =====
N=128

# ===== Output =====
out="twist_tower.yaml"

python3 "${PY_SCRIPT}" \
  --z0 "${z0}" \
  --z1 "${z1}" \
  --tf-cell "${tf_cell}" \
  --tg-base "${tg_base}" \
  --cx "${cx}" \
  --cy "${cy}" \
  --de "${de}" \
  --th-cell "${th_cell}" \
  --tg-head "${tg_head}" \
  --rcx "${rcx}" \
  --rcy "${rcy}" \
  --rdx "${rdx}" \
  --rdy "${rdy}" \
  --R "${R}" \
  --N "${N}" \
  --twist-deg "${twist_deg}" \
  --out "${out}"
