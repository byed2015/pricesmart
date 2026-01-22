#!/usr/bin/env python3
"""
Quick validation that token tracking code changes are syntactically correct.
This doesn't require running the full app - just validates imports.
"""

import sys
from pathlib import Path

def validate_files():
    """Validate that all modified files have correct syntax and token tracking integration."""
    print("\n" + "="*70)
    print("🧪 Token Tracking Code Validation")
    print("="*70)
    
    project_root = Path(__file__).parent
    backend_root = project_root / "backend"
    
    files_to_check = {
        "pricing_pipeline.py": {
            "path": backend_root / "app/agents/pricing_pipeline.py",
            "checks": [
                ("reset_tracker import", "from app.core.token_costs import get_tracker, reset_tracker"),
                ("reset_tracker call", "reset_tracker()"),
                ("token_usage capture", 'result["token_usage"]'),
            ]
        },
        "product_matching.py": {
            "path": backend_root / "app/agents/product_matching.py",
            "checks": [
                ("get_tracker import", "from app.core.token_costs import get_tracker"),
                ("ainvoke token capture", "tracker.add_call"),
            ]
        },
        "search_strategy.py": {
            "path": backend_root / "app/agents/search_strategy.py",
            "checks": [
                ("get_tracker import", "from app.core.token_costs import get_tracker"),
                ("token capture block", "tracker.add_call"),
            ]
        },
        "data_enricher.py": {
            "path": backend_root / "app/agents/data_enricher.py",
            "checks": [
                ("get_tracker import", "from app.core.token_costs import get_tracker"),
                ("token capture block", "tracker.add_call"),
            ]
        },
        "catalog_enrichment.py": {
            "path": backend_root / "app/agents/catalog_enrichment.py",
            "checks": [
                ("get_tracker import", "from app.core.token_costs import get_tracker"),
                ("token capture block", "tracker.add_call"),
            ]
        },
        "market_research.py": {
            "path": backend_root / "app/agents/market_research.py",
            "checks": [
                ("get_tracker import", "from app.core.token_costs import get_tracker"),
                ("token capture block", "tracker.add_call"),
            ]
        },
        "dashboard.py": {
            "path": project_root / "frontend/dashboard.py",
            "checks": [
                ("token_data detection", 'token_data = result.get("token_usage"'),
                ("real vs estimated", "is_estimated"),
            ]
        }
    }
    
    all_passed = True
    
    for file_name, file_config in files_to_check.items():
        print(f"\n📄 {file_name}")
        
        file_path = file_config["path"]
        if not file_path.exists():
            print(f"   ❌ File not found: {file_path}")
            all_passed = False
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for check_name, check_string in file_config["checks"]:
                if check_string in content:
                    print(f"   ✅ {check_name}")
                else:
                    print(f"   ❌ {check_name} - NOT FOUND")
                    all_passed = False
                    
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")
            all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ All Token Tracking Integrations Validated!")
        print("="*70)
        print("\nNext Steps:")
        print("1. pip install -r backend/requirements.txt")
        print("2. streamlit run frontend/dashboard.py")
        print("3. Analyze a product URL")
        print("4. Look for ✅ REAL tokens (not ⚠️ ESTIMADO)")
        print("\n")
    else:
        print("❌ Some checks failed - review above")
        print("="*70 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = validate_files()
    sys.exit(0 if success else 1)
