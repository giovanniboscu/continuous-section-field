$ErrorActionPreference = "Stop"

$inputFile = ".\out\twist_tower.txt"

# Extract all z values from the file (lines like "# z=0.0")
$zValues = Get-Content $inputFile | Where-Object { $_ -match '^# z=(.+)$' } | ForEach-Object {
    $matches[1].Trim()
}

Write-Host "Found $($zValues.Count) z values: $($zValues -join ', ')"
Write-Host ""

foreach ($z in $zValues) {
    Write-Host ">>> Processing z = $z ..."
    python -m csf.utils.csf_sp $inputFile --z=$z 
    Write-Host "    Done z = $z"
    Write-Host ""
}

Write-Host "=== All z values processed ==="

