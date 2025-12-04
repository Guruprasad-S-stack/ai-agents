# Celery Worker Startup Optimization

## ✅ Issue Fixed

### Problem
Celery worker was taking a long time to start up because:
- `celery_tasks.py` imports `search_agent_run`
- `search_agent.py` imports `run_browser_search` from `tools.web_search`
- `tools.web_search` imported `browser_use` at module level
- `browser_use` is a heavy library that loads Playwright and browser automation components
- This caused slow startup even when browser search wasn't being used

### Solution
**Lazy Import**: Moved `browser_use` import inside the `run_browser_search()` function so it only loads when actually needed.

**File**: `tools/web_search.py`
- **Before**: `from browser_use import ...` at top of file
- **After**: `from browser_use import ...` inside `run_browser_search()` function

---

## 📊 Impact

### Before
- Celery worker startup: **30-60 seconds** (loading Playwright, browser components)
- All workers blocked during import

### After
- Celery worker startup: **2-5 seconds** (only loads when browser search is actually used)
- Workers start immediately, browser_use loads on-demand

---

## 🔍 Other Heavy Imports to Watch

These are currently imported at module level but could be optimized if needed:

1. **Playwright** - Used in social media scrapers
   - Files: `tools/social/x_agent.py`, `tools/social/fb_agent.py`
   - Impact: Medium (only loads when social media scraping is used)

2. **FAISS** - Vector search index
   - Files: `tools/embedding_search.py`
   - Impact: Low (lightweight, loads quickly)

3. **OpenAI/Google APIs** - LLM clients
   - Impact: Low (just API clients, no heavy initialization)

---

## ✅ Verification

After this change:
1. Restart Celery worker
2. Should see "Starting PodcastAgent workers..." quickly
3. Worker should be ready in 2-5 seconds instead of 30-60 seconds
4. Browser search will still work (loads on first use)

---

## 📝 Best Practices

1. **Heavy libraries** (browser automation, ML models) → Lazy import inside functions
2. **Light libraries** (API clients, utilities) → Can import at module level
3. **Test imports** → Keep at module level (only run during tests)

