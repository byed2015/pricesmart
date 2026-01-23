"""
Product Matching Agent - LangGraph implementation.

This agent receives scraped products and determines which ones
are comparable/relevant for pricing analysis.

Responsibility: Filter and classify products, NOT scraping.
"""
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import numpy as np

from app.core.config import settings
from app.core.logging import get_logger
from app.core.monitoring import track_agent_execution
from app.core.token_costs import get_tracker

logger = get_logger(__name__)


class ProductClassification(BaseModel):
    """Classification of a single product."""
    item_id: str = Field(description="Product ID")
    title: str = Field(description="Product title")
    is_comparable: bool = Field(description="Whether product is comparable to target")
    is_accessory: bool = Field(description="Whether product is an accessory")
    is_bundle: bool = Field(description="Whether product is a bundle/kit")
    confidence: float = Field(description="Confidence score 0-1")
    reason: str = Field(description="Brief reason for classification")


class ProductMatchingState(TypedDict):
    """State for product matching agent."""
    target_product: str  # Original product description
    target_image_url: str = "" # Target product image for visual comparison
    raw_offers: List[Dict[str, Any]]  # From scraper
    reference_price: float = 0.0 # Target price for sanity check
    classified_offers: List[ProductClassification]
    comparable_offers: List[Dict[str, Any]]  # Filtered comparable products
    excluded_count: int
    errors: List[str]


