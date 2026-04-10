# Requires: Windows PowerShell 5.1+ or PowerShell 7+
# =============================================================================
# Project : Pier50 — Urban Viaduct, Seismic Zone 2 (NTC2018)
# Segment : 1 — Base zone  (z = 0 → 8 m)
# =============================================================================
# The base segment covers the plastic-hinge region defined by EC8-2 §4.1.6.
# Section is enlarged to accommodate the high seismic moment demand at the
# pier-foundation interface and to satisfy the confinement requirements of
# NTC2018 §7.4.4.1 (DCM ductility class).
#
# Geometry
# --------
#   S0  z =  0 m :  6.40 × 3.60 m,  tg = 0.70 m   (at pile-cap level)
#   S1  z =  8 m :  5.20 × 3.20 m,  tg = 0.60 m   (transition to shaft)
#   Corner radius R = 0.30 m  (constant along full pier height)
#
# Materials  (NTC2018 §11 / EC2 §3)
# ----------
#   Concrete  C35/45   fck = 35 MPa   Ecm = 34 GPa
#   Steel     B450C    fyk = 450 MPa  Es  = 200 GPa
#
# Reinforcement  (seismic — heavy base zone)
# ---------------
#   Outer row : 48 bars Ø28 mm   cover = 75 mm   (EC8-2 §6.2.1 min. 40 mm)
#   Inner row : 32 bars Ø22 mm   cover = 75 mm (inner face)
# =============================================================================
$ErrorActionPreference = 'Stop'

$PyModule = 'csf.utils.writegeometry_rio_v2'

# --- Longitudinal coordinates [m] ---
$z0 = 0.0
$z1 = 8.0

# --- Base section S0  (z = 0 m — pile-cap interface) ---
$s0_x      = 0.0
$s0_y      = 0.0
$s0_dx     = 6.40
$s0_dy     = 3.60
$s0_R      = 0.30
$s0_tg     = 0.70
$s0_t_cell = 0.0

# --- Head section S1  (z = 8 m — top of plastic-hinge zone) ---
# Must match S0 of Segment 2 exactly.
$s1_x      = 0.0
$s1_y      = 0.0
$s1_dx     = 5.20
$s1_dy     = 3.20
$s1_R      = 0.30
$s1_tg     = 0.60
$s1_t_cell = 0.0

# --- Discretisation ---
$twist_deg     = 0
$N             = 128
$singlepolygon = 'true'

# --- Reinforcement ---
# Outer row : 48 bars Ø28 mm   area = pi/4 * 0.028^2 = 6.16e-4 m²
# Inner row : 32 bars Ø22 mm   area = pi/4 * 0.022^2 = 3.80e-4 m²
# dist_row1_outer = cover(75) + radius(14) = 89 mm
# dist_row2_inner = cover(75) + radius(11) = 86 mm (from inner void face)
$n_bars_row1     = 48
$n_bars_row2     = 32
$area_bar_row1   = 0.000616    # m²  Ø28
$area_bar_row2   = 0.000380    # m²  Ø22
$dist_row1_outer = 0.089       # m
$dist_row2_inner = 0.086       # m
$rebar_weight    = 1.0

# --- Weight laws (constant reinforcement within segment) ---
$bars_row1_law = ""
$bars_row2_law = ""
$s0_law        = ""
$s1_law        = ""

# --- Output ---
$out = '..\yaml\pier_seg1.yaml'

# --- Python launcher ---
if (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = 'python'; $PythonPrefix = @()
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCmd = 'py'; $PythonPrefix = @('-3')
} else { throw 'Python not found.' }

$pyArgs = $PythonPrefix + @(
    '-m', $PyModule,
    '--z0', "$z0", '--z1', "$z1",
    '--s0-t-cell', "$s0_t_cell", '--s0-tg', "$s0_tg",
    '--s0-x', "$s0_x", '--s0-y', "$s0_y",
    '--s0-dx', "$s0_dx", '--s0-dy', "$s0_dy", '--s0-R', "$s0_R",
    '--s1-t-cell', "$s1_t_cell", '--s1-tg', "$s1_tg",
    '--s1-x', "$s1_x", '--s1-y', "$s1_y",
    '--s1-dx', "$s1_dx", '--s1-dy', "$s1_dy", '--s1-R', "$s1_R",
    '--twist-deg', "$twist_deg", '--N', "$N",
    '--singlepolygon', "$singlepolygon",
    '--n-bars-row1', "$n_bars_row1", '--n-bars-row2', "$n_bars_row2",
    '--area-bar-row1', "$area_bar_row1", '--area-bar-row2', "$area_bar_row2",
    '--dist-row1-outer', "$dist_row1_outer", '--dist-row2-inner', "$dist_row2_inner",
    '--rebar-weight', "$rebar_weight", '--out', "$out"
)
if (-not [string]::IsNullOrWhiteSpace($bars_row1_law)) { $pyArgs += '--bars-row1-law'; $pyArgs += "$bars_row1_law" }
if (-not [string]::IsNullOrWhiteSpace($bars_row2_law)) { $pyArgs += '--bars-row2-law'; $pyArgs += "$bars_row2_law" }
if (-not [string]::IsNullOrWhiteSpace($s0_law))        { $pyArgs += '--s0-law';        $pyArgs += "$s0_law"        }
if (-not [string]::IsNullOrWhiteSpace($s1_law))        { $pyArgs += '--s1-law';        $pyArgs += "$s1_law"        }

& $PythonCmd @pyArgs
if ($LASTEXITCODE -ne 0) { throw "Python script failed with exit code $LASTEXITCODE" }
