"""
server.py
---------
Servidor MCP principal para la aplicación de Gestión Inmobiliaria.

Registra todas las tools y expone el servidor via transporte stdio
para ser consumido por clientes MCP (Streamlit app, Claude Desktop, etc.)

Tools registradas:
    API de terceros:
        - geocode_address    (Nominatim / OpenStreetMap)
        - convert_currency   (Frankfurter API)

    Herramientas existentes:
        - search_properties  (SQLite)
        - generate_property_report (ReportLab PDF)

    Lógica propia:
        - calculate_mortgage
        - estimate_property_value
        - market_analysis    (EXTRA)

Uso:
    python mcp_server/server.py
"""

import os
import sys

# Asegurar que el directorio raíz del proyecto esté en el path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from mcp.server.fastmcp import FastMCP

# Importar todas las tools de los módulos
from mcp_server.tools.api_tools import geocode_address, convert_currency
from mcp_server.tools.integration_tools import search_properties, generate_property_report
from mcp_server.tools.logic_tools import (
    calculate_mortgage,
    estimate_property_value,
    market_analysis
)

# ── Crear el servidor MCP principal ──────────────────────────────────────────
mcp = FastMCP(
    name="InmobiliariaServer",
    instructions="""
    Eres un asistente experto en gestión inmobiliaria para el mercado español.
    
    Tienes acceso a las siguientes herramientas:
    
    📍 DATOS Y LOCALIZACIÓN:
    - geocode_address: Obtén coordenadas y datos de ubicación de cualquier dirección
    - search_properties: Busca propiedades en el catálogo con múltiples filtros
    
    💰 FINANZAS:
    - convert_currency: Convierte precios entre divisas (EUR, USD, GBP, etc.)
    - calculate_mortgage: Calcula cuotas hipotecarias con tabla de amortización
    
    📊 VALORACIÓN Y ANÁLISIS:
    - estimate_property_value: Estima el valor de mercado de una propiedad
    - market_analysis: Analiza estadísticas del mercado inmobiliario por ciudad
    
    📄 DOCUMENTACIÓN:
    - generate_property_report: Genera informes PDF profesionales de propiedades
    
    Responde siempre en español y de forma profesional.
    """,
)

# ── Registrar todas las tools ─────────────────────────────────────────────────
mcp.add_tool(geocode_address)
mcp.add_tool(convert_currency)
mcp.add_tool(search_properties)
mcp.add_tool(generate_property_report)
mcp.add_tool(calculate_mortgage)
mcp.add_tool(estimate_property_value)
mcp.add_tool(market_analysis)


if __name__ == "__main__":
    print("🏢 Iniciando InmobiliariaServer MCP...")
    print(f"   Tools registradas: {len(mcp._tool_manager._tools)}")
    for name in mcp._tool_manager._tools:
        print(f"   ✅ {name}")
    print("\n   Servidor listo. Esperando conexiones via stdio...\n")
    mcp.run(transport="stdio")
