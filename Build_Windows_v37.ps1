$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
& py -3.12 -c 'import sys; print(sys.version)'
if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.12 with the Windows Python launcher first.' }
$compilerCandidates = @(
    (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'),
    (Join-Path $env:ProgramFiles 'Inno Setup 6\ISCC.exe')
)
$innoCompiler = $compilerCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $innoCompiler) { throw 'Install Inno Setup 6 before building the Windows installer.' }
& py -3.12 -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Build dependency installation failed.' }
& py -3.12 -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Regression tests failed. Installer build stopped.' }
& py -3.12 -m PyInstaller --noconfirm --clean WaterPanda.spec
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }
$appExecutable = Join-Path $PSScriptRoot 'dist\WaterPanda\WaterPanda.exe'
$uiEvidence = Join-Path $PSScriptRoot 'windows-ui-evidence-v37'
$validationProcess = Start-Process -FilePath $appExecutable -ArgumentList '--verify-ui', ('"' + $uiEvidence + '"') -PassThru
if (-not $validationProcess.WaitForExit(180000)) {
    Stop-Process -Id $validationProcess.Id -Force
    throw 'Packaged Windows UI validation timed out.'
}
if ($validationProcess.ExitCode -ne 0) { throw 'Packaged Windows UI validation failed. See windows-ui-evidence-v37.' }
Get-Content (Join-Path $uiEvidence 'report.json')
& $innoCompiler 'installer\WaterPanda.iss'
if ($LASTEXITCODE -ne 0) { throw 'Inno Setup installer build failed.' }
$installerPath = Join-Path $PSScriptRoot 'installer\output\Water_Panda_Setup.exe'
Get-FileHash $installerPath -Algorithm SHA256 | Format-List
Write-Host ('Built v37 installer: ' + $installerPath)
