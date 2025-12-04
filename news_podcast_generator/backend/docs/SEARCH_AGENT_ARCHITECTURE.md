# Search Agent Architecture: How Tools Are Selected

## 🔍 How It Actually Works

### **NOT a Hardcoded Sequence**

The search agent does **NOT** work like this:
```python
# ❌ This is NOT how it works
try:
    google_news_discovery()
except:
    try:
        browser_search()
    except:
        try:
            duckduckgo()
        except:
            ...
```

### **LLM-Driven Decision Making**

Instead, it works like this:

1. **All tools are registered** (lines 96-105 in `search_agent.py`):
   ```python
   tools=[
       google_news_discovery_run,
       DuckDuckGoTools(),
       wikipedia_search,
       jikan_search,
       embedding_search,
       social_media_search,
       social_media_trending_search,
       search_articles,
       run_browser_search,  # ← browser_search is just one of many tools
   ]
   ```

2. **LLM (Gemini) sees all tools** and decides which to use based on:
   - The query content
   - The instructions (priority guidance)
   - Tool descriptions
   - Previous tool results (if any)

3. **LLM can call multiple tools**:
   - It might call `google_news_discovery` first
   - Then call `embedding_search` for diversity
   - Then call `wikipedia_search` for background
   - **OR** it might skip some tools entirely if not needed

4. **If a tool returns an error**:
   - LLM sees the error message
   - LLM decides to try another tool
   - Instructions guide it: "If tool X fails, try tool Y"

---

## 📊 Example Flow

### Scenario 1: News Query
```
User: "Latest AI news"

LLM Reasoning:
1. "This is a news query, I should use google_news_discovery first"
2. Calls: google_news_discovery("Latest AI news")
3. Gets results: 5 articles
4. "Good results, but let me also check embedding_search for more diversity"
5. Calls: embedding_search("AI news")
6. Gets results: 3 more articles
7. "I have 8 diverse sources, that's enough. No need for browser_search."
8. Returns: Combined results
```

### Scenario 2: DuckDuckGo Rate Limited
```
User: "Quantum computing"

LLM Reasoning:
1. "Let me try duckduckgo first"
2. Calls: duckduckgo("Quantum computing")
3. Gets error: "Rate limit error"
4. "DuckDuckGo failed, instructions say to try google_news_discovery or browser_search"
5. Calls: google_news_discovery("Quantum computing")
6. Gets results: 4 articles
7. "Good results, no need for expensive browser_search"
8. Returns: Results from Google News
```

### Scenario 3: All Simple Tools Fail
```
User: "Obscure topic XYZ"

LLM Reasoning:
1. Calls: google_news_discovery("Obscure topic XYZ")
2. Gets: "No results found"
3. Calls: duckduckgo("Obscure topic XYZ")
4. Gets: "Rate limit error"
5. Calls: wikipedia_search("Obscure topic XYZ")
6. Gets: "Wikipedia API error"
7. "All simple tools failed. Instructions say browser_search is reliable fallback"
8. Calls: browser_search("Search for information about Obscure topic XYZ")
9. Gets: Results from browser automation
10. Returns: Browser search results
```

---

## 🎯 Key Points

### 1. **Browser Search is NOT Always Called**
- It's only called if:
  - Other tools fail
  - LLM decides it's needed for the query
  - Instructions suggest it as fallback

### 2. **LLM Decides Tool Selection**
- Not hardcoded sequence
- LLM uses reasoning to choose tools
- Can call multiple tools or skip tools
- Can call tools in any order

### 3. **Instructions Guide, Not Enforce**
- Instructions say: "Prefer google_news_discovery first"
- But LLM can override if it thinks another tool is better
- Instructions are suggestions, not hard rules

### 4. **Error Handling is LLM-Driven**
- When a tool returns an error, LLM sees the error message
- LLM decides whether to try another tool
- Instructions guide: "If tool X fails, try tool Y"

---

## 🔄 Actual Architecture

```
User Query
    ↓
Search Agent (Gemini LLM)
    ↓
LLM Sees: [tool1, tool2, tool3, ..., browser_search]
    ↓
LLM Decides: "I'll try tool1 first"
    ↓
Tool1 Called → Returns Results/Error
    ↓
LLM Sees Results/Error
    ↓
LLM Decides: "Need more diversity, try tool2"
    OR "Tool1 failed, try browser_search"
    OR "Enough results, return"
    ↓
Final Results Returned
```

---

## ✅ Summary

- **Browser search is NOT part of a mandatory sequence**
- **Browser search is a fallback option** that LLM can choose
- **LLM decides** which tools to use based on query + instructions
- **All tools are available**, but not all are called
- **Error handling** is LLM-driven, not hardcoded try/except chains

The architecture is **intelligent and adaptive**, not rigid and sequential.

