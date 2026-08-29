# CivicLens Windows Setup Script
# Usage: .\setup.ps1

Write-Host "=== CivicLens Local Environment Setup ===" -ForegroundColor Green

# 1. Locate Python 3.11+
$pyExe = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $ver = & py -3.11 --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $pyExe = "py -3.11"
        Write-Host "Found Python 3.11 via py launcher" -ForegroundColor Cyan
    }
}

if (-not $pyExe) {
    $pyExe = "python"
    Write-Host "Using default system python" -ForegroundColor Yellow
}

Set-Location backend

# 2. Create virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment .venv..." -ForegroundColor Cyan
    Invoke-Expression "$pyExe -m venv .venv"
} else {
    Write-Host "Virtual environment .venv already exists." -ForegroundColor Yellow
}

# 3. Upgrade pip and install dependencies
Write-Host "Installing runtime and test dependencies..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\pip install -r requirements.txt
& .\.venv\Scripts\pip install -e .

# 4. Verify critical imports
Write-Host "Verifying critical packages (pgvector, psycopg v3, SQLAlchemy)..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -c "import pgvector; import psycopg; import sqlalchemy; print('=== All critical imports verified successfully! ===')"

Write-Host "`nSetup complete! Activate environment with: .venv\Scripts\Activate.ps1" -ForegroundColor Green
Set-Location ..
