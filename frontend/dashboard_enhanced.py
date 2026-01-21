"""
Louder Price Intelligence - Enhanced Streamlit Frontend
Shows analysis progress step-by-step with data enrichment
"""
import streamlit as st
import asyncio
import sys
import os
from pathlib import Path
import time

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Page config
st.set_page_config(
    page_title="Louder - Análisis de Precios",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
.step-container {
    background-color: #f0f2f6;
    padding: 15px;
    border-radius: 8px;
    margin: 10px 0;
    border-left: 4px solid #1f77b4;
}
.step-complete {
    border-left: 4px solid #2ca02c;
}
.step-running {
    border-left: 4px solid #ff7f0e;
}
.metric-card {
    background-color: white;
    padding: 15px;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
}
.spec-item {
    background-color: #f9f9f9;
    padding: 10px;
    margin: 5px 0;
    border-radius: 5px;
    border-left: 3px solid #1f77b4;
}
</style>
""", unsafe_allow_html=True)

def main():
    st.title("📊 Louder - Análisis Inteligente de Precios")
    st.markdown("Sistema de análisis con enriquecimiento automático de datos")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Input
        product_input = st.text_input(
            "🔗 URL del Producto o Descripción",
            placeholder="https://www.mercadolibre.com.mx/...",
            key="product_input"
        )
        
        st.divider()
        
        # Cost and Margin
        cost_price = st.number_input(
            "💰 Costo del Producto (MXN)",
            min_value=0.0,
            step=50.0,
            value=500.0
        )
        
        target_margin = st.slider(
            "📈 Margen Objetivo (%)",
            min_value=10,
            max_value=100,
            value=30,
            step=5
        )
        
        # Price Tolerance
        st.divider()
        st.subheader("🎯 Tolerancia de Precio")
        price_tolerance = st.radio(
            "Rango de búsqueda",
            options=["±10%", "±20%", "±30%", "±40%", "±50%", "Sin filtro"],
            index=2,  # Default ±30%
            help="Rango de precios para buscar competidores"
        )
        
        # Parse tolerance
        tolerance_map = {
            "±10%": 0.10,
            "±20%": 0.20,
            "±30%": 0.30,
            "±40%": 0.40,
            "±50%": 0.50,
            "Sin filtro": 0.0
        }
        tolerance_value = tolerance_map[price_tolerance]
        
        st.divider()
        analyze_button = st.button(
            "▶️ Iniciar Análisis",
            use_container_width=True,
            type="primary"
        )
    
    # Main area
    if analyze_button and product_input:
        run_analysis(product_input, cost_price, target_margin, tolerance_value)
    elif analyze_button:
        st.error("⚠️ Por favor ingresa un URL de producto o descripción")


def run_analysis(product_input: str, cost_price: float, target_margin: float, tolerance_value: float):
    """Run the full analysis with step-by-step progress display."""
    
    try:
        from app.agents.pricing_pipeline import PricingPipeline
        from app.mcp_servers.mercadolibre.scraper import MLWebScraper
        from app.agents.data_enricher import DataEnricherAgent
        from app.agents.search_strategy import SearchStrategyAgent
    except ImportError as e:
        st.error(f"❌ Error importando módulos: {e}")
        return
    
    # Create columns for progress display
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📋 Proceso de Análisis")
    
    # Progress placeholder
    progress_container = st.container()
    
    async def run_full_analysis():
        """Run the complete analysis pipeline."""
        pipeline = PricingPipeline()
        scraper = MLWebScraper()
        enricher = DataEnricherAgent()
        searcher = SearchStrategyAgent()
        
        result = {
            "steps": {},
            "error": None
        }
        
        try:
            # Step 1: Extract Product
            with progress_container:
                st.markdown("### 📥 Paso 1: Extracción de Datos del Producto")
                step1_progress = st.empty()
                step1_status = st.empty()
            
            step1_progress.progress(10)
            step1_status.info("Extrayendo información del producto...")
            
            scraper = MLWebScraper()
            product = await scraper.extract_product_details(product_input)
            
            if not product:
                raise Exception("No se pudo extraer la información del producto")
            
            with progress_container:
                step1_status.success(f"✅ Producto encontrado: {product.title}")
                st.markdown(f"""
                <div class="metric-card">
                <b>ID:</b> {product.product_id} | <b>Precio:</b> ${product.price:,.0f} {product.currency}
                </div>
                """, unsafe_allow_html=True)
            
            # Step 2: Enrich Data
            with progress_container:
                st.divider()
                st.markdown("### 🔍 Paso 2: Enriquecimiento de Datos")
                step2_progress = st.empty()
                step2_status = st.empty()
            
            step2_progress.progress(25)
            step2_status.info("Analizando especificaciones del producto...")
            
            enrichment_result = await enricher.analyze_product(product)
            
            if enrichment_result.get("status") == "success":
                enriched = enrichment_result.get("enriched_specs")
                patterns = enrichment_result.get("search_patterns", [])
                
                with progress_container:
                    step2_status.success("✅ Análisis completado")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Categoría", enriched.category)
                    with col2:
                        st.metric("Segmento", enriched.market_segment)
                    with col3:
                        st.metric("Specs Extraídas", len(enriched.key_specs))
                    
                    # Show specs
                    st.markdown("**📊 Especificaciones Técnicas Extraídas:**")
                    for spec, value in list(enriched.key_specs.items())[:5]:
                        st.markdown(f'<div class="spec-item">• <b>{spec}:</b> {value}</div>', unsafe_allow_html=True)
                    
                    st.markdown("**🎯 Funcionalidad Identificada:**")
                    for desc in enriched.functional_descriptors[:3]:
                        st.markdown(f'<div class="spec-item">• {desc}</div>', unsafe_allow_html=True)
                    
                    st.markdown("**🏪 Segmento de Mercado:**")
                    st.markdown(f'<div class="spec-item">{enriched.market_segment.upper()}</div>', unsafe_allow_html=True)
            else:
                with progress_container:
                    step2_status.warning(f"⚠️ Enriquecimiento parcial: {enrichment_result.get('error')}")
            
            # Step 3: Generate Search Strategy
            with progress_container:
                st.divider()
                st.markdown("### 🔎 Paso 3: Generación de Estrategia de Búsqueda")
                step3_progress = st.empty()
                step3_status = st.empty()
            
            step3_progress.progress(40)
            step3_status.info("Generando términos de búsqueda inteligentes...")
            
            search_strategy = searcher.generate_search_terms(product)
            
            with progress_container:
                step3_status.success("✅ Estrategia generada")
                
                st.markdown("**🔍 Búsqueda Primaria:**")
                st.markdown(f'<div class="metric-card" style="font-size: 18px; font-weight: bold; background-color: #e8f4f8;">{search_strategy.get("primary_search")}</div>', unsafe_allow_html=True)
                
                st.markdown("**🔄 Búsquedas Alternativas:**")
                for i, alt in enumerate(search_strategy.get("alternative_searches", []), 1):
                    st.markdown(f'<div class="spec-item">{i}. {alt}</div>', unsafe_allow_html=True)
                
                st.markdown("**🎯 Especificaciones para Validación:**")
                specs_str = " | ".join(search_strategy.get("key_specs", [])[:4])
                st.markdown(f'<div class="spec-item">{specs_str}</div>', unsafe_allow_html=True)
            
            # Step 4-7: Run Full Pipeline
            with progress_container:
                st.divider()
                st.markdown("### ⚙️ Paso 4-7: Análisis Completo")
                overall_progress = st.progress(50)
                overall_status = st.empty()
            
            overall_status.info("Ejecutando análisis completo del pipeline...")
            
            pipeline_result = await pipeline.analyze_product(
                product_input=product_input,
                max_offers=25,
                cost_price=cost_price,
                target_margin=target_margin,
                price_tolerance=tolerance_value
            )
            
            with progress_container:
                overall_progress.progress(100)
                
                # Show pipeline steps
                st.markdown("**📊 Detalles del Pipeline:**")
                
                steps = pipeline_result.get("pipeline_steps", {})
                
                # Scraping
                if "scraping" in steps:
                    scrape = steps["scraping"]
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Ofertas Encontradas", scrape.get("offers_found", 0))
                    with col2:
                        st.metric("Estrategia", scrape.get("strategy", "N/A"))
                    with col3:
                        if scrape.get("price_filter_applied"):
                            st.metric("Filtro Precio", f"${scrape.get('price_min'):,.0f} - ${scrape.get('price_max'):,.0f}")
                
                # Matching
                if "matching" in steps:
                    match = steps["matching"]
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Ofertas", match.get("total_offers", 0))
                    with col2:
                        st.metric("Comparables", match.get("comparable", 0))
                    with col3:
                        st.metric("Excluidas", match.get("excluded", 0))
                
                # Statistics
                if "statistics" in steps:
                    stats = steps["statistics"]
                    overall_stats = stats.get("overall", {})
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Precio Promedio", f"${overall_stats.get('mean_price', 0):,.0f}")
                    with col2:
                        st.metric("Mediana", f"${overall_stats.get('median_price', 0):,.0f}")
                    with col3:
                        st.metric("Desv. Est.", f"${overall_stats.get('std_dev', 0):,.0f}")
                
                overall_status.success("✅ Análisis completado")
            
            # Final Recommendation
            with progress_container:
                st.divider()
                st.markdown("### 💡 Paso 8: Recomendación de Precio")
                
                recommendation = pipeline_result.get("final_recommendation")
                if recommendation:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            "💰 Precio Recomendado",
                            f"${recommendation.get('recommended_price', 0):,.0f}",
                            delta=f"{recommendation.get('margin_percent', 0):.1f}% margen"
                        )
                    with col2:
                        st.metric(
                            "🎯 Estrategia",
                            recommendation.get("strategy", "N/A"),
                            help="Estrategia de precios recomendada"
                        )
                    
                    if "reasoning" in recommendation:
                        with st.expander("📖 Ver Razonamiento"):
                            st.write(recommendation["reasoning"])
                
                # Profitability
                if "profitability" in pipeline_result:
                    prof = pipeline_result["profitability"]
                    st.divider()
                    st.markdown("### 📈 Análisis de Rentabilidad")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("💰 Ganancia Neta", f"${prof.get('net_profit', 0):,.0f}")
                    with col2:
                        st.metric("📊 Margen Neto", f"{prof.get('net_margin', 0):.1f}%")
                    with col3:
                        st.metric("📈 ROI", f"{prof.get('roi', 0):.1f}%")
                    with col4:
                        st.metric("💵 Costo", f"${cost_price:,.0f}")
            
            # Errors
            if pipeline_result.get("errors"):
                st.warning("⚠️ Advertencias:")
                for error in pipeline_result.get("errors"):
                    st.write(f"• {error}")
        
        except Exception as e:
            st.error(f"❌ Error en análisis: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    # Run async function
    asyncio.run(run_full_analysis())


if __name__ == "__main__":
    main()
