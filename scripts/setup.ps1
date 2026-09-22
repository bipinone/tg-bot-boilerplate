# TeleCore Telegram Bot Framework - Windows PowerShell Automated Setup Script
# Author: bipinone (https://github.com/bipinone)
# Repository: https://github.com/bipinone/tg-bot-boilerplate

$ErrorActionPreference = "Stop"

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "⚡ TeleCore Telegram Bot Framework — Automated Windows Setup" -ForegroundColor Cyan
Write-Host "👨‍💻 Author: bipinone (https://github.com/bipinone)" -ForegroundColor White
Write-Host "📦 Repo:   https://github.com/bipinone/tg-bot-boilerplate" -ForegroundColor White
Write-Host "========================================================================`n" -ForegroundColor Cyan

# 1. Locate Python
$PythonExe = $null

foreach ($cmd in @("py", "python", "python3")) {
    try {
        $verCheck = & $cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($verCheck) {
            $parts = $verCheck.Trim().Split(".")
            if ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 10) {
                $PythonExe = $cmd
                Write-Host "[✔ SUCCESS] Found compatible Python ($verCheck): $cmd" -ForegroundColor Green
                break
            }
        }
    } catch {
        # continue searching
    }
}

if (-not $PythonExe) {
    Write-Host "[▲ WARNING] Python 3.10+ not detected in PATH." -ForegroundColor Yellow
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "[INFO] Attempting auto-installation via Windows Package Manager (winget)..." -ForegroundColor Blue
        winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements
        Write-Host "[INFO] Please restart PowerShell and re-run this script after Python completes installation." -ForegroundColor Yellow
        exit 0
    } else {
        Write-Host "[✖ ERROR] Please download and install Python 3.10+ from https://www.python.org/downloads/" -ForegroundColor Red
        Write-Host "Make sure to check the box: 'Add python.exe to PATH'" -ForegroundColor Red
        exit 1
    }
}

# 2. Virtual Environment
$VenvDir = Join-Path $PSScriptRoot "..\venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "[INFO] Creating virtual environment in ./venv..." -ForegroundColor Blue
    try {
        & $PythonExe -m venv $VenvDir
    } catch {
        Write-Host "[▲ WARNING] Standard venv failed. Attempting pip virtualenv fallback..." -ForegroundColor Yellow
        & $PythonExe -m pip install --user virtualenv
        & $PythonExe -m virtualenv $VenvDir
    }
} else {
    Write-Host "[✔ SUCCESS] Healthy virtual environment already exists." -ForegroundColor Green
}

# 3. Upgrading pip and installing requirements
Write-Host "[INFO] Upgrading pip, setuptools, and wheel..." -ForegroundColor Blue
& $VenvPython -m pip install --upgrade pip setuptools wheel

$ReqFile = Join-Path $PSScriptRoot "..\requirements.txt"
if (Test-Path $ReqFile) {
    Write-Host "[INFO] Installing dependencies from requirements.txt..." -ForegroundColor Blue
    try {
        & $VenvPip install -r $ReqFile
        Write-Host "[✔ SUCCESS] Dependencies installed successfully." -ForegroundColor Green
    } catch {
        Write-Host "[▲ WARNING] Full requirements install had errors. Installing core packages..." -ForegroundColor Yellow
        & $VenvPip install aiogram>=3.13.0 pydantic>=2.7.0 pydantic-settings>=2.2.0 python-dotenv>=1.0.1 aiohttp>=3.9.5 cachetools>=5.3.0 aiosqlite>=0.20.0
    }
}

# 4. Environment (.env) Setup
$EnvFile = Join-Path $PSScriptRoot "..\.env"
$EnvExample = Join-Path $PSScriptRoot "..\.env.example"

if (-not (Test-Path $EnvFile)) {
    if (Test-Path $EnvExample) {
        Copy-Item $EnvExample $EnvFile
        Write-Host "[✔ SUCCESS] Created .env from .env.example." -ForegroundColor Green
    } else {
        Set-Content -Path $EnvFile -Value "BOT_TOKEN=`nBOT_ADMINS=`nDB_TYPE=sqlite`n"
    }
}

# Prompt for BOT_TOKEN if empty
$EnvContent = Get-Content $EnvFile -Raw
if ($EnvContent -match "BOT_TOKEN=\s*`r?`n" -or $EnvContent -match "BOT_TOKEN=your_bot_token_here") {
    Write-Host "`n--- Interactive Bot Configuration ---" -ForegroundColor Yellow
    $TokenInput = Read-Host "🤖 Enter your Telegram BOT_TOKEN from @BotFather (or press Enter to skip)"
    if ($TokenInput -and $TokenInput.Contains(":") -and $TokenInput.Length -gt 25) {
        $EnvContent = $EnvContent -replace "BOT_TOKEN=.*", "BOT_TOKEN=$TokenInput"
        Set-Content -Path $EnvFile -Value $EnvContent
        Write-Host "[✔ SUCCESS] Configured BOT_TOKEN." -ForegroundColor Green
    }

    $AdminInput = Read-Host "👑 Enter your numeric Telegram User ID (optional, or press Enter to skip)"
    if ($AdminInput -match "^\d+$") {
        $EnvContent = Get-Content $EnvFile -Raw
        $EnvContent = $EnvContent -replace "BOT_ADMINS=.*", "BOT_ADMINS=$AdminInput"
        Set-Content -Path $EnvFile -Value $EnvContent
        Write-Host "[✔ SUCCESS] Configured BOT_ADMINS." -ForegroundColor Green
    }
}

# 5. Pre-Flight Health Check
Write-Host "[INFO] Performing pre-flight verification..." -ForegroundColor Blue
$HealthCheckCode = "import aiogram, aiosqlite; from app.config import config; print('HEALTH_OK')"
$CheckResult = & $VenvPython -c $HealthCheckCode 2>$null
if ($CheckResult -match "HEALTH_OK") {
    Write-Host "[✔ SUCCESS] Pre-flight health check PASSED!" -ForegroundColor Green
}

# 6. Next Steps
Write-Host "`n========================================================================" -ForegroundColor Green
Write-Host "🎉 TeleCore Setup Completed Successfully!" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Green
Write-Host "`nQuick Launch Commands:"
Write-Host "  1. Activate virtual environment:" -ForegroundColor White
Write-Host "     .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host "  2. Start the bot:" -ForegroundColor White
Write-Host "     python -m app.main" -ForegroundColor Green
Write-Host "`nUseful Shortcuts:"
Write-Host "  • Run all tests:        python -m unittest discover tests" -ForegroundColor Cyan
Write-Host "  • Scaffold new module:  python -m app.cli make:module <name>" -ForegroundColor Cyan
Write-Host "`n👨‍💻 Developed with ❤️ by Bipin (@bipinone)" -ForegroundColor White
Write-Host "📢 Channel:    https://t.me/BipinOne" -ForegroundColor White
Write-Host "💬 Community:  https://t.me/BipinOneChat" -ForegroundColor White
Write-Host "⭐ GitHub:     https://github.com/bipinone/tg-bot-boilerplate" -ForegroundColor White
Write-Host "========================================================================`n" -ForegroundColor Green
