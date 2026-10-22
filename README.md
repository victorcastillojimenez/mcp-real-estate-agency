# mcp-real-estate-agency

Servidor MCP personalizado para una agencia inmobiliaria digital española, con interfaz Streamlit
como cliente. El servidor expone 7 herramientas que pueden consumir tanto la aplicación web como
Claude Desktop u otro cliente MCP compatible.

Desarrollado como trabajo del Curso de Especialización en IA y Big Data — Instituto Nebrija (2026).

## El problema que resuelve

Las agencias inmobiliarias manejan múltiples fuentes de datos heterogéneas: catálogo de propiedades,
geolocalización, tipos de cambio, valoraciones comparativas e informes en PDF.
Este proyecto las unifica en un único servidor MCP, de modo que cualquier cliente compatible
(aplicación web o agente de IA) accede a todas las operaciones con la misma interfaz.

## Stack

| Capa | Tecnología |
|---|---|
| Servidor MCP | Python 3.11, FastMCP |
| Cliente web | Streamlit >= 1.32 |
| Base de datos | SQLite (aiosqlite para operaciones async) |
| Geolocalización | Nominatim / OpenStreetMap (sin clave de API) |
| Tipos de cambio | Frankfurter API / BCE (sin clave de API) |
| Generación de PDF | ReportLab |
| Mapas interactivos | Folium + streamlit-folium |
| Gráficas | Plotly |

## Arquitectura

```
Streamlit (cliente)  ──stdio──►  MCP Server (FastMCP)
                                        │
                       ┌────────────────┼────────────────┐
                       │                │                 │
                 api_tools.py   integration_tools.py  logic_tools.py
                 Nominatim,     SQLite, ReportLab      Hipotecas,
                 Frankfurter                           valoración,
                                                       análisis
                                        │
                                   db.py (SQLite)
```

## Herramientas MCP disponibles

| Herramienta | Descripción |
|---|---|
| `geocode_address` | Devuelve coordenadas y datos de ubicación vía OpenStreetMap |
| `convert_currency` | Convierte importes entre divisas en tiempo real (Banco Central Europeo) |
| `search_properties` | Búsqueda avanzada en catálogo con filtros de precio, ciudad y tipo |
| `generate_property_report` | Genera informe PDF profesional de una propiedad concreta |
| `calculate_mortgage` | Calcula cuotas e intereses con sistema francés de amortización |
| `estimate_property_value` | Valoración por comparables con coeficientes de ajuste de mercado |
| `market_analysis` | Estadísticas del mercado por ciudad con niveles de confianza |

## Cómo ejecutarlo

No se necesitan claves de API. Las APIs externas (Nominatim y Frankfurter) son gratuitas y de acceso público.

```bash
# 1. Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Inicializar la base de datos con datos de muestra
python setup_db.py

# 4. Lanzar la aplicación
streamlit run app/streamlit_app.py
```

La base de datos se pobla con ~27 propiedades ficticias en Madrid, Barcelona, Valencia, Sevilla y Bilbao.

## Uso con Claude Desktop

Para usar el servidor MCP directamente desde Claude Desktop, añade esta entrada en
`claude_desktop_config.json` (en Windows: `%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "inmobiliaria": {
      "command": "C:/ruta/al/proyecto/venv/Scripts/python.exe",
      "args": ["C:/ruta/al/proyecto/mcp_server/server.py"]
    }
  }
}
```

Sustituye `C:/ruta/al/proyecto` por la ruta absoluta donde clonaste el repositorio.
Una vez configurado, Claude Desktop puede llamar directamente a las 7 herramientas del servidor.

## Qué demuestra este proyecto

- Implementación de un servidor MCP personalizado con FastMCP
- Separación de responsabilidades: servidor, herramientas de API, herramientas de integración, lógica de negocio y cliente
- Integración de APIs públicas sin autenticación
- Generación de documentos PDF con ReportLab
- Mapas interactivos con Folium
- Operaciones asíncronas con aiosqlite

## Sobre el código

Proyecto desarrollado durante el curso de especialización. Utilicé herramientas de IA como asistente de programación; el diseño de las herramientas MCP, la estructura del proyecto y la integración son decisión mía.

## Autor

Victor Castillo Jiménez
