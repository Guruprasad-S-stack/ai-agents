"""
Professional Cost Tracking System for Gemini API Calls

This module provides accurate, scientific cost tracking by:
1. Extracting exact token counts from Gemini API responses
2. Calculating costs based on official pricing
3. Storing usage data in SQLite database
4. Providing real-time cost monitoring and reporting
"""

import os
import sqlite3
from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass
from contextlib import contextmanager
import json

# Gemini 2.5 Flash Pricing (per 1M tokens)
# Source: https://ai.google.dev/gemini-api/docs/pricing
PRICING = {
    "gemini-2.5-flash": {
        "input": 0.30,  # $0.30 per 1M tokens (text/image/video)
        "output": 2.50,  # $2.50 per 1M tokens
        "input_audio": 1.00,  # $1.00 per 1M tokens (audio)
    },
    "gemini-2.5-pro": {
        "input": 1.25,  # $1.25 per 1M tokens (≤200k tokens)
        "input_large": 2.50,  # $2.50 per 1M tokens (>200k tokens)
        "output": 10.00,  # $10.00 per 1M tokens (≤200k tokens)
        "output_large": 15.00,  # $15.00 per 1M tokens (>200k tokens)
    },
}


@dataclass
class TokenUsage:
    """Token usage data from a single API call."""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model: str
    timestamp: datetime
    call_id: str
    context: Optional[str] = None  # e.g., "search_agent", "scrape_agent"


@dataclass
class CostRecord:
    """Cost record for a single API call."""
    call_id: str
    model: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    timestamp: datetime
    context: Optional[str] = None


