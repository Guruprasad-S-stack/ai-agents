# 🏗️ PodcastAgent Backend Architecture Walkthrough

This document provides a comprehensive understanding of the PodcastAgent backend architecture, components, and how everything works together.

---

## 📐 Overall Architecture

PodcastAgent uses a **multi-service architecture** with three main components:

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│              http://localhost:3000 or :7000                  │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST API
┌──────────────────────▼──────────────────────────────────────┐
│              FastAPI Backend (main.py)                      │
│              - REST API Endpoints                            │
│              - Serves React frontend                         │
│              - Manages sessions                              │
└──────┬──────────────────┬──────────────────┬────────────────┘
       │                  │                  │
       │                  │                  │
┌──────▼──────┐  ┌────────▼────────┐  ┌──────▼──────────┐
│   Redis     │  │  Celery Worker │  │   Scheduler     │
│  (Message   │  │  (Background   │  │  (Task Runner)  │
│   Broker)   │  │   Processing)  │  │                 │
└─────────────┘  └────────────────┘  └─────────────────┘
```

### **Three Services Running:**

1. **Backend Server** (`main.py`) - FastAPI web server
2. **Celery Worker** (`celery_worker.py`) - Processes AI agent tasks asynchronously
3. **Scheduler** (`scheduler.py`) - Runs scheduled tasks (RSS feeds, social media scraping)

---

## 🎯 Core Agentic Framework: **Agno**

**Agno** is the AI agent framework used here. It's similar to LangChain but more focused on agent orchestration.

### Key Agno Concepts:

- **Agent**: The main AI assistant that can use tools and maintain state
- **Tools**: Functions the agent can call (search, scrape, generate audio, etc.)
- **Storage**: SQLite storage for conversation history and session state
- **Session State**: Persistent state across conversations

### Why Agno?

- Built-in tool calling and function execution
- Session management with SQLite
- Easy integration with OpenAI, Anthropic, etc.
- Supports complex multi-step workflows

---

## 📦 Key Packages & Their Roles

### **Core Framework:**
- **`agno==1.4.2`** - AI agent framework (the brain of the system)
- **`fastapi==0.115.12`** - Web framework for REST API
- **`celery==5.5.2`** - Distributed task queue for async processing
- **`redis==5.3.0`** - Message broker for Celery + session locking

### **AI/ML / Search:**
- **`google-generativeai`** - Gemini models (2.5 Pro / 2.5 Flash) for orchestration, extraction
- **`tavily-python`** - Tavily search API (primary web search tool)
- **`sentence-transformers==4.1.0`** - Embeddings for semantic search (optional/local)
- **`faiss-cpu==1.9.0`** - Vector similarity search (optional)

### **Web Scraping & Browser:**
- **`crawl4ai`** - LLM-powered scraping/extraction (used with Gemini), parallel asyncio
- **`playwright==1.52.0`** - Browser automation engine (used only if browser_use is enabled)
- **`beautifulsoup4`**, **`newspaper4k`** - HTML parsing / legacy extraction (fallback)

### **Text-to-Speech:**
- **`edge-tts`** - Primary TTS (free, parallel, fast)
- **`elevenlabs==1.57.0`** - Optional TTS
- **`openai`** - Optional TTS

### **Database:**
- **`aiosqlite==0.21.0`** - Async SQLite for databases
- **`sqlalchemy==2.0.40`** - ORM for task scheduling

### **Scheduling:**
- **`APScheduler==3.11.0`** - Advanced Python Scheduler for cron jobs

### **Utilities:**
- **`python-dotenv==1.1.0`** - Load environment variables from .env
- **`feedparser==6.0.11`** - RSS feed parsing
- **`pydantic==2.10.6`** - Data validation

---

## 🔑 Required API Keys

### **Essential:**
```env
OPENAI_API_KEY=sk-...          # REQUIRED - For AI agent (GPT-4o)
```

### **Optional but Recommended:**
```env
ELEVENSLAB_API_KEY=...         # For high-quality TTS (optional - can use OpenAI TTS)
```

### **Infrastructure (No API Key Needed):**
```env
REDIS_HOST=localhost          # Redis server location
REDIS_PORT=6379               # Redis port
REDIS_DB=0                    # Redis database number
```

**Where to get keys:**
- **OpenAI**: https://platform.openai.com/api-keys
- **ElevenLabs**: https://elevenlabs.io/app/settings/api-keys

---

## 📁 Directory Structure & File Purposes

### **`main.py`** - Application Entry Point
- **Purpose**: FastAPI web server that handles all HTTP requests
- **What it does**:
  - Initializes databases on startup
  - Registers all API routes
  - Serves React frontend (if built)
  - Handles file streaming (audio, recordings)
- **Runs on**: Port 7000 by default

### **`celery_worker.py`** - Background Task Processor
- **Purpose**: Processes AI agent tasks asynchronously
- **What it does**:
  - Listens to Redis for tasks
  - Runs AI agent when user sends message
  - Prevents concurrent processing of same session
- **Why separate**: AI processing can take 30+ seconds, so it runs in background

### **`scheduler.py`** - Automated Task Runner
- **Purpose**: Runs scheduled tasks (RSS feeds, social media scraping)
- **What it does**:
  - Checks database for pending scheduled tasks
  - Executes processors (feed_processor, x_scraper, etc.)
  - Updates task status
- **Runs**: Continuously, checking every few seconds

---

## 🗂️ Core Directories Explained

### **`routers/`** - API Endpoints
Each file defines REST API endpoints:

- **`async_podcast_agent_router.py`** - Chat endpoints (`/api/podcast-agent/chat`)
- **`article_router.py`** - Article management (`/api/articles`)
- **`source_router.py`** - RSS source management (`/api/sources`)
- **`podcast_router.py`** - Podcast CRUD (`/api/podcasts`)
- **`task_router.py`** - Scheduled task management (`/api/tasks`)
- **`social_media_router.py`** - Social media data (`/api/social-media`)

### **`services/`** - Business Logic
Contains core service classes:

- **`async_podcast_agent_service.py`** - Manages agent sessions and chat
- **`celery_tasks.py`** - Defines the `agent_chat` Celery task
- **`celery_app.py`** - Celery configuration and session locking
- **`db_init.py`** - Database initialization
- **`article_service.py`** - Article business logic
- **`podcast_service.py`** - Podcast generation logic
- **`task_service.py`** - Task scheduling logic

### **`agents/`** - Specialized AI Agents
Sub-agents that handle specific tasks:

- **`search_agent.py`** - Searches for articles/content
- **`scrape_agent.py`** - Scrapes web pages
- **`script_agent.py`** - Generates podcast scripts
- **`image_generate_agent.py`** - Creates podcast banners
- **`audio_generate_agent.py`** - Generates audio from text (Edge TTS primary; ElevenLabs/OpenAI optional)

### **`tools/`** - Agent Tools
Functions the main agent can call:

- **`tavily_search.py`** - Primary web search (Tavily API)
- **Backups**: `google_news_discovery.py`, `wikipedia_search.py`, `DuckDuckGoTools` (via search agent)
- **`crawl4ai_scraper.py`** - LLM-powered scraping/extraction (parallel)
- **`web_search.py`** - Browser-use/Playwright (currently disabled by default)
- **`user_source_selection.py`** - UI tool (auto-select fallback if called without indices)
- **`ui_manager.py`** - Manages UI state (blocks source selection UI)
- **`session_state_manager.py`** - Manages session state
- **`social/`** - Social media scrapers (X.com, Facebook)

### **`processors/`** - Background Processors
Standalone scripts that process content:

- **`feed_processor.py`** - Processes RSS feeds
- **`url_processor.py`** - Processes individual URLs
- **`ai_analysis_processor.py`** - AI analysis of content
- **`embedding_processor.py`** - Creates vector embeddings
- **`faiss_indexing_processor.py`** - Builds search index
- **`podcast_generator_processor.py`** - Generates podcasts
- **`x_scraper_processor.py`** - Scrapes X.com (Twitter)
- **`fb_scraper_processor.py`** - Scrapes Facebook

### **`db/`** - Database Layer
Database schemas and connection management:

- **`config.py`** - Database paths and configuration
- **`connection.py`** - Database connection utilities
- **`articles.py`** - Article database schema
- **`podcasts.py`** - Podcast database schema
- **`tasks.py`** - Task database schema
- **`agent_config_v2.py`** - Agent instructions and configuration

### **`models/`** - Data Models (Pydantic)
Request/response schemas:

- **`article_schemas.py`** - Article data models
- **`podcast_schemas.py`** - Podcast data models
- **`source_schemas.py`** - Source data models
- **`tasks_schemas.py`** - Task data models

### **`utils/`** - Utility Functions
Helper functions:

- **`load_api_keys.py`** - Loads API keys from .env
- **`text_to_audio_*.py`** - TTS engine wrappers
- **`tts_engine_selector.py`** - Selects TTS engine
- **`rss_feed_parser.py`** - RSS parsing utilities
- **`crawl_url.py`** - URL crawling utilities

---

## 🔄 How It All Works Together

### **1. User Sends Message (Chat Flow)**

```
User → Frontend → POST /api/podcast-agent/chat
                ↓
         async_podcast_agent_router.py
                ↓
    async_podcast_agent_service.py
                ↓
         Creates Celery Task
                ↓
         Redis Queue
                ↓
    celery_worker.py (picks up task)
                ↓
    services/celery_tasks.py::agent_chat()
                ↓
    Creates Agno Agent with tools
                ↓
    Agent processes message, calls tools
                ↓
    Returns response
                ↓
    Frontend polls /api/podcast-agent/status
                ↓
    User sees response
