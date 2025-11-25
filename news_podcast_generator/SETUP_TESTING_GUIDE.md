# 🧪 PodcastAgent News Podcast Generator - Setup & Testing Guide

This guide will walk you through setting up and testing the PodcastAgent application step by step.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.11 or higher installed
- [ ] Redis Server installed and running
- [ ] OpenAI API key
- [ ] (Optional) ElevenLabs API key for better TTS
- [ ] Node.js and npm (for frontend)
- [ ] Git (if cloning from repository)

---

## Step 1: Install Redis (Windows)

### Option A: Using WSL (Recommended)
If you have WSL installed:
```bash
wsl
sudo apt-get update
sudo apt-get install redis-server
sudo service redis-server start
```

### Option B: Using Windows Native
1. Download Redis for Windows from: https://github.com/microsoftarchive/redis/releases
2. Or use Chocolatey: `choco install redis-64`
3. Start Redis: `redis-server`

### Option C: Using Docker
```bash
docker run -d -p 6379:6379 redis:latest
```

### Verify Redis is Running
Open a new terminal and run:
```bash
redis-cli ping
```
You should see: `PONG`

---

## Step 2: Navigate to Backend Directory

```powershell
cd news_podcast_generator\backend
```

---

## Step 3: Create Virtual Environment

```powershell
python -m venv venv
```

Activate the virtual environment:
```powershell
.\venv\Scripts\Activate.ps1
```

If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Step 4: Install Python Dependencies

```powershell
pip install -r requirements.txt
```

**Note:** This may take 5-10 minutes due to many dependencies. If you encounter errors with:
- **Kokoro**: You can skip it (optional TTS engine)
- **FAISS**: You can skip it (only needed for semantic search)
- **browseruse**: Make sure Playwright is installed first

---

## Step 5: Install Playwright Browsers

```powershell
python -m playwright install
```

This installs browser binaries needed for web scraping features.

---

## Step 6: Create Environment File

Create a `.env` file in the `backend` directory:

```powershell
# Create .env file
New-Item -Path .env -ItemType File
```

Then add the following content to `.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
ELEVENSLAB_API_KEY=your_elevenlabs_api_key_here
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

**Important:** Replace `your_openai_api_key_here` with your actual OpenAI API key.

---

## Step 7: Initialize Database (First Run)

The first time you run `main.py`, it will initialize the databases. This may take 2-3 minutes.

```powershell
python main.py
```

Wait for the message: `Application startup complete!`

Then press `Ctrl+C` to stop it. We'll start it properly in the next step.

---

## Step 8: Start All Required Services

You need to run **3 separate services** in **3 separate terminal windows**. Make sure to activate the virtual environment in each terminal.

### Terminal 1: Main Backend Server

```powershell
cd news_podcast_generator\backend
.\venv\Scripts\Activate.ps1
python main.py
```

Wait for: `Application startup complete!` and `Uvicorn running on http://0.0.0.0:7000`

### Terminal 2: Scheduler Service

Open a **new** PowerShell window:

```powershell
cd news_podcast_generator\backend
.\venv\Scripts\Activate.ps1
python -m scheduler
```

You should see: `Scheduler started successfully`

### Terminal 3: Celery Worker

Open **another** PowerShell window:

```powershell
cd news_podcast_generator\backend
.\venv\Scripts\Activate.ps1
python -m celery_worker
```

You should see: `Starting PodcastAgent workers...` and worker connection messages.

---

## Step 9: (Optional) Start Frontend Development Server

If you want to use the React frontend, open a **4th terminal**:

```powershell
cd news_podcast_generator\frontend
npm install
npm start
```

This will start the React dev server on `http://localhost:3000`

**Note:** The backend also serves the built frontend if you build it first:
```powershell
cd news_podcast_generator\frontend
npm install
npm run build
```

---

## Step 10: Test the Application

### Test 1: Check Backend API Health

Open your browser or use curl:

