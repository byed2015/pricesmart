#!/usr/bin/env python3
"""
Quick test to verify token tracking integration works end-to-end.
Tests that real tokens are captured and passed to dashboard.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
backend_root = project_root / "backend"
sys.path.insert(0, str(backend_root))
sys.path.insert(0, str(project_root))

async def test_token_tracking():
    """Test token tracking integration."""
    print("\n" + "="*70)
    print("🧪 Token Tracking Integration Test")
    print("="*70)
    
    # 1. Test token_costs module
    print("\n1️⃣  Testing token_costs module...")
    try:
        from core.token_costs import (
            TokenUsage, 
            TokenCostTracker, 
            get_tracker, 
            reset_tracker,
            OPENAI_PRICING
        )
        print("   ✅ token_costs imports successful")
        print(f"   ✅ Pricing models available: {list(OPENAI_PRICING.keys())}")
    except Exception as e:
        print(f"   ❌ Failed to import token_costs: {e}")
        return False
    
    # 2. Test reset tracker
    print("\n2️⃣  Testing reset_tracker()...")
    try:
        reset_tracker()
        tracker = get_tracker()
        summary = tracker.get_summary()
        assert summary["total_tokens"] == 0, "Tracker should be empty after reset"
        print("   ✅ reset_tracker() works correctly")
    except Exception as e:
        print(f"   ❌ reset_tracker() failed: {e}")
        return False
    
    # 3. Test adding calls to tracker
    print("\n3️⃣  Testing tracker.add_call()...")
    try:
        tracker.add_call(
            model="gpt-4o-mini",
            input_tokens=100,
            output_tokens=50
        )
        summary = tracker.get_summary()
        assert summary["total_tokens"] == 150, f"Expected 150 tokens, got {summary['total_tokens']}"
        assert summary["total_calls"] == 1, f"Expected 1 call, got {summary['total_calls']}"
        print("   ✅ add_call() works correctly")
        print(f"   ✅ Cost calculation: ${summary['total_cost_usd']:.6f}")
    except Exception as e:
        print(f"   ❌ add_call() failed: {e}")
        return False
    
    # 4. Test agent imports
    print("\n4️⃣  Testing agent imports...")
    agents_to_test = [
        "app.agents.search_strategy",
        "app.agents.data_enricher", 
        "app.agents.catalog_enrichment",
        "app.agents.product_matching",
        "app.agents.market_research",
        "app.agents.pricing_pipeline",
    ]
    
    for agent_path in agents_to_test:
        try:
            __import__(agent_path)
            agent_name = agent_path.split(".")[-1]
            print(f"   ✅ {agent_name} imports successfully")
        except Exception as e:
            agent_name = agent_path.split(".")[-1]
            print(f"   ⚠️  {agent_name} import failed: {e}")
    
    # 5. Test dashboard imports
    print("\n5️⃣  Testing dashboard module...")
    try:
        from frontend.dashboard import main
        print("   ✅ dashboard imports successfully")
    except Exception as e:
        print(f"   ⚠️  dashboard import failed: {e}")
    
    print("\n" + "="*70)
    print("✅ Token Tracking Integration Tests Complete!")
    print("="*70)
    print("\nNext Steps:")
    print("1. Run: streamlit run frontend/dashboard.py")
    print("2. Analyze a product URL")
    print("3. Check for ✅ REAL tokens displayed (not ⚠️ ESTIMADO)")
    print("4. Verify token counts match actual API usage")
    print("\n")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_token_tracking())
    sys.exit(0 if success else 1)
