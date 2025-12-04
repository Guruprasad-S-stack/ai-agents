# PodcastAgent (Backend) – Current Agentic Architecture

## Overview
Agentic pipeline to go from user topic → search → scrape → script → audio, optimized for speed, cost, and reliability on Gemini + free TTS.

## End-to-End Flow (fast path)
1) User sends topic in Studio.
2) `search_agent_run` (Agno tool)  
   - Primary: `tavily_search` (LLM-augmented search API).  
   - Backups: `google_news_discovery`, `DuckDuckGoTools`, `wikipedia_search`.  
   - Hard cap: exactly 5 sources; auto-trims extras, warns if fewer.  
   - `is_scrapping_required` set for all URLs; results saved to session state.
3) `scrape_agent_run`  
   - Uses `crawl4ai_scraper` (Gemini LLM extraction) with parallel asyncio scraping.  
   - Hard cap: 5 URLs.  
   - Auto-confirms all scraped sources; sets `sources_auto_confirmed=True` in session state. ThHis bypasses user confirmaton for lower latency
4) `podcast_script_agent_run`  
   - Generates conversational, two-host script using all confirmed sources.  
   - Script saved to session state; script confirmation UI is skipped for speed.
5) `audio_generate_agent_run`  
   - Primary TTS: Edge TTS , parallel generation, FFmpeg path auto-detected (WinGet).  
   - Fallbacks available: ElevenLabs, OpenAI (if keys provided).  
   - Combines segments, saves final MP3, updates session state and audio URL.
6) UI updates  
   - Source selection UI blocked (`ui_manager`: show_sources_for_selection disabled).  
   - Script confirmation skipped; audio confirmation can be shown.  
   - Final assistant message: “I have completed your podcast on ‘<title>’ …”

## Key Architecture Changes (latest)
- Search: Replaced browser-use path with Tavily as primary; backups remain (Google News, DuckDuckGoTools, Wikipedia).  
- Scrape: Replaced Playwright/Newspaper with Crawl4AI (Gemini LLM extraction), parallel scraping, hard cap 5 URLs, auto-confirm sources.  
- Audio: Switched to Edge TTS by default; parallel async generation; FFmpeg configured before pydub import to avoid WinError 2; manual streaming write replaces flaky `save()`.  
- Flow: Skipped source and script confirmations to hit <5 min end-to-end; orchestrator prompt updated accordingly.  
- Logging: `flush=True` across agents; added timing logs in Celery task init; improved error handling in search/scrape tools.  
- Cost/Docs/Tests: Added cost-tracking utilities (`utils/cost_tracker.py`, `gemini_cost_wrapper.py`), example integration, and reorganized docs/tests.

## Tooling Summary
- Search tools: `tavily_search`, `google_news_discovery`, `DuckDuckGoTools`, `wikipedia_search` (browser_use disabled by default).  
- Scrape tools: `crawl4ai_scraper` (LLM extraction with Gemini), fallback to browser crawler if enabled.  
- UI tools: `ui_manager_run` (source selection blocked), `user_source_selection_run` auto-selects if called without indices.  
- TTS: Edge TTS (parallel, free), ElevenLabs/OpenAI as optional fallbacks.

## Operational Notes
- FFmpeg: auto-discovered from WinGet path; pydub configured before import to prevent missing-exe errors.  
- Rate limits: Gemini calls reduced by hard-capping sources to 5 and parallelizing scraping/tts.  
- Sensitive files: `credentials.json` ignored; large audio/recordings ignored.  
- Logs: use `start_celery_with_logging.py` or `watch_celery_log.ps1` for full worker logs.
- Celery & Redis (scaling):  
  - Redis = broker + result backend. Each user chat message is enqueued as a Celery task (`services.celery_tasks.agent_chat`).  
  - Workers: start with `python -u celery_worker.py` (or `start_celery_with_logging.py`). Increase concurrency via `-c N` to scale horizontally/vertically.  
  - Agent startup: Celery task loads session state from SQLite (`internal_sessions.db`), instantiates Agno Agent with tools, then runs the workflow (search→scrape→script→audio) inside the worker.  
  - Scaling: add more workers (or containers/VMs) pointing to the same Redis broker; sessions are isolated by `session_id`, so tasks are safe to run in parallel.  
  - Keep broker and worker clocks roughly in sync; monitor Redis memory for large payloads (scraped content).
- Embedded SQL / processors (social + articles):  
  - The app keeps an embedded SQLite store (`databases/`) for articles, embeddings, and session state.  
  - Processor modules (e.g., `processors/x_scraper_processor.py`) handle social media scraping/ingest into SQLite.  
  - Search agent can still fall back to local/article DB queries when configured, but the primary path is live web search + scrape.  
  - Social media/search processors run via Celery as well, so they scale with additional workers and reuse the same Redis broker.

## Quick Start (backend)
```bash
pip install -r requirements.txt      # or requirements-minimal.txt
python -m playwright install         # if using browser-based tools
python main.py                       # FastAPI
python -u celery_worker.py           # Celery worker (or use start_celery_with_logging.py)
```

## Frontend Wait Messaging
- Updated loading text to: “🎙️ Creating your podcast! Expected time: 3-5 mins. Hold tight for an engaging conversation...”

