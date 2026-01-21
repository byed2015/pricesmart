"""
Script to load product catalog from CSV into database.

Usage:
    python scripts/load_catalog.py path/to/catalog.csv
    
Or from project root:
    python -m scripts.load_catalog "reporte resumen ventas de 2025-10 a 2026-01 Todos.csv"
"""
import sys
import csv
from pathlib import Path
from decimal import Decimal
from datetime import datetime
import asyncio

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.database import SessionLocal
from backend.app.models.product import Product
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


def parse_price(price_str: str) -> float:
    """Parse price string like '$155.00' to float."""
    if not price_str:
        return 0.0
    # Remove $, commas
    cleaned = price_str.replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        logger.warning(f"Could not parse price: {price_str}")
        return 0.0


def parse_int(value: str) -> int:
    """Parse integer safely."""
    if not value or value == "":
        return 0
    try:
        return int(float(value))
    except ValueError:
        return 0


def load_catalog_from_csv(csv_path: str):
    """
    Load products from CSV into database.
    
    CSV Expected columns:
    - Id_Articulo: Product SKU
    - Marca: Brand
    - Linea: Category line
    - Titulo: Product title
    - Ubicacion: Warehouse location
    - 2025-10, 2025-11, 2025-12, 2026-01: Monthly sales
    - totalSalidas: Total sales
    - Stock: Current stock
    - rotacion: Rotation index
    - enlace: MercadoLibre URL
    - costo: Cost price
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return
    
    logger.info(f"Loading catalog from {csv_path}")
    
    db = SessionLocal()
    products_created = 0
    products_updated = 0
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                sku = row.get("Id_Articulo", "").strip()
                if not sku:
                    continue
                
                # Check if product exists
                existing = db.query(Product).filter(Product.sku == sku).first()
                
                # Prepare product data
                title = row.get("Titulo", "").strip()
                product_data = {
                    "sku": sku,
                    "name": title,  # Use title for name field
                    "brand": row.get("Marca", "").strip(),
                    "category": row.get("Linea", "").strip(),
                    "title": title,
                    "warehouse_location": row.get("Ubicacion", "").strip(),
                    "ml_url": row.get("enlace", "").strip(),
                    "cost_price": parse_price(row.get("costo", "0")),
                    "current_stock": parse_int(row.get("Stock", "0")),
                    "rotation_index": float(row.get("rotacion", "0.0") or "0.0"),
                    "total_sales": parse_int(row.get("totalSalidas", "0")),
                    # Sales history
                    "sales_oct_2025": parse_int(row.get("2025-10", "0")),
                    "sales_nov_2025": parse_int(row.get("2025-11", "0")),
                    "sales_dec_2025": parse_int(row.get("2025-12", "0")),
                    "sales_jan_2026": parse_int(row.get("2026-01", "0")),
                }
                
                if existing:
                    # Update existing product
                    for key, value in product_data.items():
                        setattr(existing, key, value)
                    existing.updated_at = datetime.utcnow()
                    products_updated += 1
                    logger.info(f"Updated product: {sku} - {product_data['title'][:50]}")
                else:
                    # Create new product
                    product = Product(**product_data)
                    db.add(product)
                    products_created += 1
                    logger.info(f"Created product: {sku} - {product_data['title'][:50]}")
        
        db.commit()
        logger.info(
            f"Catalog loaded successfully",
            created=products_created,
            updated=products_updated,
            total=products_created + products_updated
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error loading catalog: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/load_catalog.py <path_to_csv>")
        print("Example: python scripts/load_catalog.py 'reporte resumen ventas de 2025-10 a 2026-01 Todos.csv'")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    load_catalog_from_csv(csv_path)
    print(f"\n✅ Catalog loaded from {csv_path}")
