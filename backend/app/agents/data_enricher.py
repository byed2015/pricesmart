"""
Data Enricher Agent - Analyzes product information to extract detailed specifications.

This agent takes a product and enriches its data by:
1. Analyzing the title and description with LLM
2. Extracting detailed technical specifications
3. Identifying key search characteristics
4. Categorizing the product type

This enriched data is then used by SearchStrategyAgent to generate better search terms.
"""
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import json
import re
import os

from app.core.config import settings
from app.core.logging import get_logger
from app.core.monitoring import track_agent_execution
from app.core.token_costs import get_tracker
from app.mcp_servers.mercadolibre.scraper import ProductDetails

logger = get_logger(__name__)


class EnrichedSpecification(BaseModel):
    """Enriched product specification with multiple detail levels."""
    category: str = Field(description="Product category (e.g., bocina, cable, tripie)")
    subcategory: str = Field(description="Product subcategory")
    key_specs: Dict[str, Any] = Field(description="Key technical specifications")
    functional_descriptors: List[str] = Field(description="How the product functions/is used")
    synonyms: List[str] = Field(description="Alternative names for this product")
    material_features: List[str] = Field(description="Material and construction features")
    connectivity: List[str] = Field(description="Connection types (e.g., USB, Bluetooth, XLR)")
    power_profile: Optional[Dict[str, str]] = Field(description="Power specifications")
    dimensions_weight: Optional[Dict[str, str]] = Field(description="Physical dimensions and weight")
    performance_metrics: Dict[str, str] = Field(description="Performance specs (watts, impedance, etc)")
    compatibility_notes: List[str] = Field(description="What this works with")
    market_segment: str = Field(description="Market segment (económico, medio, premium)")
    similar_product_patterns: List[str] = Field(description="Patterns to find similar products")


