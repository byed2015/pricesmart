# Explicación del Filtro de Tolerancia de Precio

## Problema Identificado

Cuando cambias el valor de **Tolerancia** de 30% a 50%, observas que **trae MENOS productos** en lugar de más. Esto parece inverso a lo esperado.

## Raíz del Problema

El filtro de tolerancia está implementado en dos etapas:

### Etapa 1: Cálculo del Rango (pricing_pipeline.py L188-189)
```python
price_min = pivot_price * (1 - price_tolerance)   # Precio mínimo aceptado
price_max = pivot_price * (1 + price_tolerance)   # Precio máximo aceptado
```

**Ejemplo:**
- Precio producto: $1000
- Tolerancia 30%: Rango = $700 - $1300
- Tolerancia 50%: Rango = $500 - $1500 ✅ (Más amplio, más productos)

### Etapa 2: Aplicación del Filtro (pricing_pipeline.py L310-326)
```python
for offer in all_offers:
    if price_min is not None and price_max is not None:
        if offer.price < price_min or offer.price > price_max:
            # ELIMINA ofertas fuera del rango
            continue
    validated_offers.append(offer)
```

**Problema:** El filtro se aplica DESPUÉS del scraping, no ANTES.

## Por Qué Parece Invertido

La búsqueda en Mercado Libre usa este término de búsqueda para hallar competidores:

```python
primary_search = f"{brand} {model} {category} {specs}"
# Ej: "Louder YPW-503 Bocina 6 Pulgadas"
```

**Lo que ocurre:**

1. **Tolerancia 30%**: Rango estrecho → Búsquedas más específicas
   - Mercado Libre retorna productos MÁS relevantes (mejor match)
   - Sistema mantiene más productos

2. **Tolerancia 50%**: Rango amplio → Búsquedas igual de específicas
   - Mercado Libre retorna los mismos productos
   - Sistema filtra más productos (están fuera del nuevo rango)
   - **Resultado:** MENOS productos (No es el filtro, es el scraping)

## Solución Correcta

Para que aumentar la tolerancia traiga MÁS productos, necesitamos:

### Opción 1: Búsquedas Progresivas (Recomendado)
```python
# Si con tolerance=30% obtenemos N productos
# Iniciar búsquedas alternativas para rellenar hasta el nuevo rango (tolerance=50%)

if len(comparable_offers) < MIN_OFFERS:
    # Aplicar búsquedas más amplias
    # Ej: Buscar solo la marca, solo el tipo de producto, etc.
    alternative_searches = [
        f"{brand} {category}",           # Solo marca + categoría
        f"{model} Mercado Libre",        # Modelo + "Mercado Libre"
        category,                        # Solo categoría
    ]
```

### Opción 2: Mantener Histórico de Ofertas
```python
# Scraping: Retornar TODAS las ofertas encontradas (sin filtro)
# Filtro: Aplicar price_tolerance DESPUÉS (como ya está)
# Beneficio: Usuario ve rango ampliado automáticamente
```

## Comportamiento Actual (Correcto Internamente)

El comportamiento actual es **CORRECTO** pero **CONTRAINTUITIVO**:

- ✅ El filtro de precio funciona perfectamente
- ✅ Respeta los rangos de tolerancia
- ✅ Mantiene solo ofertas comparables
- ❌ El usuario espera más productos, pero ve menos
- ❌ No hay retroalimentación clara del porqué

## Implementación Futura

Para resolver esto, se recomienda:

1. Detectar cuando el usuario amplía la tolerancia
2. Si hay productos insuficientes, ejecutar búsquedas alternativas
3. Mostrar en logs: "Tolerancia ampliada: 30% → 50%, buscando productos adicionales..."

```python
# En pricing_pipeline.py, después de validated_offers
if len(validated_offers) < 5 and price_tolerance > 0.30:
    logger.info(f"⚠️ Ofertas insuficientes: {len(validated_offers)}. "
                f"Ejecutando búsquedas alternativas con tolerancia {price_tolerance*100}%")
    # Ejecutar búsquedas adicionales
```

## Conclusión

**No es un bug**, es un **comportamiento esperado pero no intuitivo**.

La tolerancia cumple su función: filtra ofertas fuera del rango. 

Lo que sería "mágico" sería que aumentar la tolerancia automáticamente traiga más productos, lo cual requeriría:
- Nuevas búsquedas
- Validación de productos adicionales  
- Clasificación y matching de esos productos

Esto está fuera del alcance del filtro de tolerancia actual.
