# Requires: Windows PowerShell 5.1+ or PowerShell 7+
$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PyScript  = Join-Path $ScriptDir '..\..\src\csf\utils\writegeometry_rio_v2.py'

# -------------------------
# Global coordinates
# -------------------------
$z0 = 0.0
$z1 = 50.0

# -------------------------
# S0
# -------------------------
$s0_x = 0.0
$s0_y = 0.0
$s0_dx = 10.5
$s0_dy = 10.5
$s0_R = 4
$s0_tg = 0.25
$s0_t_cell = 0.0

# -------------------------
# S1
# -------------------------
$s1_x = 0.0
$s1_y = 0.0
$s1_dx = 5
$s1_dy = 7
$s1_R = 1.2
$s1_tg = 0.25
$s1_t_cell = 0.0

# -------------------------
# Common
# -------------------------
$twist_deg     = 30
$N             = 128
$singlepolygon = 'false'

# -------------------------
# Rebars
# -------------------------
$n_bars_row1     = 60
$n_bars_row2     = 60
$area_bar_row1   = 0.001257
$area_bar_row2   = 0.001257
$dist_row1_outer = 0.06
$dist_row2_inner = 0.06
$rebar_weight    = 5.71

# -------------------------
# Optional weight laws appended at the end of the YAML
# -------------------------
$bars_row1_law = "np.maximum(0.2, 1.0 - 0.8*(z/L))"
$bars_row2_law = "np.maximum(0.2, 1.0 - 0.8*(z/L))"
$s0_law        = ""# w0 +  0.5 * (1.0 + np.cos(2.0 * np.pi * (t - 0.5)))"
#$s1_law        = ""

# -------------------------
# Output
# -------------------------
$out = 'twist_tower.yaml'

# Prefer the Windows launcher when available.
if (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCmd = 'py'
    $PythonPrefix = @('-3')
}
elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = 'python'
    $PythonPrefix = @()
}
else {
    throw 'Python was not found. Install Python 3 and ensure "py" or "python" is available in PATH.'
}

# Build the argument list.
$args = @()
$args += $PythonPrefix
$args += @(
    $PyScript,
    '--z0', "$z0",
    '--z1', "$z1",
    '--s0-t-cell', "$s0_t_cell",
    '--s0-tg', "$s0_tg",
    '--s0-x', "$s0_x",
    '--s0-y', "$s0_y",
    '--s0-dx', "$s0_dx",
    '--s0-dy', "$s0_dy",
    '--s0-R', "$s0_R",
    '--s1-t-cell', "$s1_t_cell",
    '--s1-tg', "$s1_tg",
    '--s1-x', "$s1_x",
    '--s1-y', "$s1_y",
    '--s1-dx', "$s1_dx",
    '--s1-dy', "$s1_dy",
    '--s1-R', "$s1_R",
    '--twist-deg', "$twist_deg",
    '--N', "$N",
    '--singlepolygon', "$singlepolygon",
    '--n-bars-row1', "$n_bars_row1",
    '--n-bars-row2', "$n_bars_row2",
    '--area-bar-row1', "$area_bar_row1",
    '--area-bar-row2', "$area_bar_row2",
    '--dist-row1-outer', "$dist_row1_outer",
    '--dist-row2-inner', "$dist_row2_inner",
    '--rebar-weight', "$rebar_weight",
    '--out', "$out"
)

# Append optional laws only when they are actually provided.
if (-not [string]::IsNullOrWhiteSpace($bars_row1_law)) {
    $args += '--bars-row1-law'
    $args += "$bars_row1_law"
}

if (-not [string]::IsNullOrWhiteSpace($bars_row2_law)) {
    $args += '--bars-row2-law'
    $args += "$bars_row2_law"
}

if (-not [string]::IsNullOrWhiteSpace($s0_law)) {
    $args += '--s0-law'
    $args += "$s0_law"
}

if (-not [string]::IsNullOrWhiteSpace($s1_law)) {
    $args += '--s1-law'
    $args += "$s1_law"
}

# Execute the Python generator.
& $PythonCmd @args
if ($LASTEXITCODE -ne 0) {
    throw "Python script failed with exit code $LASTEXITCODE"
}
