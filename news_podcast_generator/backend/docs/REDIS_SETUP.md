# Redis Setup Guide for Windows

## Option 1: Docker Desktop (Recommended)

### Step 1: Install Docker Desktop
1. Download from: https://www.docker.com/products/docker-desktop/
2. Install and restart your computer
3. Start Docker Desktop (wait for it to fully start)

### Step 2: Start Redis Container
Open PowerShell in the `backend` folder and run:

```powershell
docker run -d --name redis-podcast -p 6379:6379 redis:7-alpine
```

### Step 3: Verify Redis is Running
```powershell
docker ps
# Should show redis-podcast container running

# Test connection
docker exec -it redis-podcast redis-cli ping
# Should return: PONG
```

### Step 4: Stop Redis (when needed)
```powershell
docker stop redis-podcast
```

### Step 5: Start Redis Again (after restart)
```powershell
docker start redis-podcast
```

---

## Option 2: Install Redis Directly on Windows

### Using Memurai (Redis-compatible for Windows)
1. Download from: https://www.memurai.com/get-memurai
2. Install Memurai
3. It will run as a Windows service automatically
4. Default port: 6379 (same as Redis)

### Using WSL2 + Redis (Alternative)
1. Install WSL2: `wsl --install`
2. Restart computer
3. In WSL terminal: `sudo apt update && sudo apt install redis-server -y`
4. Start Redis: `sudo service redis-server start`

---

## Option 3: Cloud Redis (Quick Testing)

### Redis Cloud (Free Tier)
1. Sign up: https://redis.com/try-free/
2. Create a free database
3. Get connection URL
4. Update `.env`:
   ```
   REDIS_HOST=your-redis-host.redis.cloud
   REDIS_PORT=12345
   REDIS_DB=0
   ```

---

## Verify Redis Connection

After setup, test from Python:

```powershell
python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); print('✅ Redis connected!' if r.ping() else '❌ Connection failed')"
```

---

## Current Configuration

Your app expects Redis at:
- **Host**: `localhost` (or from `.env` `REDIS_HOST`)
- **Port**: `6379` (or from `.env` `REDIS_PORT`)
- **Database**: `0` (or from `.env` `REDIS_DB`)

Make sure your `.env` file has:
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```


