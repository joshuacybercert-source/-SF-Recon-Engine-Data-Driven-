$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$distDir = Join-Path $projectRoot "dist"
$distExe = Join-Path $distDir "security_posture_app.exe"
$wxsFile = Join-Path $projectRoot "installer\security_posture.wxs"
$msiPath = Join-Path $distDir "SecurityPosture.msi"

Write-Host "Generating app icon..."
Push-Location $projectRoot
python .\scripts\generate_icon.py

if (-not (Test-Path $distExe)) {
    Write-Host "Building executable with PyInstaller..."
    python -m pip install -r requirements.txt
    python -m pip install pyinstaller
    python -m PyInstaller --onefile --windowed --icon .\assets\app.ico security_posture_app.py
}
Pop-Location

if (-not (Test-Path $distExe)) {
    throw "Executable not found at $distExe"
}

if (-not (Test-Path $distDir)) {
    New-Item -ItemType Directory -Path $distDir | Out-Null
}

if (Get-Command wix -ErrorAction SilentlyContinue) {
    Write-Host "Building MSI using WiX v4..."
    wix build $wxsFile -out $msiPath
    Write-Host "MSI created at $msiPath"
    exit 0
}

if ((Get-Command candle -ErrorAction SilentlyContinue) -and (Get-Command light -ErrorAction SilentlyContinue)) {
    Write-Host "Building MSI using WiX v3..."
    $objPath = Join-Path $projectRoot "installer\security_posture.wixobj"
    candle $wxsFile -out $objPath
    light $objPath -out $msiPath
    Write-Host "MSI created at $msiPath"
    exit 0
}

Write-Host "WiX not found. Install WiX Toolset and retry."
Write-Host "WiX v4: https://wixtoolset.org/"
Write-Host "WiX v3: https://wixtoolset.org/releases/"
