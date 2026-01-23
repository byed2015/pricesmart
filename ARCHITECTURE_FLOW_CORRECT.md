# Flujo Completo de Arquitectura - Louder Price Intelligence

## Resumen Ejecutivo

El pipeline completo tiene **8 STEPS** (no 6):

1. **STEP 0**: Product Extractor - Extrae datos de tu producto (sin LLM)
2. **STEP 1**: Data Enricher (LLM) - Enriquece especificaciones
3. **STEP 2**: Search Strategy (LLM) - Determina búsquedas óptimas
4. **STEP 3**: Market Research - Scraping + Price Filter (sin LLM)
5. **STEP 3b**: Price Validation - Valida tolerance range (sin LLM)
6. **STEP 4**: Product Matcher (LLM) - Clasifica comparables
7. **STEP 5**: Statistics - Calcula estadísticas (sin LLM)
8. **STEP 6**: Pricing Intelligence (LLM) - Genera recomendación
9. **STEP 7**: Commission Calculator - Desglose de ganancias (sin LLM)
10. **STEP 8**: Token Tracking - Captura uso API real (sin LLM)

---

## Diagrama Completo del Pipeline

```mermaid
graph TD
    START["🌐 INPUT: URL Producto<br/>Mercado Libre"]
    
    START -->|Usuario aporta| DASHBOARD["📊 DASHBOARD<br/>Streamlit Frontend"]
    
    DASHBOARD -->|cost_price + target_margin + price_tolerance| PIPELINE["🔄 PRICING PIPELINE<br/>Orquestador Central"]
    
    PIPELINE -->|STEP 0| EXTRACT["🔍 PRODUCT EXTRACTOR<br/>Sin LLM - HTML Scraping<br/>Tu producto"]
    EXTRACT -->|Title, Brand, Specs<br/>Price, Images| PIVOT["📦 PIVOT PRODUCT<br/>Datos base del producto<br/>a analizar"]
    
    PIVOT -->|STEP 1| ENRICH["💡 DATA ENRICHER<br/>LLM gpt-4o-mini<br/>Analiza descripción"]
    ENRICH -->|enriched_specs<br/>search_patterns<br/>functional_descriptors| ENRICHED["🎯 ENRICHED DATA<br/>Category, key_specs<br/>market_segment<br/>patterns para búsqueda"]
    
    ENRICHED -->|STEP 2| STRATEGY["🔎 SEARCH STRATEGY<br/>LLM gpt-4o-mini<br/>Genera queries"]
    STRATEGY -->|primary_search<br/>alternative_searches| QUERIES["📋 SEARCH TERMS<br/>Búsqueda principal<br/>Búsquedas alternativas<br/>Keywords weight"]
    
    QUERIES -->|STEP 3| SCRAPE["🌍 MARKET RESEARCH<br/>Sin LLM - Scraping<br/>Búsquedas múltiples"]
    
    SCRAPE -->|PRIMARY + ALTERNATIVE<br/>searches| SCRAPE2["🔍 Ejecuta:<br/>1. Primary search<br/>2. Alternative searches"]
    
    SCRAPE2 -->|50+ Ofertas<br/>raw_offers| RAW["📦 RAW OFFERS<br/>Productos encontrados<br/>sin filtrar"]
    
    RAW -->|STEP 3b| VALIDATE["📋 PRICE VALIDATION<br/>Sin LLM - Lógica pura<br/>Filtra por tolerance"]
    
    VALIDATE -->|precio < min OR<br/>precio > max| OUTSIDE["🚫 OUT OF RANGE<br/>Removed from list"]
    
    VALIDATE -->|precio dentro<br/>de [min-max]| VALID["✅ VALIDATED OFFERS<br/>Solo productos en<br/>rango de tolerancia"]
    
    VALID -->|STEP 4| MATCHER["🧠 PRODUCT MATCHER<br/>LLM gpt-4o-mini<br/>Clasificación inteligente"]
    
    MATCHER -->|LLM returns| CLASSIFICATION["📊 CLASSIFICATION RESULT<br/>product<br/>classification: comparable | excluded<br/>confidence: 0.0-1.0<br/>reasoning"]
    
    CLASSIFICATION -->|is_comparable=true<br/>confidence >= 0.7| PASS1["✔️ PASS 1<br/>Comparables SEGUROS<br/>Confianza alta"]
    
    CLASSIFICATION -->|is_comparable=false<br/>confidence < 0.7| UNCERTAIN["❓ UNCERTAIN<br/>Podría ser comparable<br/>pero poco confianza"]
    
    CLASSIFICATION -->|is_comparable=false<br/>razón clara| EXCLUDED["❌ EXCLUDED<br/>Función diferente<br/>Solo accesorios<br/>Fuera de rango"]
    
    UNCERTAIN -->|PASS 2<br/>Re-evaluación| PASS2["↔️ FALLBACK LOGIC<br/>Acepta inciertos<br/>si misma categoría"]
    
    PASS2 -->|Resultado final| COMPARABLES["✅ FINAL COMPARABLES<br/>Merge: PASS1 + PASS2<br/>Lista limpia"]
    
    EXCLUDED -->|Info de referencia| STATS["(Se guarda para reporting)"]
    
    COMPARABLES -->|STEP 5| CALC_STATS["📈 STATISTICS<br/>Sin LLM - Math puro<br/>get_price_recommendation_data"]
    
    CALC_STATS -->|IQR Outlier Removal<br/>Percentiles| STATS_OUT["📊 PRICE STATISTICS<br/>mean, median<br/>std_dev, percentiles<br/>by_condition"]
    
    STATS_OUT -->|STEP 6| PRICING["💰 PRICING INTELLIGENCE<br/>LLM gpt-4o-mini<br/>Análisis de mercado"]
    
    PRICING -->|competitor_prices<br/>cost_price + margin| REC["💵 RECOMMENDATION<br/>recommended_price<br/>margin_percent<br/>strategy<br/>reasoning"]
    
    REC -->|STEP 7| PROFIT["🏦 COMMISSION CALCULATOR<br/>Sin LLM - Fórmulas<br/>Desglose real"]
    
    PROFIT -->|Shipping, Fees<br/>Commission %| PROFIT_OUT["💹 PROFITABILITY<br/>net_profit<br/>net_margin_percent<br/>roi_percent<br/>breakdown"]
    
    PROFIT_OUT -->|STEP 8| TOKENS["📈 TOKEN TRACKING<br/>Sin LLM - Recolección<br/>Suma de todos los agentes"]
    
    TOKENS -->|De cada agent LLM<br/>response_metadata<br/>['token_usage']| TOKEN_OUT["🔑 TOKEN SUMMARY<br/>total_tokens<br/>cost_usd<br/>by_agent"]
    
    TOKEN_OUT -->|STEP 9| RENDER["🎨 DASHBOARD RENDER<br/>Streamlit<br/>Visualización"]
    
    RENDER -->|Muestra| FINAL["📊 FINAL RESULT<br/>Pivot product<br/>Comparable offers<br/>Price stats<br/>Recommendation<br/>Profitability<br/>Token costs"]
    
    FINAL -->|Usuario revisa| ACTION["✅ ACTION<br/>Aceptar precio<br/>Rechazar<br/>Ajustar params<br/>Iterar"]
    
    ACTION -->|Nuevo análisis| DASHBOARD
    
    style START fill:#e1f5ff
    style DASHBOARD fill:#fff3e0
    style PIPELINE fill:#f3e5f5
    style EXTRACT fill:#e8f5e9
    style PIVOT fill:#e0f2f1
    style ENRICH fill:#f0f4c3
    style ENRICHED fill:#fff9c4
    style STRATEGY fill:#ffe0b2
    style QUERIES fill:#ffccbc
    style SCRAPE fill:#f8bbd0
    style SCRAPE2 fill:#f8bbd0
    style RAW fill:#c8e6c9
    style VALIDATE fill:#a5d6a7
    style OUTSIDE fill:#ef9a9a
    style VALID fill:#81c784
    style MATCHER fill:#c5cae9
    style CLASSIFICATION fill:#b3e5fc
    style PASS1 fill:#81d4fa
    style UNCERTAIN fill:#fff9c4
    style EXCLUDED fill:#ffcdd2
    style PASS2 fill:#ffd54f
    style COMPARABLES fill:#fbc02d
    style STATS fill:#b0bec5
    style CALC_STATS fill:#f9a825
    style STATS_OUT fill:#fb8c00
    style PRICING fill:#d84315
    style REC fill:#c62828
    style PROFIT fill:#7b1fa2
    style PROFIT_OUT fill:#5e35b1
    style TOKENS fill:#b3e5fc
    style TOKEN_OUT fill:#4fc3f7
    style RENDER fill:#29b6f6
    style FINAL fill:#039be5
    style ACTION fill:#0277bd
```

