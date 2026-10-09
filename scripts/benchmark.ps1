param(
    [string]$VivadoRoot = 'E:\Vivado\2026.1',
    [string]$Part = 'xcu50-fsvh2104-2-e',
    [string]$Width = 'all',
    [string]$Implementation = 'all'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Push-Location $projectRoot
try {
    New-Item -ItemType Directory -Force -Path 'build' | Out-Null
    & (Join-Path $VivadoRoot 'Vivado\bin\vivado.bat') -mode batch -log build/synthesis.log -journal build/synthesis.jou -source scripts/synthesize.tcl -tclargs $Part $Width $Implementation
    if ($LASTEXITCODE -ne 0) { throw 'Vivado implementation failed' }
    & (Join-Path $VivadoRoot 'tps\win64\python-3.13.0\python.exe') tools/summarize.py
    if ($LASTEXITCODE -ne 0) { throw 'Report generation failed' }
} finally { Pop-Location }
