param([string]$VivadoRoot = 'E:\Vivado\2026.1')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$binRoot = Join-Path $VivadoRoot 'Vivado\bin'
$pythonExe = Join-Path $VivadoRoot 'tps\win64\python-3.13.0\python.exe'
function Invoke-Checked([string]$Exe, [string[]]$Arguments) {
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Exe failed with exit code $LASTEXITCODE" }
}
Push-Location $projectRoot
try {
    Invoke-Checked $pythonExe @('tools/generate.py')
    Invoke-Checked $pythonExe @('tools/vectors.py')
    New-Item -ItemType Directory -Force -Path 'build/sim' | Out-Null
    Push-Location 'build/sim'
    try {
        $runStarted = Get-Date
        $sources = @('../../rtl/generated/decode_pkg.sv', '../../rtl/generated/control_direct.sv',
          '../../rtl/generated/control_pla.sv', '../../rtl/generated/control_shared.sv',
          '../../rtl/superscalar_decoder.sv', '../../rtl/decode_pipeline.sv',
          '../../tb/tb_decoder.sv', '../../tb/tb_pipeline.sv')
        Invoke-Checked (Join-Path $binRoot 'xvlog.bat') (@('--sv') + $sources)
        foreach ($top in @('tb_decoder','tb_pipeline')) {
            Invoke-Checked (Join-Path $binRoot 'xelab.bat') @($top,'-s',$top,'--debug','typical')
            Invoke-Checked (Join-Path $binRoot 'xsim.bat') @($top,'-tclbatch','../../scripts/sim.tcl')
        }
    } finally { Pop-Location }
    foreach ($report in @('build/decode_simulation.json','build/pipeline_simulation.json')) {
        if (!(Test-Path $report)) { throw "Missing simulation report: $report" }
        if ((Get-Item $report).LastWriteTime -lt $runStarted) { throw "Stale simulation report: $report" }
        if ((Get-Content $report -Raw | ConvertFrom-Json).status -ne 'PASS') { throw "Failed: $report" }
    }
} finally { Pop-Location }
