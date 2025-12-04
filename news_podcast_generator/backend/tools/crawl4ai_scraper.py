from typing import Dict, List
from datetime import datetime
import os
from utils.env_loader import load_backend_env

load_backend_env()

try:
    from crawl4ai import AsyncWebCrawler, LLMExtractionStrategy, LLMConfig
    import asyncio
except ImportError:
    AsyncWebCrawler = None
    LLMExtractionStrategy = None
    LLMConfig = None
    asyncio = None


class Crawl4AIScraper:
    """
    Modern web scraper using Crawl4AI - AI-powered web crawling and scraping.
    Replaces Playwright + Newspaper4k with a more streamlined solution.
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
    
    def scrape_urls(self, urls: List[str]) -> List[Dict]:
        """
        Scrape multiple URLs using Crawl4AI.
        
        Args:
            urls: List of URLs to scrape
        
        Returns:
            List of dictionaries with scraped content
        """
        if AsyncWebCrawler is None:
            return [
                {
                    "original_url": url,
                    "error": "crawl4ai package not installed. Install with: pip install crawl4ai",
                    "success": False,
                    "timestamp": datetime.now().isoformat(),
                }
                for url in urls
            ]
        
        # Run async scraping
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running (e.g., in Celery), use nest_asyncio
                try:
                    import nest_asyncio
                    nest_asyncio.apply()
                except ImportError:
                    pass
            
            return asyncio.run(self._scrape_urls_async(urls))
        except RuntimeError:
            # Create new event loop if needed
            return asyncio.run(self._scrape_urls_async(urls))
    
    async def _scrape_urls_async(self, urls: List[str]) -> List[Dict]:
        """Async implementation of URL scraping - PARALLEL for speed."""
        import time
        start_time = time.time()
        print(f"🚀 Starting PARALLEL scraping of {len(urls)} URLs...", flush=True)
        
        async with AsyncWebCrawler(headless=self.headless) as crawler:
            # Create tasks for all URLs to scrape in parallel
            tasks = [self._scrape_single_url(crawler, url, i, len(urls)) for i, url in enumerate(urls)]
            
            # Run all scraping tasks in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any exceptions that were returned
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    final_results.append({
                        "original_url": urls[i],
                        "final_url": urls[i],
                        "error": str(result),
                        "success": False,
                        "timestamp": datetime.now().isoformat(),
                    })
                else:
                    final_results.append(result)
        
        elapsed = time.time() - start_time
        success_count = sum(1 for r in final_results if r.get("success", False))
        print(f"✅ Parallel scraping complete: {success_count}/{len(urls)} successful in {elapsed:.1f}s", flush=True)
        return final_results
    
    async def _scrape_single_url(self, crawler: AsyncWebCrawler, url: str, index: int, total: int) -> Dict:
        """Scrape a single URL - called in parallel."""
        try:
            print(f"  [{index+1}/{total}] Scraping: {url[:60]}...", flush=True)
            
            # Crawl4AI with LLM extraction for better content quality
            google_api_key = os.getenv("GOOGLE_API_KEY")
            extraction_strategy = None
            
            if LLMExtractionStrategy and LLMConfig and google_api_key:
                # Use LLM extraction with LLMConfig wrapper (official API)
                try:
                    extraction_strategy = LLMExtractionStrategy(
                        llm_config=LLMConfig(
                            provider="google/gemini-2.5-flash",
                            api_token=google_api_key,
                        ),
                        instruction="Extract the main article content, title, authors, and published date. Remove navigation, ads, and boilerplate. Focus on the core article text.",
                    )
                except Exception as e1:
                    try:
                        extraction_strategy = LLMExtractionStrategy(
                            llm_config=LLMConfig(
                                provider="gemini/gemini-2.5-flash",
                                api_token=google_api_key,
                            ),
                            instruction="Extract the main article content, title, authors, and published date. Remove navigation, ads, and boilerplate. Focus on the core article text.",
                        )
                    except Exception as e2:
                        print(f"  ⚠️ [{index+1}] LLM extraction failed, using basic scraping", flush=True)
            
            if extraction_strategy:
                result = await crawler.arun(
                    url=url,
                    timeout=self.timeout,
                    extraction_strategy=extraction_strategy,
                )
            else:
                result = await crawler.arun(
                    url=url,
                    timeout=self.timeout,
                )
            
            if result.success:
                content = result.markdown or result.cleaned_html or result.html
                metadata = result.metadata or {}
                title = metadata.get("title", "") or (result.markdown.split("\n")[0] if result.markdown else "")
                
                print(f"  ✓ [{index+1}] Success: {title[:50] if title else 'No title'}", flush=True)
                return {
                    "original_url": url,
                    "final_url": result.url or url,
                    "title": title,
                    "authors": metadata.get("authors", []),
                    "published_date": metadata.get("published_date", ""),
                    "full_text": content[:50000] if content else "",
                    "success": True,
                }
            else:
                print(f"  ✗ [{index+1}] Failed: {result.error_message or 'Unknown'}", flush=True)
                return {
                    "original_url": url,
                    "final_url": url,
                    "error": result.error_message or "Unknown error",
                    "success": False,
                    "timestamp": datetime.now().isoformat(),
                }
        
        except Exception as e:
            print(f"  ✗ [{index+1}] Error: {str(e)[:50]}", flush=True)
            return {
                "original_url": url,
                "final_url": url,
                "error": str(e),
                "success": False,
                "timestamp": datetime.now().isoformat(),
            }


def create_crawl4ai_scraper(headless=True, timeout=30000):
    """Factory function to create a new Crawl4AIScraper instance."""
    return Crawl4AIScraper(headless=headless, timeout=timeout)

