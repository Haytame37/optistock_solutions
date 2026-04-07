$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Host "Virtual environment not found at .venv. Create it first with:" -ForegroundColor Yellow
    Write-Host "python -m venv .venv" -ForegroundColor Cyan
    Write-Host ".\.venv\Scripts\python.exe -m pip install -r requirements.txt" -ForegroundColor Cyan
    exit 1
}

Set-Location $projectRoot
& $pythonExe -m streamlit run app.py
