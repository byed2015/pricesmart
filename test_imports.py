import sys
from pathlib import Path

# Add backend to path the same way dashboard does it
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from app.agents.pricing_pipeline import PricingPipeline
    print("✅ PricingPipeline import ok")
    from app.core.token_costs import get_tracker
    print("✅ token_costs import ok")
except Exception as e:
    print("❌ Import failed:", type(e).__name__, e)
    import traceback
    traceback.print_exc()