class CostTracker:
    """
    Professional cost tracking system for Gemini API calls.
    
    Features:
    - Extracts exact token counts from API responses
    - Calculates costs based on official pricing
    - Stores usage in SQLite database
    - Provides real-time cost monitoring
    """
    
    def __init__(self, db_path: str = "cost_tracking.db"):
        """
        Initialize the cost tracker.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    call_id TEXT UNIQUE NOT NULL,
                    model TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    input_cost REAL NOT NULL,
                    output_cost REAL NOT NULL,
                    total_cost REAL NOT NULL,
                    context TEXT,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON api_calls(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_model ON api_calls(model)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_context ON api_calls(context)
            """)
            
            conn.commit()
    
    def extract_token_usage(self, response, model: str, context: Optional[str] = None) -> Optional[TokenUsage]:
        """
        Extract exact token usage from Gemini API response.
        
        Args:
            response: Gemini API response object (from google.generativeai or agno)
            model: Model name (e.g., "gemini-2.5-flash")
            context: Context identifier (e.g., "search_agent", "scrape_agent")
        
        Returns:
            TokenUsage object if usage data found, None otherwise
        """
        try:
            # Method 1: Direct API response (google.generativeai)
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                return TokenUsage(
                    input_tokens=usage.prompt_token_count,
                    output_tokens=usage.candidates_token_count,
                    total_tokens=usage.total_token_count,
                    model=model,
                    timestamp=datetime.now(),
                    call_id=self._generate_call_id(),
                    context=context,
                )
            
            # Method 2: Agno Agent response (check if it wraps the response)
            if hasattr(response, 'response') and hasattr(response.response, 'usage_metadata'):
                usage = response.response.usage_metadata
                return TokenUsage(
                    input_tokens=usage.prompt_token_count,
                    output_tokens=usage.candidates_token_count,
                    total_tokens=usage.total_token_count,
                    model=model,
                    timestamp=datetime.now(),
                    call_id=self._generate_call_id(),
                    context=context,
                )
            
            # Method 3: Check for usage in response metadata
            if hasattr(response, 'metadata') and 'usage' in response.metadata:
                usage = response.metadata['usage']
                return TokenUsage(
                    input_tokens=usage.get('prompt_token_count', 0),
                    output_tokens=usage.get('candidates_token_count', 0),
                    total_tokens=usage.get('total_token_count', 0),
                    model=model,
                    timestamp=datetime.now(),
                    call_id=self._generate_call_id(),
                    context=context,
                )
            
            # Method 4: Try to access via __dict__ or getattr
            if hasattr(response, '__dict__'):
                for key in ['usage_metadata', 'usage', 'token_usage']:
                    if hasattr(response, key):
                        usage = getattr(response, key)
                        if hasattr(usage, 'prompt_token_count'):
                            return TokenUsage(
                                input_tokens=usage.prompt_token_count,
                                output_tokens=usage.candidates_token_count,
                                total_tokens=usage.total_token_count,
                                model=model,
                                timestamp=datetime.now(),
                                call_id=self._generate_call_id(),
                                context=context,
                            )
            
            return None
            
        except Exception as e:
            print(f"⚠️  Error extracting token usage: {e}")
            return None
    
    def calculate_cost(self, token_usage: TokenUsage) -> CostRecord:
        """
        Calculate cost based on token usage and model pricing.
        
        Args:
            token_usage: TokenUsage object
        
        Returns:
            CostRecord object
        """
        model_pricing = PRICING.get(token_usage.model, PRICING["gemini-2.5-flash"])
        
        # Calculate input cost
        if token_usage.model == "gemini-2.5-pro":
            # Tiered pricing based on prompt size
            if token_usage.input_tokens <= 200_000:
                input_cost = (token_usage.input_tokens / 1_000_000) * model_pricing["input"]
            else:
                input_cost = (token_usage.input_tokens / 1_000_000) * model_pricing["input_large"]
            
            if token_usage.input_tokens <= 200_000:
                output_cost = (token_usage.output_tokens / 1_000_000) * model_pricing["output"]
            else:
                output_cost = (token_usage.output_tokens / 1_000_000) * model_pricing["output_large"]
        else:
            # Flat pricing for Flash models
            input_cost = (token_usage.input_tokens / 1_000_000) * model_pricing["input"]
            output_cost = (token_usage.output_tokens / 1_000_000) * model_pricing["output"]
        
        total_cost = input_cost + output_cost
        
        return CostRecord(
            call_id=token_usage.call_id,
            model=token_usage.model,
            input_tokens=token_usage.input_tokens,
            output_tokens=token_usage.output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            timestamp=token_usage.timestamp,
            context=token_usage.context,
        )
    
    def record_call(self, cost_record: CostRecord):
        """
        Record an API call and its cost in the database.
        
        Args:
            cost_record: CostRecord object
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO api_calls 
                (call_id, model, input_tokens, output_tokens, total_tokens,
                 input_cost, output_cost, total_cost, context, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cost_record.call_id,
                cost_record.model,
                cost_record.input_tokens,
                cost_record.output_tokens,
                cost_record.input_tokens + cost_record.output_tokens,
                cost_record.input_cost,
                cost_record.output_cost,
                cost_record.total_cost,
                cost_record.context,
                cost_record.timestamp.isoformat(),
            ))
            conn.commit()
    
    def track_api_call(self, response, model: str, context: Optional[str] = None) -> Optional[CostRecord]:
        """
        Track an API call: extract usage, calculate cost, and store.
        
        Args:
            response: Gemini API response object
            model: Model name
            context: Context identifier
        
        Returns:
            CostRecord if successful, None otherwise
        """
        token_usage = self.extract_token_usage(response, model, context)
        
        if token_usage is None:
            print(f"⚠️  Could not extract token usage for {context or 'unknown'} call")
            return None
        
        cost_record = self.calculate_cost(token_usage)
        self.record_call(cost_record)
        
        return cost_record
    
    def get_total_cost(self, start_date: Optional[datetime] = None, 
                      end_date: Optional[datetime] = None,
                      model: Optional[str] = None,
                      context: Optional[str] = None) -> Dict:
        """
        Get total cost for a time period.
        
        Args:
            start_date: Start date (optional)
            end_date: End date (optional)
            model: Filter by model (optional)
            context: Filter by context (optional)
        
        Returns:
            Dictionary with cost summary
        """
        query = "SELECT SUM(input_cost), SUM(output_cost), SUM(total_cost), SUM(input_tokens), SUM(output_tokens), COUNT(*) FROM api_calls WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        if model:
            query += " AND model = ?"
            params.append(model)
        
        if context:
            query += " AND context = ?"
            params.append(context)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            
            return {
                "total_input_cost": row[0] or 0.0,
                "total_output_cost": row[1] or 0.0,
                "total_cost": row[2] or 0.0,
                "total_input_tokens": row[3] or 0,
                "total_output_tokens": row[4] or 0,
                "total_calls": row[5] or 0,
            }
    
    def get_cost_summary(self) -> Dict:
        """Get overall cost summary."""
        return self.get_total_cost()
    
    def _generate_call_id(self) -> str:
        """Generate a unique call ID."""
        return f"call_{datetime.now().timestamp()}_{os.urandom(4).hex()}"


# Global instance
_tracker = None

def get_cost_tracker() -> CostTracker:
    """Get or create the global cost tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = CostTracker()
    return _tracker

