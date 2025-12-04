#!/usr/bin/env python3
"""
Test script to demonstrate professional cost tracking with exact token counts.

This script shows:
1. How to extract exact token counts from Gemini API responses
2. How to track costs for every API call
3. How to query cost summaries
"""

import os
import asyncio
from datetime import datetime
from utils.env_loader import load_backend_env
from utils.cost_tracker import get_cost_tracker
from utils.gemini_cost_wrapper import GeminiCostWrapper

load_backend_env()

# Test with direct Gemini API call
def test_direct_gemini_api():
    """Test cost tracking with direct Gemini API call."""
    print("=" * 70)
    print("TEST 1: Direct Gemini API Call")
    print("=" * 70)
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        prompt = "Write a brief summary of artificial intelligence in 100 words."
        
        print(f"Prompt: {prompt[:50]}...")
        print("Calling Gemini API...")
        
        response = model.generate_content(prompt)
        
        # Track the cost
        wrapper = GeminiCostWrapper()
        wrapper.track_response(response, "gemini-2.5-flash", context="test_direct_api")
        
        print(f"Response: {response.text[:100]}...")
        print("✅ Cost tracked successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_agno_agent():
    """Test cost tracking with Agno Agent."""
    print("\n" + "=" * 70)
    print("TEST 2: Agno Agent Call")
    print("=" * 70)
    
    try:
        from agno.agent import Agent
        from agno.models.google import Gemini
        
        agent = Agent(
            model=Gemini(id="gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY")),
            instructions="You are a helpful assistant.",
        )
        
        query = "What is machine learning?"
        print(f"Query: {query}")
        print("Calling Agno Agent...")
        
        response = agent.run(query)
        
        # Track the cost
        wrapper = GeminiCostWrapper()
        wrapper.track_response(response, "gemini-2.5-flash", context="test_agno_agent")
        
        print(f"Response: {response.content[:100]}...")
        print("✅ Cost tracked successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_cost_summary():
    """Test cost summary queries."""
    print("\n" + "=" * 70)
    print("TEST 3: Cost Summary")
    print("=" * 70)
    
    tracker = get_cost_tracker()
    
    # Get overall summary
    summary = tracker.get_cost_summary()
    
    print("\n📊 Overall Cost Summary:")
    print(f"   Total Calls: {summary['total_calls']}")
    print(f"   Total Input Tokens: {summary['total_input_tokens']:,}")
    print(f"   Total Output Tokens: {summary['total_output_tokens']:,}")
    print(f"   Total Input Cost: ${summary['total_input_cost']:.6f}")
    print(f"   Total Output Cost: ${summary['total_output_cost']:.6f}")
    print(f"   Total Cost: ${summary['total_cost']:.6f}")
    
    # Get summary for specific context
    if summary['total_calls'] > 0:
        test_summary = tracker.get_total_cost(context="test_direct_api")
        print(f"\n📊 Test Direct API Summary:")
        print(f"   Calls: {test_summary['total_calls']}")
        print(f"   Cost: ${test_summary['total_cost']:.6f}")


def test_usage_extraction():
    """Test extracting usage from different response types."""
    print("\n" + "=" * 70)
    print("TEST 4: Usage Extraction")
    print("=" * 70)
    
    wrapper = GeminiCostWrapper()
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        response = model.generate_content("Say hello in 5 words.")
        
        print("Response type:", type(response))
        print("Response attributes:", [attr for attr in dir(response) if not attr.startswith('_')])
        
        usage_data = wrapper.extract_usage_from_response(response, "gemini-2.5-flash")
        
        if usage_data:
            print("\n✅ Successfully extracted usage:")
            print(f"   Input tokens: {usage_data['input_tokens']}")
            print(f"   Output tokens: {usage_data['output_tokens']}")
            print(f"   Total tokens: {usage_data['total_tokens']}")
        else:
            print("\n⚠️  Could not extract usage data")
            print("   This might mean the API response format has changed")
            print("   or we need to update the extraction logic")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 70)
    print("PROFESSIONAL COST TRACKING TEST")
    print("=" * 70)
    print("\nThis script demonstrates how to track exact token counts")
    print("and costs for every Gemini API call.\n")
    
    # Run tests
    test_direct_gemini_api()
    test_agno_agent()
    test_cost_summary()
    test_usage_extraction()
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print("\n💡 Next steps:")
    print("1. Integrate GeminiCostWrapper into your agents")
    print("2. Call wrapper.track_response() after each API call")
    print("3. Query cost summaries using tracker.get_total_cost()")
    print("4. Monitor costs in real-time")

