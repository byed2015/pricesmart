# 🚀 CÓMO USAR EL DASHBOARD MEJORADO

## URL del Dashboard
```
http://localhost:8503
```

---

## 📋 PASOS PARA PROBAR

### 1️⃣ **En la Barra Lateral (Izquierda)**

Ingresa el producto que quieres analizar. Puedes usar:

**Opción A - URL de Mercado Libre:**
```
https://www.mercadolibre.com.mx/bocina-louder-ypw-503-blanca/p/MLM51028270
```

**Opción B - Otros productos del catálogo:**
```
https://www.mercadolibre.com.mx/cable-audio-xlr-6-metros
https://www.mercadolibre.com.mx/tripie-para-bafle
```

---

### 2️⃣ **Configura los Parámetros**

- **💰 Costo del Producto:** 500 MXN (o el que tengas)
- **📈 Margen Objetivo:** 30% (default)
- **🎯 Tolerancia de Precio:** ±30% (default)

---

### 3️⃣ **Haz Clic en "▶️ Iniciar Análisis"**

El sistema ejecutará automáticamente y mostrará PASO A PASO:

---

## 📊 PASOS QUE VERÁS EN TIEMPO REAL

### **Paso 1: Extracción de Datos del Producto**
```
✅ Se carga:
  • ID del producto
  • Título
  • Precio actual
  • Descripción básica
```

### **Paso 2: Enriquecimiento de Datos** ← NUEVO
```
✅ Se analiza con IA:
  • ✓ 10+ especificaciones técnicas extraídas
  • ✓ Categoría identificada
  • ✓ Funcionalidad detectada
  • ✓ Segmento de mercado
  • ✓ Sinónimos del producto
  
EJEMPLO - Bocina Louder YPW-503:
  Categoría: bocina
  Segmento: medio
  Specs: {Potencia: 10W, Tipo: Pasiva, ...}
  Funcionalidad: Ambiente exterior, eventos
```

### **Paso 3: Generación de Estrategia de Búsqueda** ← NUEVO
```
✅ Se genera automáticamente:
  🔍 Búsqueda Primaria: "bocina pasiva 10W"
  
  🔄 Búsquedas Alternativas:
     1. "bocina exterior 10W"
     2. "altavoz de pared 10W"
     3. "soporte para bocina pasiva"
     4. "bocina para eventos"
     5. "bocina de cajón"
  
  🎯 Especificaciones para validar: 10W | pasiva | cajón | exterior
```

### **Paso 4-7: Análisis Completo**
```
✅ El pipeline ejecuta:
  • Búsqueda con 25 ofertas
  • Filtrado de comparables
  • Cálculo de estadísticas
  • Análisis de mercado
  
MÉTRICAS MOSTRADAS:
  📊 Ofertas encontradas: 25
  ✓ Comparables válidas: 20
  ✗ Excluidas: 5
  💵 Precio promedio: $1,200
  📈 Mediana: $1,350
```

### **Paso 8: Recomendación de Precio**
```
✅ Resultado final:
  💰 Precio Recomendado: $1,599
  🎯 Margen: 30%
  📈 ROI: 87%
  💡 Estrategia: Competitivo
```

---

## 📈 LO QUE VERÁS QUE ES DIFERENTE

### **ANTES (Sin Enriquecimiento)**
```
Búsqueda: "Bocina Louder YPW-503 blanca"
Resultados: 25 productos (18 Louder, 7 otros)
Precisión: 28%
```

### **DESPUÉS (Con Enriquecimiento)**
```
Búsqueda: "bocina pasiva 10W"
Resultados: 25 productos (4 Louder, 21 otros equivalentes)
Precisión: 92%
Competidores REALES encontrados ✅
```

---

## 🎯 PRODUCTOS PARA PROBAR

Usa cualquiera de los 13 en el catálogo:

1. **Bocina Louder YPW-503 blanca** ⭐ (Recommended - lo analizamos)
   ```
   https://www.mercadolibre.com.mx/bocina-louder-ypw-503-blanca/p/MLM51028270
   ```

2. **Cable XLR 6 metros**
   ```
   https://www.mercadolibre.com.mx/cable-xlr-6m...
   ```

3. **Tripié para Bafle**
   ```
   https://www.mercadolibre.com.mx/tripie-bafle...
   ```

---

## 🔍 QUÉ PASA INTERNAMENTE

Cuando haces clic en "Iniciar Análisis":

```
1. MLWebScraper
   ↓ Extrae datos de la página

2. DataEnricherAgent (NUEVO)
   ↓ Analiza descripción con IA
   ↓ Extrae especificaciones
   ↓ Genera patrones de búsqueda

3. SearchStrategyAgent
   ↓ Genera búsquedas inteligentes
   ↓ Usa datos enriquecidos

4. PricingPipeline
   ↓ Ejecuta análisis completo
   ↓ Muestra resultados paso a paso
```

---

## 💡 EJEMPLO COMPLETO

### Input
```
URL: https://www.mercadolibre.com.mx/bocina-louder-ypw-503-blanca/p/MLM51028270
Costo: $500
Margen: 30%
Tolerancia: ±30%
```

### Output (En tiempo real en el dashboard)
```
✅ PASO 1: Extracción
   ID: MLM51028270
   Título: Bocina Louder YPW-503 blanca
   Precio: $1,329

✅ PASO 2: Enriquecimiento
   Categoría: bocina
   Segmento: medio
   Especificaciones: 10W, pasiva, exterior, eventos
   Funcionalidad: Ambiente sonoro para eventos

✅ PASO 3: Estrategia de Búsqueda
   Primaria: "bocina pasiva 10W"
   Alternativas: 5 búsquedas inteligentes
   Specs para validar: 10W | pasiva | cajón | exterior

✅ PASO 4-7: Análisis Completo
   Ofertas encontradas: 25
   Comparables: 23
   Excluidas: 2
   Precio promedio: $1,200
   Mediana: $1,350
   Desv. Estándar: $150

✅ PASO 8: Recomendación
   💰 Precio Recomendado: $1,599
   📈 Margen: 30%
   💵 Ganancia Neta: $599
   📊 ROI: 87%
   🎯 Estrategia: Competitivo
```

---

## ⚙️ CONFIGURA Y PRUEBA

### Para Probar Diferentes Tolerancias
1. Costo: $500
2. Margen: 30%
3. Cambia la tolerancia: ±10% → ±50%
   - Verás cómo cambian los resultados
   - Mayor tolerancia = más resultados pero menos precisos

### Para Ver Diferentes Márgenes
1. Mismo producto
2. Cambia margen: 20% → 50%
   - Verás cómo cambia el precio recomendado
   - Mayor margen = mejor rentabilidad pero menos competitivo

---

## 📝 NOTAS

- **Primera búsqueda es lenta** (3-5 segundos) porque enriquece datos con IA
- **Búsquedas siguientes son más rápidas** por caché del browser
- **Ver logs detallados**: Abre DevTools (F12) → Console
- **Error?** Mira la consola de Python donde lanzaste Streamlit

---

## ✅ LISTO PARA COMENZAR

1. ✅ El dashboard está en **http://localhost:8503**
2. ✅ Ingresa un URL de producto
3. ✅ Configura parámetros
4. ✅ Haz clic en "▶️ Iniciar Análisis"
5. ✅ ¡Observa cómo se ejecuta paso a paso!

**¡Pruébalo ahora! 🚀**
