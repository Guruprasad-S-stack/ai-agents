# PowerShell script to watch Celery log file in real-time
# Usage: .\watch_celery_log.ps1

$logFile = "celery_output.log"

if (-not (Test-Path $logFile)) {
    Write-Host "Log file not found: $logFile" -ForegroundColor Red
    Write-Host "Make sure Celery worker is running with: python celery_worker.py > celery_output.log 2>&1" -ForegroundColor Yellow
    exit
}

Write-Host "Watching Celery log: $logFile" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop watching" -ForegroundColor Yellow
Write-Host "=" * 80

# Show last 50 lines and then follow
Get-Content $logFile -Wait -Tail 50

