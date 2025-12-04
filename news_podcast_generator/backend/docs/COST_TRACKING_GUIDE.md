# Professional Cost Tracking Guide

## Overview

This guide explains how to implement **scientific, professional cost tracking** for Gemini API calls by extracting **exact token counts** from API responses and calculating costs accurately.

## Key Concepts

### 1. Exact Token Counts vs Estimates

**❌ Estimates (Inaccurate):**
```python
# BAD: Estimating tokens from character count
tokens = len(text) / 3.5  # Approximation, not exact!
```

**✅ Exact Counts (Accurate):**
```python
# GOOD: Getting exact counts from API response
usage = response.usage_metadata
input_tokens = usage.prompt_token_count  # Exact!
output_tokens = usage.candidates_token_count  # Exact!
```

### 2. How Gemini API Returns Token Counts

The Gemini API response includes a `usage_metadata` object with exact token counts:

```python
response = model.generate_content("Hello")
usage = response.usage_metadata

print(usage.prompt_token_count)      # Exact input tokens
print(usage.candidates_token_count)   # Exact output tokens
print(usage.total_token_count)        # Total tokens
```

## Implementation

### Step 1: Install Cost Tracking System

The cost tracking system is already created in:
- `utils/cost_tracker.py` - Core tracking logic
- `utils/gemini_cost_wrapper.py` - Wrapper for API calls

### Step 2: Integrate into Your Agents

#### Example: Search Agent

**Before (no tracking):**
```python
def search_agent_run(agent: Agent, query: str) -> str:
    search_agent = Agent(
        model=Gemini(id="gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY")),
        # ... config ...
    )
    response = search_agent.run(query, session_id=session_id)
    return response.content
```

**After (with tracking):**
```python
from utils.gemini_cost_wrapper import GeminiCostWrapper

def search_agent_run(agent: Agent, query: str) -> str:
    search_agent = Agent(
        model=Gemini(id="gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY")),
        # ... config ...
    )
    response = search_agent.run(query, session_id=session_id)
    
    # Track cost - extracts exact token counts from response
    wrapper = GeminiCostWrapper()
    wrapper.track_response(response, "gemini-2.5-flash", context="search_agent")
    
    return response.content
```

### Step 3: Query Cost Summaries

```python
from utils.cost_tracker import get_cost_tracker
from datetime import datetime, timedelta

tracker = get_cost_tracker()

# Overall summary
summary = tracker.get_cost_summary()
print(f"Total Cost: ${summary['total_cost']:.6f}")
print(f"Total Calls: {summary['total_calls']}")
print(f"Total Tokens: {summary['total_input_tokens'] + summary['total_output_tokens']:,}")

# Today's costs
today_start = datetime.now().replace(hour=0, minute=0, second=0)
today = tracker.get_total_cost(start_date=today_start)
print(f"Today's Cost: ${today['total_cost']:.6f}")

# By context (e.g., search_agent, scrape_agent)
search_costs = tracker.get_total_cost(context="search_agent")
print(f"Search Agent Cost: ${search_costs['total_cost']:.6f}")
```

## How It Works

### 1. Token Extraction

The `GeminiCostWrapper` tries multiple methods to extract usage metadata:

1. **Direct API response** (`response.usage_metadata`)
2. **Agno Agent wrapper** (`response.response.usage_metadata`)
3. **Metadata dictionary** (`response.metadata['usage']`)
4. **Response attributes** (checks various attribute names)

### 2. Cost Calculation

Costs are calculated based on official Gemini pricing:

```python
# Gemini 2.5 Flash pricing
input_cost = (input_tokens / 1_000_000) * 0.30   # $0.30 per 1M tokens
output_cost = (output_tokens / 1_000_000) * 2.50  # $2.50 per 1M tokens
total_cost = input_cost + output_cost
```

### 3. Database Storage

All API calls are stored in SQLite database (`cost_tracking.db`):

```sql
CREATE TABLE api_calls (
    call_id TEXT UNIQUE,
    model TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    input_cost REAL,
    output_cost REAL,
    total_cost REAL,
    context TEXT,
    timestamp TEXT
)
```

## Testing

Run the test script to verify everything works:

```bash
python test_cost_tracking.py
```

This will:
1. Test direct Gemini API calls
2. Test Agno Agent calls
3. Show cost summaries
4. Demonstrate usage extraction

## Integration Checklist

- [ ] Add `from utils.gemini_cost_wrapper import GeminiCostWrapper` to your agent files
- [ ] Add `wrapper.track_response()` after each `agent.run()` call
- [ ] Set appropriate `context` parameter (e.g., "search_agent", "scrape_agent")
- [ ] Query cost summaries periodically
- [ ] Monitor costs in production

## Example: Complete Integration

```python
# agents/search_agent.py
from utils.gemini_cost_wrapper import GeminiCostWrapper

def search_agent_run(agent: Agent, query: str) -> str:
    # ... existing code ...
    
    response = search_agent.run(query, session_id=session_id)
    
    # Track cost with exact token counts
    wrapper = GeminiCostWrapper()
    wrapper.track_response(
        response, 
        model="gemini-2.5-flash",
        context="search_agent"
    )
    
    # ... rest of code ...
    return response.content
```

## Cost Monitoring Dashboard (Optional)

You can create a simple dashboard to monitor costs:

```python
from utils.cost_tracker import get_cost_tracker
from datetime import datetime, timedelta

def print_cost_dashboard():
    tracker = get_cost_tracker()
    
    # Today
    today_start = datetime.now().replace(hour=0, minute=0, second=0)
    today = tracker.get_total_cost(start_date=today_start)
    
    # This week
    week_start = today_start - timedelta(days=7)
    week = tracker.get_total_cost(start_date=week_start)
    
    # By context
    search = tracker.get_total_cost(context="search_agent")
    scrape = tracker.get_total_cost(context="scrape_agent")
    
    print("=" * 70)
    print("COST DASHBOARD")
    print("=" * 70)
    print(f"Today:     ${today['total_cost']:.6f} ({today['total_calls']} calls)")
    print(f"This Week: ${week['total_cost']:.6f} ({week['total_calls']} calls)")
    print(f"Search:    ${search['total_cost']:.6f} ({search['total_calls']} calls)")
    print(f"Scrape:    ${scrape['total_cost']:.6f} ({scrape['total_calls']} calls)")
    print("=" * 70)
```

## Important Notes

1. **Exact Token Counts**: The system extracts exact token counts from API responses, not estimates
2. **Automatic Tracking**: Once integrated, costs are tracked automatically for every API call
3. **Context Tracking**: Use meaningful context names to track costs by agent/function
4. **Database**: All costs are stored in SQLite for historical analysis
5. **Free Tier**: Costs are tracked even on free tier (shows $0.00 but tracks usage)

## Troubleshooting

### Issue: "Could not extract token usage"

**Solution**: The API response format may have changed. Check:
1. Response type: `print(type(response))`
2. Available attributes: `print([attr for attr in dir(response) if not attr.startswith('_')])`
3. Update `extract_usage_from_response()` in `gemini_cost_wrapper.py`

### Issue: Agno Agent responses not tracked

**Solution**: Agno Agent may wrap the response. Check:
1. `response.response.usage_metadata` (nested response)
2. `response.metadata` (metadata dictionary)
3. Add more extraction methods to the wrapper

## Next Steps

1. Integrate cost tracking into `search_agent.py`
2. Integrate cost tracking into `scrape_agent.py`
3. Create a cost monitoring endpoint in your API
4. Set up alerts for high costs
5. Generate daily/weekly cost reports