---

## Desglose Detallado de Cada Step

### STEP 0: PRODUCT EXTRACTOR
```
COMPONENTE: MLWebScraper.extract_product_details()
TIPO: Sin LLM (Puro HTML scraping)
ENTRADA: URL del producto Mercado Libre
SALIDA: ProductDetails object

Información Extraída:
- product_id (MLM code)
- title
- brand
- price (precio actual)
- images (list)
- image_url (thumbnail principal)
- attributes (specs normalizadas)
- description (texto completo)
- availability
- rating, reviews

ERRORES COMUNES:
- URL inválida → return error
- Producto no encontrado → return null
- Specs incompletos → fallback a valores default

OUTPUT VARIABLES:
pivot_product = ProductDetails(
    product_id="MLM1234567",
    title="Bocina 18 Pulgadas Profesional",
    brand="Louder",
    price=3500.00,
    image_url="https://...",
    images=["https://1", "https://2"],
    attributes={"size": "18in", "power": "1000W", ...}
)
```

### STEP 1: DATA ENRICHER AGENT
```
COMPONENTE: DataEnricherAgent.analyze_product(pivot_product)
TIPO: LLM (gpt-4o-mini)
ENTRADA: ProductDetails del pivot
SALIDA: Enrichment result

ANÁLISIS REALIZADO:
- Lee título, descripción, atributos
- Identifica categoría real del producto
- Extrae key specs (tamaño, potencia, rango)
- Genera functional_descriptors (para búsqueda)
- Detecta market_segment
- Crea search_patterns (variantes de nombres)

LLM PROMPT OBJETIVO:
"Analiza este producto y dame:
1. Categoría exacta
2. Especificaciones clave
3. Patrones de búsqueda alternativos
4. Segmento de mercado"

OUTPUT VARIABLES:
enriched_specs = {
    "category": "AUDIO - Bocinas",
    "key_specs": {
        "size": "18 pulgadas",
        "power": "1000W",
        "impedance": "8 ohms"
    },
    "functional_descriptors": [
        "bocina profesional",
        "woofer 18",
        "subwoofer audio"
    ],
    "market_segment": "Professional Audio",
    "search_patterns": [
        "bocina 18",
        "bocina profesional",
        "woofer 18 pulgadas"
    ]
}

FALLBACK SI FALLA:
- Se usa solo el título y atributos básicos
- Se generan search_patterns simples
```

