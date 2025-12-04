"""
Test to verify browser_use compatibility with Gemini via LangChain.
Run this test to confirm ChatGoogleGenerativeAI works with browser_use.
"""
import os
import sys
import asyncio

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent
from utils.env_loader import load_backend_env

load_backend_env()

async def test_browser_use_with_gemini():
    """Test if browser_use works with Gemini via LangChain"""
    try:
        # Create Gemini LLM via LangChain
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        print("✅ ChatGoogleGenerativeAI created successfully")
        
        # Test basic LangChain interface
        test_response = llm.invoke("Say 'Hello'")
        print(f"✅ LangChain invoke works: {test_response.content[:50]}")
        
        # Test with browser_use (simple task)
        print("\n🧪 Testing browser_use with Gemini...")
        agent = Agent(
            task="Navigate to https://example.com and get the page title",
            llm=llm,
        )
        
        result = await agent.run(max_steps=3)
        print(f"✅ browser_use with Gemini works! Result: {result.final_result()[:100] if result else 'No result'}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"❌ Type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_browser_use_with_gemini())
    if result:
        print("\n✅ SUCCESS: browser_use is compatible with Gemini!")
    else:
        print("\n❌ FAILED: browser_use may not be compatible with Gemini")

