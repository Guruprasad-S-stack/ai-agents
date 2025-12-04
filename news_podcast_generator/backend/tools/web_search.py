import os
import asyncio
from typing import List
from pydantic import BaseModel, Field
# Lazy import: browser_use is heavy (loads Playwright), only import when needed
# Using Gemini instead of OpenAI for browser automation
from langchain_google_genai import ChatGoogleGenerativeAI
from utils.env_loader import load_backend_env
from agno.agent import Agent


import json

load_backend_env()

BROWSER_AGENT_MODEL = "gemini-2.5-flash"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
MAX_STEPS = 15
MAX_ACTIONS_PER_STEP = 5
USER_DATA_DIR = "browsers/playwright_persistent_profile_web"


class WebSearchResult(BaseModel):
    title: str = Field(..., description="The title of the search result")
    url: str = Field(..., description="The URL of the search result")
    content: str = Field(..., description="Full content of the source, be elaborate at the same time be concise")


class WebSearchResults(BaseModel):
    results: List[WebSearchResult] = Field(..., description="List of search results")


def run_browser_search(agent: Agent, instruction: str) -> str:
    """
    Run browser search to get the results.
    Args:
        agent: The agent instance
        instruction: The instruction to run the browser search, give detailed step by step prompt on how to collect the information.
    Returns:
        The results of the browser search
    """
    print("=" * 80)
    print("🔍 BROWSER SEARCH STARTED")
    print(f"📝 Instruction: {instruction[:100]}...")
    print("=" * 80)
    try:
        # Lazy import: Only load browser_use when actually needed (it's heavy)
        from browser_use import Agent as BrowserAgent, Controller, BrowserSession, BrowserProfile
        
        controller = Controller(output_model=WebSearchResults)
        session_id = agent.session_id
        recordings_dir = os.path.join("podcasts/recordings", session_id)
        os.makedirs(recordings_dir, exist_ok=True)

        headless = True
        browser_profile = BrowserProfile(
            user_data_dir=USER_DATA_DIR, headless=headless, viewport={"width": 1280, "height": 800}, record_video_dir=recordings_dir,
            downloads_path="podcasts/browseruse_downloads",
        )

        browser_session = BrowserSession(
            browser_profile=browser_profile,
            headless=headless,
            disable_security=False,
            record_video=True,
            record_video_dir=recordings_dir,
        )

        browser_agent = BrowserAgent(
            browser_session=browser_session,
            task=instruction,
            llm=ChatGoogleGenerativeAI(model=BROWSER_AGENT_MODEL, google_api_key=os.getenv("GOOGLE_API_KEY")),
            use_vision=False,
            controller=controller,
            max_actions_per_step=MAX_ACTIONS_PER_STEP,
        )
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            history = loop.run_until_complete(browser_agent.run(max_steps=MAX_STEPS))
        except RuntimeError:
            history = asyncio.run(browser_agent.run(max_steps=MAX_STEPS))
        result = history.final_result()
        if result:
            parsed: WebSearchResults = WebSearchResults.model_validate_json(result)
            results_list = [
                {"title": post.title, "url": post.url, "description": post.content, "is_scrapping_required": False} for post in parsed.results
            ]
            num_results = len(results_list)
            print(f"✅ Browser Search SUCCESS: Found {num_results} results with full content (is_scrapping_required: False)")
            print(f"📊 Browser Search Results: {num_results} items - URLs: {[r['url'] for r in results_list[:3]]}...")
            return f"is_scrapping_required: False, results: {json.dumps(results_list)}"
        else:
            print("❌ Browser Search FAILED: No results found")
            return "No results found, something went wrong with browser based search."
    except Exception as e:
        print(f"❌ Browser Search ERROR: {str(e)}")
        print("=" * 80)
        return f"Error running browser search: {e}"
    finally:
        pass


def main():
    return run_browser_search(agent={"session_id": "123"}, instruction="gene therapy")


if __name__ == "__main__":
    print(main())