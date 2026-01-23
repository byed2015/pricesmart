"""
Search Strategy Agent - Determines optimal search terms for similar products.

This agent analyzes the characteristics of a pivot product (e.g., your Louder branded item)
and generates search terms to find similar products in the market, regardless of brand.

Enhanced with DataEnricherAgent for detailed specification extraction and analysis.

Use case: You import and rebrand products, so you need to find competitors with similar
specifications, not the same brand.
"""
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json
import asyncio
import os

from app.core.config import settings
from app.core.logging import get_logger
from app.core.monitoring import track_agent_execution
from app.core.token_costs import get_tracker
from app.mcp_servers.mercadolibre.scraper import ProductDetails

logger = get_logger(__name__)


class SearchStrategyAgent:
    """
    Agent that determines optimal search strategy for finding similar products.
    
    Input: Complete product details (specifications, attributes)
    Output: Optimized search terms that focus on product category and key specifications
    """
    
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.2):
        """
        Initialize the search strategy agent.
        
        Args:
            model: OpenAI model to use
            temperature: Temperature for generation (0.2 = more focused)
        """
        # Dynamic API Key fetch (Crucial for Streamlit Local Mode where env is set late)
        api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=api_key
        )
        logger.info(
            "SearchStrategyAgent initialized",
            model=model,
            temperature=temperature,
            has_api_key=bool(api_key)
        )
    
    def generate_search_terms(self, product: ProductDetails) -> Dict[str, Any]:
        """
        Generate optimal search terms based on product characteristics.
        
        Args:
            product: Complete product details
            
        Returns:
            Dict with:
                - primary_search: Main search term (most likely to find similar products)
                - alternative_searches: List of alternative search terms
                - key_specs: Key specifications to focus on
                - reasoning: Why these terms were chosen
        """
        logger.info(
            "Generating search strategy",
            product_id=product.product_id,
            title=product.title
        )
        
        # Build product description for LLM
        product_info = self._build_product_description(product)
        
        # Create prompt
        prompt = f"""Eres un experto en análisis de productos electrónicos y estrategias de búsqueda para e-commerce.

Tu tarea es analizar un producto que el usuario importa y rebrandea, y generar los MEJORES términos de búsqueda para encontrar productos FUNCIONALMENTE EQUIVALENTES de OTRAS marcas/proveedores en Mercado Libre.

OBJETIVO: Búsqueda inteligente cross-marca que encuentre competidores directos.

ESTRATEGIAS REQUERIDAS:
1. **Búsqueda genérica por categoría + specs técnicas**
   - SIN marca, enfoque en especificaciones
   - Ejemplo: "cable micrófono XLR 6 metros" (no "cable Louder XLR")
   - Ejemplo: "tripie bafle altura ajustable" (no "tripie Fussion")

2. **Búsqueda por función/uso real**
   - Cómo lo usaría un cliente
   - Ejemplo: "pedestal para bocina profesional"
   - Ejemplo: "soporte audio eventos"

3. **Búsqueda por especificaciones técnicas exactas**
   - Números, dimensiones, potencia, impedancia
   - Ejemplo: "driver 44mm 1000w titanio"
   - Ejemplo: "bocina 15 pulgadas 4 ohms"

4. **Sinónimos y términos alternativos**
   - Diferentes palabras para el mismo concepto
   - Ejemplo: "bafle" → ["bocina", "altavoz", "parlante"]
   - Ejemplo: "tripie" → ["pedestal", "stand", "soporte"]

PRODUCTO A ANALIZAR:
{product_info}

IMPORTANTE - FILTRADO INTELIGENTE:
- EXCLUIR la marca propia del usuario (si aparece en el título)
- EXCLUIR marcas premium que no compiten en mismo segmento de precio
- EXCLUIR accesorios, bundles, refacciones, productos usados
- INCLUIR variantes genéricas y marcas de precio similar

Por favor, genera:
1. **primary_search**: Término de búsqueda PRINCIPAL genérico (SIN marca)
   - Tipo de producto + especificación clave más distintiva
   - Ejemplo: "bocina techo 5 pulgadas" o "cable audio xlr 6m"
   
2. **alternative_searches**: 3-5 búsquedas alternativas inteligentes
   - Sinónimos y formas alternativas de describir el producto
   - Combinaciones de specs diferentes
   - Términos de uso/aplicación
   
3. **key_specs**: Especificaciones técnicas CLAVE para validar equivalencia
   - Dimensiones, potencia, impedancia, voltaje, conectores
   - Ejemplo: ["5 pulgadas", "10W", "8 ohms", "empotrable"]
   
4. **exclude_terms**: Términos a EXCLUIR en resultados
   - Marca propia del usuario
   - Accesorios no equivalentes (funda, cable, adaptador, refacción)
   - Bundles/paquetes que no sean solo el producto
   - Productos usados o reacondicionados (si aplica)
   
5. **exclude_premium_brands**: Lista de marcas premium a excluir (opcional)
   - Solo si el producto es económico/medio y no compite con premium
   - Ejemplo: ["JBL", "Bose", "Sony"] para productos económicos
   
6. **reasoning**: Explicación de la estrategia de búsqueda
   - Por qué estos términos encontrarán equivalentes funcionales
   - Qué hace comparable a otro producto

Responde SOLO en formato JSON válido:
{{
  "primary_search": "término principal genérico",
  "alternative_searches": ["búsqueda 1", "búsqueda 2", "búsqueda 3", "búsqueda 4"],
  "key_specs": ["spec técnica 1", "spec técnica 2", ...],
  "exclude_terms": ["marca propia", "accesorio 1", "bundle", "usado"],
  "exclude_premium_brands": ["Marca Premium 1", "Marca Premium 2"],
  "reasoning": "explicación de estrategia"
}}"""
        
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
            
            result = self._parse_llm_response(response.content)
            
            logger.info(
                "Search strategy generated",
                primary_search=result.get("primary_search"),
                alternatives_count=len(result.get("alternative_searches", []))
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Error generating search strategy: {e}")
            # Fallback to basic strategy
            return self._fallback_strategy(product)
    
    def _build_product_description(self, product: ProductDetails) -> str:
        """Build a comprehensive product description for the LLM."""
        lines = [
            f"Título: {product.title}",
            f"Precio: ${product.price:,.2f} {product.currency}",
            f"Condición: {product.condition}",
        ]
        
        if product.brand:
            lines.append(f"Marca: {product.brand}")
        
        if product.category:
            lines.append(f"Categoría: {product.category}")
        
        if product.attributes:
            lines.append("\nEspecificaciones técnicas:")
            for key, value in product.attributes.items():
                lines.append(f"  - {key}: {value}")
        
        if product.description:
            desc_short = product.description[:500] if len(product.description) > 500 else product.description
            lines.append(f"\nDescripción: {desc_short}")
        
        return "\n".join(lines)
    
    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM JSON response."""
        import json
        import re
        
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, re.DOTALL)
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
            raise
    
    def _fallback_strategy(self, product: ProductDetails) -> Dict[str, Any]:
        """Fallback strategy when LLM fails."""
        logger.warning("Using fallback search strategy")
        
        # Extract key terms from title (remove brand)
        title_clean = product.title.lower()
        if product.brand:
            title_clean = title_clean.replace(product.brand.lower(), "").strip()
        
        # Simple word extraction
        words = [w for w in title_clean.split() if len(w) > 3][:5]
        primary = " ".join(words)
        
        return {
            "primary_search": primary,
            "alternative_searches": [product.title],
            "key_specs": list(product.attributes.keys())[:5] if product.attributes else [],
            "exclude_terms": [],
            "reasoning": "Fallback strategy - usando términos básicos del título"
        }
