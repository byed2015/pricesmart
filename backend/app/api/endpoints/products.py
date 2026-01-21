from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from ...database import get_db
from ...models import Product
from ...schemas import ProductCreate, ProductUpdate, ProductResponse, ProductList
from ...agents.pricing_pipeline import PricingPipeline
from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=ProductList)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Lista todos los productos Louder con paginación.
    """
    query = db.query(Product)
    
    # Filtros opcionales
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    if category:
        query = query.filter(Product.category == category)
    
    # Total count
    total = query.count()
    
    # Paginación
    products = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return ProductList(
        total=total,
        page=page,
        page_size=page_size,
        products=products
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene un producto por ID.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
):
    """
    Crea un nuevo producto Louder.
    """
    # Verificar que el SKU no exista
    existing = db.query(Product).filter(Product.sku == product_data.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Product with SKU '{product_data.sku}' already exists")
    
    product = Product(**product_data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
):
    """
    Actualiza un producto existente.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Actualizar solo los campos proporcionados
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    """
    Elimina (desactiva) un producto.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.is_active = False
    db.commit()
    return None


@router.post("/{product_id}/scan", status_code=202)
async def trigger_product_scan(
    product_id: int,
    db: Session = Depends(get_db),
):
    """
    Trigger un scan on-demand para un producto específico.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # TODO: Implement Celery task trigger
    # from ...tasks import scan_single_product
    # task = scan_single_product.delay(product_id)
    
    return {
        "message": f"Scan triggered for product {product.name}",
        "product_id": product_id,
        # "task_id": task.id
    }


@router.post("/catalog/bulk-analyze")
async def bulk_analyze_catalog(
    product_ids: Optional[List[int]] = None,
    category: Optional[str] = None,
    price_tolerance: float = 0.30,
    max_offers_per_product: int = 25,
    skip_low_rotation: bool = True,
    db: Session = Depends(get_db),
):
    """
    Analiza múltiples productos del catálogo vs competencia.
    
    Args:
        product_ids: Lista específica de product IDs a analizar (si None, analiza todos)
        category: Filtrar por categoría (ej: "BOCINAS GENERAL")
        price_tolerance: Rango de precio ±tolerance para búsqueda (0.30 = ±30%)
        max_offers_per_product: Máximo de competidores a analizar por producto
        skip_low_rotation: Omitir productos con rotación baja (<1.5)
        db: Database session
    
    Returns:
        Dict con resultados de análisis de múltiples productos
        
    Example:
        POST /api/products/catalog/bulk-analyze
        {
            "product_ids": [1, 2, 3],
            "price_tolerance": 0.30,
            "max_offers_per_product": 25
        }
    """
    logger.info(
        "Starting bulk catalog analysis",
        product_ids=product_ids,
        category=category,
        price_tolerance=price_tolerance,
        skip_low_rotation=skip_low_rotation
    )
    
    # Build query
    query = db.query(Product).filter(Product.is_active == True)
    
    # Filter by specific IDs if provided
    if product_ids:
        query = query.filter(Product.id.in_(product_ids))
    
    # Filter by category if provided
    if category:
        query = query.filter(Product.category == category)
    
    # Skip low rotation products if requested
    if skip_low_rotation:
        query = query.filter(Product.rotation_index >= 1.5)
    
    products = query.all()
    
    if not products:
        return {
            "status": "no_products",
            "message": "No products found matching criteria",
            "analyzed": 0,
            "results": []
        }
    
    logger.info(f"Found {len(products)} products to analyze")
    
    # Initialize pipeline
    pipeline = PricingPipeline()
    results = []
    
    # Analyze each product
    for idx, product in enumerate(products, 1):
        try:
            logger.info(
                f"Analyzing product {idx}/{len(products)}",
                sku=product.sku,
                title=product.title
            )
            
            # Skip if no ML URL
            if not product.ml_url:
                logger.warning(f"Skipping product {product.sku}: no ML URL")
                results.append({
                    "product_id": product.id,
                    "sku": product.sku,
                    "title": product.title,
                    "status": "skipped",
                    "reason": "No MercadoLibre URL"
                })
                continue
            
            # Run analysis
            analysis = await pipeline.analyze_product(
                product_input=product.ml_url,
                cost_price=float(product.cost_price or 0),
                price_tolerance=price_tolerance,
                max_offers=max_offers_per_product
            )
            
            # Extract recommendation
            final_rec = analysis.get("final_recommendation")
            search_strategy = analysis.get("pipeline_steps", {}).get("search_strategy", {})
            
            if final_rec and analysis.get("success", True):
                status = "success"
                current_price = analysis.get("pipeline_steps", {}).get("pivot_product", {}).get("price", 0)
                recommended_price = final_rec.get("recommended_price", 0)
                price_gap = ((current_price - recommended_price) / recommended_price * 100) if recommended_price > 0 else 0
                
                result = {
                    "product_id": product.id,
                    "sku": product.sku,
                    "title": product.title,
                    "status": status,
                    "current_price": current_price,
                    "recommended_price": recommended_price,
                    "price_gap_percent": round(price_gap, 2),
                    "competitors_found": len(analysis.get("pipeline_steps", {}).get("scraping", {}).get("offers", [])),
                    "confidence": final_rec.get("confidence_score", final_rec.get("confidence", 0)),
                    "market_position": final_rec.get("market_position", "unknown"),
                    "reasoning": final_rec.get("reasoning", ""),
                    "search_strategy": {
                        "primary_search": search_strategy.get("primary_search"),
                        "alternative_searches": search_strategy.get("alternative_searches", [])
                    }
                }
            else:
                status = "error"
                result = {
                    "product_id": product.id,
                    "sku": product.sku,
                    "title": product.title,
                    "status": status,
                    "error": analysis.get("errors", ["Unknown error"])
                }
            
            results.append(result)
            
        except Exception as e:
            logger.error(
                f"Error analyzing product {product.sku}",
                error=str(e),
                exc_info=True
            )
            results.append({
                "product_id": product.id,
                "sku": product.sku,
                "title": product.title,
                "status": "error",
                "error": str(e)
            })
    
    # Count successes
    successful = sum(1 for r in results if r.get("status") == "success")
    
    logger.info(
        "Bulk analysis completed",
        total=len(results),
        successful=successful
    )
    
    return {
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat(),
        "analyzed": len(results),
        "successful": successful,
        "price_tolerance": price_tolerance,
        "results": results
    }
