$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot

Write-Host "Starting BBF Viewer application for E2E Testing..." -ForegroundColor Cyan

# Start Backend
Write-Host "Starting Backend (Uvicorn) on port 8000..." -ForegroundColor Yellow
$BackendJob = Start-Job -ScriptBlock {
    param($Path)
    Set-Location $Path
    uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
} -ArgumentList "$ProjectRoot\backend"

# Start Frontend
Write-Host "Starting Frontend (Vite) on port 5174..." -ForegroundColor Yellow
$FrontendJob = Start-Job -ScriptBlock {
    param($Path)
    Set-Location $Path
    npm run dev
} -ArgumentList "$ProjectRoot\frontend"

Write-Host "Waiting for servers to start (5 seconds)..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

$TestFailed = $false

try {
    Write-Host "Running Playwright E2E Tests..." -ForegroundColor Green
    Set-Location "$ProjectRoot\e2e"
    
    # Run playwright tests
    # Using CMD to properly handle npm execution in PowerShell
    cmd /c "npx playwright test"
    
    if ($LASTEXITCODE -ne 0) {
        $TestFailed = $true
        Write-Host "E2E Tests Failed!" -ForegroundColor Red
    } else {
        Write-Host "E2E Tests Passed Successfully!" -ForegroundColor Green
    }
}
finally {
    Write-Host "Cleaning up test environment... Stopping servers." -ForegroundColor Yellow
    Stop-Job $BackendJob
    Stop-Job $FrontendJob
    Remove-Job $BackendJob -Force
    Remove-Job $FrontendJob -Force
    # Stop any detached node or python processes related to our apps
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.Path -match "frontend" } | Stop-Process -Force
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.Path -match "backend" } | Stop-Process -Force
    Write-Host "Servers stopped." -ForegroundColor Green
}

if ($TestFailed) {
    exit 1
} else {
    exit 0
}
