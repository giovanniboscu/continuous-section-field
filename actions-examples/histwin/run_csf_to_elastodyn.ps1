param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$YAML
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $YAML)) {
    Write-Host "ERROR: file not found: $YAML"
    exit 1
}

# Material parameters
$E    = 210e9
$G    = 80.8e9
$RHO  = 8500
$N    = 100
$DAMP = 1.0

# RNA tip-mass parameters
# Placeholder values for pipeline testing only.
$MASS_TIP = "350000"
$IXX_TIP  = "2607890"
$IYY_TIP  = "43784227"
$IZZ_TIP  = "2607890"
$CM_LOC   = "-1.9"
$CM_AXIAL = "1.75"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# BModes executable discovery
$BmodesExe = $env:BMODES_EXE
if ([string]::IsNullOrWhiteSpace($BmodesExe)) {
    $CandidateExe   = Join-Path $ScriptDir "BModes\build\bmodes\bmodes.exe"
    $CandidateNoExt = Join-Path $ScriptDir "BModes\build\bmodes\bmodes"

    if (Test-Path -LiteralPath $CandidateExe) {
        $BmodesExe = $CandidateExe
    }
    elseif (Test-Path -LiteralPath $CandidateNoExt) {
        $BmodesExe = $CandidateNoExt
    }
    else {
        $BmodesExe = ""
    }
}

$ArgList = @()
$ArgList += (Join-Path $ScriptDir "csf_to_elastodyn.py")
$ArgList += $YAML
$ArgList += "--E"
$ArgList += "$E"
$ArgList += "--G"
$ArgList += "$G"
$ArgList += "--rho"
$ArgList += "$RHO"
$ArgList += "--n"
$ArgList += "$N"
$ArgList += "--damp"
$ArgList += "$DAMP"

$HaveAllRna = (
    (-not [string]::IsNullOrWhiteSpace($MASS_TIP)) -and
    (-not [string]::IsNullOrWhiteSpace($IXX_TIP))  -and
    (-not [string]::IsNullOrWhiteSpace($IYY_TIP))  -and
    (-not [string]::IsNullOrWhiteSpace($IZZ_TIP))  -and
    (-not [string]::IsNullOrWhiteSpace($CM_LOC))   -and
    (-not [string]::IsNullOrWhiteSpace($CM_AXIAL))
)

if ($HaveAllRna) {
    $ArgList += "--mass-tip"
    $ArgList += "$MASS_TIP"
    $ArgList += "--ixx-tip"
    $ArgList += "$IXX_TIP"
    $ArgList += "--iyy-tip"
    $ArgList += "$IYY_TIP"
    $ArgList += "--izz-tip"
    $ArgList += "$IZZ_TIP"
    $ArgList += "--cm-loc"
    $ArgList += "$CM_LOC"
    $ArgList += "--cm-axial"
    $ArgList += "$CM_AXIAL"
}

if (-not [string]::IsNullOrWhiteSpace($BmodesExe)) {
    Write-Host "INFO: BModes executable found - full pipeline will run automatically."
    Write-Host "      $BmodesExe"
    Write-Host ""
    $ArgList += "--bmodes-exe"
    $ArgList += "$BmodesExe"
}
else {
    Write-Host "INFO: BMODES_EXE not set and local BModes executable not found."
    Write-Host "      The script will stop after writing .dat/.bmt/.bmi."
    Write-Host ""
}

& python @ArgList
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
