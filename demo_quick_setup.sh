#!/bin/bash
# Script rápido para probar la demostración

echo "🚀 PRICESMART - SETUP RÁPIDO PARA DEMOSTRACIÓN"
echo "=============================================="
echo ""

# 1. Cargar catálogo
echo "1️⃣  Cargando catálogo desde CSV..."
uv run python scripts/load_catalog.py "reporte resumen ventas de 2025-10 a 2026-01 Todos.csv"

if [ $? -eq 0 ]; then
    echo "✅ Catálogo cargado exitosamente"
else
    echo "❌ Error cargando catálogo"
    exit 1
fi

echo ""
echo "2️⃣  Validando implementación..."
uv run python scripts/validate_implementation.py

if [ $? -eq 0 ]; then
    echo "✅ Validación completada"
else
    echo "❌ Error en validación"
    exit 1
fi

echo ""
echo "3️⃣  Frontend ya está corriendo en http://localhost:8502"
echo ""
echo "4️⃣  Para probar el endpoint de análisis masivo:"
echo "    curl -X POST 'http://localhost:8000/api/products/catalog/bulk-analyze' \\"
echo "      -H 'Content-Type: application/json' \\"
echo "      -d '{\"price_tolerance\": 0.30, \"skip_low_rotation\": true}'"
echo ""
echo "🎯 Demo lista! Abre http://localhost:8502 en tu navegador"
