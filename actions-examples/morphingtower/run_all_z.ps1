$ErrorActionPreference = "Stop"

$inputFile = ".\out\twist_tower.txt"

# Estrae tutti i valori z dal file (righe come "# z=0.0")
$zValues = Get-Content $inputFile | Where-Object { $_ -match '^# z=(.+)$' } | ForEach-Object {
    $matches[1].Trim()
}

Write-Host "Trovati $($zValues.Count) valori z: $($zValues -join ', ')"
Write-Host ""

foreach ($z in $zValues) {
    Write-Host ">>> Elaborazione z = $z ..."
    python -m csf.utils.csf_sp $inputFile --z=$z
    Write-Host "    Completato z = $z"
    Write-Host ""
}

Write-Host "=== Tutti i valori z elaborati ==="
