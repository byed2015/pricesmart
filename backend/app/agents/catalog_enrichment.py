"""
Catalog Enrichment Agent - Normalizes product catalog data with AI intelligence.

Purpose:
- Transforms raw CSV titles (e.g., "ETB-1810 TRIPIE PARA BAFLE FUSSION")
- Into clean, searchable product descriptions
- Extracts key technical specifications
- Generates intelligent search keywords for cross-brand competitor discovery

Architecture:
- LangGraph-based agent for structured processing
- Uses gpt-4o-mini for efficiency and consistency
- Outputs JSON with normalized data for database storage
"""

import json
import re
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.logging import get_logger
from app.core.config import settings
from app.core.token_costs import get_tracker

logger = get_logger(__name__)


class CatalogEnrichmentAgent:
    """
    Agent that enriches raw catalog data with AI-generated normalized information.
    
    Input: Raw product data from CSV (title, brand, category, specs)
    Output: Enriched product data with:
        - normalized_title: Clean title without SKU/internal codes
        - generic_description: Human-readable description
        - key_specs: Extracted technical specifications
        - search_keywords: Keywords for intelligent competitor search
    """
    
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.1):
        """
        Initialize the enrichment agent.
        
        Args:
            model: OpenAI model to use (gpt-4o-mini for speed/cost)
            temperature: Low temperature for consistency (0.1)
        """
        self.llm = ChatOpenAI(model=model, temperature=temperature)
        logger.info(
            "CatalogEnrichmentAgent initialized",
            model=model,
            temperature=temperature
        )
    
    async def enrich_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a single product with normalized data.
        
        Args:
            product_data: Dict with fields:
                - title: Raw title from CSV (e.g., "ETB-1810 TRIPIE PARA BAFLE FUSSION")
                - brand: Brand name (WAHRGENOMEN, FUSSION, etc.)
                - category: Product category/line
                - ml_url: MercadoLibre URL (optional, for extracting current price info)
        
        Returns:
            Dict with enriched data:
                - normalized_title: Clean title
                - generic_description: Description for search
                - key_specs: List of technical specs
                - search_keywords: List of search terms
                - category_normalized: Standardized category
                - target_market: Intended use/market segment
        """
        logger.info(
            "Enriching product",
            title=product_data.get("title"),
            brand=product_data.get("brand")
        )
        
        # Build prompt for LLM
        prompt = self._build_enrichment_prompt(product_data)
        
        try:
            response = self.llm.invoke(prompt)
            
            # Capture token usage if available
            try:
                if hasattr(response, 'response_metadata') and 'token_usage' in response.response_metadata:
                    usage = response.response_metadata['token_usage']
                    tracker = get_tracker()
                    tracker.add_call(
                        model=settings.OPENAI_MODEL_MINI,
                        input_tokens=usage.get('prompt_tokens', 0),
                        output_tokens=usage.get('completion_tokens', 0)
                    )
                    logger.info(f"✅ Tokens captured: {usage.get('prompt_tokens', 0)} input, {usage.get('completion_tokens', 0)} output")
            except Exception as e:
                logger.debug(f"Could not capture token usage: {e}")
            
            enriched = self._parse_enrichment_response(response.content)
            
            logger.info(
                "Product enriched successfully",
                title=product_data.get("title"),
                normalized_title=enriched.get("normalized_title")
            )
            
            return enriched
        
        except Exception as e:
            logger.error(
                f"Error enriching product: {e}",
                title=product_data.get("title")
            )
            # Return fallback enrichment
            return self._fallback_enrichment(product_data)
    
    def _build_enrichment_prompt(self, product_data: Dict[str, Any]) -> List:
        """Build the prompt for LLM enrichment."""
        title = product_data.get("title", "")
        brand = product_data.get("brand", "")
        category = product_data.get("category", "")
        
        system_prompt = """Eres un experto en e-commerce y análisis de productos de audio profesional.

Tu tarea es ENRIQUECER datos de catálogo transformando títulos internos cripticos 
en descripciones claras y buscables.

IMPORTANTE:
- Los títulos tienen códigos internos (SKU, códigos modelo) que DEBEN removerse
- Debes extraer características técnicas reales del título
- Genera keywords que OTROS vendedores usarían para este producto
- La descripción debe ser genérica (sin marca específica)
- Categoriza el producto de forma estándar (audio, accesorios, etc.)

