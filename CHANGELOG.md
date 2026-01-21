# Changelog

## [v1.2.0] - 2026-01-21

### ✨ Nuevas Características
- **Catálogo Interno**: Sistema de gestión de productos internos con CSV
  - Selector de productos con búsqueda/filtrado
  - Auto-carga de costo desde catálogo
  - Dos modos de entrada: URL Manual vs Catálogo Interno
  
- **Cálculo de Profitabilidad Real**:
  - Ganancia Neta después de comisiones ML, envío, ISR e IVA
  - ROI calculado basado en costo real
  - Margen Neto como % del precio de venta
  - Desglose completo en tabla interactiva

- **Búsqueda Ampliada**:
  - Implementación de multi-search (primaria + alternativas)
  - Recuperación de hasta 50 productos (vs 6 anteriores)
  - Deduplicación automática por item_id

### 🐛 Correcciones
- Arreglo: Recomendación de precio mostraba $0 en ganancia/ROI
  - Enriquecimiento de modelo `PricingRecommendation` con campos `profit_per_unit` y `roi_percent`
  - Transferencia de cálculos de profitabilidad al objeto recommendation
  
- Arreglo: Error de validación Streamlit con productos <$100
  - Cambio de min_value: 100.0 → 1.0 en campo de costo
  - Permite toda la gama de precios ($40 - $728)

- Arreglo: Errores de tipo numérico en Streamlit
  - Conversión consistente a float en todos los number_input
  - Eliminación de warnings `use_container_width` (reemplazado por `width="stretch"`)

### 📚 Documentación
- Actualización de README.md con nuevas características
- Mejora de .gitignore para proteger API keys (OPENAI_API_KEY)
- Documentación de archivos nuevos:
  - `backend/app/services/catalog_service.py`: Singleton para catálogo
  - `frontend/dashboard_simple.py`: Dashboard mejorado con dual input
  - `backend/data/productos_catalogo.csv`: Catálogo interno (12 productos)

### 🔄 Cambios Internos
- **Models** (`pricing_intelligence.py`):
  - Agregados campos opcionales `profit_per_unit` y `roi_percent` a `PricingRecommendation`

- **Pipeline** (`pricing_pipeline.py`):
  - Lógica mejorada para enriquecer recommendation con profitabilidad
  - Cálculo de `suggested_margin_percent` desde `CommissionCalculator`

- **Servicios** (`catalog_service.py`):
  - Nuevo servicio para gestionar catálogo CSV
  - Métodos: `get_all_products()`, `search_products()`, `get_product_by_id()`
  - Patrón Singleton para única instancia por aplicación

- **Frontend** (`dashboard_simple.py`):
  - Radio selector para elegir fuente (URL Manual / Catálogo Interno)
  - Integración con CatalogService para cargar y filtrar productos
  - Expander para detalles de producto seleccionado
  - Mejor visualización de estadísticas con Plotly

### 🔒 Seguridad
- Mejorado .gitignore con protecciones explícitas:
  - `OPENAI_API_KEY` y `openai_key.txt`
  - `api_keys.txt`, `config/secrets/`
  - `.aws/` para credenciales AWS
  - Nunca más compartir API keys en repositorio

## [v1.1.0] - 2026-01-15

### ✨ Nuevas Características
- Sistema de estadísticas con desviación estándar
- Análisis de outliers con Rango Intercuartil (IQR)
- Dashboard mejorado con gráficos Plotly
- Clasificación visual de ofertas comparables

### 🐛 Correcciones
- Arreglo: Indentación en `product_matching.py`
- Arreglo: Cálculo de `std_dev` en estadísticas
- Eliminación de campos redundantes en UI

## [v1.0.0] - 2025-12-01

### ✨ Características Iniciales
- Scraper de Mercado Libre sin API
- Agente de matching de productos con visión IA
- Calculadora de rentabilidad 2026
- Dashboard en Streamlit
- Soporte para múltiples categorías