### STEP 2: SEARCH STRATEGY AGENT
```
COMPONENTE: SearchStrategyAgent.generate_search_terms(pivot_product)
TIPO: LLM (gpt-4o-mini)
ENTRADA: ProductDetails + enriched data
SALIDA: Search strategy dict

ANÁLISIS REALIZADO:
- Analiza enriched_specs si disponible
- Genera query principal balanceada
- Crea 2-3 queries alternativas
- Asigna pesos a keywords
- Determina rango de precios

LLM PROMPT OBJETIVO:
"Este producto es una Bocina 18. Dame:
1. Query principal para buscar competencia
2. Queries alternativas (con sinónimos)
3. Pesos de relevancia para cada termino"

OUTPUT VARIABLES:
search_strategy = {
    "primary_search": "bocina 18 pulgadas profesional",
    "alternative_searches": [
        "bocina 18 woofer",
        "bocina profesional",
        "subwoofer 18"
    ],
    "key_specs": ["size", "power", "brand"],
    "reasoning": "Balanceado entre específico y flexible"
}

CÓMO SE USA:
1. Ejecuta PRIMARY_SEARCH en ML
2. Si pocos resultados → ejecuta ALTERNATIVE[0]
3. Si aún pocos → ejecuta ALTERNATIVE[1]
4. Limita a 50 ofertas totales
```

