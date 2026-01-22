# ✅ Token Tracking Implementation - Complete Integration

## Overview
Implementación completa de captura y visualización de **tokens reales** consumidos del API de OpenAI, reemplazando estimaciones hardcodeadas (5000/3000) con datos precisos.

---

## Architecture

### 1. **Core Layer** (`backend/core/`)
- **token_costs.py**: Modelos, tracker global y pricing de OpenAI
- **token_tracker.py**: Decoradores y utilidades de extracción

### 2. **Pipeline Layer** (`backend/app/agents/pricing_pipeline.py`)
```python
# Al inicio de cada análisis
reset_tracker()  # Limpia tokens previos

# Durante procesamiento
# [Cada agente ejecuta LLM calls y captura tokens]

# Al final
token_summary = get_tracker().get_summary()
result["token_usage"] = {
    "input_tokens": int,
    "output_tokens": int,
    "total_tokens": int,
    "total_cost_usd": float,
    "cost_by_model": dict,
    "api_calls": int
}
```

### 3. **Agent Layer** - Token Capture Pattern

Todos los agentes implementan el mismo patrón después de cada LLM call:

```python
# Después de response = llm.invoke() o llm.ainvoke()
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
```

### 4. **Dashboard Layer** (`frontend/dashboard.py`)
```python
# Detección automática
token_data = result.get("token_usage", {})
if token_data and token_data.get("total_tokens", 0) > 0:
    # Display REAL tokens ✅
    is_estimated = False
else:
    # Display ESTIMATED fallback ⚠️
    is_estimated = True
```

---

## Integrated Agents

| Agente | LLM Call | Line | Status | Tokens Capturados |
|--------|----------|------|--------|------------------|
| **pricing_pipeline.py** | invoke/ainvoke | 151, 546 | ✅ Reset + Capture | Input, Output, Summary |
| **product_matching.py** | ainvoke | 378 | ✅ Captured | Input, Output |
| **product_matching.py** | invoke | 593 | ✅ Captured | Input, Output |
| **search_strategy.py** | invoke | 157 | ✅ Captured | Input, Output |
| **data_enricher.py** | invoke | 189 | ✅ Captured | Input, Output |
| **catalog_enrichment.py** | invoke | 83 | ✅ Captured | Input, Output |
| **market_research.py** | ainvoke | 127 | ✅ Captured | Input, Output |

---

## Data Flow

```
1. User Analysis Request
   ↓
2. pricing_pipeline._analyze_from_url()
   ├─ reset_tracker() [línea ~151]
   ├─ product_matching → capture tokens
   ├─ search_strategy → capture tokens
   ├─ data_enricher → capture tokens
   ├─ catalog_enrichment → capture tokens
   ├─ market_research → capture tokens
   ├─ pricing_intelligence → [uses graph]
   └─ tracker.get_summary() [línea ~510]
   ↓
3. result["token_usage"] populated
   ↓
4. Dashboard receives result
   ├─ Detects token_data
   ├─ Shows ✅ REAL or ⚠️ ESTIMADO
   ├─ Displays API calls count
   └─ Shows cost breakdown by model
```

---

## Token Display in Dashboard

### Real Data (✅ REAL)
Cuando hay captura exitosa de tokens desde API:
```
✅ Estos son costos REALES capturados del API de OpenAI
- Input Tokens: 1,234
- Output Tokens: 567
- Total Tokens: 1,801
- Costo Total: $0.045 USD
- API Calls: 5
- Desglose por Modelo:
  • gpt-4o-mini: $0.044 (5 calls)
```

### Estimated Data (⚠️ ESTIMADO)
Cuando no hay datos reales disponibles:
```
⚠️ Estos son costos ESTIMADOS (promedio del proceso)
- Input Tokens: 5,000 (estimado)
- Output Tokens: 3,000 (estimado)
- Total Tokens: 8,000
- Costo Estimado: $0.22 USD
```

---

## Configuration

### OpenAI Pricing (January 2026)
```python
OPENAI_PRICING = {
    "gpt-4o-mini": {
        "input": 0.15,      # $ per 1M tokens
        "output": 0.60      # $ per 1M tokens
    },
    "gpt-4o": {
        "input": 2.50,
        "output": 10.00
    }
}
```

### Model Selection
- **Pipeline/Agents**: `settings.OPENAI_MODEL_MINI` (gpt-4o-mini)
- **Fallback**: Defined in `settings.py`

---

## Implementation Details

### Syntax Validation ✅
Todos los archivos compilados exitosamente:
- `search_strategy.py`: ✅
- `data_enricher.py`: ✅
- `catalog_enrichment.py`: ✅
- `product_matching.py`: ✅
- `market_research.py`: ✅
- `pricing_pipeline.py`: ✅
- `dashboard.py`: ✅

### Commits
- **356e09d**: Pipeline + Dashboard Integration
- **81927e8**: Complete Agent Integration (Latest)

---

## Testing Recommendations

1. **Captura de Tokens**:
   ```bash
   # Ejecutar análisis
   python scripts/verify_pipeline_full.py
   # Verificar tokens en output
   ```

2. **Display en Dashboard**:
   - Abrir dashboard
   - Ejecutar análisis
   - Verificar ✅ REAL tokens mostrados

3. **API Calls Count**:
   - Debe corresponder con número de invocaciones LLM
   - Esperado: ~5-7 calls por análisis

4. **Cost Calculation**:
   - Validar fórmula: `(input_tokens * price_input + output_tokens * price_output) / 1_000_000`

---

## Known Limitations

1. **Graph-based Agents**: `pricing_intelligence.py`, `orchestrator.py`, `data_extractor.py` usan `graph.ainvoke()` que pueden no exponer `response_metadata` directamente. Estos dejan que sus sub-nodos capturen tokens.

2. **Error Handling**: Try/except blocks aseguran que fallos en captura de tokens no rompan el flujo.

3. **Fallback**: Si no hay tokens reales, dashboard muestra estimaciones sin error.

---

## Future Enhancements

- [ ] Token tracking para graph-based agents
- [ ] Persistencia de histórico de tokens en database
- [ ] Análisis de tendencias de costo
- [ ] Alertas si tokens exceden umbral
- [ ] Dashboard de admin para histórico de costos por usuario

---

## Files Modified

```
backend/
├── app/
│   ├── agents/
│   │   ├── pricing_pipeline.py          [Reset + Summary Capture]
│   │   ├── product_matching.py          [2x Token Capture]
│   │   ├── search_strategy.py           [Token Capture]
│   │   ├── data_enricher.py             [Token Capture]
│   │   ├── catalog_enrichment.py        [Token Capture]
│   │   └── market_research.py           [Token Capture]
│   └── core/
│       ├── token_costs.py               [Created earlier]
│       └── token_tracker.py             [Created earlier]
└── frontend/
    └── dashboard.py                     [Detection + Display Logic]
```

---

## Validation Checklist

- ✅ Todas las importaciones agregadas correctamente
- ✅ Syntax válida en todos los archivos
- ✅ Try/except blocks presentes
- ✅ Logging de debug para fallos silenciosos
- ✅ Pipeline reset + capture implementado
- ✅ Dashboard detection logic implementada
- ✅ Commits creados con mensajes descriptivos

---

**Status**: 🟢 COMPLETE - Full token tracking integration ready for testing
