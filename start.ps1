param (
    [switch]$Install
)

$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot

if ($Install) {
    Write-Host "Installing backend dependencies..." -ForegroundColor Cyan
    Set-Location "$ProjectRoot\backend"
    uv sync

    Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
    Set-Location "$ProjectRoot\frontend"
    npm install
}

Write-Host "Starting BBF Viewer application..." -ForegroundColor Green

# Start Backend
Write-Host "Starting Backend (Uvicorn) on port 8000..." -ForegroundColor Yellow
$BackendJob = Start-Job -ScriptBlock {
    param($Path)
    Set-Location $Path
    # Using python directly via uv
    uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
} -ArgumentList "$ProjectRoot\backend"

# Start Frontend
Write-Host "Starting Frontend (Vite) on port 5174..." -ForegroundColor Yellow
$FrontendJob = Start-Job -ScriptBlock {
    param($Path)
    Set-Location $Path
    npm run dev
} -ArgumentList "$ProjectRoot\frontend"

Write-Host "Applications starting... Press Ctrl+C to stop both servers." -ForegroundColor Green
Write-Host "Frontend will be available at http://localhost:5174/"

try {
    # Keep script running to hold jobs
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
finally {
    Write-Host "Stopping servers..." -ForegroundColor Yellow
    Stop-Job $BackendJob
    Stop-Job $FrontendJob
    Remove-Job $BackendJob -Force
    Remove-Job $FrontendJob -Force
    # Stop any detached node or uvicorn processes if necessary
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.Path -match "frontend" } | Stop-Process -Force
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.Path -match "backend" } | Stop-Process -Force
    Write-Host "Servers stopped." -ForegroundColor Green
}
