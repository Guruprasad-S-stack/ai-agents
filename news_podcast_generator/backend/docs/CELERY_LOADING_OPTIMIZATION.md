# Celery Loading Optimization Status

## ✅ Already Optimized

### 1. **Browser Search (browser_use)** ✅
- **File**: `tools/web_search.py`
- **Status**: Lazy imported inside function
- **Impact**: Prevents 30-60 second startup delay
- **Code**: `from browser_use import ...` is inside `run_browser_search()` function

---

## ⚠️ Potential Optimizations Needed

### 1. **Browser Crawler (Playwright)** ⚠️
- **File**: `tools/browser_crawler.py`
- **Issue**: Imports `playwright` at module level (line 1)
- **Import Chain**: 
  ```
  celery_tasks.py 
    → scrape_agent.py 
      → browser_crawler.py 
        → playwright (HEAVY - loads at startup)
  ```
- **Impact**: Medium - Playwright loads even when scraping isn't used
- **Recommendation**: Lazy import Playwright inside `PlaywrightScraper.__init__()` or methods

### 2. **Social Media Browser (Playwright)** ✅ (Acceptable)
- **File**: `tools/social/browser.py`
- **Status**: Imports `playwright` at module level
- **Import Chain**: Only imported when social media tools are actually used
- **Impact**: Low - Not imported in `celery_tasks.py` directly
- **Recommendation**: Keep as-is (only loads when needed)

---

## 📊 Current Import Chain Analysis

### Heavy Imports in Startup Path:

```
celery_tasks.py (STARTUP)
  ├─ search_agent.py
  │   ├─ web_search.py ✅ (browser_use lazy imported)
  │   ├─ social_media_search.py ✅ (lightweight)
  │   └─ Other tools ✅ (lightweight)
  │
  ├─ scrape_agent.py
  │   └─ browser_crawler.py ⚠️ (playwright imported at module level)
  │
  ├─ script_agent.py ✅ (lightweight)
  ├─ audio_generate_agent.py ✅ (scipy/soundfile - acceptable)
  └─ Other tools ✅ (lightweight)
```

---

## 🔧 Recommended Optimization

### Fix Browser Crawler Lazy Import

**File**: `tools/browser_crawler.py`

**Current** (line 1):
```python
from playwright.sync_api import sync_playwright  # ❌ Loads at import time
```

**Recommended**:
```python
# Remove top-level import
# Add lazy import inside methods:
def scrape_urls(self, urls: List[str]) -> List[Dict]:
    from playwright.sync_api import sync_playwright  # ✅ Loads only when used
    with sync_playwright() as playwright:
        ...
```

**Impact**: 
- **Before**: Playwright loads during Celery startup (~5-10 seconds)
- **After**: Playwright loads only when scraping is actually used
- **Savings**: ~5-10 seconds faster startup

---

## ✅ Current Status Summary

| Component | Status | Impact | Action Needed |
|-----------|--------|--------|---------------|
| browser_use | ✅ Optimized | High | None |
| browser_crawler | ⚠️ Can optimize | Medium | Lazy import Playwright |
| social/browser | ✅ Acceptable | Low | None |
| Other imports | ✅ Optimized | Low | None |

---

## 🎯 Overall Assessment

**Current State**: **Mostly Optimized** ✅

- Main heavy import (`browser_use`) is already lazy loaded
- One medium optimization opportunity (`browser_crawler`)
- Startup should be reasonably fast (~5-10 seconds vs 30-60 seconds before)

**Recommendation**: 
- ✅ **Current state is acceptable** for production
- ⚠️ **Optional**: Optimize `browser_crawler.py` for even faster startup (saves ~5-10 seconds)