```

### **2. Scheduled Task Flow (RSS Feed)**

```
Scheduler (scheduler.py) runs every 30 seconds
                ↓
    Checks database for pending tasks
                ↓
    Finds RSS feed task scheduled for now
                ↓
    Executes: python -m processors.feed_processor
                ↓
    Processor fetches RSS feed
                ↓
    Saves articles to database
                ↓
    Updates task status to "completed"
```

### **3. Agent Tool Execution**

When the agent needs to search for articles:

```
Agent receives: "Find articles about AI"
                ↓
    Calls tool: search_articles()
                ↓
    search_articles() queries database
                ↓
    Returns results to agent
                ↓
    Agent uses results in response
```

---

## 🗄️ Database Structure

The system uses **SQLite** databases stored in `databases/`:

1. **`agent_sessions.db`** - Chat history and session state
2. **`articles.db`** - Stored articles from RSS/sources
3. **`podcasts.db`** - Generated podcasts
4. **`sources.db`** - RSS feed sources
5. **`tasks.db`** - Scheduled tasks
6. **`social_media.db`** - Social media posts

---

## 🔐 Session Management

### **Session Locking:**
- Uses Redis to prevent concurrent processing
- If user sends message while one is processing, returns "busy" status
- Lock expires after 10 minutes

### **Session State:**
- Stored in SQLite via Agno's storage
- Tracks: current stage, selected sources, language, etc.
- Persists across restarts

---

## 🚀 Starting the System

### **Step 1: Start Backend**
```bash
cd backend
python main.py
```
- Initializes databases
- Starts FastAPI server on port 7000

### **Step 2: Start Celery Worker** (New Terminal)
```bash
cd backend
python -m celery_worker
```
- Connects to Redis
- Waits for tasks

### **Step 3: Start Scheduler** (New Terminal)
```bash
cd backend
python -m scheduler
```
- Starts background scheduler
- Begins checking for scheduled tasks

---

## 🎯 Key Design Decisions

1. **Why Celery?** - AI processing is slow (30+ seconds), so it runs asynchronously
2. **Why Redis?** - Fast message broker + session locking
3. **Why SQLite?** - Simple, no setup needed, perfect for single-server deployment
4. **Why Agno?** - Built-in tool calling, session management, and state persistence
5. **Why FastAPI?** - Modern, fast, async-capable, auto-documentation

---

## 📝 Next Steps

Now that you understand the architecture:

1. **Set up environment**: Create `.env` with API keys
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Start services**: Follow the startup sequence above
4. **Test**: Send a message through the API or frontend

---

## 🔍 Debugging Tips

- **Check Redis**: `redis-cli ping` should return `PONG`
- **Check Celery**: Look for worker connection messages
- **Check Logs**: All services print to console
- **Database Location**: Check `databases/` folder
- **Session Issues**: Check Redis locks with `redis-cli keys "lock:*"`

---

This architecture provides a scalable, maintainable system for AI-powered podcast generation! 🎙️

