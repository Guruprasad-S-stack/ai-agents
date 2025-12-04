#!/usr/bin/env python3
"""
Comprehensive test script for Tavily Search and Crawl4AI implementations.
Tests both installation and actual API functionality with LLM extraction.
"""

import os
import sys
import asyncio
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_environment():
    """Check if required environment variables are set."""
    print("=" * 70)
    print("ENVIRONMENT CHECK")
    print("=" * 70)
    
    tavily_key = os.getenv("TAVILY_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    
    print(f"TAVILY_API_KEY: {'✅ Set' if tavily_key else '❌ Missing'}")
    print(f"GOOGLE_API_KEY: {'✅ Set' if google_key else '❌ Missing'}")
    
    if not tavily_key:
        print("⚠️  Warning: TAVILY_API_KEY not set. Tavily tests will fail.")
    if not google_key:
        print("⚠️  Warning: GOOGLE_API_KEY not set. Crawl4AI LLM extraction will fail.")
    
    print()
    return tavily_key, google_key

def test_tavily_search(query="Pyramids of Gaza"):
    """Test Tavily Search implementation matching our code."""
    print("=" * 70)
    print("TESTING TAVILY SEARCH")
    print("=" * 70)
    print(f"Query: {query}\n")
    
    try:
        from tavily import TavilyClient
        
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not tavily_api_key:
            print("❌ TAVILY_API_KEY not found. Skipping Tavily test.")
            return False
        
        client = TavilyClient(api_key=tavily_api_key)
        print("✅ TavilyClient created successfully")
        
        # Test with advanced parameters first (matching our implementation)
        try:
            print("\n📡 Attempting search with advanced parameters...")
            response = client.search(
                query=query,
                max_results=5,  # Limit to 5 for testing
                search_depth="advanced",
                include_answer=False,
                include_raw_content=False,
            )
            print("✅ Advanced parameters accepted")
        except TypeError as e:
            print(f"⚠️  Advanced parameters failed: {e}")
            print("📡 Falling back to basic search...")
            response = client.search(query=query, max_results=5)
            print("✅ Basic search successful")
        
        # Process results (matching our implementation)
        results = response.get("results", [])
        print(f"\n✅ Found {len(results)} results")
        
        if results:
            print("\n📋 Sample Results:")
            for i, item in enumerate(results[:3], 1):
                print(f"\n  {i}. {item.get('title', 'No title')}")
                print(f"     URL: {item.get('url', 'No URL')}")
                print(f"     Content preview: {item.get('content', '')[:100]}...")
            
            return True
        else:
            print("⚠️  No results returned")
            return False
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("   Install with: pip install tavily-python")
        return False
    except Exception as e:
        print(f"❌ Error during Tavily search: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_crawl4ai_scraping(query="Pyramids of Gaza"):
    """Test Crawl4AI scraping with LLM extraction (matching our implementation)."""
    print("\n" + "=" * 70)
    print("TESTING CRAWL4AI WITH LLM EXTRACTION")
    print("=" * 70)
    print(f"Query: {query}\n")
    
    try:
        from crawl4ai import AsyncWebCrawler, LLMExtractionStrategy, LLMConfig
        import nest_asyncio
        
        print("✅ All Crawl4AI modules imported successfully")
        
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            print("❌ GOOGLE_API_KEY not found. Skipping LLM extraction test.")
            print("   Testing basic scraping only...")
            use_llm = False
        else:
            use_llm = True
        
        # Test URL (using Wikipedia as it's reliable)
        test_url = "https://en.wikipedia.org/wiki/Pyramids_of_Giza"
        print(f"📡 Testing URL: {test_url}\n")
        
        # Apply nest_asyncio for Celery compatibility
        try:
            nest_asyncio.apply()
            print("✅ nest_asyncio applied")
        except Exception as e:
            print(f"⚠️  nest_asyncio warning: {e}")
        
        async with AsyncWebCrawler(headless=True) as crawler:
            print("✅ AsyncWebCrawler created")
            
            if use_llm:
                # Test LLM extraction (matching our exact implementation)
                print("\n🤖 Testing LLM extraction with Gemini...")
                
                extraction_strategy = None
                try:
                    # Try google/ prefix first (matching our implementation)
                    extraction_strategy = LLMExtractionStrategy(
                        llm_config=LLMConfig(
                            provider="google/gemini-2.5-flash",
                            api_token=google_api_key,
                        ),
                        instruction="Extract the main article content, title, authors, and published date. Remove navigation, ads, and boilerplate. Focus on the core article text.",
                    )
                    print("✅ LLM extraction strategy created (google/gemini-2.5-flash)")
                except Exception as e1:
                    print(f"⚠️  google/ prefix failed: {e1}")
                    try:
                        # Try gemini/ prefix as fallback
                        extraction_strategy = LLMExtractionStrategy(
                            llm_config=LLMConfig(
                                provider="gemini/gemini-2.5-flash",
                                api_token=google_api_key,
                            ),
                            instruction="Extract the main article content, title, authors, and published date. Remove navigation, ads, and boilerplate. Focus on the core article text.",
                        )
                        print("✅ LLM extraction strategy created (gemini/gemini-2.5-flash)")
                    except Exception as e2:
                        print(f"❌ LLM extraction setup failed: {e1}, {e2}")
                        extraction_strategy = None
                
                if extraction_strategy:
                    print("\n📡 Scraping with LLM extraction...")
                    result = await crawler.arun(
                        url=test_url,
                        timeout=30000,
                        extraction_strategy=extraction_strategy,
                    )
                else:
                    print("\n📡 Falling back to basic scraping...")
                    result = await crawler.arun(
                        url=test_url,
                        timeout=30000,
                    )
            else:
                # Basic scraping without LLM
                print("\n📡 Scraping without LLM extraction...")
                result = await crawler.arun(
                    url=test_url,
                    timeout=30000,
                )
            
            if result.success:
                print("✅ Scraping successful!")
                
                # Extract content (matching our implementation)
                content = result.markdown or result.cleaned_html or result.html
                metadata = result.metadata or {}
                title = metadata.get("title", "") or (result.markdown.split("\n")[0] if result.markdown else "")
                
                print(f"\n📊 Results:")
                print(f"   Title: {title[:80]}..." if title else "   Title: Not found")
                print(f"   Content length: {len(content)} characters")
                print(f"   Final URL: {result.url or test_url}")
                
                if result.extracted_content:
                    print(f"   LLM Extracted: {len(result.extracted_content)} characters")
                    print(f"   Preview: {result.extracted_content[:200]}...")
                
                if result.markdown:
                    print(f"\n   Markdown preview (first 300 chars):")
                    print(f"   {result.markdown[:300]}...")
                
                return True
            else:
                print(f"❌ Scraping failed: {result.error_message or 'Unknown error'}")
                return False
                
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("   Install with: pip install crawl4ai nest-asyncio")
        return False
    except Exception as e:
        print(f"❌ Error during Crawl4AI scraping: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("TAVILY & CRAWL4AI IMPLEMENTATION TEST")
    print("=" * 70)
    print(f"Test Query: 'Pyramids of Gaza'")
    print(f"Timestamp: {datetime.now().isoformat()}\n")
    
    # Load environment variables
    try:
        from utils.env_loader import load_backend_env
        load_backend_env()
        print("✅ Environment variables loaded\n")
    except Exception as e:
        print(f"⚠️  Could not load .env file: {e}")
        print("   Make sure TAVILY_API_KEY and GOOGLE_API_KEY are set\n")
    
    # Check environment
    tavily_key, google_key = check_environment()
    
    # Test Tavily
    tavily_result = test_tavily_search("Pyramids of Gaza")
    
    # Test Crawl4AI
    try:
        crawl4ai_result = asyncio.run(test_crawl4ai_scraping("Pyramids of Gaza"))
    except RuntimeError:
        # If event loop is already running, use nest_asyncio
        import nest_asyncio
        nest_asyncio.apply()
        crawl4ai_result = asyncio.run(test_crawl4ai_scraping("Pyramids of Gaza"))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tavily Search:     {'✅ PASS' if tavily_result else '❌ FAIL'}")
    print(f"Crawl4AI Scraping: {'✅ PASS' if crawl4ai_result else '❌ FAIL'}")
    print("=" * 70)
    
    if tavily_result and crawl4ai_result:
        print("\n✅ All tests passed! Your implementations are working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

