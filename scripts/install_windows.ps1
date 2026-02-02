$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$distExe = Join-Path $projectRoot "dist\security_posture_app.exe"
$iconPath = Join-Path $projectRoot "assets\app.ico"

if (-not (Test-Path $distExe)) {
    Write-Host "Generating app icon..."
    Push-Location $projectRoot
    python .\scripts\generate_icon.py
    Pop-Location

    Write-Host "Building executable with PyInstaller..."
    Push-Location $projectRoot
    python -m pip install -r requirements.txt
    python -m pip install pyinstaller
    python -m PyInstaller --onefile --windowed --icon .\assets\app.ico security_posture_app.py
    Pop-Location
}

if (-not (Test-Path $distExe)) {
    throw "Executable not found at $distExe"
}

$installDir = Join-Path $env:LOCALAPPDATA "SecurityPosture"
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir | Out-Null
}

$targetExe = Join-Path $installDir "SecurityPosture.exe"
Copy-Item -Path $distExe -Destination $targetExe -Force
if (Test-Path $iconPath) {
    Copy-Item -Path $iconPath -Destination (Join-Path $installDir "app.ico") -Force
}

$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Security Posture.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetExe
$shortcut.WorkingDirectory = $installDir
$shortcut.WindowStyle = 1
$shortcut.Description = "Security Posture + Wi-Fi Health Check"
if (Test-Path (Join-Path $installDir "app.ico")) {
    $shortcut.IconLocation = (Join-Path $installDir "app.ico")
}
$shortcut.Save()

Write-Host "Installed to $installDir"
Write-Host "Desktop shortcut created: $shortcutPath"
