"""
Token cost tracking for OpenAI API calls
Provides pricing information and cost calculation utilities
"""

from dataclasses import dataclass
from typing import Dict, Optional

# OpenAI pricing as of January 2026
# Reference: https://openai.com/pricing
OPENAI_PRICING = {
    "gpt-4o": {
        "input": 0.0025,      # $2.50 per 1M input tokens = $0.0025 per 1K
        "output": 0.010,      # $10.00 per 1M output tokens = $0.010 per 1K
        "name": "GPT-4 Omni"
    },
    "gpt-4o-mini": {
        "input": 0.00015,     # $0.15 per 1M input tokens = $0.00015 per 1K
        "output": 0.0006,     # $0.60 per 1M output tokens = $0.0006 per 1K
        "name": "GPT-4 Omni Mini"
    },
    "gpt-4-turbo": {
        "input": 0.00003,     # $0.03 per 1K
        "output": 0.0001,     # $0.10 per 1K
        "name": "GPT-4 Turbo"
    },
    "gpt-3.5-turbo": {
        "input": 0.0000005,   # $0.50 per 1M input tokens
        "output": 0.0000015,  # $1.50 per 1M output tokens
        "name": "GPT-3.5 Turbo"
    },
    "text-embedding-3-small": {
        "input": 0.00000002,  # $0.02 per 1M tokens
        "output": 0,
        "name": "Embedding 3 Small"
    },
    "text-embedding-3-large": {
        "input": 0.00000013,  # $0.13 per 1M tokens
        "output": 0,
        "name": "Embedding 3 Large"
    }
}


@dataclass
class TokenUsage:
    """Tracks token usage for a single API call"""
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    
    @property
    def total_cost_usd(self) -> float:
        """Calculate total cost in USD"""
        if self.model not in OPENAI_PRICING:
            return 0.0
        
        pricing = OPENAI_PRICING[self.model]
        input_cost = (self.input_tokens / 1000) * pricing["input"]
        output_cost = (self.output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost
    
    @property
    def model_name(self) -> str:
        """Get human-readable model name"""
        return OPENAI_PRICING.get(self.model, {}).get("name", self.model)


class TokenCostTracker:
    """Track and aggregate token costs across multiple API calls"""
    
    def __init__(self):
        self.calls: list[TokenUsage] = []
    
    def add_call(self, model: str, input_tokens: int, output_tokens: int) -> None:
        """Record a token usage from an API call"""
        usage = TokenUsage(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens
        )
        self.calls.append(usage)
    
    @property
    def total_input_tokens(self) -> int:
        """Get total input tokens across all calls"""
        return sum(call.input_tokens for call in self.calls)
    
    @property
    def total_output_tokens(self) -> int:
        """Get total output tokens across all calls"""
        return sum(call.output_tokens for call in self.calls)
    
    @property
    def total_tokens(self) -> int:
        """Get total tokens (input + output)"""
        return self.total_input_tokens + self.total_output_tokens
    
    @property
    def total_cost_usd(self) -> float:
        """Get total cost in USD for all calls"""
        return sum(call.total_cost_usd for call in self.calls)
    
    @property
    def cost_breakdown_by_model(self) -> Dict[str, Dict]:
        """Get cost breakdown by model"""
        breakdown = {}
        for call in self.calls:
            model = call.model
            if model not in breakdown:
                breakdown[model] = {
                    "model_name": call.model_name,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0.0
                }
            breakdown[model]["input_tokens"] += call.input_tokens
            breakdown[model]["output_tokens"] += call.output_tokens
            breakdown[model]["total_tokens"] += call.total_tokens
            breakdown[model]["cost_usd"] += call.total_cost_usd
        return breakdown
    
    def get_summary(self) -> Dict:
        """Get comprehensive summary of token usage and costs"""
        return {
            "total_calls": len(self.calls),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost_usd,
            "cost_per_1k_tokens": (self.total_cost_usd / max(self.total_tokens / 1000, 1)),
            "cost_by_model": self.cost_breakdown_by_model
        }
    
    def format_summary_for_display(self) -> str:
        """Format summary as readable string"""
        summary = self.get_summary()
        lines = [
            f"📊 API USAGE SUMMARY",
            f"Total Calls: {summary['total_calls']}",
            f"",
            f"🔤 TOKENS",
            f"  Input:  {summary['total_input_tokens']:,}",
            f"  Output: {summary['total_output_tokens']:,}",
            f"  Total:  {summary['total_tokens']:,}",
            f"",
            f"💰 COSTS",
            f"  Total Cost: ${summary['total_cost_usd']:.6f} USD",
            f"  Cost per 1K tokens: ${summary['cost_per_1k_tokens']:.6f}",
        ]
        
        if summary['cost_by_model']:
            lines.append("")
            lines.append("📈 COST BY MODEL")
            for model, data in summary['cost_by_model'].items():
                lines.append(f"  {data['model_name']}:")
                lines.append(f"    Tokens: {data['total_tokens']:,} ({data['input_tokens']:,}→{data['output_tokens']:,})")
                lines.append(f"    Cost: ${data['cost_usd']:.6f}")
        
        return "\n".join(lines)


# Global tracker instance
_tracker: Optional[TokenCostTracker] = None


def get_tracker() -> TokenCostTracker:
    """Get or create the global token cost tracker"""
    global _tracker
    if _tracker is None:
        _tracker = TokenCostTracker()
    return _tracker


def reset_tracker() -> None:
    """Reset the global tracker"""
    global _tracker
    _tracker = TokenCostTracker()