### STEP 3: MARKET RESEARCH (SCRAPING)
```
COMPONENTE: MLWebScraper.search_products()
TIPO: Sin LLM (Web scraping + requests)
ENTRADA: search_term, max_offers, price_min/max
SALIDA: List[Offer]

FLUJO REAL:
1. Ejecuta primary_search
   → Retorna X ofertas
2. Si X < max_offers:
   → Ejecuta alternative_search[0]
   → Evita duplicados (by item_id)
3. Si X < max_offers:
   → Ejecuta alternative_search[1]
4. Limita resultado a max_offers

OFERTAS CAPTURADAS:
Para cada producto en resultados:
- item_id (MLM code)
- title
- seller_name
- price
- seller_rating
- reviews_count
- images
- condition (new/used)
- url

CANTIDAD:
- Busca max 50 ofertas
- Típicamente retorna 40-50

OUTPUT VARIABLES:
all_offers = [
    Offer(
        item_id="MLM2345678",
        title="Bocina 18 Bajos Alta Potencia",
        price=3200.00,
        seller_name="Audio Profesional",
        condition="new",
        ...
    ),
    ... (40+ más)
]
```

### STEP 3b: PRICE VALIDATION
```
COMPONENTE: Lógica pura en pipeline
TIPO: Sin LLM (Validación matemática)
ENTRADA: all_offers + price_min/max
SALIDA: validated_offers

CÁLCULO DE RANGE:
price_min = pivot_price * (1 - tolerance)
price_max = pivot_price * (1 + tolerance)

EJEMPLO:
- pivot_price = 3500 MXN
- tolerance = 0.30 (±30%)
- price_min = 3500 * 0.70 = 2450 MXN
- price_max = 3500 * 1.30 = 4550 MXN

FILTRADO:
Para cada offer:
  if offer.price < price_min OR offer.price > price_max:
    → REMOVE (fuera de rango)
  else:
    → KEEP (dentro de rango)

RESULTADO:
- Reduces offers de ~50 a ~30-40
- Solo productos "comparables" por precio
- Evita ruido extremo (muy caros/muy baratos)

LOGGING:
"Offers filtered by price tolerance:
 removed=12, remaining=38,
 tolerance_percent=30"
```

