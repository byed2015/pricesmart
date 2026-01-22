"""
OpenAI API wrapper with automatic token cost tracking
Intercepts API calls to record token usage
"""

import logging
from typing import Optional, Any
from functools import wraps
from backend.core.token_costs import get_tracker

logger = logging.getLogger(__name__)


def track_tokens(model: str):
    """Decorator to track tokens from function that returns OpenAI response"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Try to extract token usage from response
            if hasattr(result, 'usage'):
                usage = result.usage
                tracker = get_tracker()
                tracker.add_call(
                    model=model,
                    input_tokens=getattr(usage, 'prompt_tokens', 0),
                    output_tokens=getattr(usage, 'completion_tokens', 0)
                )
                logger.debug(f"Tracked tokens for {model}: {getattr(usage, 'prompt_tokens', 0)} input, {getattr(usage, 'completion_tokens', 0)} output")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Try to extract token usage from response
            if hasattr(result, 'usage'):
                usage = result.usage
                tracker = get_tracker()
                tracker.add_call(
                    model=model,
                    input_tokens=getattr(usage, 'prompt_tokens', 0),
                    output_tokens=getattr(usage, 'completion_tokens', 0)
                )
                logger.debug(f"Tracked tokens for {model}: {getattr(usage, 'prompt_tokens', 0)} input, {getattr(usage, 'completion_tokens', 0)} output")
            
            return result
        
        # Return async or sync wrapper based on function type
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x100:
            return async_wrapper
        return sync_wrapper
    
    return decorator


def extract_and_track_tokens(response: Any, model: str) -> None:
    """Extract tokens from response and track them"""
    if hasattr(response, 'usage'):
        usage = response.usage
        tracker = get_tracker()
        tracker.add_call(
            model=model,
            input_tokens=getattr(usage, 'prompt_tokens', 0),
            output_tokens=getattr(usage, 'completion_tokens', 0)
        )
        logger.debug(f"Tracked tokens for {model}: {getattr(usage, 'prompt_tokens', 0)} input, {getattr(usage, 'completion_tokens', 0)} output")
