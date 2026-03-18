# Requires Python 3 installed and accessible via 'python' or 'python3'
$ErrorActionPreference = "Stop"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PY_SCRIPT   = Join-Path $SCRIPT_DIR "writegeometry_v6_twist.py"
# -------------------------
# Parameters — NREL 5-MW Reference Tower
# -------------------------
$z0 = "0.0"
$z1 = "87.6"
# ===== Base circular annulus =====
$tf_cell = "0"
$tg_base = "0.0351"
$cx      = "0.0"
$cy      = "0.0"
$de      = "6.0"
# ===== Head circular annulus (circle via R = rdx/2) =====
$th_cell = "0"
$tg_head = "0.0247"
$rcx     = "0.0"
$rcy     = "0.0"
$rdx     = "3.87"
$rdy     = "3.87"
$R       = "1.935"
# ===== No twist =====
$twist_deg = "0"
# ===== Discretization =====
$N = "1024"
# ===== Output =====
$out = "NREL-5-MW.yaml"
# -------------------------
# Run Python script
# -------------------------
python $PY_SCRIPT `
  --z0        $z0        `
  --z1        $z1        `
  --tf-cell   $tf_cell   `
  --tg-base   $tg_base   `
  --cx        $cx        `
  --cy        $cy        `
  --de        $de        `
  --th-cell   $th_cell   `
  --tg-head   $tg_head   `
  --rcx       $rcx       `
  --rcy       $rcy       `
  --rdx       $rdx       `
  --rdy       $rdy       `
  --R         $R         `
  --N         $N         `
  --twist-deg $twist_deg `
  --out       $out