### STEP 4: PRODUCT MATCHER (LLM)
```
COMPONENTE: ProductMatchingAgent.execute()
TIPO: LLM (gpt-4o-mini)
ENTRADA: pivot_product.title, validated_offers
SALIDA: classification dict

FILOSOFÍA:
"Find all products a CUSTOMER might consider"

CLASIFICACIÓN POR OFERTA:
Para cada offer:
  - ¿Es misma categoría?
  - ¿Specs comparables?
  - ¿Precio en rango?
  
LLM RETORNA:
{
    "product": "título de la oferta",
    "classification": "comparable" | "excluded",
    "confidence": 0.0-1.0,
    "reasoning": "texto explicativo",
    "category": "tipo",
    "spec_variance": "%"
}

REGLAS DE CLASIFICACIÓN:

COMPARABLE (✅):
- Misma categoría producto
- ±30% tamaño/dimensiones
- ±40% potencia/watts
- Variantes de familia aceptables
- Color diferente NO auto-rechaza

EXCLUDED (❌):
- Función completamente diferente
- Solo accesorios (sin producto base)
- Producto dañado/defectuoso
- Especificaciones fuera de tolerancia extrema

CONFIANZA (confidence score):
- 0.9-1.0: Muy seguro (PASS 1)
- 0.7-0.9: Seguro (PASS 1)
- 0.5-0.7: Incierto (PASS 2 candidate)
- <0.5: Probablemente erróneo (EXCLUDED)

TWO-PASS STRATEGY:

PASS 1: Selecciona is_comparable=true
  → Ofertas que LLM clasifica como comparables

PASS 2: Selecciona is_comparable=false AND confidence < 0.7
  → Ofertas inciertas pero posibles
  → Fallback para asegurar resultados

MERGE: PASS1 ∪ PASS2
  → Lista final de comparables
```

### STEP 5: STATISTICS
```
COMPONENTE: get_price_recommendation_data()
TIPO: Sin LLM (Pura matemática)
ENTRADA: comparable_offers
SALIDA: statistics dict

ANÁLISIS REALIZADO:

1. OUTLIER REMOVAL (IQR Method):
   - Calcula Q1, Q3 (cuartiles)
   - IQR = Q3 - Q1
   - Outlier si: price < Q1-1.5*IQR OR price > Q3+1.5*IQR
   - Remueve extremos

2. AGREGACIÓN POR CONDICIÓN:
   - new: análisis separado
   - used: análisis separado

3. CÁLCULOS POR GRUPO:
   - mean: promedio
   - median: valor central
   - std_dev: desviación estándar
   - percentiles: 25%, 75%
   - count: número de ofertas
   - min/max: rango

OUTPUT VARIABLES:
statistics = {
    "overall": {
        "total_offers": 35,
        "outliers_removed": 3,
        "mean": 3420.00,
        "median": 3350.00,
        "std_dev": 280.00,
        "p25": 3150.00,
        "p75": 3650.00
    },
    "by_condition": {
        "new": {
            "total": 25,
            "mean": 3500.00,
            "median": 3450.00
        },
        "used": {
            "total": 10,
            "mean": 3200.00,
            "median": 3100.00
        }
    }
}

CÓMO SE USA EN SIGUIENTE STEP:
- Precio sugerido basado en median/mean
- Contexto para LLM (¿estamos caros o baratos?)
```

### STEP 6: PRICING INTELLIGENCE (LLM)
```
COMPONENTE: PricingIntelligenceAgent.run()
TIPO: LLM (gpt-4o-mini)
ENTRADA: 
  - product_name
  - cost_price (tu costo)
  - competitor_prices (lista de precios)
  - current_price (precio actual mercado)
  - target_margin_percent (tu margen deseado)
SALIDA: recommendation dict

LÓGICA DEL AGENTE:

1. ANÁLISIS DE MERCADO:
   - ¿Dónde estamos vs competencia?
   - ¿Hay oportunidad de subida?
   - ¿Hay presión bajista?

2. CÁLCULO DE RANGO:
   - min_price = cost * (1 + min_markup)
   - max_price = cost * (1 + max_markup)
   - suggested = (median_competitive + min_price) / 2
   - Ajusta por target_margin

3. ANÁLISIS DE POSICIÓN:
   - Si suggested < median: "aggressive pricing"
   - Si suggested ≈ median: "competitive pricing"
   - Si suggested > median: "premium pricing"

LLM RETORNA:
{
    "recommended_price": 3650.00,
    "price_range_min": 3200.00,
    "price_range_max": 4100.00,
    "margin_percent": 35.0,
    "strategy": "competitive_with_slight_premium",
    "reasoning": "Similar a competencia pero 5% arriba"
}

VALIDACIONES:
- recommended_price > cost_price
- recommended_price dentro de price_range
- margin_percent >= target_margin (si possible)
```

