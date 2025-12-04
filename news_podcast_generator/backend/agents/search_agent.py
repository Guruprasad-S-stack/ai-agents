import os
from typing import List
from agno.agent import Agent
from agno.models.google import Gemini
from pydantic import BaseModel, Field
from utils.env_loader import load_backend_env
from agno.tools.duckduckgo import DuckDuckGoTools
from textwrap import dedent
from tools.wikipedia_search import wikipedia_search
from tools.google_news_discovery import google_news_discovery_run
from tools.jikan_search import jikan_search
from tools.embedding_search import embedding_search
from tools.social_media_search import social_media_search, social_media_trending_search
from tools.search_articles import search_articles
# Browser search commented out - using Tavily Search instead (more efficient)
# from tools.web_search import run_browser_search
# Tavily Search - modern AI-optimized search
try:
    from tools.tavily_search import tavily_search
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False


load_backend_env()


class ReturnItem(BaseModel):
    url: str = Field(..., description="The URL of the search result")
    title: str = Field(..., description="The title of the search result")
    description: str = Field(..., description="A brief description or summary of the search result content")
    source_name: str = Field(
        ...,
        description="The name/type of the source (e.g., 'wikipedia', 'general', or any reputable source tag)",
    )
    tool_used: str = Field(
        ...,
        description="The tools used to generate the search results, unknown if not used or not applicable",
    )
    published_date: str = Field(
        ...,
        description="The published date of the content in ISO format, if not available keep it empty",
    )
    is_scrapping_required: bool = Field(
        ...,
        description="Set to True if the content need scraping, False otherwise, default keep it True if not sure",
    )


class SearchResults(BaseModel):
    items: List[ReturnItem] = Field(..., description="A list of search result items")


SEARCH_AGENT_DESCRIPTION = "You are a helpful assistant that can search the web for information."
SEARCH_AGENT_INSTRUCTIONS = dedent("""
    You are a helpful assistant that can search the web or any other sources for information.
    You should create topic for the search from the given query instead of blindly apply the query to the search tools.
    
    HARD CAP: You MUST return EXACTLY 5 sources. No more, no less.
    
    Keep the search sources of high quality and reputable, and sources should be relevant to the asked topic.
    Sources should be from diverse platforms with no duplicates.
    IMPORTANT: User queries might be fuzzy or misspelled. Understand the user's intent and act accordingly.
    IMPORTANT: The output source_name field can be one of ["wikipedia", "general", or any source tag used"].
    IMPORTANT: You have access to different search tools use them when appropriate which one is best for the given search query.
    IMPORTANT: Make sure you are able to detect what tool to use. Available tool tags = ["tavily_search", "google_news_discovery", "duckduckgo", "wikipedia_search", "jikan_search", "social_media_search", "social_media_trending_search", "unknown"].
    
    MANDATORY Tool Priority and Fallback Strategy:
        1. Use tavily_search FIRST (AI-optimized, reliable)
        2. If tavily_search returns FEWER than 5 results: You MUST use backup tools to reach exactly 5
           - Example: Tavily returns 3 → Use google_news_discovery or wikipedia_search to get 2 more
        3. If tavily_search returns MORE than 5 results: Select the best 5
        4. BACKUP ORDER: google_news_discovery → DuckDuckGoTools → wikipedia_search
        5. For news queries: Prefer google_news_discovery first
        6. Use embedding_search and search_articles for local database searches (fast and reliable)
        
    CRITICAL: Never return fewer than 5 sources. Always use backup tools if primary returns < 5.
        - Fallback order: tavily_search → google_news_discovery → DuckDuckGoTools → wikipedia_search → embedding_search → search_articles
    IMPORTANT: If a tool returns an error message (like "rate limit", "API error", "JSON parse error"), immediately try the next tool in priority order. Don't retry failed tools.
    IMPORTANT: If returned sources are not of high quality or not relevant to the asked topic, don't include them in the returned sources.
    IMPORTANT: Never include dates to the search query unless user explicitly asks for it.
    IMPORTANT: You are allowed to use appropriate tools to get the best results even the single tool return enough results diverse check is better.
    IMPORTANT: Use Tavily Search as primary tool for general queries. Fallback to google_news_discovery, DuckDuckGoTools, and wikipedia_search if Tavily is unavailable or returns insufficient results.
    IMPORTANT: All search tools return URLs that need scraping. The scrape agent will automatically scrape these URLs using Crawl4AI (with LLM extraction for better content quality).
    """)


def search_agent_run(agent: Agent, query: str) -> str:
    """
    Search Agent which searches the web and other sources for relevant sources about the given topic or query.
    Args:
        agent: The agent instance
        query: The search query
    Returns:
        A formatted string response with the search results (link and gist only)
    """
    print("Search Agent Input:", query, flush=True)
    session_id = agent.session_id
    from services.internal_session_service import SessionService

    try:
        session = SessionService.get_session(session_id)
        current_state = session["state"]
        search_agent = Agent(
            model=Gemini(id="gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY")),
            instructions=SEARCH_AGENT_INSTRUCTIONS,
            description=SEARCH_AGENT_DESCRIPTION,
            use_json_mode=True,
            response_model=SearchResults,
            tools=(
                [
                    tavily_search,  # Primary: Tavily Search (AI-optimized)
                ]
                if TAVILY_AVAILABLE
                else []
            )
            + [
                google_news_discovery_run,  # Backup: Google News (reliable for news)
                DuckDuckGoTools(),  # Backup: DuckDuckGo (may hit rate limits)
                wikipedia_search,  # Backup: Wikipedia (reliable for general topics)
                jikan_search,
                embedding_search,
                social_media_search,
                social_media_trending_search,
                search_articles,
                # run_browser_search,  # Commented out - using Tavily Search instead (more efficient)
            ],
            session_id=session_id,
        )
        print(f"🔍 Starting search for: {query}", flush=True)
        response = search_agent.run(query, session_id=session_id)
        response_dict = response.to_dict()
        current_state["stage"] = "search"
        search_results = response_dict["content"]["items"]
        
        # HARD CAP: Exactly 5 sources
        num_results = len(search_results)
        if num_results > 5:
            print(f"⚠️ Got {num_results} sources, trimming to 5 (hard cap)", flush=True)
            search_results = search_results[:5]
            num_results = 5
        elif num_results < 5:
            print(f"⚠️ Only {num_results} sources found (expected 5). Backup tools should have been used.", flush=True)
        
        current_state["search_results"] = search_results
        SessionService.save_session(session_id, current_state)
        has_results = "search_results" in current_state and current_state["search_results"]
        
        # Track which tools were used
        tools_used = set()
        for item in search_results:
            tool = item.get("tool_used", "unknown")
            tools_used.add(tool)
        
        print(f"📊 Search Agent Summary:", flush=True)
        print(f"   - Query: {query}", flush=True)
        print(f"   - Total results: {num_results} (Hard Cap: 5)", flush=True)
        print(f"   - Tools used: {', '.join(tools_used) if tools_used else 'None'}", flush=True)
        print(f"   - Results: {[r.get('title', 'N/A')[:50] for r in search_results]}", flush=True)
        
        return f"Found {len(response_dict['content']['items'])} sources about {query} {'and added to the search_results' if has_results else ''}"
    except Exception as e:
        print(f"Error in search_agent_run: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        import sys
        sys.stdout.flush()
        # Return empty results instead of crashing
        return f"Error during search: {str(e)}. Please try again or rephrase your query."