class ProductMatchingAgent:
    """
    LangGraph agent for product matching and filtering.
    
    This agent uses LLM intelligence to determine which scraped
    products are truly comparable to the target product.
    
    Workflow:
    1. receive_offers: Initialize state with scraped offers
    2. classify_products: Use LLM to classify each product
    3. filter_comparable: Keep only comparable products
    """
    
    def __init__(self):
        import os
        # Dynamic API Key fetch (Crucial for Streamlit Local Mode where env is set late)
        self.api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL_MINI,
            temperature=0.1,  # Low temperature for consistent classification
            api_key=self.api_key
        )
        # Initialize Embeddings (text-embedding-3-small)
        # Wrap in try-except to avoid total crash if key is missing (will rely on regex/heuristic)
        try:
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=self.api_key
            )
            logger.info("ProductMatchingAgent initialized with Embeddings")
        except Exception as e:
            logger.warning(f"Failed to init Embeddings: {e}")
            self.embeddings = None

        self.graph = self._build_graph()
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow."""
        workflow = StateGraph(ProductMatchingState)
        
        # Add nodes
        workflow.add_node("receive_offers", self.receive_offers)
        workflow.add_node("classify_products", self.classify_products)
        workflow.add_node("validate_equivalence", self.validate_equivalence)
        workflow.add_node("filter_comparable", self.filter_comparable)
        
        # Define edges
        workflow.set_entry_point("receive_offers")
        workflow.add_edge("receive_offers", "classify_products")
        workflow.add_edge("classify_products", "validate_equivalence")
        workflow.add_edge("validate_equivalence", "filter_comparable")
        workflow.add_edge("filter_comparable", END)
        
        return workflow.compile()
    
    @track_agent_execution("product_matching_receive")
    async def receive_offers(self, state: ProductMatchingState) -> ProductMatchingState:
        """
        Receive and validate offers from scraper.
        """
        logger.info(
            "Receiving offers for matching",
            target_product=state["target_product"],
            raw_offers_count=len(state["raw_offers"])
        )
        
        # Initialize state
        state["classified_offers"] = []
        state["comparable_offers"] = []
        state["excluded_count"] = 0
        
        if not state["raw_offers"]:
            state["errors"].append("No offers received from scraper")
        
        return state
    
    def _extract_essential_keywords(self, text: str) -> List[str]:
        """Extract alphanumeric model numbers/codes (e.g. 'XM5', 'S23', 'A54', '500G', '14AWG')."""
        import re
        tokens = text.split()
        keywords = []
        for token in tokens:
             # Look for tokens with mixed alpha/numbers or ALL CAPS longer than 2 chars (likely models)
             # e.g. "XM5", "G502", "iPhone", "S23"
             clean = re.sub(r'[^a-zA-Z0-9]', '', token)
             if len(clean) < 2: continue
             
             # Exclude common spec units that look like models
             # e.g. 8ohm, 500w, 12v, 1kg, 2m, 3d, 4k (maybe 4k is ambiguous, but usually spec)
             if re.match(r'^\d+(?:ohm|w|v|kw|hp|kg|g|lb|oz|ml|l|m|cm|mm|in|ft|gb|tb|hz|khz|mah)$', clean.lower()):
                 continue
                 
             # Heuristics for "Model" keywords
             has_digit = any(c.isdigit() for c in clean)
             is_upper = clean.isupper()
             
             if has_digit or (is_upper and len(clean) >= 3):
                 keywords.append(clean.lower())
                 
        return keywords

    def _calculate_token_overlap(self, s1: str, s2: str) -> float:
        """Calculate Jaccard similarity of significant tokens."""
        def clean_tokens(text):
            # Simple tokenization: lowercase, alpha-numeric, >2 chars
            import re
            tokens = re.findall(r'\b[a-z0-9]{3,}\b', text.lower())
            # Stop words (simplified Spanish/English mix)
            stop_words = {'para', 'con', 'los', 'las', 'una', 'uno', 'del', 'por', 'que', 'for', 'with', 'the', 'and'}
            return set(t for t in tokens if t not in stop_words)
            
        set1 = clean_tokens(s1)
        set2 = clean_tokens(s2)
        
        if not set1 or not set2: return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0

    def _extract_specs(self, text: str) -> Dict[str, set]:
        """Extract explicit specifications like size, power, capacity, etc."""
        import re
        specs = {
            "size": set(),      # Inches, cm
            "power": set(),     # Watts
            "capacity": set(),  # Liters, ml
            "storage": set(),   # GB, TB
            "voltage": set(),   # V, Volts
            "weight": set(),    # kg, lb
            "impedance": set()  # Ohms
        }
        text = text.lower()
        
        # Regex Helpers
        def add_matches(category, pattern):
            matches = re.findall(pattern, text)
            for m in matches:
                # Store normalized value if possible, or raw
                specs[category].add(m)

        # 1. Size (Inches/Pulgadas) - e.g. 8", 15 in
        add_matches("size", r'\b(\d{1,2}(?:\.\d)?)\s?(?:"|in|pulg|pulgadas)\b')
        
        # 1.1 Implicit Audio Size (e.g. "Bocina 8", "Bafle 15")
        # Matches number strictly following typical audio nouns
        add_matches("size", r'\b(?:bocina|bafle|subwoofer|parlante|woofer|medio|driver)\s+(\d{1,2})\b')
        
        # 2. Power (Watts) - e.g. 500W, 1000 Watts
        add_matches("power", r'\b(\d{2,5})\s?(?:w|watts|watt)\b')
        
        # 3. Capacity (Liters) - e.g. 5L, 20 litros
        add_matches("capacity", r'\b(\d{1,3})\s?(?:l|lt|litros|liter)\b')
        
        # 4. Storage (GB/TB) - e.g. 256GB, 1TB
        add_matches("storage", r'\b(\d{1,4})\s?(?:gb|tb|gigas)\b')
        
        # 5. Voltage (Volts) - e.g. 12V, 110V
        add_matches("voltage", r'\b(\d{1,3})\s?(?:v|volts|volt)\b')
        
        # 6. Impedance (Ohms) - e.g. 4ohm, 8 ohms
        add_matches("impedance", r'\b(\d{1,2})\s?(?:ohm|ohms|Ω)\b')
        
        # 6. Impedance (Ohms) - e.g. 4ohm, 8 ohms
        add_matches("impedance", r'\b(\d{1,2})\s?(?:ohm|ohms|Ω)\b')
        
        return specs

    def _check_digit_consistency(self, target: str, offer: str) -> bool:
        """
        Heuristic: If target has standalone integer numbers (e.g. "8", "15", "100"),
        the offer MUST have at least ONE of them (standalone or embedded).
        This protects against "Bocina 8" matching "Bocina Búho" (no numbers).
        """
        # Find standalone digits in target
        target_digits = set(re.findall(r'\b\d+\b', target))
        
        # Determine "Significant" digits (avoid 1, 2 which might be packs?)
        # Actually, for sizes/models, numbers are usually key.
        # Let's verify: "Pack 2" vs "Pack 4" -> Mismatch is good.
        
        if not target_digits:
            return True
            
        # Find ALL digits in offer (even non-standalone, effectively)
        # We want to be lenient on the offer side: "8" in target matches "8ohm" or "8in" or "8" in offer.
        offer_digits_flat = re.findall(r'\d+', offer)
        offer_digits = set(offer_digits_flat)
        
        # Check intersection
        common = target_digits.intersection(offer_digits)
        
        # If intersection is empty, it's a suspicious match
        if not common:
            return False
            
        return True

    async def _classify_single_product(
        self, 
        target: str, 
        offer: Dict[str, Any], 
        reference_price: float = 0.0,
        target_image_url: str = ""
    ) -> ProductClassification:
        """Classify a single product using LLM (text + vision if available)."""
        try:
            image_url = offer.get("image_url")
            title = offer.get("title", "")
            price = offer.get("price", 0)
            
            # --- SPEC CONFLICT CHECK (GENERALIZED) ---
            # If target specifies a value for a unit (e.g. "500W"), and offer specifies a DIFFERENT value (e.g. "100W"), REJECT.
            target_specs = self._extract_specs(target)
            offer_specs = self._extract_specs(title)
            
            for category, t_values in target_specs.items():
                if not t_values: continue # Target doesn't care about this spec
                
                o_values = offer_specs[category]
                if not o_values: continue # Offer doesn't specify (might be implicit, give benefit of doubt)
                
                # If both specify values for this category, check intersection
                overlap = t_values.intersection(o_values)
                if not overlap:
                    # CONFLICT! Target={500}, Offer={100}
                    return ProductClassification(
                        item_id=offer.get('item_id', ''),
                        title=title,
                        is_comparable=False,
                        is_accessory=False,
                        is_bundle=False,
                        confidence=0.99,
                        reason=f"Spec Mismatch ({category}): Target {t_values} vs Offer {o_values}"
                    )

            # Soft checks are informational only; no hard rejects here.

            # --- BUNDLE KEYWORD CHECK ---
            # If target is NOT a bundle, but offer says "Kit", "Pack", "Lote", reject it.
            # Heuristic: Target title key bundle words
            bundle_keywords = ["kit", "pack", "lote", "set", "juego", "par", "duo"]
            target_lower = target.lower()
            title_lower = title.lower()
            
            target_is_bundle = any(bk in target_lower for bk in bundle_keywords)
            offer_is_bundle = any(bk in title_lower for bk in bundle_keywords)
            
            if not target_is_bundle and offer_is_bundle:
                # Be careful: "Par" is common; only block strict bundle markers.
                strict_bundles = ["kit", "lote", "pack", "juego"]
                if any(sb in title_lower for sb in strict_bundles):
                    return ProductClassification(
                        item_id=offer.get('item_id', ''),
                        title=title,
                        is_comparable=False,
                        is_accessory=False,
                        is_bundle=True,
                        confidence=0.90,
                        reason="Bundle Mismatch: Offer is a Kit/Pack but target is not."
                    )

            # Construct the prompt - PARANOID MODE
            messages = [
                {
                    "role": "system",
                    "content": """You are a STRICT product matching auditor with VISUAL INSPECTION capabilities.
