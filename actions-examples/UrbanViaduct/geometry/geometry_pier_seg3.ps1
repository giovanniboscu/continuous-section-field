# Requires: Windows PowerShell 5.1+ or PowerShell 7+
# =============================================================================
# Project : Pier50 — Urban Viaduct, Seismic Zone 2 (NTC2018)
# Segment : 3 — Pier head  (z = 38 → 50 m)
# =============================================================================
# The pier head (sommità) widens to:
#   a) support the transverse deck beam and bearings (pot-type, seismic);
#   b) accommodate the shear keys required by NTC2018 §7.4.3.2;
#   c) provide the cap-beam geometry for deck erection (incremental launching).
#
# The top section is wider in the longitudinal direction (deck axis) to carry
# the bearing pads at ~1.80 m spacing from the pier centreline.
# Wall thickness increased to 0.55 m to resist local bearing stresses.
#
# Geometry
# --------
#   S0  z = 38 m :  4.00 × 2.60 m,  tg = 0.45 m   (must match S1 of Seg 2)
#   S1  z = 50 m :  5.60 × 3.00 m,  tg = 0.55 m   (bearing level)
#   Corner radius R = 0.30 m
#
# Reinforcement  (increased — high local demands from bearings + seismic)
# ---------------
#   Outer row : 44 bars Ø25 mm   cover = 75 mm
#   Inner row : 32 bars Ø20 mm   cover = 75 mm (inner face)
# =============================================================================
$ErrorActionPreference = 'Stop'

$PyModule = 'csf.utils.writegeometry_rio_v2'

$z0 = 38.0
$z1 = 50.0

# --- Base section S0  (z = 38 m) — must match S1 of Segment 2 ---
$s0_x = 0.0; $s0_y = 0.0
$s0_dx = 4.00; $s0_dy = 2.60; $s0_R = 0.30; $s0_tg = 0.45; $s0_t_cell = 0.0

# --- Head section S1  (z = 50 m) — bearing level ---
$s1_x = 0.0; $s1_y = 0.0
$s1_dx = 5.60; $s1_dy = 3.00; $s1_R = 0.30; $s1_tg = 0.55; $s1_t_cell = 0.0

$twist_deg = 0; $N = 128; $singlepolygon = 'true'

# Outer row : 44 bars Ø25 mm   area = 4.91e-4 m²
# Inner row : 32 bars Ø20 mm   area = 3.14e-4 m²
$n_bars_row1 = 44;  $n_bars_row2 = 32
$area_bar_row1 = 0.000491;  $area_bar_row2 = 0.000314
$dist_row1_outer = 0.088;   $dist_row2_inner = 0.085
$rebar_weight = 1.0

$bars_row1_law = ""; $bars_row2_law = ""; $s0_law = ""; $s1_law = ""
$out = '..\yaml\pier_seg3.yaml'

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