```powershell
# Using PowerShell
Invoke-WebRequest -Uri "http://localhost:7000/api/articles" -Method GET
```

Or visit in browser: `http://localhost:7000/api/articles`

You should get a JSON response (may be empty array `[]`).

### Test 2: Access the Web Interface

1. If you built the frontend: Visit `http://localhost:7000`
2. If using React dev server: Visit `http://localhost:3000`

### Test 3: Test API Endpoints

You can test various endpoints:

- Articles: `http://localhost:7000/api/articles`
- Sources: `http://localhost:7000/api/sources`
- Podcasts: `http://localhost:7000/api/podcasts`
- Tasks: `http://localhost:7000/api/tasks`

### Test 4: Create a Test Session (Podcast Agent)

Using PowerShell or Postman:

```powershell
# Create a new session
$body = @{
    session_id = $null
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:7000/api/podcast-agent/session" -Method POST -Body $body -ContentType "application/json"
```

---

## Step 11: (Optional) Bootstrap Demo Data

To populate the system with sample data:

```powershell
cd news_podcast_generator\backend
.\venv\Scripts\Activate.ps1
python bootstrap_demo.py
```

This adds sample articles, sources, and configurations.

---

## Troubleshooting

### Issue: Redis Connection Error

**Error:** `Error 10061: No connection could be made`

**Solution:**
1. Verify Redis is running: `redis-cli ping`
2. Check REDIS_HOST and REDIS_PORT in `.env`
3. Try restarting Redis

### Issue: Port Already in Use

**Error:** `Address already in use`

**Solution:**
1. Find process using port 7000: `netstat -ano | findstr :7000`
2. Kill the process or change port in `main.py`

### Issue: Module Not Found

**Error:** `ModuleNotFoundError: No module named 'X'`

**Solution:**
1. Make sure virtual environment is activated
2. Reinstall requirements: `pip install -r requirements.txt`

### Issue: Playwright Browser Not Found

**Error:** `Browser not found`

**Solution:**
```powershell
python -m playwright install
python -m playwright install-deps
```

### Issue: Celery Worker Not Starting

**Error:** `Connection refused` or `Redis connection error`

**Solution:**
1. Ensure Redis is running
2. Check `.env` file has correct Redis settings
3. Verify Redis is accessible: `redis-cli ping`

### Issue: Database Locked

**Error:** `database is locked`

**Solution:**
1. Close all connections to the database
2. Restart all services
3. Check if another process is using the database

---

## Quick Status Check

Run these commands to verify everything is working:

```powershell
# Check Redis
redis-cli ping

# Check if backend is running
Invoke-WebRequest -Uri "http://localhost:7000/api/articles" -Method GET

# Check Python processes
Get-Process python
```

---

## Next Steps After Setup

1. **Explore the Web UI**: Navigate to `http://localhost:7000`
2. **Add RSS Sources**: Use the Sources tab to add RSS feeds
3. **Create a Podcast**: Use the Podcast Agent to generate your first podcast
4. **Monitor Tasks**: Check the Voyager/Tasks tab for scheduled jobs

---

## Stopping the Application

To stop all services:

1. Press `Ctrl+C` in each terminal window
2. Stop Redis if needed: `redis-cli shutdown` (or stop the service)

---

## Need Help?

If you encounter issues not covered here:

1. Check the main README.md for more details
2. Review error messages in the terminal outputs
3. Verify all environment variables are set correctly
4. Ensure all prerequisites are installed

---

## Testing Checklist

- [ ] Redis is running and accessible
- [ ] Virtual environment is activated
- [ ] All Python dependencies installed
- [ ] `.env` file created with API keys
- [ ] Backend server starts without errors
- [ ] Scheduler service starts successfully
- [ ] Celery worker starts successfully
- [ ] API endpoints respond correctly
- [ ] Web interface loads (if frontend built)
- [ ] Can create a new session
- [ ] Can send a message to the podcast agent

---

**Good luck with testing! 🚀**

