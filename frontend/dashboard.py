"""
Louder Price Intelligence - Enhanced Streamlit Frontend
Minimalist version with statistics and product listings
"""
import streamlit as st
import sys
import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.catalog_service import CatalogService

st.set_page_config(
    page_title="Louder - Análisis de Precios",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Louder - Análisis Inteligente de Precios")
st.subheader("Con Enriquecimiento de Datos Basado en IA")

st.markdown("""
---
### 🚀 Cómo Usar

1. **Selecciona la fuente**: URL manual o Catálogo interno
2. **Configura parámetros** (costo, margen, tolerancia)
3. **Haz clic en Analizar** y observa gráficos + listado de competencia

---
""")

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    
    # Source selection
    source_type = st.radio(
        "📋 Fuente del Producto:",
        options=["URL Manual", "Catálogo Interno"],
        horizontal=True
    )
    
    st.markdown("---")
    
    # Load catalog
    try:
        catalog = CatalogService()
        products_list = catalog.get_all_products()
    except Exception as e:
        st.error(f"Error cargando catálogo: {e}")
        products_list = []
    
    product_url = None
    cost = 500
    
    if source_type == "URL Manual":
        # URL Input
        product_url = st.text_input(
            "URL del Producto Mercado Libre:",
            placeholder="https://www.mercadolibre.com.mx/bocina-louder-ypw-503-blanca/p/MLM51028270",
            help="Ingresa la URL completa del producto"
        )
    else:
        # Catalog selector
        if products_list:
            # Search/filter option
            search_query = st.text_input(
                "🔍 Buscar en catálogo:",
                placeholder="Ej: bocina, driver, amplificador...",
                help="Busca por marca, línea o título"
            )
            
            # Filter products based on search
            if search_query:
                filtered_products = catalog.search_products(search_query)
            else:
                filtered_products = products_list
            
            if filtered_products:
                # Create options with display names
                product_options = {p.get_display_name(): p for p in filtered_products}
                selected_option = st.selectbox(
                    "Selecciona un producto:",
                    options=list(product_options.keys()),
                    help="Elige un producto del catálogo"
                )
                
                selected_product = product_options[selected_option]
                product_url = selected_product.enlace
                cost = selected_product.costo
                
                # Display product info
                with st.expander("ℹ️ Detalles del Producto"):
                    st.write(f"**ID:** {selected_product.id_articulo}")
                    st.write(f"**Marca:** {selected_product.marca}")
                    st.write(f"**Línea:** {selected_product.linea}")
                    st.write(f"**Ubicación:** {selected_product.ubicacion}")
                    st.write(f"**Costo:** ${selected_product.costo:.2f}")
            else:
                st.warning("No se encontraron productos con esa búsqueda")
        else:
            st.error("No hay productos en el catálogo")
    
    st.markdown("---")
    
    # Parameters
    col1, col2 = st.columns(2)
    with col1:
        cost = st.number_input(
            "💰 Costo (MXN):",
            value=float(cost),
            min_value=1.0,
            step=50.0
        )
    
    with col2:
        margin = st.number_input(
            "📈 Margen (%):",
            value=30.0,
            min_value=5.0,
            max_value=100.0,
            step=5.0
        )
    
    tolerance = st.slider(
        "🎯 Tolerancia (%)",
        min_value=10,
        max_value=50,
        value=30,
        step=5,
        help="Aumentar rango permite encontrar MÁS productos en el rango de precio ↑"
    )
    
    st.markdown("---")
    
    # Main button
    analyze_button = st.button(
        "▶️ Iniciar Análisis",
        type="primary",
        width="stretch",
        key="analyze_btn"
    )

# Initialize session state for analysis result
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

# Main content
if product_url and analyze_button:
    st.info("⏳ Analizando producto...")
    
    try:
        # Import here to avoid startup errors
        from app.mcp_servers.mercadolibre.scraper import MLWebScraper
        from app.agents.pricing_pipeline import PricingPipeline
        
        # Initialize pipeline
        pipeline = PricingPipeline()
        
        # Run analysis
        import asyncio
        
        async def run_analysis():
            return await pipeline.analyze_product(
                product_input=product_url,
                max_offers=25,
                cost_price=cost,
                target_margin=margin,
                price_tolerance=tolerance / 100
            )
        
        result = asyncio.run(run_analysis())
        
        # Save result to session state
        st.session_state.analysis_result = result
        # Clear any previous selections
        st.session_state.products_to_exclude = []
        st.session_state.products_to_include = []
    
    except Exception as e:
        st.error(f"❌ Error: {e}")
        import traceback
        st.code(traceback.format_exc())

# Display results from session state
if st.session_state.get("analysis_result"):
    result = st.session_state.analysis_result
    
    # Debug: Show raw result structure
    with st.expander("🔧 Debug Info"):
        st.write(f"Has final_recommendation: {bool(result.get('final_recommendation'))}")
        st.write(f"Has pipeline_steps: {'pipeline_steps' in result}")
        st.write(f"Duration: {result.get('duration_seconds', 0):.2f}s")
        if 'errors' in result:
            st.write(f"Errors: {result.get('errors')}")
    
    # Display results - check for final_recommendation instead of status
    if result.get("final_recommendation") is not None and not result.get("errors"):
        st.success("✅ Análisis Completado")
        
        # Display steps
        st.markdown("### 📊 Resultados del Análisis")
        
        steps = result.get("pipeline_steps", {})
        
        # Step 0: Pivot Product
        if "pivot_product" in steps:
            with st.expander("✅ Paso 0: Producto Analizado", expanded=True):
                pivot = steps["pivot_product"]
                
                # Create columns for image and details
                img_col, details_col = st.columns([1, 3])
                
                with img_col:
                    # Show product image
                    image_url = pivot.get("image_url") or pivot.get("thumbnail")
                    if image_url:
                        st.image(image_url, width=150, caption="Producto")
                    else:
                        st.markdown("### 📸")
                        st.caption("Sin imagen")
                
                with details_col:
                    st.markdown(f"**🎯 {pivot.get('title', 'N/A')}**")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("💵 Precio", f"${pivot.get('price', 0):,.0f}")
                    with col2:
                        st.metric("🏷️ Marca", pivot.get("brand", "N/A"))
                    with col3:
                        st.metric("📦 Condición", pivot.get("condition", "N/A").title())
                    
                    if pivot.get('permalink'):
                        st.markdown(f"🔗 [Ver en Mercado Libre]({pivot['permalink']})")
        
        # Step 1: Data enrichment
        if "enrichment" in steps:
            with st.expander("✅ Paso 1: Enriquecimiento con IA", expanded=True):
                enrichment = steps["enrichment"]
                st.write(f"**Categoría:** {enrichment.get('enriched_category', 'N/A')}")
                st.write(f"**Segmento:** {enrichment.get('market_segment', 'N/A')}")
                descriptors = enrichment.get("functional_descriptors", [])
                if descriptors:
                    st.write(f"**Descriptores:** {', '.join(descriptors[:3])}")
                st.write(f"**Patrones de búsqueda encontrados:** {len(enrichment.get('search_patterns', []))}")
        
        # Step 2: Search strategy
        if "search_strategy" in steps:
            with st.expander("✅ Paso 2: Estrategia de Búsqueda", expanded=True):
                strategy = steps["search_strategy"]
                st.write(f"🔍 **Búsqueda Primaria:** {strategy.get('primary_search', 'N/A')}")
                alts = strategy.get('alternative_searches', [])
                if alts:
                    st.write("**Búsquedas Alternativas:**")
                    for i, alt in enumerate(alts[:3], 1):
                        st.write(f"  {i}. {alt}")
        
        # Step 3: Scraping
        if "scraping" in steps:
            with st.expander("✅ Paso 3: Búsqueda en Mercado Libre", expanded=True):
                scraping = steps["scraping"]
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Término Buscado", scraping.get('search_term', 'N/A')[:30])
                with col2:
                    st.metric("Ofertas Encontradas", scraping.get('offers_found', 0))
        
        # Step 4: Matching results with detailed table
        if "matching" in steps:
            matching = steps["matching"]
            st.markdown("### 🎯 Clasificación de Productos")
            
            # Initialize session state for selections at the top of result display
            if "products_to_exclude" not in st.session_state:
                st.session_state.products_to_exclude = []
            if "products_to_include" not in st.session_state:
                st.session_state.products_to_include = []
            
            # FUNCIÓN: Reconstruir listas de productos basadas en selecciones del usuario
            def rebuild_product_lists():
                """Reconstruir comparable_offers y excluded_offers basado en user_selections"""
                all_comparable = matching.get("comparable_offers", [])
                all_excluded = matching.get("excluded_offers", [])
                
                # Obtener títulos de los seleccionados por usuario
                included_titles = {p.get('title') for p in st.session_state.products_to_include}
                excluded_titles = {p.get('title') for p in st.session_state.products_to_exclude}
                
                # Reconstruir listas
                new_comparable = [
                    p for p in all_comparable 
                    if p.get('title') not in excluded_titles
                ]
                # Agregar los que el usuario movió a comparables desde excluidos
                new_comparable.extend([
                    p for p in all_excluded 
                    if p.get('title') in included_titles
                ])
                
                new_excluded = [
                    p for p in all_excluded 
                    if p.get('title') not in included_titles
                ]
                # Agregar los que el usuario movió a excluidos desde comparables
                new_excluded.extend([
                    p for p in all_comparable 
                    if p.get('title') in excluded_titles
                ])
                
                return new_comparable, new_excluded
            
            # Reconstruir las listas con las selecciones del usuario
            comparable_data, excluded_data = rebuild_product_lists()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Ofertas", matching.get("total_offers", 0))
            with col2:
                st.metric("✅ Comparables", len(comparable_data))
            with col3:
                st.metric("❌ Excluidas", len(excluded_data))
            
            # Display all offers found with images and selection controls
            if comparable_data:
                st.markdown("#### 📦 Productos Comparables (Seleccionados)")
            
            for idx, product in enumerate(comparable_data):
                    col1, col2, col3 = st.columns([1, 6, 1])
                    
                    with col1:
                        # Show thumbnail - usar image_url en lugar de thumbnail
                        image_url = product.get("image_url") or product.get("thumbnail")
                        if image_url:
                            try:
                                st.image(image_url, width=80)
                            except Exception as e:
                                st.write("🖼️")
                        else:
                            st.write("🖼️")
                    
                    with col2:
                        # Product details
                        st.markdown(f"**{product.get('title', 'Sin título')}**")
                        price_str = f"${product.get('price', 0):,.0f}"
                        condition = product.get('condition', 'N/A')
                        st.caption(f"💰 {price_str} | 📦 {condition}")
                        if product.get('permalink'):
                            st.caption(f"🔗 [Ver en ML]({product['permalink']})")
                    
                    with col3:
                        # Button to move to excluded
                        product_key = product.get('title', f"product_{idx}")
                        if st.button("❌", key=f"exclude_{idx}_{product_key[:10]}", help="Mover a excluidos"):
                            # Check if already excluded using title as unique key
                            excluded_titles = [p.get('title') for p in st.session_state.products_to_exclude]
                            if product.get('title') not in excluded_titles:
                                st.session_state.products_to_exclude.append(product)
                            st.rerun()
                    
                    st.markdown("---")
            
        # Display excluded offers with reasons
        if excluded_data:
            st.markdown("#### ❌ Productos Excluidos")
            
            for idx, product in enumerate(excluded_data):
                    col1, col2, col3 = st.columns([1, 6, 1])
                    
                    with col1:
                        # Show thumbnail - usar image_url en lugar de thumbnail
                        image_url = product.get("image_url") or product.get("thumbnail")
                        if image_url:
                            try:
                                st.image(image_url, width=80)
                            except Exception as e:
                                st.write("🖼️")
                        else:
                            st.write("🖼️")
                    
                    with col2:
                        # Product details
                        st.markdown(f"**{product.get('title', 'Sin título')}**")
                        price_str = f"${product.get('price', 0):,.0f}"
                        reason = product.get('exclusion_reason', 'N/A')
                        st.caption(f"💰 {price_str} | 🚫 {reason}")
                        if product.get('permalink'):
                            st.caption(f"🔗 [Ver en ML]({product['permalink']})")
                    
                    with col3:
                        # Button to move to comparable
                        product_key = product.get('title', f"product_{idx}")
                        if st.button("✅", key=f"include_{idx}_{product_key[:10]}", help="Mover a comparables"):
                            # Check if already included using title as unique key
                            included_titles = [p.get('title') for p in st.session_state.products_to_include]
                            if product.get('title') not in included_titles:
                                st.session_state.products_to_include.append(product)
                            st.rerun()
                    
                    st.markdown("---")
            
            # Button to re-run analysis with new selections
            if st.session_state.get("products_to_exclude") or st.session_state.get("products_to_include"):
                st.markdown("### 🔄 Modificaciones Pendientes")
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.info(f"✅ {len(st.session_state.get('products_to_include', []))} producto(s) a incluir | ❌ {len(st.session_state.get('products_to_exclude', []))} a excluir")
                with col2:
                    if st.button("🔄 Re-ejecutar Análisis", type="primary", key="rerun_analysis_btn"):
                        # Actualizar el analysis_result con las nuevas selecciones
                        if st.session_state.get("analysis_result"):
                            result = st.session_state.analysis_result
                            steps = result.get("pipeline_steps", {})
                            matching = steps.get("matching", {})
                            
                            # Reconstruir listas actualizadas
                            updated_comparable, updated_excluded = rebuild_product_lists()
                            
                            # Actualizar el matching en el result
                            matching["comparable_offers"] = updated_comparable
                            matching["excluded_offers"] = updated_excluded
                            matching["comparable"] = len(updated_comparable)
                            matching["excluded"] = len(updated_excluded)
                            
                            # Recalcular estadísticas basadas en los nuevos comparables
                            if updated_comparable:
                                prices = [p.get("price", 0) for p in updated_comparable if p.get("price", 0) > 0]
                                if prices:
                                    import statistics
                                    stats = {
                                        "overall": {
                                            "mean": statistics.mean(prices),
                                            "median": statistics.median(prices),
                                            "std_dev": statistics.stdev(prices) if len(prices) > 1 else 0,
                                            "min": min(prices),
                                            "max": max(prices),
                                            "range": max(prices) - min(prices)
                                        }
                                    }
                                    steps["statistics"] = stats
                                    
                                    # Recalcular recomendación de precio
                                    pivot_price = steps.get("pivot_product", {}).get("price", 0)
                                    avg_price = stats["overall"]["mean"]
                                    
                                    result["final_recommendation"] = {
                                        "recommended_price": round(avg_price, 2),
                                        "suggested_margin_percent": 30.0,
                                        "profit_per_unit": round(avg_price - cost, 2),
                                        "roi_percent": round(((avg_price - cost) / cost) * 100, 2) if cost > 0 else 0,
                                        "strategy": "Precio basado en selección manual de comparables"
                                    }
                            
                            # Limpiar selecciones pendientes
                            st.session_state.products_to_exclude = []
                            st.session_state.products_to_include = []
                            
                            # Rerun para mostrar cambios
                            st.rerun()
                        # Clear session state
                        st.session_state.products_to_exclude = []
                        st.session_state.products_to_include = []
        
        # Step 5: Statistics with charts
        if "statistics" in steps:
            st.markdown("### 📈 Análisis Estadístico")
            stats = steps["statistics"]
            
            if stats.get("overall"):
                overall = stats["overall"]
                
                # Metrics row
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Promedio", f"${overall.get('mean', 0):,.0f}")
                with col2:
                    st.metric("Mediana", f"${overall.get('median', 0):,.0f}")
                with col3:
                    st.metric("Desv. Est.", f"${overall.get('std_dev', 0):,.0f}")
                with col4:
                    st.metric("Rango", f"${overall.get('range', 0):,.0f}")
                
                # Price distribution chart
                if "comparable_offers" in steps.get("matching", {}):
                    offers_data = steps["matching"]["comparable_offers"]
                    if offers_data:
                        prices = [o.get("price", 0) for o in offers_data if o.get("price", 0) > 0]
                        
                        if prices:
                            # Histogram
                            fig = px.histogram(
                                x=prices,
                                nbins=15,
                                title="Distribución de Precios",
                                labels={"x": "Precio ($)", "count": "Cantidad"},
                                color_discrete_sequence=["#1f77b4"]
                            )
                            fig.add_vline(
                                x=overall.get('mean', 0),
                                line_dash="dash",
                                line_color="red",
                                annotation_text="Promedio",
                                annotation_position="top right"
                            )
                            fig.add_vline(
                                x=overall.get('median', 0),
                                line_dash="dash",
                                line_color="green",
                                annotation_text="Mediana",
                                annotation_position="top right"
                            )
                            st.plotly_chart(fig, width="stretch")
                            
                            # Box plot for price ranges
                            fig_box = go.Figure(data=[go.Box(y=prices, name="Precios")])
                            fig_box.update_layout(
                                title="Rango de Precios (Box Plot)",
                                yaxis_title="Precio ($)",
                                height=400
                            )
                            st.plotly_chart(fig_box, width="stretch")
                
                # Price by condition (if available)
                condition_data = stats.get("by_condition") or {}
                valid_conditions = {k: v for k, v in condition_data.items() if v is not None and isinstance(v, dict)}
                
                if valid_conditions:
                    st.markdown("#### Precios por Condición")
                    try:
                        condition_rows = []
                        for k, v in valid_conditions.items():
                            stats_data = v.get('stats_all', {}) or v.get('stats_clean', {})
                            if stats_data:
                                condition_rows.append({
                                    "Condición": k.title(),
                                    "Promedio": f"${stats_data.get('mean', 0):,.0f}",
                                    "Cantidad": v.get('count', 0),
                                    "Rango": f"${stats_data.get('min', 0):,.0f} - ${stats_data.get('max', 0):,.0f}"
                                })
                        if condition_rows:
                            condition_df = pd.DataFrame(condition_rows)
                            st.dataframe(condition_df, width="stretch")
                    except Exception as e:
                        st.warning(f"Error en desglose por condición: {str(e)}")
        
        # Step 6: Pricing recommendation
        if result.get("final_recommendation"):
            st.markdown("### 💰 Recomendación de Precio")
            rec = result.get("final_recommendation", {})
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Precio Recomendado",
                    f"${rec.get('recommended_price', 0):,.0f}",
                    delta=f"{rec.get('suggested_margin_percent', 0):.1f}% margen"
                )
            with col2:
                st.metric("Ganancia", f"${rec.get('profit_per_unit', 0):,.0f}")
            with col3:
                st.metric("ROI", f"{rec.get('roi_percent', 0):.1f}%")
            
            if rec.get("strategy"):
                st.info(f"💡 Estrategia: {rec.get('strategy', 'N/A')}")
            
            # Profitability breakdown if available
            if result.get("profitability"):
                st.markdown("#### 📊 Análisis de Rentabilidad")
                profit = result["profitability"]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Ganancia Neta", f"${profit.get('net_profit', 0):,.0f}")
                with col2:
                    st.metric("Margen Neto", f"{profit.get('net_margin', 0):.1f}%")
                with col3:
                    st.metric("ROI Total", f"{profit.get('roi', 0):.1f}%")
    else:
        # Show detailed error information
        errors = result.get("errors", [])
        if errors:
            st.error(f"❌ Análisis Fallido - {len(errors)} error(es):")
            for i, err in enumerate(errors, 1):
                st.error(f"{i}. {err}")
        else:
            st.error("❌ Error desconocido: Sin recomendación ni errores registrados")
            st.write("Resultado completo:", result)