### STEP 7: COMMISSION CALCULATOR
```
COMPONENTE: CommissionCalculator.calculate_profit()
TIPO: Sin LLM (Fórmulas reales)
ENTRADA:
  - selling_price (precio recomendado)
  - cost_of_goods (tu costo)
  - weight_kg (peso estimado)
  - category_fee_percent (comisión ML)
SALIDA: profit breakdown

CÁLCULOS REALIZADOS:

1. COMISIÓN ML:
   commission = selling_price * (category_fee_percent / 100)

2. COSTO DE ENVÍO (tabla de ML):
   - 0-300g: $15 MXN
   - 300g-1kg: $25 MXN
   - 1-5kg: $45 MXN
   - ... (tabla real de ML 2026)

3. IMPUESTOS:
   tax = cost_of_goods * 0.16  (16% IEPS estimado)

4. COSTO TOTAL:
   total_cost = cost_of_goods + shipping + tax

5. GANANCIA NETA:
   net_profit = selling_price - commission - total_cost

6. MÁRGENES:
   net_margin_percent = (net_profit / selling_price) * 100
   roi = (net_profit / cost_of_goods) * 100

OUTPUT VARIABLES:
profitability = {
    "breakdown": {
        "selling_price": 3650.00,
        "cost_of_goods": 1200.00,
        "ml_commission": -547.50,  # 15%
        "shipping_cost": -45.00,
        "taxes_estimated": -192.00,  # 16% de COGS
        "net_profit": 1665.50
    },
    "net_margin_percent": 45.65,
    "roi_percent": 138.79,
    "currency": "MXN"
}

IMPORTANTE:
- Envío es estimado (usuario puede refinar)
- Impuestos son aproximados
- No incluye costos operativos (packaging, etc)
- Es baseline para decisión rápida
```

### STEP 8: TOKEN TRACKING
```
COMPONENTE: Token tracking en core/token_tracker.py
TIPO: Sin LLM (Recolección)
ENTRADA: Respuestas de TODOS los agentes LLM
SALIDA: token_summary

AGENTES QUE GENERAN TOKENS:
1. DataEnricherAgent (STEP 1)
2. SearchStrategyAgent (STEP 2)
3. ProductMatchingAgent (STEP 4) - **MAYOR CONSUMIDOR**
4. PricingIntelligenceAgent (STEP 6)

CAPTURA POR AGENTE:
Para cada respuesta LLM:
  tokens_used = response.response_metadata['token_usage']
  track(agent_name, tokens_used)

ESTRUCTURA CAPTURADA:
{
    "agent": "product_matching",
    "prompt_tokens": 2150,
    "completion_tokens": 850,
    "total_tokens": 3000,
    "model": "gpt-4o-mini",
    "timestamp": "2026-01-23T..."
}

CÁLCULOS GLOBALES:
total_tokens = sum(all_agents)
total_cost = (prompt_tokens * 0.00015) + (completion_tokens * 0.0006)
              para gpt-4o-mini

EJEMPLO REAL:
data_enricher: 500 tokens
search_strategy: 600 tokens
product_matching: 3500 tokens  ← La más grande
pricing_intelligence: 800 tokens
─────────────────────────
TOTAL: 5400 tokens
COST: ~$2.43 USD

SALIDA:
token_summary = {
    "total_tokens": 5400,
    "total_cost_usd": 2.43,
    "by_agent": {
        "data_enricher": 500,
        "search_strategy": 600,
        "product_matching": 3500,
        "pricing_intelligence": 800
    },
    "all_real": True  # ✅ REALES, no estimados
}
```

