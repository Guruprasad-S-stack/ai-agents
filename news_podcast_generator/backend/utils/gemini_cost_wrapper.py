"""
Gemini API Cost Tracking Wrapper

This module provides a wrapper around Gemini API calls to automatically track costs.
It extracts exact token counts from API responses and records them.
"""

import os
from typing import Optional, Any
from utils.cost_tracker import get_cost_tracker, CostTracker


class GeminiCostWrapper:
    """
    Wrapper for Gemini API calls that automatically tracks costs.
    
    Usage:
        wrapper = GeminiCostWrapper()
        response = wrapper.call_gemini(model, prompt, context="search_agent")
        # Cost is automatically tracked
    """
    
    def __init__(self, tracker: Optional[CostTracker] = None):
        """
        Initialize the wrapper.
        
        Args:
            tracker: Optional CostTracker instance (uses global if None)
        """
        self.tracker = tracker or get_cost_tracker()
    
    def extract_usage_from_response(self, response: Any, model: str) -> Optional[dict]:
        """
        Extract usage metadata from Gemini API response.
        
        This method tries multiple ways to access usage data:
        1. Direct usage_metadata attribute (google.generativeai)
        2. Response.usage_metadata (Agno wrapper)
        3. Metadata dictionary
        4. Response attributes
        
        Args:
            response: API response object
            model: Model name
        
        Returns:
            Dictionary with input_tokens, output_tokens, total_tokens, or None
        """
        try:
            # Method 1: Direct usage_metadata (google.generativeai.types.GenerateContentResponse)
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                if hasattr(usage, 'prompt_token_count'):
                    return {
                        'input_tokens': usage.prompt_token_count,
                        'output_tokens': usage.candidates_token_count,
                        'total_tokens': usage.total_token_count,
                    }
            
            # Method 2: Check if response has a nested response attribute
            if hasattr(response, 'response') and hasattr(response.response, 'usage_metadata'):
                usage = response.response.usage_metadata
                if hasattr(usage, 'prompt_token_count'):
                    return {
                        'input_tokens': usage.prompt_token_count,
                        'output_tokens': usage.candidates_token_count,
                        'total_tokens': usage.total_token_count,
                    }
            
            # Method 3: Check for metadata dictionary
            if hasattr(response, 'metadata'):
                metadata = response.metadata
                if isinstance(metadata, dict) and 'usage' in metadata:
                    usage = metadata['usage']
                    return {
                        'input_tokens': usage.get('prompt_token_count', 0),
                        'output_tokens': usage.get('candidates_token_count', 0),
                        'total_tokens': usage.get('total_token_count', 0),
                    }
            
            # Method 4: Try accessing via __dict__
            if hasattr(response, '__dict__'):
                # Check for various possible attribute names
                for attr_name in ['usage_metadata', 'usage', 'token_usage', '_usage']:
                    if hasattr(response, attr_name):
                        usage = getattr(response, attr_name)
                        # Check if it's an object with token counts
                        if hasattr(usage, 'prompt_token_count'):
                            return {
                                'input_tokens': usage.prompt_token_count,
                                'output_tokens': usage.candidates_token_count,
                                'total_tokens': usage.total_token_count,
                            }
                        # Check if it's a dictionary
                        elif isinstance(usage, dict):
                            return {
                                'input_tokens': usage.get('prompt_token_count', usage.get('input_tokens', 0)),
                                'output_tokens': usage.get('candidates_token_count', usage.get('output_tokens', 0)),
                                'total_tokens': usage.get('total_token_count', usage.get('total_tokens', 0)),
                            }
            
            # Method 5: Try to find usage in response text/JSON
            if hasattr(response, 'text') and hasattr(response, 'raw_response'):
                try:
                    import json
                    raw = response.raw_response
                    if isinstance(raw, dict) and 'usageMetadata' in raw:
                        usage = raw['usageMetadata']
                        return {
                            'input_tokens': usage.get('promptTokenCount', 0),
                            'output_tokens': usage.get('candidatesTokenCount', 0),
                            'total_tokens': usage.get('totalTokenCount', 0),
                        }
                except:
                    pass
            
            return None
            
        except Exception as e:
            print(f"⚠️  Error extracting usage from response: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def track_response(self, response: Any, model: str, context: Optional[str] = None):
        """
        Track cost for an API response.
        
        Args:
            response: Gemini API response object
            model: Model name (e.g., "gemini-2.5-flash")
            context: Context identifier (e.g., "search_agent", "scrape_agent")
        """
        usage_data = self.extract_usage_from_response(response, model)
        
        if usage_data:
            # Create a mock TokenUsage object
            from utils.cost_tracker import TokenUsage
            from datetime import datetime
            
            token_usage = TokenUsage(
                input_tokens=usage_data['input_tokens'],
                output_tokens=usage_data['output_tokens'],
                total_tokens=usage_data['total_tokens'],
                model=model,
                timestamp=datetime.now(),
                call_id=self.tracker._generate_call_id(),
                context=context,
            )
            
            cost_record = self.tracker.calculate_cost(token_usage)
            self.tracker.record_call(cost_record)
            
            print(f"💰 Cost tracked: {cost_record.input_tokens:,} input + {cost_record.output_tokens:,} output = ${cost_record.total_cost:.6f} ({context or 'unknown'})")
        else:
            print(f"⚠️  Could not extract token usage from response (context: {context or 'unknown'})")


def track_agent_response(agent_response: Any, model: str, context: Optional[str] = None):
    """
    Convenience function to track cost from an Agno Agent response.
    
    Usage:
        response = agent.run(query)
        track_agent_response(response, "gemini-2.5-flash", context="search_agent")
    
    Args:
        agent_response: Response from Agno Agent.run()
        model: Model name
        context: Context identifier
    """
    wrapper = GeminiCostWrapper()
    wrapper.track_response(agent_response, model, context)

