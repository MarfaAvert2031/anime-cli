# anime-cli setup for Windows. Run through setup.bat (double-click).
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

function Has($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

function Refresh-Path {
    $m = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $u = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$m;$u"
}

function Winget-Install($id, $label) {
    Write-Host "Installing $label ..." -ForegroundColor Cyan
    winget install --id $id -e --accept-source-agreements --accept-package-agreements
    Refresh-Path
}

if (-not (Has "winget")) {
    Write-Host "winget not found. Install 'App Installer' from the Microsoft Store, then run this again." -ForegroundColor Red
    exit 1
}

# 1. System programs
if (-not ((Has "py") -or (Has "python"))) { Winget-Install "Python.Python.3.12" "Python" }
if (-not (Has "node"))   { Winget-Install "OpenJS.NodeJS.LTS" "Node.js" }
if (-not (Has "git"))    { Winget-Install "Git.Git" "Git" }
if (-not (Has "mpv"))    { Winget-Install "shinchiro.mpv" "mpv" }
if (-not (Has "ffmpeg")) { Winget-Install "Gyan.FFmpeg" "ffmpeg" }

# 2. Python virtual environment + libraries
$py = if (Has "py") { "py" } else { "python" }
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment ..." -ForegroundColor Cyan
    & $py -m venv .venv
}
$venvPy = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    Write-Host "Could not create .venv. Close this window, reopen it, and run setup.bat again." -ForegroundColor Red
    exit 1
}
& $venvPy -m pip install --upgrade pip
& $venvPy -m pip install -r requirements.txt

# 3. Node package (JustalK)
if (Has "npm") {
    Write-Host "Installing Node package ..." -ForegroundColor Cyan
    if (-not (Test-Path "package.json")) { npm init -y | Out-Null }
    npm install @justalk/anime-api
} else {
    Write-Host "npm not found yet. Reopen the terminal and run setup.bat again." -ForegroundColor Yellow
}

# 4. Settings file
if (-not (Test-Path "settings.xml") -and (Test-Path "settings.example.xml")) {
    Copy-Item "settings.example.xml" "settings.xml"
    Write-Host "Created settings.xml from settings.example.xml"
}

Write-Host ""
Write-Host "Done. Run the CLI with:" -ForegroundColor Green
Write-Host "  .\.venv\Scripts\python.exe player.py"
Write-Host "If a program is reported missing, reopen the terminal so PATH updates."