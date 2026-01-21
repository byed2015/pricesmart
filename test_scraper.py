"""
Test rápido del scraper para verificar funcionalidad
"""
import asyncio
import sys
import os
from pathlib import Path

# Fix encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.mcp_servers.mercadolibre.scraper import MLWebScraper


async def test_scraper():
    print("[TEST] Probando scraper...")
    scraper = MLWebScraper()
    
    try:
        result = await scraper.search_products("bocina pasiva 10W")
        print(f"[OK] Encontradas {len(result.offers)} ofertas")
        
        for i, o in enumerate(result.offers[:5]):
            print(f"  {i+1}. {o.title[:60]} - ${o.price:,.0f}")
        
        return True
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_scraper())
    sys.exit(0 if success else 1)