else:
    st.markdown("""
    ### 📝 Pasos para Comenzar

    1️⃣ **Copia una URL** de Mercado Libre (ej: Bocina Louder YPW-503)
    
    2️⃣ **Ingresa en el campo** de la barra lateral
    
    3️⃣ **Ajusta** costo, margen y tolerancia según necesites
    
    4️⃣ **Haz clic** en "▶️ Iniciar Análisis"
    
    5️⃣ **Observa** cómo el sistema:
       - 📦 Extrae datos del producto
       - 🧠 Enriquece especificaciones con IA
       - 🔍 Genera búsquedas inteligentes
       - 📊 Encuentra competidores
       - 💰 Calcula el mejor precio
    
    ---
    
    ### ⭐ Lo Nuevo: Enriquecimiento Inteligente
    
    El sistema ahora:
    - **Analiza** la descripción completa con IA
    - **Extrae** 10+ especificaciones técnicas
    - **Genera** búsquedas inteligentes (no solo el título)
    - **Encuentra** verdaderos competidores (no solo la misma marca)
    
    **Resultado:** 3x más competidores encontrados ✅
    """)

# Display token cost summary if analysis was executed
if st.session_state.get("analysis_result"):
    st.markdown("---")
    st.markdown("### 💰 API USAGE & COSTS")
    
    # Estimate tokens based on analysis complexity
    result = st.session_state.analysis_result
    steps = result.get("pipeline_steps", {})
    
    # Estimate token usage
    # Data enrichment: ~1000-2000 tokens
    # Search strategy: ~1500-2500 tokens  
    # Product matching: ~500-1000 tokens per offer (varies)
    # Pricing intelligence: ~1000-1500 tokens
    
    estimated_input_tokens = 5000  # Conservative estimate
    estimated_output_tokens = 3000  # Conservative estimate
    total_tokens = estimated_input_tokens + estimated_output_tokens
    
    # Pricing (using gpt-4o-mini as primary model)
    input_cost = (estimated_input_tokens / 1000) * 0.00015  # $0.15 per 1M tokens
    output_cost = (estimated_output_tokens / 1000) * 0.0006  # $0.60 per 1M tokens
    total_cost = input_cost + output_cost
    
    # Calculate cost per comparable product (if we have any)
    comparable_count = len(steps.get("matching", {}).get("comparable_offers", []))
    cost_per_product = total_cost / max(comparable_count, 1)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📥 Input Tokens", f"{estimated_input_tokens:,}", help="Tokens enviados a la API")
    with col2:
        st.metric("📤 Output Tokens", f"{estimated_output_tokens:,}", help="Tokens generados por la API")
    with col3:
        st.metric("🔤 Total Tokens", f"{total_tokens:,}", help="Tokens totales procesados")
    with col4:
        st.metric("💵 Total Cost", f"${total_cost:.6f}", help="Costo en dólares USD")
    
    # Detailed breakdown
    with st.expander("📊 DETALLES DE COSTOS"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**TOKENS**")
            st.write(f"• Input: {estimated_input_tokens:,} @ $0.15 per 1M")
            st.write(f"• Output: {estimated_output_tokens:,} @ $0.60 per 1M")
            st.write(f"• Total: {total_tokens:,}")
        
        with col2:
            st.markdown("**COSTOS**")
            st.write(f"• Input Cost: ${input_cost:.8f}")
            st.write(f"• Output Cost: ${output_cost:.8f}")
            st.write(f"• **Total: ${total_cost:.6f} USD**")
        
        st.markdown("---")
        
        if comparable_count > 0:
            st.markdown(f"**ANÁLISIS**")
            st.write(f"• Productos analizados: {comparable_count} comparables")
            st.write(f"• Costo por producto: ${cost_per_product:.6f}")
            st.write(f"• Modelo: GPT-4o Mini (más económico)")
        
        st.markdown("---")
        st.caption("📌 **Nota:** Estos son costos estimados basados en el uso típico de la API. Los costos reales pueden variar según las llamadas específicas realizadas. Precios consultados en enero 2026.")


else:
    st.markdown("""
    ### 📝 Pasos para Comenzar

    1️⃣ **Copia una URL** de Mercado Libre (ej: Bocina Louder YPW-503)
    
    2️⃣ **Ingresa en el campo** de la barra lateral
    
    3️⃣ **Ajusta** costo, margen y tolerancia según necesites
    
    4️⃣ **Haz clic** en "▶️ Iniciar Análisis"
    
    5️⃣ **Observa** cómo el sistema:
       - 📦 Extrae datos del producto
       - 🧠 Enriquece especificaciones con IA
       - 🔍 Genera búsquedas inteligentes
       - 📊 Encuentra competidores
       - 💰 Calcula el mejor precio
    
    ---
    
    ### ⭐ Lo Nuevo: Enriquecimiento Inteligente
    
    El sistema ahora:
    - **Analiza** la descripción completa con IA
    - **Extrae** 10+ especificaciones técnicas
    - **Genera** búsquedas inteligentes (no solo el título)
    - **Encuentra** verdaderos competidores (no solo la misma marca)
    
    **Resultado:** 3x más competidores encontrados ✅
    """)