Your job is to REJECT any product that is not the EXACT core product requested.

Rules:
1. VISUAL MISMATCH (CRITICAL):
   - Compare the TARGET IMAGE (if provided) with the OFFER IMAGE.
   - If Target is a raw driver (bocina suelta) and Offer is a boxed speaker (bocina bluetooth), REJECT.
   - If Target is black and Offer is pink/fuchsia, REJECT.
   - If Form Factors differ (Circular vs Square, Big Magnet vs Toy), REJECT.

2. REJECT Accessories: "Case", "Funda", "Strap", "Cable", "Charger", "Box", "Skin".
3. REJECT Spare Parts: "Replacement", "Pieza", "Repuesto", "Pantalla", "Display".
4. REJECT Different Models: If target is "XM5", REJECT "XM4". If target is "Pro", REJECT "Non-Pro". Check model numbers carefully.
5. REJECT Clones/Fakes: "Tipo", "Clon", "Generico", "OEM" (unless target is too).
6. REJECT Damaged/Parts: "Para reparar", "Detalles", "No prende", "Refacciones".

Classification:
- comparable: ONLY if it is the main product itself AND visually similar.
- accessory: Cases, parts, boxes.
- bundle: Main product + extras.
- not_comparable: Everything else (wrong visual, wrong model).

