# 📤 Release Notes v1.2.0 - Ready for Deployment

**Versión:** 1.2.0  
**Fecha:** 21 de Enero, 2026  
**Status:** ✅ LISTO PARA USAR / PULL / DEPLOY  
**Commit:** `5b7ed14`

---

## 🎯 ¿Qué cambió?

### 💰 **Profitabilidad Real Visible**
Antes: `Ganancia: $0, ROI: 0%` ❌  
Ahora: `Ganancia: $337.68, ROI: 46.4%` ✅

Esto es real después de:
- Comisión Mercado Libre (15%)
- Envío (Mercado Envíos 2026)
- Impuestos (ISR 2.5% + IVA 8%)
- Costo del producto

### 📦 **Catálogo Interno**
Nueva funcionalidad: Elige productos de un catálogo interno sin escribir URLs.

**Dos modos en el dashboard:**
- 🔗 **URL Manual**: Pega la URL de Mercado Libre (como siempre)
- 📋 **Catálogo Interno**: Selecciona de 12 productos + costo auto-cargado

### 🔍 **Más Competidores (6 → 50)**
Ahora busca hasta 50 competidores en lugar de 6.

### 🔒 **API Keys Protegidas**
Mejorado `.gitignore` para evitar exponer `OPENAI_API_KEY` accidentalmente.

---

## 📥 Cómo Obtener Esta Versión

### Opción 1: Clonar Directamente
```bash
git clone https://github.com/tu-usuario/price-smart-ia.git
cd price-smart-ia
```

El commit más reciente ya contiene los cambios.

### Opción 2: Pull de Cambios (Si ya tienes el repo)
```bash
git pull origin main
```

---

## 🚀 Cómo Usar

### 1. Instalar Dependencias (Primera Vez)
```bash
pip install -r requirements.txt
```

### 2. Configurar API Key
```bash
# En Windows
set OPENAI_API_KEY=sk-...
# O copiar a .env (nunca lo comitees)
```

### 3. Ejecutar Dashboard
```bash
streamlit run frontend/dashboard_simple.py --server.port 8504
```

Abre: `http://localhost:8504`

### 4. Analizar Producto

**Modo 1 - URL Manual:**
1. Selecciona "URL Manual"
2. Pega URL de Mercado Libre
3. Ingresa Costo, Margen, Tolerancia
4. Haz clic "▶️ Iniciar Análisis"

**Modo 2 - Catálogo Interno:**
1. Selecciona "Catálogo Interno"
2. Busca o selecciona un producto
3. El costo se auto-carga
4. Ajusta Margen y Tolerancia si necesitas
5. Haz clic "▶️ Iniciar Análisis"

---

## ✅ Verificación: Sin API Keys Expuestas

```bash
# Verificar que no hay API keys en el código
git log --all -S "sk-" --oneline
# (Debería estar vacío)

# Verificar archivos ignorados
git check-ignore -v *.env .env.local OPENAI_API_KEY
# (Deberían estar en .gitignore)
```

**Resultado Esperado:** ✅ NINGUNA API KEY en historial de git

---

## 📊 Archivos Principales

| Archivo | Propósito |
|---------|-----------|
| `frontend/dashboard_simple.py` | Dashboard Streamlit mejorado |
| `backend/app/services/catalog_service.py` | Gestor de catálogo CSV |
| `backend/data/productos_catalogo.csv` | Datos internos 12 productos |
| `backend/app/agents/pricing_intelligence.py` | Agente con campos de profitabilidad |
| `backend/app/agents/pricing_pipeline.py` | Orquestador con enriquecimiento |
| `README.md` | Documentación actualizada |
| `CHANGELOG.md` | Histórico de versiones |

---

## 🎓 Para Equipo / Academia

Si necesitas compartir esto:

**✅ SEGURO COMPARTIR:**
- Código fuente completo
- Documentación
- Resultados de análisis
- Estructura del proyecto
- Historico de commits

**❌ NUNCA COMPARTIR:**
- Archivo `.env` con claves
- `OPENAI_API_KEY` en texto
- Credenciales personales
- Tokens ML

**Control:** Usa `git check-ignore -v <file>` para verificar qué NO se commitea.

---

## 🐛 Si Algo No Funciona

### Dashboard no inicia
```bash
# Revisar Python
python --version  # Debe ser 3.10+

# Revisar Streamlit
pip install --upgrade streamlit

# Ejecutar con debug
streamlit run frontend/dashboard_simple.py --logger.level=debug
```

### API Key Error
```bash
# Verificar que la variable de entorno existe
echo $OPENAI_API_KEY  # Windows: echo %OPENAI_API_KEY%

# Si no, configurarla
export OPENAI_API_KEY=sk-...
```

### Catálogo No Carga
```bash
# Verificar que el archivo existe
ls -la backend/data/productos_catalogo.csv

# Si no existe, crear desde plantilla
cp backend/data/productos_catalogo.csv.example backend/data/productos_catalogo.csv
```

---

## 🔄 Próximo Release (v1.3.0)

- [ ] Persistencia en base de datos
- [ ] API REST para queries
- [ ] Alertas de precios
- [ ] Integración Slack
- [ ] Sistema de favoritos

---

## 📧 Soporte

Si encuentras problemas:
1. Verifica el `.env` esté configurado (pero NO commitees)
2. Ejecuta `git status` para ver archivos sin trackear
3. Revisa `git log -p` para ver cambios en archivos específicos
4. Abre un issue con el error exact

---

**✅ Estado Final:** LISTO PARA GITHUB / PRODUCCIÓN  
**Cambios Pendientes:** 0  
**API Keys Expuestas:** 0 ✓  
**Tests Manuales:** ✓ Completados  

🚀 **¡A vender más!**
