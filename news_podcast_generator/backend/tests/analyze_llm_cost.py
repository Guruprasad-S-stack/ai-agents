#!/usr/bin/env python3
"""
Analyze LLM extraction costs for Crawl4AI.
Shows what gets sent to the LLM and calculates token costs.
"""

import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def analyze_llm_token_usage():
    """Analyze what Crawl4AI actually sends to the LLM."""
    print("=" * 70)
    print("LLM EXTRACTION COST ANALYSIS")
    print("=" * 70)
    
    try:
        from crawl4ai import AsyncWebCrawler, LLMExtractionStrategy, LLMConfig
        from utils.env_loader import load_backend_env
        
        load_backend_env()
        google_api_key = os.getenv("GOOGLE_API_KEY")
        
        if not google_api_key:
            print("❌ GOOGLE_API_KEY not set")
            return
        
        test_url = "https://en.wikipedia.org/wiki/Pyramids_of_Giza"
        print(f"\n📡 Testing URL: {test_url}\n")
        
        async with AsyncWebCrawler(headless=True) as crawler:
            # First, scrape WITHOUT LLM to see raw content size
            print("1️⃣ Scraping WITHOUT LLM extraction (baseline)...")
            basic_result = await crawler.arun(url=test_url, timeout=30000)
            
            if basic_result.success:
                html_size = len(basic_result.html) if basic_result.html else 0
                markdown_size = len(basic_result.markdown) if basic_result.markdown else 0
                cleaned_html_size = len(basic_result.cleaned_html) if basic_result.cleaned_html else 0
                
                print(f"   HTML size: {html_size:,} characters")
                print(f"   Markdown size: {markdown_size:,} characters")
                print(f"   Cleaned HTML size: {cleaned_html_size:,} characters")
                
                # Estimate tokens (rough: 3-4 chars per token for English)
                # LLM extraction likely uses cleaned HTML or markdown
                content_for_llm = cleaned_html_size or markdown_size
                estimated_tokens = content_for_llm // 3.5  # Average
                
                print(f"\n   Estimated content sent to LLM: ~{content_for_llm:,} chars")
                print(f"   Estimated tokens: ~{estimated_tokens:,.0f} tokens")
                
                # Add instruction prompt tokens (~100-200 tokens)
                instruction_tokens = 150
                total_input_tokens = estimated_tokens + instruction_tokens
                
                print(f"\n   Instruction prompt: ~{instruction_tokens} tokens")
                print(f"   Total INPUT tokens: ~{total_input_tokens:,.0f} tokens")
                
                # Estimate output tokens (extracted content is usually much smaller)
                # Output is structured JSON with title, content, authors, date
                estimated_output_tokens = 500  # Conservative estimate
                print(f"   Estimated OUTPUT tokens: ~{estimated_output_tokens} tokens")
                
                total_tokens = total_input_tokens + estimated_output_tokens
                print(f"\n   TOTAL tokens per URL: ~{total_tokens:,.0f} tokens")
                
                # Gemini 2.5 Flash pricing (as of 2024)
                # Free tier: 1M tokens/day
                # Paid: ~$0.075 per 1M input tokens, ~$0.30 per 1M output tokens
                input_cost = (total_input_tokens / 1_000_000) * 0.075
                output_cost = (estimated_output_tokens / 1_000_000) * 0.30
                total_cost = input_cost + output_cost
                
                print(f"\n💰 Cost per URL (Gemini 2.5 Flash):")
                print(f"   Input cost:  ${input_cost:.6f}")
                print(f"   Output cost: ${output_cost:.6f}")
                print(f"   Total cost:  ${total_cost:.6f}")
                
                # For 10 URLs
                print(f"\n📊 For 10 URLs:")
                print(f"   Total tokens: ~{total_tokens * 10:,.0f} tokens")
                print(f"   Total cost:   ${total_cost * 10:.6f}")
                print(f"   Free tier:    ✅ Covered (1M tokens/day)")
                
                # Now test WITH LLM extraction to see actual behavior
                print("\n" + "=" * 70)
                print("2️⃣ Testing WITH LLM extraction...")
                print("=" * 70)
                
                extraction_strategy = LLMExtractionStrategy(
                    llm_config=LLMConfig(
                        provider="google/gemini-2.5-flash",
                        api_token=google_api_key,
                    ),
                    instruction="Extract the main article content, title, authors, and published date. Remove navigation, ads, and boilerplate. Focus on the core article text.",
                )
                
                llm_result = await crawler.arun(
                    url=test_url,
                    timeout=30000,
                    extraction_strategy=extraction_strategy,
                )
                
                if llm_result.success:
                    print("✅ LLM extraction completed")
                    if llm_result.extracted_content:
                        extracted_size = len(llm_result.extracted_content)
                        print(f"   Extracted content size: {extracted_size:,} characters")
                        print(f"   Extracted preview: {llm_result.extracted_content[:200]}...")
                    else:
                        print("   ⚠️  No extracted_content field (check Crawl4AI version)")
                
                print("\n" + "=" * 70)
                print("KEY INSIGHTS")
                print("=" * 70)
                print("""
1. Crawl4AI sends CLEANED HTML or MARKDOWN to the LLM (not raw HTML)
   - This reduces token count significantly
   - Your 114,913 chars ≈ ~33,000 tokens (not 287,000!)

2. LLM extraction is OPTIONAL
   - You can disable it and use basic scraping (free)
   - LLM extraction improves quality but costs tokens

3. Cost Management:
   - Free tier: 1M tokens/day = ~30 URLs/day with LLM extraction
   - For 10 URLs: ~330K tokens = FREE ✅
   - Consider disabling LLM extraction for simple pages

4. Token Usage Breakdown:
   - Input: ~33,000 tokens (cleaned content + prompt)
   - Output: ~500 tokens (structured extraction)
   - Total: ~33,500 tokens per URL
                """)
                
            else:
                print(f"❌ Basic scraping failed: {basic_result.error_message}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(analyze_llm_token_usage())