### STEP 9: DASHBOARD RENDER
```
COMPONENTE: frontend/dashboard.py (Streamlit)
TIPO: Sin LLM (Presentación)
ENTRADA: Todos los resultados anteriores
SALIDA: Interfaz visual

SECCIONES MOSTRADAS:

1. INFORMACIÓN DEL PRODUCTO:
   - Imagen (con fallback)
   - Título, marca, especificaciones
   - Precio original

2. BÚSQUEDA Y SCRAPING:
   - Search terms utilizados
   - Cantidad de ofertas encontradas
   - Rango de precios buscados

3. TABLA DE COMPARABLES:
   - Título, precio, seller
   - Condición (new/used)
   - Clasificación LLM
   - Links a products

4. ANÁLISIS DE PRECIOS:
   - Gráfico: distribución de precios
   - Estadísticas: mean, median, percentiles
   - Pivot vs competencia

5. RECOMENDACIÓN DE PRECIO:
   - Precio sugerido (destacado)
   - Rango aceptable
   - Margen % esperado
   - Estrategia (competitive, premium, etc)

6. ANÁLISIS DE GANANCIAS:
   - Desglose: ventas - comisión - envío - impuestos
   - Ganancia neta
   - % Margen neto
   - ROI %

7. COSTOS API:
   - ✅ Tokens REALES capturados
   - Desglose por agente
   - Costo USD total

8. ERRORES (si aplica):
   - Se muestra error message
   - Pero mantiene info del producto
   - Sugiere próximas acciones

FLUJO SI HAY ERROR:
- Product extractor falla → return inmediato
- Data enricher falla → continúa con data básica
- Search strategy falla → usa query simple
- Scraping falla → muestra error, producto sigue visible
- Matcher falla → muestra oferta con warning
- Statistics falla → usa raw prices
```

---

## Vista Temporal del Pipeline Completo

```
TIMELINE DE EJECUCIÓN:

USUARIO INGRESA URL
    ↓
    [~2 seg] STEP 0: Extract product
    ↓
    [~3 seg] STEP 1: Data enricher (LLM) ─────────┐
    ↓                                              │
    [~2 seg] STEP 2: Search strategy (LLM) ───────┤ Llamadas LLM
    ↓                                              │
    [~5 seg] STEP 3: Market research (scraping) ──┼ Más lentas
    ↓                                              │
    [~1 seg] STEP 3b: Price validation ───────────┤
    ↓                                              │
    [~5 seg] STEP 4: Product matcher (LLM) ───────┤ PASO MÁS LENTO
    ↓                                              │ (clasifica 30+ ofertas)
    [~2 seg] STEP 5: Statistics ───────────────────┼
    ↓                                              │
    [~3 seg] STEP 6: Pricing intelligence (LLM) ──┤
    ↓                                              │
    [~1 seg] STEP 7: Commission calculator ───────┘
    ↓
    [~0.5 seg] STEP 8: Token tracking
    ↓
    [~0.5 seg] STEP 9: Dashboard render
    ↓
    USUARIO VE RESULTADOS
    (Total: ~24 segundos típico)
```

---

## Consideraciones en Cada Step

| Step | Tipo | Entrada | Función Clave | Error Crítico | Fallback |
|------|------|---------|---|---|---|
| 0 | No LLM | URL | Extrae base | URL inválida | null |
| 1 | LLM | Producto | Enriquece specs | Descripción vacía | Usa atributos básicos |
| 2 | LLM | Enriched data | Genera queries | API error | Query simple del título |
| 3 | No LLM | Query | Scraping ML | Timeout / Rate limit | Reintentos con backoff |
| 3b | No LLM | Raw offers | Filtra por rango | Tolerance muy restrictivo | Amplía rango 20% |
| 4 | LLM | Validated offers | Clasifica | Respuesta no-JSON | Por defecto excluded |
| 5 | No LLM | Comparables | Estadísticas | Pocas ofertas < 3 | Usa raw prices |
| 6 | LLM | Stats | Recomendación | Margin negativo | Multiplica cost × 1.3 |
| 7 | No LLM | Price | Ganancias | Weight desconocido | Estima 1kg |
| 8 | No LLM | Tokens | Tracking | Key mismatch | Token defaults |
| 9 | No LLM | Resultados | Visualiza | Render crash | Error page |

