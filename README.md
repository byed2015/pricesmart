# 💰 Price Smart IA

**Evaluación inteligente de viabilidad comercial en Mercado Libre**

Sistema avanzado que combina **Inteligencia Artificial** con **Web Scraping** para decirte si un producto es rentable antes de venderlo.

![Price Smart IA](https://raw.githubusercontent.com/tusuario/price-smart-ia/main/docs/screenshot.png)

## 🚀 ¿Qué hace este proyecto?

Si importas o vendes productos en Mercado Libre, sabes que el precio no lo es todo. Necesitas saber:
1. **¿Es rentable?** (Calculando comisiones reales, impuestos y envío).
2. **¿Hay competencia?** (¿Está saturado el mercado?).
3. **¿A qué precio vender?** (Recomendación basada en IA).

Este sistema automatiza todo ese análisis en 30 segundos.

## ✨ Características Clave

- **💰 Calculadora Real 2026**: Desglose exacto de Comisiones ML, Envío (por peso), ISR e IVA.
- **🎯 Recomendación de Precio Inteligente**: Con cálculo real de Ganancia Neta y ROI después de impuestos.
- **📦 Catálogo Interno**: Dos modos de entrada (URL manual o selector de catálogo interno).
- **🤖 Agentes de IA**:
  - `Data Enrichment Agent`: Extrae +10 especificaciones técnicas usando visión de GPT-4.
  - `Search Strategy Agent`: Genera 5+ búsquedas inteligentes (no solo el título).
  - `Visual Matching Agent`: Compara imágenes para asegurar que los competidores sean idénticos.
  - `Pricing Intelligence Agent`: Estratega de precios con análisis de rentabilidad.
- **📊 Dashboard Interactivo**: Control total con gráficos, estadísticas y clasificación de ofertas.
- **🚫 Filtrado Inteligente**: Ignora accesorios, repuestos y productos fuera de rango.
- **📈 Estadísticas Completas**: Media, mediana, desviación estándar, IQR y análisis de outliers.

## 🛠️ Instalación (3 Minutos)

### Prerrequisitos
- Python 3.10 o superior
- Una API Key de OpenAI (para la inteligencia)

### Paso 1: Clonar
```bash
git clone https://github.com/tu-usuario/price-smart-ia.git
cd price-smart-ia
```

### Paso 2: Instalar Dependencias
```bash
pip install -r requirements.txt
```

### Paso 3: Configurar
Renombra el archivo de ejemplo y agrega tu API Key:
```bash
cp .env.example .env
# Abre .env y pega tu OPENAI_API_KEY
```

## 🎮 Cómo Usar

### Opción A: Dashboard Visual (Recomendado)
Ejecuta la interfaz web:
```bash
streamlit run frontend/dashboard_simple.py --server.port 8504
```
Abre `http://localhost:8504` en tu navegador.

**Modos de Entrada:**
1. **URL Manual**: Pega el link de un producto de Mercado Libre directamente.
2. **Catálogo Interno**: Selecciona un producto del catálogo (se auto-llena el costo).

**Flujo de Análisis:**
1. Selecciona fuente (URL o Catálogo).
2. Ingresa tu **Costo Real** (para calcular utilidad).
3. Ajusta **Margen Objetivo** y **Tolerancia de Búsqueda**.
4. ¡Analiza! El sistema:
   - Busca +50 competidores
   - Clasifica qué es comparable
   - Calcula rentabilidad real (incluido envío, impuestos, comisiones)
   - Sugiere precio óptimo con ROI

### Opción B: Script de Terminal
Si prefieres línea de comandos:
```bash
python scripts/demo_data_enrichment.py
```

## 🏗️ Arquitectura Técnica

El sistema utiliza una arquitectura de **Agentes Autónomos** con LangGraph:

1. **Scraper**: Extrae HTML crudo (sin API oficial) para ver lo que ve el cliente.
2. **Matching Agent**: Usa GPT-4-Vision para "ver" las fotos y descartar productos diferentes.
3. **Profit Calculator**: Motor de cálculo financiero con tablas de costos 2026.
4. **Dashboard**: Interfaz en Streamlit para visualización de datos.

## 📄 Licencia

Este proyecto es Open Source bajo la licencia MIT. ¡Úsalo para vender más!

---
**Desarrollado con ❤️ para vendedores inteligentes.**
# pricesmart