class DataEnricherAgent:
    """
    Enriches product data by analyzing descriptions and extracting detailed information.
    """
    
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.1):
        """Initialize the data enricher agent."""
        # Dynamic API Key fetch (Crucial for Streamlit Local Mode where env is set late)
        api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=api_key
        )
        logger.info(
            "DataEnricherAgent initialized",
            model=model,
            temperature=temperature,
            has_api_key=bool(api_key)
        )
    
    @track_agent_execution("data_enricher_analyze_product")
    async def analyze_product(self, product: ProductDetails) -> Dict[str, Any]:
        """
        Analyze a product and extract detailed enriched information.
        
        Args:
            product: ProductDetails object with title, description, attributes
            
        Returns:
            Dict with enriched specifications and analysis
        """
        logger.info(
            "Analyzing product for enrichment",
            product_id=product.product_id,
            title=product.title[:50]
        )
        
        try:
            # Build comprehensive product context
            product_context = self._build_product_context(product)
            
            # Use LLM to analyze and extract detailed specs
            enriched = await self._extract_enriched_specs(product_context)
            
            # Additional pattern extraction
            patterns = self._extract_search_patterns(product, enriched)
            
            result = {
                "status": "success",
                "enriched_specs": enriched,
                "search_patterns": patterns,
                "analysis_confidence": 0.9
            }
            
            logger.info(
                "Product enrichment completed",
                category=enriched.category,
                specs_count=len(enriched.key_specs),
                patterns_count=len(patterns)
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error enriching product: {e}")
            return {
                "status": "error",
                "error": str(e),
                "enriched_specs": None,
                "search_patterns": []
            }
    
    def _build_product_context(self, product: ProductDetails) -> str:
        """Build comprehensive product context for LLM analysis."""
        lines = [
            "=== PRODUCT ANALYSIS CONTEXT ===\n",
            f"TÍTULO: {product.title}",
            f"ID: {product.product_id}",
            f"PRECIO: ${product.price:,.2f} {product.currency}",
            f"CONDICIÓN: {product.condition}",
        ]
        
        if product.brand:
            lines.append(f"MARCA: {product.brand}")
        if product.model:
            lines.append(f"MODELO: {product.model}")
        if product.category:
            lines.append(f"CATEGORÍA: {product.category}")
        
        # Add all attributes as key-value pairs
        if product.attributes:
            lines.append("\nATRIBUTOS EXTRAÍDOS:")
            for key, value in product.attributes.items():
                lines.append(f"  • {key}: {value}")
        
        # Add description
        if product.description:
            desc_preview = product.description[:1000] if len(product.description) > 1000 else product.description
            lines.append(f"\nDESCRIPCIÓN (preview):\n{desc_preview}")
        
        return "\n".join(lines)
    
    @track_agent_execution("data_enricher_extract_specs")
    async def _extract_enriched_specs(self, product_context: str) -> EnrichedSpecification:
        """Use LLM to extract detailed enriched specifications."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un experto en análisis de productos electrónicos y audio profesional.
            
Tu tarea es analizar la información del producto y extraer especificaciones detalladas y enriquecidas.

IMPORTANTE - Debes ser EXHAUSTIVO:
1. Analiza TODOS los atributos y descripción
2. Extrae especificaciones técnicas explícitas
3. Infiere especificaciones técnicas implícitas del título/descripción
4. Identifica para qué sirve exactamente el producto
5. Encuentra sinónimos y nombres alternativos
6. Categoriza el segmento de mercado

SALIDA: Devuelve JSON VÁLIDO con estos campos exactos (todos requeridos):
{
  "category": "nombre de categoría",
  "subcategory": "subcategoría",
  "key_specs": {"spec_name": "value"},
  "functional_descriptors": ["descriptor1", "descriptor2"],
  "synonyms": ["sinónimo1"],
  "material_features": ["material1"],
  "connectivity": ["conexión1"],
  "power_profile": {"watts": "500", "voltage": "120V"},
  "dimensions_weight": {"ancho": "valor"},
  "performance_metrics": {"métrica": "valor"},
  "compatibility_notes": ["nota1"],
  "market_segment": "medio",
  "similar_product_patterns": ["patrón1"]
}"""),
            ("human", """{product_context}

Analiza exhaustivamente y extrae todas las especificaciones en formato JSON válido.
Responde SOLO con JSON válido, sin explicaciones adicionales.""")
        ])
        
        try:
            response = self.llm.invoke(prompt.format_prompt(product_context=product_context))
            
            # Capture token usage if available
            try:
                if hasattr(response, 'response_metadata') and 'usage' in response.response_metadata:
                    usage = response.response_metadata['usage']
                    tracker = get_tracker()
                    tracker.add_call(
                        model=settings.OPENAI_MODEL_MINI,
                        input_tokens=usage.get('prompt_tokens', 0),
                        output_tokens=usage.get('completion_tokens', 0)
                    )
            except Exception as e:
                logger.debug(f"Could not capture token usage: {e}")
            
            # Try to parse as JSON first
            json_str = response.content.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:-3]  # Remove markdown code blocks
            elif json_str.startswith("```"):
                json_str = json_str[3:-3]
            
            data = json.loads(json_str)
            
            # If wrapped in EnrichedSpecification key, unwrap it
            if "EnrichedSpecification" in data:
                data = data["EnrichedSpecification"]
            
            # Ensure all required fields have values
            data.setdefault("category", "general")
            data.setdefault("subcategory", "general")
            data.setdefault("key_specs", {"info": "N/A"})
            data.setdefault("functional_descriptors", ["producto"])
            data.setdefault("synonyms", [])
            data.setdefault("material_features", [])
            data.setdefault("connectivity", [])
            data.setdefault("power_profile", {})
            data.setdefault("dimensions_weight", {})
            data.setdefault("performance_metrics", {})
            data.setdefault("compatibility_notes", [])
            data.setdefault("market_segment", "general")
            data.setdefault("similar_product_patterns", [])
            
            enriched = EnrichedSpecification(**data)
            return enriched
            
        except Exception as e:
            logger.warning(f"Error parsing LLM response: {e}, using fallback")
            return self._fallback_enriched_specs(product_context)
    
    def _extract_search_patterns(self, product: ProductDetails, enriched: EnrichedSpecification) -> List[str]:
        """Extract patterns that will help find similar products."""
        patterns = []
        
        # Pattern 1: Category + key spec
        if enriched.category and enriched.key_specs:
            # Get first 2-3 key specs
            specs_list = list(enriched.key_specs.items())[:3]
            spec_str = " ".join([f"{k}={v}" for k, v in specs_list])
            patterns.append(f"{enriched.category} {spec_str}")
        
        # Pattern 2: Functional descriptors
        for desc in enriched.functional_descriptors[:2]:
            patterns.append(f"{enriched.category} {desc}")
        
        # Pattern 3: Connectivity + purpose
        if enriched.connectivity and enriched.functional_descriptors:
            conn_str = "+".join(enriched.connectivity[:2])
            patterns.append(f"{enriched.category} {conn_str} {enriched.functional_descriptors[0]}")
        
        # Pattern 4: Market segment + category
        patterns.append(f"{enriched.category} {enriched.market_segment}")
        
        # Pattern 5: Performance metrics
        if enriched.performance_metrics:
            perf_str = " ".join([f"{k}={v}" for k, v in list(enriched.performance_metrics.items())[:2]])
            patterns.append(f"{perf_str}")
        
        return list(set(patterns))  # Remove duplicates
    
    def _fallback_enriched_specs(self, product_context: str) -> EnrichedSpecification:
        """Fallback enriched specs when LLM parsing fails."""
        # Simple regex-based extraction
        logger.warning("Using fallback enriched specs extraction")
        
        # Extract basic info from product context
        lines = product_context.split("\n")
        title = next((l.split(": ", 1)[1] for l in lines if l.startswith("TÍTULO:")), "")
        
        # Determine basic category
        category = self._infer_category(title)
        
        return EnrichedSpecification(
            category=category,
            subcategory="general",
            key_specs={"name": title},
            functional_descriptors=[f"Audio {category}"],
            synonyms=[],
            material_features=[],
            connectivity=[],
            power_profile=None,
            dimensions_weight=None,
            performance_metrics={},
            compatibility_notes=[],
            market_segment="medio",
            similar_product_patterns=[category, title]
        )
    
    def _infer_category(self, text: str) -> str:
        """Infer product category from text."""
        text_lower = text.lower()
        
        # Audio categories
        if any(w in text_lower for w in ["bocina", "altavoz", "parlante", "speaker"]):
            return "bocina"
        elif any(w in text_lower for w in ["cable", "xlr", "rca", "usb"]):
            return "cable"
        elif any(w in text_lower for w in ["tripie", "pedestal", "soporte", "stand"]):
            return "tripie"
        elif any(w in text_lower for w in ["driver", "tweeter", "woofer"]):
            return "driver"
        elif any(w in text_lower for w in ["bafle", "caja", "cabinet"]):
            return "bafle"
        elif any(w in text_lower for w in ["amplificador", "amp", "potencia"]):
            return "amplificador"
        elif any(w in text_lower for w in ["interfaz", "interface", "tarjeta audio"]):
            return "interfaz"
        else:
            return "audio_equipment"


# Export for use in pricing_pipeline
__all__ = ["DataEnricherAgent", "EnrichedSpecification"]
