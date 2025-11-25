# PodcastAgent Setup Verification Script
# This script checks if your environment is ready

Write-Host "🔍 PodcastAgent Setup Verification" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
    
    $versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
    if ($versionMatch) {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
            Write-Host "❌ Python 3.11+ required!" -ForegroundColor Red
            $allGood = $false
        }
    }
} catch {
    Write-Host "❌ Python not found!" -ForegroundColor Red
    $allGood = $false
}

Write-Host ""

# Check virtual environment
Write-Host "Checking virtual environment..." -ForegroundColor Cyan
if (Test-Path "venv") {
    Write-Host "✅ Virtual environment exists" -ForegroundColor Green
} else {
    Write-Host "❌ Virtual environment not found" -ForegroundColor Red
    Write-Host "   Run: python -m venv venv" -ForegroundColor Yellow
    $allGood = $false
}

Write-Host ""

# Check .env file
Write-Host "Checking .env file..." -ForegroundColor Cyan
if (Test-Path ".env") {
    Write-Host "✅ .env file exists" -ForegroundColor Green
    
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "OPENAI_API_KEY=your_openai_api_key_here" -or $envContent -notmatch "OPENAI_API_KEY=") {
        Write-Host "⚠️  Please update OPENAI_API_KEY in .env file" -ForegroundColor Yellow
    } else {
        Write-Host "✅ OPENAI_API_KEY is set" -ForegroundColor Green
    }
} else {
    Write-Host "❌ .env file not found" -ForegroundColor Red
    Write-Host "   Create .env file with your API keys" -ForegroundColor Yellow
    $allGood = $false
}

Write-Host ""

# Check Redis
Write-Host "Checking Redis..." -ForegroundColor Cyan
try {
    $redisTest = redis-cli ping 2>&1
    if ($redisTest -match "PONG") {
        Write-Host "✅ Redis is running" -ForegroundColor Green
    } else {
        Write-Host "❌ Redis is not running" -ForegroundColor Red
        Write-Host "   Start Redis: redis-server" -ForegroundColor Yellow
        $allGood = $false
    }
} catch {
    Write-Host "❌ Redis CLI not found" -ForegroundColor Red
    Write-Host "   Please install Redis" -ForegroundColor Yellow
    $allGood = $false
}

Write-Host ""

# Check if dependencies are installed
Write-Host "Checking Python dependencies..." -ForegroundColor Cyan
if (Test-Path "venv") {
    $venvPython = "venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        try {
            $testImport = & $venvPython -c "import fastapi, celery, redis" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Key dependencies installed" -ForegroundColor Green
            } else {
                Write-Host "❌ Some dependencies missing" -ForegroundColor Red
                Write-Host "   Run: pip install -r requirements.txt" -ForegroundColor Yellow
                $allGood = $false
            }
        } catch {
            Write-Host "⚠️  Could not verify dependencies" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "=============================" -ForegroundColor Cyan

if ($allGood) {
    Write-Host "✅ Setup looks good! You're ready to start." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Activate venv: .\venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "2. Start backend: python main.py" -ForegroundColor White
    Write-Host "3. Start scheduler (new terminal): python -m scheduler" -ForegroundColor White
    Write-Host "4. Start worker (new terminal): python -m celery_worker" -ForegroundColor White
} else {
    Write-Host "❌ Setup incomplete. Please fix the issues above." -ForegroundColor Red
}

Write-Host ""

