# PodcastAgent Quick Start Script for Windows
# This script helps you start all required services

Write-Host "🚀 PodcastAgent Quick Start Script" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found!" -ForegroundColor Yellow
    Write-Host "Creating .env template..." -ForegroundColor Yellow
    
    $envContent = @"
OPENAI_API_KEY=your_openai_api_key_here
ELEVENSLAB_API_KEY=your_elevenlabs_api_key_here
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
"@
    
    Set-Content -Path ".env" -Value $envContent
    Write-Host "✅ Created .env file. Please add your API keys!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Press any key to continue after adding your API keys..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Check Redis connection
Write-Host "Checking Redis connection..." -ForegroundColor Cyan
try {
    $redisTest = redis-cli ping 2>&1
    if ($redisTest -match "PONG") {
        Write-Host "✅ Redis is running" -ForegroundColor Green
    } else {
        Write-Host "❌ Redis is not running or not accessible" -ForegroundColor Red
        Write-Host "Please start Redis first!" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Redis CLI not found. Please install Redis." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting services..." -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  IMPORTANT: You need to run each service in a SEPARATE terminal window!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Terminal 1 - Backend Server:" -ForegroundColor Cyan
Write-Host "  cd $PWD" -ForegroundColor White
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  python main.py" -ForegroundColor White
Write-Host ""
Write-Host "Terminal 2 - Scheduler:" -ForegroundColor Cyan
Write-Host "  cd $PWD" -ForegroundColor White
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  python -m scheduler" -ForegroundColor White
Write-Host ""
Write-Host "Terminal 3 - Celery Worker:" -ForegroundColor Cyan
Write-Host "  cd $PWD" -ForegroundColor White
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  python -m celery_worker" -ForegroundColor White
Write-Host ""
Write-Host "Would you like to start the backend server now? (y/n)" -ForegroundColor Yellow
$response = Read-Host

if ($response -eq "y" -or $response -eq "Y") {
    Write-Host ""
    Write-Host "Starting backend server..." -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
    Write-Host ""
    
    & .\venv\Scripts\python.exe main.py
} else {
    Write-Host ""
    Write-Host "Please start the services manually using the commands above." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "After starting all services, visit: http://localhost:7000" -ForegroundColor Green
}

