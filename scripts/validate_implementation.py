"""
Quick validation script to test the new features.

Usage:
    uv run python scripts/validate_implementation.py
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all new modules can be imported."""
    print("Testing imports...")
    try:
        from backend.app.agents.catalog_enrichment import CatalogEnrichmentAgent
        print("  ✅ CatalogEnrichmentAgent imported successfully")
    except Exception as e:
        print(f"  ❌ CatalogEnrichmentAgent import failed: {e}")
        return False
    
    try:
        from backend.app.models.product import Product
        print("  ✅ Product model imported successfully")
    except Exception as e:
        print(f"  ❌ Product model import failed: {e}")
        return False
    
    try:
        from backend.app.agents.pricing_pipeline import PricingPipeline
        print("  ✅ PricingPipeline imported successfully")
    except Exception as e:
        print(f"  ❌ PricingPipeline import failed: {e}")
        return False
    
    return True


def test_catalog_model():
    """Verify Product model has new fields."""
    print("\nChecking Product model fields...")
    from backend.app.models.product import Product
    
    required_fields = [
        'brand', 'category', 'warehouse_location', 'ml_url',
        'cost_price', 'current_stock', 'rotation_index', 'total_sales',
        'sales_oct_2025', 'sales_nov_2025', 'sales_dec_2025', 'sales_jan_2026',
        'normalized_title', 'generic_description', 'key_specs', 'search_keywords'
    ]
    
    for field in required_fields:
        if hasattr(Product, field):
            print(f"  ✅ Field '{field}' exists")
        else:
            print(f"  ❌ Field '{field}' missing")
            return False
    
    return True


def test_scraper_functions():
    """Verify scraper has price filter functions."""
    print("\nChecking scraper improvements...")
    import inspect
    from backend.app.mcp_servers.mercadolibre import scraper
    
    # Check listing_url function signature
    sig = inspect.signature(scraper.listing_url)
    params = list(sig.parameters.keys())
    
    if 'price_min' in params and 'price_max' in params:
        print("  ✅ listing_url has price_min and price_max parameters")
    else:
        print(f"  ❌ listing_url missing price parameters. Has: {params}")
        return False
    
    # Check search_products signature
    sig = inspect.signature(scraper.MLWebScraper.search_products)
    params = list(sig.parameters.keys())
    
    if 'price_min' in params and 'price_max' in params:
        print("  ✅ search_products has price_min and price_max parameters")
    else:
        print(f"  ❌ search_products missing price parameters. Has: {params}")
        return False
    
    return True


def test_pipeline_signature():
    """Verify PricingPipeline accepts price_tolerance."""
    print("\nChecking PricingPipeline...")
    import inspect
    from backend.app.agents.pricing_pipeline import PricingPipeline
    
    sig = inspect.signature(PricingPipeline.analyze_product)
    params = list(sig.parameters.keys())
    
    if 'price_tolerance' in params:
        print("  ✅ analyze_product has price_tolerance parameter")
        # Check default value
        default = sig.parameters['price_tolerance'].default
        if default == 0.30:
            print(f"  ✅ Default price_tolerance is 0.30 (±30%)")
        else:
            print(f"  ⚠️  Default price_tolerance is {default} (expected 0.30)")
    else:
        print(f"  ❌ analyze_product missing price_tolerance parameter. Has: {params}")
        return False
    
    return True


def test_product_matching_workflow():
    """Verify ProductMatchingAgent has validate_equivalence node."""
    print("\nChecking ProductMatchingAgent workflow...")
    import inspect
    from backend.app.agents.product_matching import ProductMatchingAgent
    
    agent = ProductMatchingAgent()
    
    # Check if validate_equivalence method exists
    if hasattr(agent, 'validate_equivalence'):
        print("  ✅ validate_equivalence method exists")
    else:
        print("  ❌ validate_equivalence method missing")
        return False
    
    # Check graph compilation
    if hasattr(agent, 'graph'):
        print("  ✅ Agent graph compiled successfully")
    else:
        print("  ❌ Agent graph failed to compile")
        return False
    
    return True


def main():
    print("=" * 60)
    print("🔍 IMPLEMENTATION VALIDATION")
    print("=" * 60)
    
    all_passed = True
    
    all_passed &= test_imports()
    all_passed &= test_catalog_model()
    all_passed &= test_scraper_functions()
    all_passed &= test_pipeline_signature()
    all_passed &= test_product_matching_workflow()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL VALIDATION CHECKS PASSED!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Load catalog: uv run python scripts/load_catalog.py 'CSV_FILE'")
        print("2. Test frontend: http://localhost:8502")
        print("3. Test API endpoint: POST /api/products/catalog/bulk-analyze")
        return 0
    else:
        print("❌ SOME VALIDATION CHECKS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
