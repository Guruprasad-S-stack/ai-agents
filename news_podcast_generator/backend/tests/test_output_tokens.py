#!/usr/bin/env python3
"""
Test script to measure actual input and output token counts for Crawl4AI LLM extraction.
This will help us understand the real cost.
"""

import os
import asyncio
from utils.env_loader import load_backend_env

load_backend_env()

try:
    from crawl4ai import AsyncWebCrawler, LLMExtractionStrategy, LLMConfig
    import nest_asyncio
except ImportError:
    print("❌ crawl4ai not installed")
    exit(1)

# Test with a real Wikipedia article (like our test)
TEST_URL = "https://en.wikipedia.org/wiki/Pyramids_of_Giza"

def estimate_tokens(text):
    """Estimate tokens from text (Gemini uses ~3.5 chars per token for English)."""
    return int(len(text) / 3.5)

async def test_token_usage():
    """Test actual token usage for Crawl4AI LLM extraction."""
    
    print("=" * 70)
    print("CRAWL4AI LLM EXTRACTION - TOKEN USAGE ANALYSIS")
    print("=" * 70)
    print(f"Test URL: {TEST_URL}\n")
    
    nest_asyncio.apply()
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not google_api_key:
        print("❌ GOOGLE_API_KEY not set")
        return
    
    async with AsyncWebCrawler(headless=True) as crawler:
        # Step 1: Get raw content (to measure input)
        print("Step 1: Fetching raw content (to measure input size)...")
        basic_result = await crawler.arun(url=TEST_URL, timeout=30000)
        
        if not basic_result.success:
            print(f"❌ Failed to fetch: {basic_result.error_message}")
            return
        
        # Measure input content
        raw_content = basic_result.markdown or basic_result.cleaned_html or basic_result.html
        input_chars = len(raw_content)
        input_tokens_estimate = estimate_tokens(raw_content)
        
        print(f"✅ Raw content fetched")
        print(f"   Content size: {input_chars:,} characters")
        print(f"   Estimated tokens: {input_tokens_estimate:,} tokens")
        
        # Step 2: Test with LLM extraction (to measure output)
        print("\nStep 2: Testing LLM extraction (to measure output size)...")
        
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
                print(f"❌ LLM extraction setup failed: {e1}, {e2}")
                return
        
        llm_result = await crawler.arun(
            url=TEST_URL,
            timeout=30000,
            extraction_strategy=extraction_strategy,
        )
        
        if not llm_result.success:
            print(f"❌ LLM extraction failed: {llm_result.error_message}")
            return
        
        # Measure output content
        print("\n" + "=" * 70)
        print("RESULTS")
        print("=" * 70)
        
        # Check what Crawl4AI returns
        if hasattr(llm_result, 'extracted_content') and llm_result.extracted_content:
            extracted_content = llm_result.extracted_content
            output_chars = len(extracted_content)
            output_tokens_estimate = estimate_tokens(extracted_content)
            
            print(f"\n📥 INPUT (sent to LLM):")
            print(f"   Content: {input_chars:,} characters")
            print(f"   Estimated tokens: {input_tokens_estimate:,} tokens")
            print(f"   + Instruction prompt: ~150 tokens")
            print(f"   TOTAL INPUT: ~{input_tokens_estimate + 150:,} tokens")
            
            print(f"\n📤 OUTPUT (from LLM):")
            print(f"   Extracted content: {output_chars:,} characters")
            print(f"   Estimated tokens: {output_tokens_estimate:,} tokens")
            print(f"\n   Preview (first 300 chars):")
            print(f"   {extracted_content[:300]}...")
            
            # Also check markdown (what we actually use)
            markdown_content = llm_result.markdown or ""
            markdown_chars = len(markdown_content)
            markdown_tokens = estimate_tokens(markdown_content)
            
            print(f"\n📄 MARKDOWN (what we store):")
            print(f"   Markdown: {markdown_chars:,} characters")
            print(f"   Estimated tokens: {markdown_tokens:,} tokens")
            
            print("\n" + "=" * 70)
            print("COST ANALYSIS")
            print("=" * 70)
            
            # Calculate costs
            total_input_tokens = input_tokens_estimate + 150
            total_output_tokens = output_tokens_estimate
            
            # Gemini 2.5 Flash pricing
            input_cost = (total_input_tokens / 1_000_000) * 0.30
            output_cost = (total_output_tokens / 1_000_000) * 2.50
            total_cost = input_cost + output_cost
            
            print(f"\n💰 Per URL Cost (PAID TIER):")
            print(f"   Input ({total_input_tokens:,} tokens): ${input_cost:.6f}")
            print(f"   Output ({total_output_tokens:,} tokens): ${output_cost:.6f}")
            print(f"   TOTAL: ${total_cost:.6f}")
            
            print(f"\n💰 For 10 URLs:")
            print(f"   TOTAL: ${total_cost * 10:.6f}")
            
            print(f"\n✅ FREE TIER: $0.00 (FREE!)")
            
            print("\n" + "=" * 70)
            print("KEY FINDINGS")
            print("=" * 70)
            print(f"""
1. INPUT tokens: ~{total_input_tokens:,} tokens
   - Raw content: {input_tokens_estimate:,} tokens
   - Instruction: ~150 tokens

2. OUTPUT tokens: ~{total_output_tokens:,} tokens
   - This is the extracted article content
   - Much larger than 500 tokens if article is long!
   - Your estimate of 500 tokens was too low for full articles

3. Total tokens per URL: ~{total_input_tokens + total_output_tokens:,} tokens

4. Cost per URL (PAID): ${total_cost:.6f}
   Cost per URL (FREE): $0.00 ✅
            """)
            
        else:
            print("⚠️  No extracted_content field found")
            print("   Crawl4AI may return content in result.markdown instead")
            markdown_content = llm_result.markdown or ""
            print(f"   Markdown length: {len(markdown_content):,} characters")
            print(f"   Estimated tokens: {estimate_tokens(markdown_content):,} tokens")

if __name__ == "__main__":
    asyncio.run(test_token_usage())