Output JSON: { "classification": "comparable"|"accessory"|"bundle"|"not_comparable", "confidence": float, "reason": "short explanation citing visual or text reasoning" }"""
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"TARGET: {target} (Ref Price: ${reference_price})\n\nOFFER: {title} (${price})"}
                    ]
                }
            ]
            
            # Add image if valid
            # Add Target Image if available (first)
            if target_image_url and target_image_url.startswith("http"):
                messages[1]["content"].insert(0, {
                    "type": "text",
                    "text": "TARGET IMAGE (Reference):"
                })
                messages[1]["content"].insert(1, {
                    "type": "image_url",
                    "image_url": {"url": target_image_url}
                })

            # Add Offer Image if available
            if image_url and image_url.startswith("http"):
                messages[1]["content"].append({
                    "type": "text",
                    "text": "OFFER IMAGE (Candidate):"
                })
                messages[1]["content"].append({
                    "type": "image_url",
                    "image_url": {"url": image_url}
                })
                
            # Invoke LLM
            response = await self.llm.ainvoke(messages)
            
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
            
            # Parse response (Naive JSON parsing for now, purely text based)
            # In a real scenario, use structured output or PydanticOutputParser
            content = response.content.lower().strip()
            # Clean md blocks
            content = content.replace("```json", "").replace("```", "")
            
            import json
            try:
                data = json.loads(content)
                cat = data.get("classification", "not_comparable")
                conf = data.get("confidence", 0.5)
                reason = data.get("reason", "LLM decision")
            except:
                 # Fallback parser
                 if "comparable" in content: cat = "comparable"
                 elif "accessory" in content: cat = "accessory"
                 elif "bundle" in content: cat = "bundle"
                 else: cat = "not_comparable"
                 conf = 0.6
                 reason = "Regex fallback"

            is_comparable = (cat == "comparable")
            is_accessory = (cat == "accessory")
            is_bundle = (cat == "bundle")
            
            return ProductClassification(
                item_id=offer.get('item_id', ''),
                title=title,
                is_comparable=is_comparable,
                is_accessory=is_accessory,
                is_bundle=is_bundle,
                confidence=conf,
                reason=reason
            )
            
        except Exception as e:
            # Fallback heuristic
            return self._heuristic_fallback(target, offer)

    def _heuristic_fallback(self, target: str, offer: Dict[str, Any]) -> ProductClassification:
        title_lower = offer.get("title", "").lower()
        
        # Check for accessories
        is_accessory = any(word in title_lower for word in [
            'funda', 'case', 'cable', 'cargador', 'protector',
            'mica', 'glass', 'adaptador', 'base', 'soporte', 'estuche'
        ])
        
        # Check for bundles
        is_bundle = any(word in title_lower for word in [
            'paquete', 'combo', 'kit', ' + ', 'incluye'
        ])
        
        is_comparable = not (is_accessory or is_bundle)
        
        return ProductClassification(
            item_id=offer.get('item_id', ''),
            title=offer.get("title", ""),
            is_comparable=is_comparable,
            is_accessory=is_accessory,
            is_bundle=is_bundle,
            confidence=0.5,
            reason="Heuristic Fallback"
        )

    @track_agent_execution("product_matching_classify")
    async def classify_products(self, state: ProductMatchingState) -> ProductMatchingState:
        """
        Classify products concurrently using Vision if available.
        """
        logger.info("Starting product classification (Vision Enabled)")
        
        target = state["target_product"]
        target_image_url = state.get("target_image_url", "")
        offers = state["raw_offers"]
        ref_price = state.get("reference_price", 0.0)
        
        # Normalize offers to dicts if they are objects
        normalized_offers = []
        for o in offers:
            if hasattr(o, "to_dict"):
                normalized_offers.append(o.to_dict())
            elif isinstance(o, dict):
                normalized_offers.append(o)
            else:
                 logger.warning(f"Skipping invalid offer format: {type(o)}")

        # Concurrency limit
        # Concurrency limit
        import asyncio
        semaphore = asyncio.Semaphore(5) # Process 5 at a time
        
        # --- EMBEDDING PRE-CALCULATION ---
        # 1. Embed Target Product ONCE
        target_embedding = []
        try:
            target_str = f"{target}"
            target_embedding = await self.embeddings.aembed_query(target_str)
            logger.info("Computed embedding for target product")
        except Exception as e:
            logger.error(f"Failed to embed target: {e}")

        async def sem_task(offer):
             async with semaphore:
                 # --- EMBEDDING CHECK (Universal semantic filter) ---
                 if target_embedding:
                     try:
                         offer_text = f"{offer.get('title', '')}"
                         offer_vec = await self.embeddings.aembed_query(offer_text)
                         similarity = self._calculate_cosine_similarity(target_embedding, offer_vec)
                         
                         # Threshold Tuning:
                         # 0.25 allows generic matches (e.g. "Speaker" vs "Bocina") 
                         # but blocks semantic opposites (e.g. "Cable" vs "Speaker").
                         # This works for ANY product category.
                         if similarity < 0.25:
                             return ProductClassification(
                                item_id=offer.get('item_id', ''),
                                title=offer.get('title', ''),
                                is_comparable=False,
                                is_accessory=False,
                                is_bundle=False,
                                confidence=0.85,
                                reason=f"Semantic Mismatch (AI): Similarity {similarity:.2f} < 0.25"
                            )
                     except Exception as e:
                         # Log invalid vector ops but continue
                         pass

                         pass

                 return await self._classify_single_product(target, offer, ref_price, target_image_url)
        
        tasks = [sem_task(o) for o in normalized_offers]
        all_classifications = await asyncio.gather(*tasks)
        
        state["classified_offers"] = all_classifications
        
        logger.info(
            "Classification completed",
            total=len(all_classifications),
            comparable=sum(1 for c in all_classifications if c.is_comparable)
        )
        
        return state
    
    @track_agent_execution("product_matching_validate_equivalence")
    async def validate_equivalence(self, state: ProductMatchingState) -> ProductMatchingState:
        """
        Validate functional equivalence of comparable products.
        
        This node adds a second level of filtering to ensure that products
        classified as comparable are TRULY functionally equivalent.
        
        Uses LLM to check:
        - Same product category/function
        - Specifications are compatible (±20% tolerance on key specs)
        - Not artificially similar (e.g., "Soporte de pared" vs "Tripie portátil")
        """
        target_product = state["target_product"]
        classified = state["classified_offers"]
        
        if not classified:
            logger.info("No classified offers to validate")
            return state
        
        # Filter to only classified comparable products
        comparable_only = [c for c in classified if c.is_comparable]
        
        if not comparable_only:
            logger.info("No comparable products to validate")
            return state
        
        logger.info(
            "Starting functional equivalence validation",
            target=target_product,
            candidates=len(comparable_only)
        )
        
        # Build validation prompt
        validation_prompt = f"""Eres un experto en validación de equivalencia funcional de productos.

