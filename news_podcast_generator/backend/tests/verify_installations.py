#!/usr/bin/env python3
"""
Verification script to check if Tavily and Crawl4AI are installed correctly.
"""

import sys

def check_tavily():
    """Check Tavily installation."""
    print("=" * 60)
    print("Checking Tavily Search...")
    print("=" * 60)
    try:
        import tavily
        print("✅ tavily module imported successfully")
        
        from tavily import TavilyClient
        print("✅ TavilyClient imported successfully")
        
        # Check version if available
        try:
            version = tavily.__version__
            print(f"✅ Tavily version: {version}")
        except AttributeError:
            print("⚠️  Version info not available (but module works)")
        
        return True
    except ImportError as e:
        print(f"❌ Tavily import failed: {e}")
        print("   Install with: pip install tavily-python")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_crawl4ai():
    """Check Crawl4AI installation."""
    print("\n" + "=" * 60)
    print("Checking Crawl4AI...")
    print("=" * 60)
    try:
        import crawl4ai
        print("✅ crawl4ai module imported successfully")
        
        from crawl4ai import AsyncWebCrawler
        print("✅ AsyncWebCrawler imported successfully")
        
        from crawl4ai import LLMExtractionStrategy
        print("✅ LLMExtractionStrategy imported successfully")
        
        from crawl4ai import LLMConfig
        print("✅ LLMConfig imported successfully")
        
        # Check version if available
        try:
            version = crawl4ai.__version__
            print(f"✅ Crawl4AI version: {version}")
        except AttributeError:
            print("⚠️  Version info not available (but module works)")
        
        return True
    except ImportError as e:
        print(f"❌ Crawl4AI import failed: {e}")
        print("   Install with: pip install crawl4ai")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_nest_asyncio():
    """Check nest-asyncio installation."""
    print("\n" + "=" * 60)
    print("Checking nest-asyncio...")
    print("=" * 60)
    try:
        import nest_asyncio
        print("✅ nest_asyncio module imported successfully")
        
        # Check version if available
        try:
            version = nest_asyncio.__version__
            print(f"✅ nest-asyncio version: {version}")
        except AttributeError:
            print("⚠️  Version info not available (but module works)")
        
        return True
    except ImportError as e:
        print(f"❌ nest-asyncio import failed: {e}")
        print("   Install with: pip install nest-asyncio")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Run all verification checks."""
    print("\n" + "=" * 60)
    print("INSTALLATION VERIFICATION")
    print("=" * 60)
    
    results = []
    results.append(("Tavily Search", check_tavily()))
    results.append(("Crawl4AI", check_crawl4ai()))
    results.append(("nest-asyncio", check_nest_asyncio()))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:20s}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✅ All packages installed correctly!")
        return 0
    else:
        print("❌ Some packages failed verification")
        return 1

if __name__ == "__main__":
    sys.exit(main())

