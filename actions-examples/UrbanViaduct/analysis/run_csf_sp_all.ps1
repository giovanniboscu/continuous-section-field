# Requires: Windows PowerShell 5.1+ or PowerShell 7+
# =============================================================================
# run_csf_sp_all.ps1
# Run  python -m csf.utils.csf_sp  on every section CSV file
# produced by run_pier50.py  (stored in out\sections\).
# =============================================================================
$ErrorActionPreference = 'Stop'

# --- Python launcher ---
if (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd    = 'python'
    $PythonPrefix = @()
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCmd    = 'py'
    $PythonPrefix = @('-3')
} else {
    throw 'Python not found. Ensure "python" or "py" is available in PATH.'
}

# --- Input folder ---
$CsvDir = Join-Path $PSScriptRoot (Join-Path '../out' 'sections')

if (-not (Test-Path $CsvDir)) {
    throw "Folder '$CsvDir' not found. Run run_pier50.py first to generate the CSV files."
}

$Files = Get-ChildItem -Path $CsvDir -Filter 'section_*.csv' | Sort-Object Name

if ($Files.Count -eq 0) {
    throw "No section_*.csv files found in '$CsvDir'."
}

Write-Host "Found $($Files.Count) section files in '$CsvDir'"
Write-Host ""

$idx = 0
foreach ($f in $Files) {
    $idx++
    Write-Host "[$idx / $($Files.Count)]  $($f.Name)"

    $pyArgs = $PythonPrefix + @('-m', 'csf.utils.csf_sp', $f.FullName)
    & $PythonCmd @pyArgs

    if ($LASTEXITCODE -ne 0) {
        throw "csf_sp failed on '$($f.Name)' with exit code $LASTEXITCODE"
    }
}

Write-Host ""
Write-Host "Done -- processed $($Files.Count) sections."