CATEGORÍAS ESTÁNDAR VÁLIDAS:
- Audio Profesional - Bocinas
- Audio Profesional - Drivers/Tweeters  
- Audio Profesional - Amplificadores
- Audio Profesional - Cables
- Audio Profesional - Accesorios
- Audio Profesional - Estructuras
- Audio Profesional - Interfaces
- Audio Profesional - Artículos Especiales

EJEMPLOS DE TRANSFORMACIÓN:
Input: "ETB-1810 TRIPIE PARA BAFLE FUSSION"
Output: {
  "normalized_title": "Trípie para bafle profesional altura ajustable",
  "generic_description": "Soporte portátil tipo trípode para bocinas y bafles de audio profesional con base estable y altura regulable entre 1.2m y 1.8m",
  "key_specs": ["tripode", "altura ajustable", "base metal reforzado", "capacidad 50kg", "profesional"],
  "search_keywords": ["tripie bafle", "pedestal bocina", "stand audio profesional", "soporte altavoz", "tripode para bocina"],
  "category_normalized": "Audio Profesional - Accesorios",
  "target_market": "Eventos, sonido profesional, instalaciones"
}

Input: "LA1501 BOCINA PROFESIONAL 15 BOBINA 3 LOUDER"  
Output: {
  "normalized_title": "Bocina profesional 15 pulgadas bobina doble",
  "generic_description": "Altavoz de 15 pulgadas para sistemas de audio profesional con bobina doble para mayor potencia y resistencia en aplicaciones de alta demanda",
  "key_specs": ["15 pulgadas", "bobina doble", "alta potencia", "profesional", "instalación fija"],
  "search_keywords": ["bocina 15 pulgadas", "altavoz profesional", "driver 15 pulgadas", "bocina doble bobina", "altavoz eventos"],
  "category_normalized": "Audio Profesional - Bocinas",
  "target_market": "Eventos, conciertos, instalaciones permanentes"
}
"""
        
        user_prompt = f"""Enriquece este producto de catálogo:

DATOS:
- Título (crudo): {title}
- Marca: {brand}
- Categoría línea: {category}

GENERA la información enriquecida en formato JSON válido."""
        
        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
    
    def _parse_enrichment_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response to extract enrichment data."""
        import json
        import re
        
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        
        # Try direct parse
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to find JSON object in text
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            raise ValueError(f"Could not parse JSON from: {content}")
    
    def _fallback_enrichment(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback enrichment using simple heuristics when LLM fails."""
        logger.warning(
            "Using fallback enrichment",
            title=product_data.get("title")
        )
        
        title = product_data.get("title", "")
        brand = product_data.get("brand", "")
        category = product_data.get("category", "")
        
        # Remove common SKU patterns and brand name
        normalized = re.sub(r"^[A-Z0-9]+-\d+-", "", title)  # Remove SKU prefix
        normalized = normalized.replace(brand, "").strip() if brand else normalized
        normalized = re.sub(r"\s{2,}", " ", normalized)  # Remove extra spaces
        
        # Extract key specs (words after numbers)
        key_specs = re.findall(r"(\d+\s*[A-Za-z]+|\d+[A-Z]{1,2}(?:\s|$))", title)
        
        return {
            "normalized_title": normalized or title,
            "generic_description": f"Producto de categoría {category}",
            "key_specs": key_specs or [category],
            "search_keywords": [
                category.lower(),
                normalized.lower()[:30]
            ] if normalized else [category.lower()],
            "category_normalized": category,
            "target_market": "General"
        }


async def enrich_catalog_batch(
    products: List[Dict[str, Any]],
    model: str = "gpt-4o-mini"
) -> List[Dict[str, Any]]:
    """
    Enrich multiple products efficiently.
    
    Args:
        products: List of product dicts with title, brand, category
        model: LLM model to use
    
    Returns:
        List of enriched product dicts
    """
    agent = CatalogEnrichmentAgent(model=model)
    enriched_products = []
    
    for i, product in enumerate(products):
        logger.info(f"Enriching product {i+1}/{len(products)}: {product.get('title')}")
        enriched = await agent.enrich_product(product)
        enriched_products.append({**product, **enriched})
    
    return enriched_products
