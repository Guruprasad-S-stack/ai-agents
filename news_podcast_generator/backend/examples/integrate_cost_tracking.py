"""
Example: How to integrate cost tracking into your agents.

This shows how to modify search_agent.py and scrape_agent.py to track costs.
"""

# ============================================================================
# EXAMPLE 1: Integrate into search_agent.py
# ============================================================================

def search_agent_run_with_tracking(agent, query: str) -> str:
    """
    Modified search_agent_run with cost tracking.
    
    Original code:
        response = search_agent.run(query, session_id=session_id)
        return response
    
    Modified code:
        response = search_agent.run(query, session_id=session_id)
        track_cost(response)  # Add this line
        return response
    """
    from agno.agent import Agent
    from agno.models.google import Gemini
    from utils.gemini_cost_wrapper import GeminiCostWrapper
    import os
    
    # ... existing code ...
    
    search_agent = Agent(
        model=Gemini(id="gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY")),
        # ... other config ...
    )
    
    response = search_agent.run(query, session_id=session_id)
    
    # ADD THIS: Track cost for this API call
    wrapper = GeminiCostWrapper()
    wrapper.track_response(response, "gemini-2.5-flash", context="search_agent")
    
    # ... rest of existing code ...
    return response


# ============================================================================
# EXAMPLE 2: Integrate into scrape_agent.py (for LLM verification)
# ============================================================================

def verify_content_with_agent_tracking(agent, query, search_results, use_agent=True):
    """
    Modified verify_content_with_agent with cost tracking.
    """
    from agno.agent import Agent
    from agno.models.google import Gemini
    from utils.gemini_cost_wrapper import GeminiCostWrapper
    import os
    
    if not use_agent:
        return search_results
    
    verified_search_results = []
    wrapper = GeminiCostWrapper()  # Create wrapper once
    
    for _, search_result in enumerate(search_results):
        # ... existing code ...
        
        scrape_agent = Agent(
            model=Gemini(id="gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY")),
            # ... config ...
        )
        
        response = scrape_agent.run(
            f"Query: {query}\nVerify and format: {content_for_verification}",
            session_id=agent.session_id,
        )
        
        # ADD THIS: Track cost for each verification call
        wrapper.track_response(response, "gemini-2.5-flash", context="scrape_agent_verification")
        
        # ... rest of existing code ...
    
    return verified_search_results


# ============================================================================
# EXAMPLE 3: Track Crawl4AI LLM extraction costs
# ============================================================================

async def scrape_with_cost_tracking(url: str):
    """
    Example of tracking Crawl4AI LLM extraction costs.
    
    Note: Crawl4AI uses Gemini internally, so we need to intercept
    the LLM calls made by Crawl4AI. This is more complex and may
    require modifying Crawl4AI or using a proxy.
    """
    from crawl4ai import AsyncWebCrawler, LLMExtractionStrategy, LLMConfig
    from utils.gemini_cost_wrapper import GeminiCostWrapper
    import os
    
    wrapper = GeminiCostWrapper()
    
    async with AsyncWebCrawler(headless=True) as crawler:
        extraction_strategy = LLMExtractionStrategy(
            llm_config=LLMConfig(
                provider="google/gemini-2.5-flash",
                api_token=os.getenv("GOOGLE_API_KEY"),
            ),
            instruction="Extract article content...",
        )
        
        result = await crawler.arun(
            url=url,
            extraction_strategy=extraction_strategy,
        )
        
        # NOTE: Crawl4AI doesn't expose the raw Gemini response,
        # so we can't directly track costs. We'd need to:
        # 1. Use a proxy/monkey-patch to intercept Gemini calls
        # 2. Or estimate based on content size
        # 3. Or modify Crawl4AI to expose usage metadata
        
        return result


# ============================================================================
# EXAMPLE 4: Query cost summaries
# ============================================================================

def get_cost_report():
    """Get cost reports for different time periods and contexts."""
    from utils.cost_tracker import get_cost_tracker
    from datetime import datetime, timedelta
    
    tracker = get_cost_tracker()
    
    # Overall summary
    overall = tracker.get_cost_summary()
    print("📊 Overall Cost Summary:")
    print(f"   Total Calls: {overall['total_calls']}")
    print(f"   Total Cost: ${overall['total_cost']:.6f}")
    print(f"   Total Tokens: {overall['total_input_tokens'] + overall['total_output_tokens']:,}")
    
    # Today's costs
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today = tracker.get_total_cost(start_date=today_start)
    print(f"\n📅 Today's Costs:")
    print(f"   Calls: {today['total_calls']}")
    print(f"   Cost: ${today['total_cost']:.6f}")
    
    # By context
    search_costs = tracker.get_total_cost(context="search_agent")
    scrape_costs = tracker.get_total_cost(context="scrape_agent")
    
    print(f"\n🔍 Search Agent Costs:")
    print(f"   Calls: {search_costs['total_calls']}")
    print(f"   Cost: ${search_costs['total_cost']:.6f}")
    
    print(f"\n📄 Scrape Agent Costs:")
    print(f"   Calls: {scrape_costs['total_calls']}")
    print(f"   Cost: ${scrape_costs['total_cost']:.6f}")


# ============================================================================
# EXAMPLE 5: Real-time cost monitoring
# ============================================================================

def monitor_costs_in_realtime():
    """
    Example of monitoring costs in real-time during agent execution.
    """
    from utils.cost_tracker import get_cost_tracker
    import time
    
    tracker = get_cost_tracker()
    
    initial_summary = tracker.get_cost_summary()
    initial_cost = initial_summary['total_cost']
    
    print(f"Starting cost: ${initial_cost:.6f}")
    
    # Run your agent here...
    # ... agent code ...
    
    # Check costs periodically
    time.sleep(5)  # Wait 5 seconds
    
    current_summary = tracker.get_cost_summary()
    current_cost = current_summary['total_cost']
    cost_increment = current_cost - initial_cost
    
    print(f"Current cost: ${current_cost:.6f}")
    print(f"Cost increment: ${cost_increment:.6f}")
    print(f"Total calls: {current_summary['total_calls']}")

