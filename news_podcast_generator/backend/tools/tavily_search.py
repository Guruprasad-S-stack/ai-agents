import os
import json
from typing import List
from agno.agent import Agent
from pydantic import BaseModel, Field
from utils.env_loader import load_backend_env

load_backend_env()

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None


class TavilySearchResult(BaseModel):
    url: str = Field(..., description="The URL of the search result")
    title: str = Field(..., description="The title of the search result")
    description: str = Field(..., description="A brief description or summary of the search result content")
    source_name: str = Field(
        default="general",
        description="The name/type of the source (e.g., 'wikipedia', 'general', or any reputable source tag)",
    )
    tool_used: str = Field(default="tavily_search", description="The tool used to generate the search results")
    published_date: str = Field(default="", description="The published date of the content in ISO format, if not available keep it empty")
    is_scrapping_required: bool = Field(
        default=True,
        description="Set to True if the content needs scraping, False otherwise. Tavily returns URLs, so this is True by default.",
    )


def tavily_search(agent: Agent, query: str, max_results: int = 10) -> str:
    """
    Search the web using Tavily Search API - optimized for AI applications.
    Tavily aggregates content from multiple sources and provides high-quality, relevant results.
    
    Args:
        agent: The agent instance
        query: The search query
        max_results: Maximum number of results to return (default: 10)
    
    Returns:
        A formatted string response with the search results
    """
    print(f"Tavily Search Input: {query}", flush=True)
    
    if TavilyClient is None:
        return "Error: tavily-python package not installed. Install with: pip install tavily-python"
    
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        return "Error: TAVILY_API_KEY not found in environment variables. Please set it in your .env file."
    
    try:
        client = TavilyClient(api_key=tavily_api_key)
        
        # Tavily search - use basic parameters first, add advanced ones if supported
        # Try with all parameters first, fallback to basic if needed
        try:
            response = client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced",  # May not be supported in all versions
                include_answer=False,
                include_raw_content=False,
            )
        except TypeError:
            # Fallback to basic search if advanced parameters not supported
            print("⚠️ Advanced Tavily parameters not supported, using basic search", flush=True)
            response = client.search(query=query, max_results=max_results)
        
        results = []
        for item in response.get("results", []):
            result = TavilySearchResult(
                url=item.get("url", ""),
                title=item.get("title", ""),
                description=item.get("content", "")[:500] if item.get("content") else item.get("title", ""),
                source_name=item.get("source", "general"),
                tool_used="tavily_search",
                published_date=item.get("published_date", "") if item.get("published_date") else "",
                is_scrapping_required=True,  # Tavily returns URLs, so scraping is required
            )
            results.append(result.model_dump())
        
        if not results:
            return "No Tavily search results found for this query. Try other search tools."
        
        print(f"Tavily Search found {len(results)} results", flush=True)
        return f"for all results is_scrapping_required: True, results: {json.dumps(results, ensure_ascii=False, indent=2)}"
    
    except Exception as e:
        print(f"Error during Tavily search: {str(e)}", flush=True)
        return f"Error in Tavily search: {str(e)}. Try other search tools like google_news_discovery or wikipedia_search."