---

## Flujo de Datos Consolidado

```mermaid
graph LR
    URL["URL Input<br/>Step 0"] 
    
    URL -->|ProductDetails| ENRICH["Enrich<br/>Step 1"]
    ENRICH -->|enriched_specs| STRATEGY["Search<br/>Step 2"]
    STRATEGY -->|search_terms| SCRAPE["Scraping<br/>Step 3"]
    SCRAPE -->|raw_offers| VALIDATE["Validate<br/>Step 3b"]
    VALIDATE -->|valid_offers| MATCHER["Match<br/>Step 4"]
    MATCHER -->|comparable_offers| STATS["Stats<br/>Step 5"]
    STATS -->|statistics| PRICING["Pricing<br/>Step 6"]
    PRICING -->|recommended_price| PROFIT["Profit<br/>Step 7"]
    PROFIT -->|profitability| TOKENS["Tokens<br/>Step 8"]
    TOKENS -->|token_summary| RENDER["Render<br/>Step 9"]
    RENDER -->|Complete Result| DASHBOARD["Dashboard<br/>Usuario"]
    
    style URL fill:#e1f5ff
    style ENRICH fill:#f0f4c3
    style STRATEGY fill:#ffe0b2
    style SCRAPE fill:#f8bbd0
    style VALIDATE fill:#a5d6a7
    style MATCHER fill:#b3e5fc
    style STATS fill:#f9a825
    style PRICING fill:#d84315
    style PROFIT fill:#7b1fa2
    style TOKENS fill:#b3e5fc
    style RENDER fill:#29b6f6
    style DASHBOARD fill:#039be5
```

---

## Decisiones Arquitectónicas Clave

### 1. **Dos Scraping Steps Separados**
   - **STEP 3**: Scraping puro (sin LLM)
   - **STEP 3b**: Validación de range (sin LLM)
   - **Razón**: Separar concerns, permitir retry independiente

### 2. **Two-Pass Matching**
   - **PASS 1**: is_comparable=true (muy seguro)
   - **PASS 2**: is_comparable=false AND confidence<0.7 (fallback)
   - **Razón**: Garantizar resultados sin ser demasiado permisivo

### 3. **Data Enricher Antes de Search Strategy**
   - **Usa**: enriched_specs para generar queries más precisas
   - **NO**: Solo el título
   - **Razón**: Búsquedas mejor dirigidas, menos ruido

### 4. **Price Tolerance Filter Dual**
   - **En scraping**: Filtra resultados para ML
   - **Post-scraping**: Revalida cada oferta
   - **Razón**: Asegurar consistency, manejo de edge cases

### 5. **Stats Sin LLM**
   - **Pura matemática**: IQR, cuartiles, percentiles
   - **NO confiamos en**: LLM para outlier detection
   - **Razón**: Reproducibilidad, velocidad, costo

### 6. **Commission Calculator Detallado**
   - **Incluye**: Shipping real de ML, impuestos estimados
   - **NO simplificado**: Desglosa cada componente
   - **Razón**: Usuario ve exactamente de dónde vienen ganancias

### 7. **Token Tracking Granular**
   - **Por agente**: Sabe cuál consume más
   - **Captura real**: response_metadata['token_usage']
   - **NO estimado**: Valores reales de OpenAI
   - **Razón**: Usuario ve costo verdadero, transparencia

---

**Versión:** v2.0 (Corregida y Completa)  
**Fecha:** 23 Enero 2026  
**Estado:** Documentación de pipeline actual ✅
