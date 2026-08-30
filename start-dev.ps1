# CivicLens -- Start All Development Servers
# Run this script from d:\CIVICLENS
# Usage: .\start-dev.ps1

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   CivicLens Dev Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Free ports if already in use
Write-Host "[1/4] Checking ports..." -ForegroundColor Yellow
foreach ($port in @(3000, 3001)) {
    $proc = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty OwningProcess -Unique
    if ($proc) {
        Stop-Process -Id $proc -Force -ErrorAction SilentlyContinue
        Write-Host "      Freed port $port (was PID $proc)" -ForegroundColor Gray
    } else {
        Write-Host "      Port $port is free" -ForegroundColor Gray
    }
}

# 2. Start backend via Docker (only backend services, not web/admin)
Write-Host ""
Write-Host "[2/4] Starting backend (Docker)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd d:\CIVICLENS; Write-Host 'BACKEND - postgres / redis / api / worker' -ForegroundColor Cyan; docker compose up postgres redis api worker migration"
) -WindowStyle Normal

Start-Sleep -Seconds 2

# 3. Start citizen web frontend (port 3000)
Write-Host "[3/4] Starting citizen frontend (port 3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd d:\CIVICLENS\frontend\web; Write-Host 'FRONTEND - Citizen App :3000' -ForegroundColor Green; npm run dev"
) -WindowStyle Normal

Start-Sleep -Seconds 1

# 4. Start admin frontend (port 3001)
Write-Host "[4/4] Starting admin panel (port 3001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd d:\CIVICLENS\frontend\admin; Write-Host 'FRONTEND - Admin Panel :3001' -ForegroundColor Magenta; npm run dev"
) -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   All servers starting in new windows!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Citizen App  :  http://localhost:3000" -ForegroundColor Green
Write-Host "   Admin Panel  :  http://localhost:3001" -ForegroundColor Magenta
Write-Host "   Backend API  :  http://localhost:8000" -ForegroundColor Yellow
Write-Host "   API Docs     :  http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "   To stop: close the 3 new windows, then Ctrl+C in each" -ForegroundColor Gray
Write-Host ""
