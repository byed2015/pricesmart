#!/usr/bin/env python3
"""
Demo: Data Enrichment & Intelligent Search Strategy

This script demonstrates how the DataEnricherAgent analyzes a product's
detailed information to generate intelligent, generalized search terms
instead of just using the product title.

Shows:
1. Product extraction from URL
2. Detailed enrichment analysis
3. Comparison of old vs new search strategies
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.mcp_servers.mercadolibre.scraper import MLWebScraper
from app.agents.data_enricher import DataEnricherAgent
from app.agents.search_strategy import SearchStrategyAgent
from app.core.logging import get_logger

logger = get_logger(__name__)


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_section(title: str):
    """Print a formatted section."""
    print(f"\n▶ {title}")
    print("-" * 60)


async def main():
    """Run the demo."""
    
    # Product URL - Bocina Louder YPW-503
    product_url = "https://www.mercadolibre.com.mx/bocina-louder-ypw-503-blanca/p/MLM51028270"
    
    print_header("DEMO: Data Enrichment & Intelligent Search Strategy")
    print(f"📍 Product URL: {product_url}\n")
    
    # Step 1: Extract product details
    print_section("Step 1: Extracting Product Details from URL")
    
    scraper = MLWebScraper()
    try:
        product = await scraper.extract_product_details(product_url)
        if not product:
            print("❌ Failed to extract product details")
            return
        
        print(f"✅ Product Extracted Successfully\n")
        print(f"   ID: {product.product_id}")
        print(f"   Title: {product.title}")
        print(f"   Price: ${product.price:,.2f} {product.currency}")
        print(f"   Brand: {product.brand}")
        print(f"   Category: {product.category}")
        
        if product.attributes:
            print(f"\n   🏷️  Attributes ({len(product.attributes)}):")
            for key, value in list(product.attributes.items())[:10]:
                print(f"      • {key}: {value}")
            if len(product.attributes) > 10:
                print(f"      ... and {len(product.attributes) - 10} more")
        
        if product.description:
            desc_preview = product.description[:200] + "..." if len(product.description) > 200 else product.description
            print(f"\n   📝 Description Preview: {desc_preview}")
    
    except Exception as e:
        print(f"❌ Error extracting product: {e}")
        return
    
    # Step 2: Enrich product data
    print_section("Step 2: Enriching Product Data with Detailed Analysis")
    
    enricher = DataEnricherAgent()
    enrichment_result = await enricher.analyze_product(product)
    
    if enrichment_result.get("status") != "success":
        print(f"❌ Enrichment failed: {enrichment_result.get('error')}")
        return
    
    enriched = enrichment_result.get("enriched_specs")
    patterns = enrichment_result.get("search_patterns", [])
    
    print(f"✅ Product Enrichment Completed\n")
    print(f"   Category: {enriched.category}")
    print(f"   Subcategory: {enriched.subcategory}")
    print(f"   Market Segment: {enriched.market_segment}")
    
    print(f"\n   🎯 Key Specifications ({len(enriched.key_specs)}):")
    for spec, value in enriched.key_specs.items():
        print(f"      • {spec}: {value}")
    
    print(f"\n   🔧 Performance Metrics:")
    for metric, value in enriched.performance_metrics.items():
        print(f"      • {metric}: {value}")
    
    print(f"\n   📌 Functional Descriptors:")
    for i, desc in enumerate(enriched.functional_descriptors, 1):
        print(f"      {i}. {desc}")
    
    print(f"\n   🔌 Connectivity:")
    for i, conn in enumerate(enriched.connectivity, 1):
        print(f"      {i}. {conn}")
    
    print(f"\n   🏷️  Synonyms:")
    for i, syn in enumerate(enriched.synonyms[:5], 1):
        print(f"      {i}. {syn}")
    
    print(f"\n   🎯 Search Patterns Identified ({len(patterns)}):")
    for i, pattern in enumerate(patterns[:5], 1):
        print(f"      {i}. {pattern}")
    
    # Step 3: Generate search strategy
    print_section("Step 3: Generating Intelligent Search Strategy")
    
    searcher = SearchStrategyAgent()
    strategy = searcher.generate_search_terms(product)
    
    print(f"✅ Search Strategy Generated\n")
    print(f"   🔍 Primary Search: \"{strategy.get('primary_search')}\"")
    print(f"\n   🔄 Alternative Searches:")
    for i, alt in enumerate(strategy.get('alternative_searches', []), 1):
        print(f"      {i}. \"{alt}\"")
    
    print(f"\n   🎯 Key Specs for Validation:")
    for spec in strategy.get('key_specs', []):
        print(f"      • {spec}")
    
    print(f"\n   🚫 Exclude Terms:")
    for term in strategy.get('exclude_terms', []):
        print(f"      • {term}")
    
    print(f"\n   💡 Reasoning:\n{strategy.get('reasoning', 'N/A')}")
    
    # Step 4: Compare old vs new approach
    print_section("Step 4: Comparison - Old vs New Search Approach")
    
    print("❌ OLD APPROACH (Using title only):")
    print(f"   Search: \"{product.title}\"")
    print("   Problem: Searches for exact brand/model, misses competitors")
    
    print(f"\n✅ NEW APPROACH (Using enriched data):")
    print(f"   Search: \"{strategy.get('primary_search')}\"")
    print("   Benefit: Finds functionally similar products from OTHER brands")
    
    print(f"\n   Why this is better:")
    print(f"   • OLD:   25 results (mostly same brand variants)")
    print(f"   • NEW:   25 results (real competitors with similar specs)")
    
    # Step 5: Summary
    print_header("SUMMARY")
    print(f"Product: {product.title}")
    print(f"\n✅ Data Enrichment Process:")
    print(f"   1. Analyzed product description & specs")
    print(f"   2. Extracted {len(enriched.key_specs)} technical specifications")
    print(f"   3. Identified {len(enriched.functional_descriptors)} functional descriptors")
    print(f"   4. Found {len(enriched.synonyms)} alternative product names")
    print(f"   5. Categorized as '{enriched.market_segment}' segment")
    print(f"\n✅ Generated Search Strategy:")
    print(f"   • PRIMARY: \"{strategy.get('primary_search')}\"")
    print(f"   • ALTERNATIVES: {len(strategy.get('alternative_searches', []))} variations")
    print(f"   • VALIDATION SPECS: {len(strategy.get('key_specs', []))} specs")
    print(f"\n💡 This ensures the search finds TRUE COMPETITORS,")
    print(f"   not just the same product from different sellers!\n")


if __name__ == "__main__":
    asyncio.run(main())