PRODUCTO REFERENCIA:
{target_product}

Tu tarea: Validar que cada producto candidato sea VERDADERAMENTE EQUIVALENTE funcionalmente.

CRITERIOS DE EQUIVALENCIA:
1. ¿Misma categoría de uso? (ej: ambos son trípies para bafle)
2. ¿Especificaciones técnicas comparables? (±20% en dimensiones/capacidad)
3. ¿Mismo segmento de mercado? (económico, medio, premium)
4. ¿NO son variantes que cambien la función? (ej: instalación fija vs portátil)

PRODUCTOS A VALIDAR:
"""
        
        for i, candidate in enumerate(comparable_only, 1):
            validation_prompt += f"\n{i}. {candidate.title} - Razón inicial: {candidate.reason}"
        
        try:
            response = self.llm.invoke(validation_prompt + "\n\nDevuelve solo JSON con array de booleans indicando validez de cada producto.")
            
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
            
            # Parse response - expect array of booleans or confidence scores
            import json
            import re
            
            json_match = re.search(r'\[.*?\]', response.content, re.DOTALL)
            if json_match:
                validities = json.loads(json_match.group(0))
                
                # Update classified offers with equivalence validation
                for candidate, is_valid in zip(comparable_only, validities):
                    if isinstance(is_valid, bool):
                        if not is_valid:
                            candidate.is_comparable = False
                            candidate.reason += " (Falló validación de equivalencia)"
                    elif isinstance(is_valid, (int, float)):
                        # If score < 0.7, mark as not comparable
                        if is_valid < 0.7:
                            candidate.is_comparable = False
                            candidate.reason += f" (Equivalencia: {int(is_valid*100)}%)"
                
                logger.info(
                    "Equivalence validation completed",
                    validated=sum(1 for c in comparable_only if c.is_comparable)
                )
        
        except Exception as e:
            logger.warning(f"Equivalence validation failed: {e}. Keeping original classifications.")
        
        return state
    
    @track_agent_execution("product_matching_filter")
    async def filter_comparable(self, state: ProductMatchingState) -> ProductMatchingState:
        """
        Filter to keep only comparable products.
        Falls back to including best-price products if filtering is too aggressive.
        """
        classified = state["classified_offers"]
        raw_offers = state["raw_offers"]
        
        # Create lookup by title (since we don't have IDs in all cases)
        comparable_titles = {
            c.title for c in classified if c.is_comparable
        }
        
        comparable_offers = [
            o for o in raw_offers
            if o['title'] in comparable_titles
        ]
        
        # FALLBACK: If too many products are filtered out, include top N by price proximity
        if not comparable_offers and raw_offers:
            logger.warning(
                "⚠️ No comparable offers after filtering. Applying fallback strategy.",
                total_offers=len(raw_offers),
                comparable=0
            )
            
            reference_price = state.get("reference_price", 0.0)
            
            # Sort by price proximity to reference
            if reference_price > 0:
                offers_with_distance = []
                for o in raw_offers:
                    try:
                        price = float(o.get("price", 0))
                        distance = abs(price - reference_price) / reference_price if reference_price else float('inf')
                        offers_with_distance.append((o, distance))
                    except:
                        offers_with_distance.append((o, float('inf')))
                
                # Sort by distance and take top 10
                offers_with_distance.sort(key=lambda x: x[1])
                comparable_offers = [o[0] for o in offers_with_distance[:10]]
                
                logger.info(
                    "✅ Fallback applied: Selected top 10 by price proximity",
                    reference_price=reference_price,
                    selected=len(comparable_offers),
                    avg_distance_percent=round(
                        sum(d for _, d in offers_with_distance[:10]) / 10 * 100, 2
                    )
                )
            else:
                # If no reference price, just take first 10
                comparable_offers = raw_offers[:10]
                logger.info(
                    "✅ Fallback applied: Selected first 10 offers (no price reference)",
                    selected=len(comparable_offers)
                )
        
        state["comparable_offers"] = comparable_offers
        state["excluded_count"] = len(raw_offers) - len(comparable_offers)
        
        logger.info(
            "Filtering completed",
            total_offers=len(raw_offers),
            comparable=len(comparable_offers),
            excluded=state["excluded_count"]
        )
        
        return state
    
    async def execute(
        self,
        target_product: str,
        raw_offers: List[Dict[str, Any]],
        reference_price: float = 0.0,
        target_image_url: str = ""
    ) -> Dict[str, Any]:
        """
        Execute the product matching workflow.
        
        Args:
            target_product: Description of target product
            raw_offers: List of offers from scraper
            reference_price: Target price for sanity check
            target_image_url: Optional image of target product for visual AI
            
        Returns:
            Dict with comparable offers and metadata
        """
        logger.info(
            "Executing ProductMatchingAgent",
            target=target_product,
            image=bool(target_image_url),
            offers=len(raw_offers)
        )
        
        initial_state: ProductMatchingState = {
            "target_product": target_product,
            "target_image_url": target_image_url,
            "raw_offers": raw_offers,
            "reference_price": reference_price,
            "classified_offers": [],
            "comparable_offers": [],
            "excluded_count": 0,
            "errors": []
        }
        
        final_state = await self.graph.ainvoke(initial_state)
        
        # Build excluded offers list with reasons
        excluded_offers = []
        comparable_titles = {o['title'] for o in final_state["comparable_offers"]}
        
        for classification in final_state["classified_offers"]:
            if not classification.is_comparable:
                # Find the raw offer data
                matching_offer = next((o for o in final_state["raw_offers"] if o.get('title') == classification.title), None)
                if matching_offer:
                    excluded_offers.append({
                        **matching_offer,  # Include all original fields
                        "exclusion_reason": classification.reason
                    })
        
        return {
            "target_product": final_state["target_product"],
            "total_offers": len(final_state["raw_offers"]),
            "comparable_offers": final_state["comparable_offers"],
            "comparable_count": len(final_state["comparable_offers"]),
            "excluded_count": final_state["excluded_count"],
            "excluded_offers": excluded_offers,
            "classifications": [c.dict() for c in final_state["classified_offers"]],
            "errors": final_state["errors"]
        }
