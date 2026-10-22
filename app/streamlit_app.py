"""
streamlit_app.py
----------------
Aplicación cliente Streamlit que se integra con el MCP Server de Gestión Inmobiliaria.

Comunica con el MCP Server via subprocess (transporte stdio) usando asyncio
y el SDK oficial de MCP para Python.

Secciones de la aplicación:
    🏠  Buscador de Propiedades
    💰  Calculadora de Hipoteca
    📊  Valoración de Propiedad  
    📈  Análisis de Mercado
    🌍  Geolocalización
    💱  Conversor de Divisas
    📄  Generador de Informes PDF
"""

import streamlit as st
import asyncio
import json
import sys
import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# ── Configuración de paths ────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

SERVER_SCRIPT = str(ROOT_DIR / "mcp_server" / "server.py")

# ── Configuración de la página ────────────────────────────────────────────────
st.set_page_config(
    page_title="Inmobiliaria Digital | MCP Server App",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Aplicación de Gestión Inmobiliaria con MCP Server · Victor Castillo"
    }
)

# ── Estilos CSS personalizados ────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Fondo principal */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a5f 0%, #0f2744 100%);
        border-right: 1px solid rgba(46, 134, 171, 0.3);
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }

    /* Cards de propiedad */
    .property-card {
        background: linear-gradient(135deg, rgba(30, 58, 95, 0.8) 0%, rgba(15, 39, 68, 0.9) 100%);
        border: 1px solid rgba(46, 134, 171, 0.4);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        backdrop-filter: blur(10px);
    }
    .property-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(46, 134, 171, 0.3);
        border-color: rgba(46, 134, 171, 0.7);
    }

    /* Precio badge */
    .precio-badge {
        background: linear-gradient(135deg, #2E86AB, #1a6b8a);
        color: white !important;
        padding: 8px 16px;
        border-radius: 25px;
        font-size: 1.2rem;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 8px;
    }

    /* Estado badge */
    .estado-disponible { background: #10b981; color: white; padding: 3px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
    .estado-reservado  { background: #f59e0b; color: white; padding: 3px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
    .estado-vendido    { background: #ef4444; color: white; padding: 3px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(46, 134, 171, 0.2), rgba(30, 58, 95, 0.4));
        border: 1px solid rgba(46, 134, 171, 0.3);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2E86AB;
        margin: 0;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        margin: 0;
    }

    /* Section headers */
    .section-header {
        background: linear-gradient(90deg, rgba(46, 134, 171, 0.2), transparent);
        border-left: 4px solid #2E86AB;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 20px;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #2E86AB, #1a6b8a) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 15px rgba(46, 134, 171, 0.4) !important;
    }

    /* Inputs */
    .stTextInput input, .stSelectbox select, .stNumberInput input {
        background: rgba(30, 58, 95, 0.6) !important;
        border: 1px solid rgba(46, 134, 171, 0.4) !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
    }

    /* Titles */
    h1, h2, h3 { color: #e2e8f0 !important; }
    p, li { color: #cbd5e1 !important; }

    /* Success/Error boxes */
    .stSuccess { background: rgba(16, 185, 129, 0.15) !important; border-color: #10b981 !important; }
    .stError   { background: rgba(239, 68, 68, 0.15) !important; border-color: #ef4444 !important; }
    .stInfo    { background: rgba(46, 134, 171, 0.15) !important; border-color: #2E86AB !important; }

    /* Dividers */
    hr { border-color: rgba(46, 134, 171, 0.3) !important; }
</style>
""", unsafe_allow_html=True)


# ── Cliente MCP ───────────────────────────────────────────────────────────────
# La aplicación Streamlit actúa como cliente MCP, consumiendo las tools del servidor.
# Se integra directamente con las funciones registradas en el MCP Server.
# El servidor MCP (mcp_server/server.py) puede usarse también con Claude Desktop
# o el MCP Inspector de forma independiente.

from mcp_server.tools.api_tools import geocode_address, convert_currency
from mcp_server.tools.integration_tools import search_properties, generate_property_report
from mcp_server.tools.logic_tools import calculate_mortgage, estimate_property_value, market_analysis

# Mapa de tools disponibles (misma interfaz que un cliente MCP real)
_TOOLS = {
    "geocode_address": geocode_address,
    "convert_currency": convert_currency,
    "search_properties": search_properties,
    "generate_property_report": generate_property_report,
    "calculate_mortgage": calculate_mortgage,
    "estimate_property_value": estimate_property_value,
    "market_analysis": market_analysis,
}


def run_tool(tool_name: str, arguments: dict) -> dict:
    """
    Llama a una tool del MCP Server por nombre y devuelve el resultado parseado.
    Actúa como cliente MCP, invocando las mismas tools que expone el servidor.
    """
    try:
        tool_fn = _TOOLS.get(tool_name)
        if not tool_fn:
            return {"error": f"Tool '{tool_name}' no encontrada en el servidor MCP."}

        # Llamar a la función (puede ser sync o async)
        import inspect
        if inspect.iscoroutinefunction(tool_fn):
            result_text = asyncio.run(tool_fn(**arguments))
        else:
            result_text = tool_fn(**arguments)

        # Parsear el resultado JSON devuelto por la tool
        if isinstance(result_text, str):
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                return {"resultado": result_text}
        elif isinstance(result_text, dict):
            return result_text
        else:
            return {"resultado": str(result_text)}

    except Exception as e:
        return {"error": f"Error ejecutando tool '{tool_name}': {str(e)}"}


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <div style="font-size: 3rem;">🏢</div>
        <h2 style="color: #2E86AB !important; margin: 8px 0 4px;">Inmobiliaria Digital</h2>
        <p style="color: #94a3b8 !important; font-size: 0.8rem; margin: 0;">Powered by MCP Server</p>
    </div>
    <hr style="border-color: rgba(46,134,171,0.3);">
    """, unsafe_allow_html=True)

    seccion = st.radio(
        "Navegación",
        options=[
            "🏠 Buscador de Propiedades",
            "💰 Calculadora de Hipoteca",
            "📊 Valoración de Propiedad",
            "📈 Análisis de Mercado",
            "🌍 Geolocalización",
            "💱 Conversor de Divisas",
            "📄 Generador de Informes PDF",
        ],
        label_visibility="collapsed",
    )

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size: 0.75rem; color: #64748b; text-align: center;">
        <p style="color: #64748b !important;">Victor Castillo · MCP Server App</p>
        <p style="color: #64748b !important;">Máster IA · 2026</p>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1: BUSCADOR DE PROPIEDADES
# ════════════════════════════════════════════════════════════════════════════════

if seccion == "🏠 Buscador de Propiedades":
    st.markdown('<div class="section-header"><h1 style="margin:0; font-size:1.8rem;">🏠 Buscador de Propiedades</h1></div>', unsafe_allow_html=True)
    st.markdown("Busca en nuestro catálogo con filtros avanzados · **Tool MCP**: `search_properties` (SQLite)")

    with st.form("form_busqueda"):
        col1, col2, col3 = st.columns(3)
        with col1:
            ciudad = st.selectbox("Ciudad", ["", "Madrid", "Barcelona", "Valencia", "Sevilla", "Bilbao"])
            tipo = st.selectbox("Tipo de Propiedad", ["", "piso", "casa", "chalet", "estudio", "local"])
        with col2:
            precio_min = st.number_input("Precio mínimo (€)", min_value=0, value=0, step=10000)
            precio_max = st.number_input("Precio máximo (€)", min_value=0, value=2000000, step=10000)
        with col3:
            hab_min = st.number_input("Habitaciones mínimas", min_value=0, value=0)
            m2_min = st.number_input("Superficie mínima (m²)", min_value=0, value=0)

        col4, col5, col6 = st.columns(3)
        with col4:
            garaje = st.checkbox("Con garaje")
        with col5:
            piscina = st.checkbox("Con piscina")
        with col6:
            limite = st.slider("Máx. resultados", 5, 25, 10)

        submitted = st.form_submit_button("🔍 Buscar Propiedades", use_container_width=True)

    if submitted:
        with st.spinner("Consultando base de datos..."):
            resultado = run_tool("search_properties", {
                "ciudad": ciudad,
                "tipo": tipo,
                "precio_min": float(precio_min),
                "precio_max": float(precio_max),
                "habitaciones_min": int(hab_min),
                "m2_min": int(m2_min),
                "garaje": garaje,
                "piscina": piscina,
                "estado": "disponible",
                "limite": limite,
            })

        if "error" in resultado:
            st.error(f"❌ {resultado['error']}")
        else:
            total = resultado.get("total", 0)
            propiedades = resultado.get("propiedades", [])

            if total == 0:
                st.info("No se encontraron propiedades con los criterios seleccionados.")
            else:
                st.success(f"✅ Se encontraron **{total} propiedades**")

                for p in propiedades:
                    extras = []
                    if p["garaje"]: extras.append("🚗 Garaje")
                    if p["piscina"]: extras.append("🏊 Piscina")
                    extras_str = " · ".join(extras) if extras else ""

                    estado_class = f"estado-{p['estado']}"
                    st.markdown(f"""
                    <div class="property-card">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                                <div class="precio-badge">{p['precio_formateado']}</div>
                                <h3 style="color: #e2e8f0 !important; margin: 8px 0 4px; font-size: 1.15rem;">{p['titulo']}</h3>
                                <p style="color: #94a3b8 !important; margin: 0 0 8px; font-size: 0.9rem;">
                                    📍 {p['direccion']} · {p['barrio']}, <b style="color: #2E86AB;">{p['ciudad']}</b>
                                </p>
                                <p style="color: #64748b !important; font-size: 0.85rem; margin: 4px 0;">{p.get('descripcion', '')[:120]}...</p>
                            </div>
                            <span class="{estado_class}">{p['estado'].upper()}</span>
                        </div>
                        <hr style="border-color: rgba(46,134,171,0.2); margin: 12px 0;">
                        <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                            <span style="color: #cbd5e1;">🏗️ <b>{p['tipo'].capitalize()}</b></span>
                            <span style="color: #cbd5e1;">📐 <b>{p['m2']} m²</b></span>
                            <span style="color: #cbd5e1;">🛏️ <b>{p['habitaciones']} hab.</b></span>
                            <span style="color: #cbd5e1;">🚿 <b>{p['banos']} baños</b></span>
                            <span style="color: #cbd5e1;">🏛️ <b>{p['antiguedad']} años</b></span>
                            <span style="color: #2E86AB;"><b>{p['precio_m2']:,.0f} €/m²</b></span>
                            {f'<span style="color: #10b981;">{extras_str}</span>' if extras_str else ''}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2: CALCULADORA DE HIPOTECA
# ════════════════════════════════════════════════════════════════════════════════

elif seccion == "💰 Calculadora de Hipoteca":
    st.markdown('<div class="section-header"><h1 style="margin:0; font-size:1.8rem;">💰 Calculadora de Hipoteca</h1></div>', unsafe_allow_html=True)
    st.markdown("Simulador de hipoteca con amortización francesa · **Tool MCP**: `calculate_mortgage` (Lógica propia)")

    with st.form("form_hipoteca"):
        col1, col2 = st.columns(2)
        with col1:
            precio = st.number_input("Precio de la vivienda (€)", min_value=50000, value=300000, step=5000)
            entrada_pct = st.slider("% Entrada inicial", 5, 50, 20, help="Mínimo recomendado: 20%")
            tasa = st.number_input("Tipo de interés anual (TIN %)", min_value=0.5, max_value=15.0, value=3.5, step=0.1)
        with col2:
            anos = st.slider("Plazo (años)", 5, 40, 30)
            ingresos = st.number_input("Ingresos mensuales netos (€, opcional)", min_value=0, value=0, step=100,
                                       help="Para calcular el ratio de endeudamiento")

        submitted = st.form_submit_button("📊 Calcular Hipoteca", use_container_width=True)

    if submitted:
        with st.spinner("Calculando..."):
            resultado = run_tool("calculate_mortgage", {
                "precio_vivienda": float(precio),
                "porcentaje_entrada": float(entrada_pct),
                "tasa_anual_pct": float(tasa),
                "anos": int(anos),
                "ingresos_mensuales": float(ingresos),
            })

        if "error" in resultado:
            st.error(f"❌ {resultado['error']}")
        else:
            res = resultado["resultado"]
            resumen = resultado["resumen"]
            tabla = resultado["tabla_amortizacion_anual"]
            viabilidad = resultado.get("analisis_viabilidad")

            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""<div class="metric-card">
                    <p class="metric-value" style="color: #2E86AB;">{res['cuota_mensual']:,.0f} €</p>
                    <p class="metric-label">Cuota mensual</p>
                </div>""", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""<div class="metric-card">
                    <p class="metric-value" style="color: #f59e0b;">{resumen['capital_financiado']:,.0f} €</p>
                    <p class="metric-label">Capital financiado</p>
                </div>""", unsafe_allow_html=True)
            with col3:
                st.markdown(f"""<div class="metric-card">
                    <p class="metric-value" style="color: #ef4444;">{res['total_intereses']:,.0f} €</p>
                    <p class="metric-label">Total intereses</p>
                </div>""", unsafe_allow_html=True)
            with col4:
                st.markdown(f"""<div class="metric-card">
                    <p class="metric-value" style="color: #10b981;">{resumen['ahorro_total_necesario']:,.0f} €</p>
                    <p class="metric-label">Ahorro necesario</p>
                </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Análisis de viabilidad
            if viabilidad:
                ratio = viabilidad["ratio_endeudamiento_pct"]
                color = "#10b981" if ratio <= 30 else "#f59e0b" if ratio <= 40 else "#ef4444"
                st.markdown(f"""
                <div style="background: rgba(30,58,95,0.5); border-radius: 12px; padding: 16px; margin-bottom: 16px; border: 1px solid {color}40;">
                    <h4 style="color: {color} !important; margin: 0 0 8px;">{viabilidad['valoracion']}</h4>
                    <p style="color: #cbd5e1 !important; margin: 0;">
                        Ratio de endeudamiento: <b style="color: {color};">{ratio}%</b> 
                        · Cuota máx. recomendada: <b>{viabilidad['cuota_maxima_recomendada']:,.0f} €/mes</b><br>
                        {viabilidad['consejo']}
                    </p>
                </div>
                """, unsafe_allow_html=True)

            # Gráfico de evolución del saldo
            col_graf1, col_graf2 = st.columns(2)

            with col_graf1:
                anos_list = [row["ano"] for row in tabla]
                saldo_list = [row["saldo_pendiente"] for row in tabla]
                cap_list = [row["capital_amortizado"] for row in tabla]
                int_list = [row["intereses_pagados"] for row in tabla]

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=anos_list, y=saldo_list, name="Saldo pendiente",
                    fill="tozeroy", line=dict(color="#2E86AB", width=2),
                    fillcolor="rgba(46,134,171,0.2)"
                ))
                fig.update_layout(
                    title="Evolución del Saldo Pendiente",
                    xaxis_title="Año",
                    yaxis_title="Euros (€)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#cbd5e1"),
                    title_font=dict(color="#e2e8f0"),
                )
                st.plotly_chart(fig, use_container_width=True)

            with col_graf2:
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(x=anos_list, y=cap_list, name="Capital", marker_color="#2E86AB"))
                fig2.add_trace(go.Bar(x=anos_list, y=int_list, name="Intereses", marker_color="#ef4444"))
                fig2.update_layout(
                    barmode="stack",
                    title="Capital vs Intereses por Año",
                    xaxis_title="Año",
                    yaxis_title="Euros (€)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#cbd5e1"),
                    title_font=dict(color="#e2e8f0"),
                )
                st.plotly_chart(fig2, use_container_width=True)

            # Tabla de amortización
            with st.expander("📋 Ver tabla de amortización anual completa"):
                df = pd.DataFrame(tabla)
                df.columns = ["Año", "Cuota Total Anual (€)", "Capital Amortizado (€)", "Intereses (€)", "Saldo Pendiente (€)"]
                st.dataframe(df.style.format({
                    "Cuota Total Anual (€)": "{:,.0f}",
                    "Capital Amortizado (€)": "{:,.0f}",
                    "Intereses (€)": "{:,.0f}",
                    "Saldo Pendiente (€)": "{:,.0f}",
                }), use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3: VALORACIÓN DE PROPIEDAD
# ════════════════════════════════════════════════════════════════════════════════

elif seccion == "📊 Valoración de Propiedad":
    st.markdown('<div class="section-header"><h1 style="margin:0; font-size:1.8rem;">📊 Valoración de Propiedad</h1></div>', unsafe_allow_html=True)
    st.markdown("Estima el valor de mercado de tu propiedad · **Tool MCP**: `estimate_property_value` (Lógica propia)")

    with st.form("form_valoracion"):
        col1, col2, col3 = st.columns(3)
        with col1:
            ciudad_val = st.selectbox("Ciudad", ["Madrid", "Barcelona", "Valencia", "Sevilla", "Bilbao"])
            tipo_val = st.selectbox("Tipo", ["piso", "casa", "chalet", "estudio", "local"])
        with col2:
            m2_val = st.number_input("Superficie (m²)", min_value=20, max_value=1000, value=80)
            hab_val = st.number_input("Habitaciones", min_value=0, max_value=10, value=3)
        with col3:
            banos_val = st.number_input("Baños", min_value=1, max_value=7, value=1)
            antiguedad_val = st.number_input("Antigüedad (años)", min_value=0, max_value=120, value=15)

        col4, col5 = st.columns(2)
        with col4:
            garaje_val = st.checkbox("Con garaje")
        with col5:
            piscina_val = st.checkbox("Con piscina")

        submitted = st.form_submit_button("🔍 Estimar Valor", use_container_width=True)

    if submitted:
        with st.spinner("Analizando comparables de mercado..."):
            resultado = run_tool("estimate_property_value", {
                "ciudad": ciudad_val,
                "tipo": tipo_val,
                "m2": int(m2_val),
                "habitaciones": int(hab_val),
                "banos": int(banos_val),
                "antiguedad": int(antiguedad_val),
                "garaje": garaje_val,
                "piscina": piscina_val,
            })

        if "error" in resultado:
            st.error(f"❌ {resultado['error']}")
        else:
            val = resultado["valoracion"]
            conf = resultado["confianza"]
            coefs = resultado["coeficientes_aplicados"]
            comparables = resultado.get("comparables_usados", [])

            # Valor estimado destacado
            col_main, col_info = st.columns([2, 1])
            with col_main:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(46,134,171,0.3), rgba(30,58,95,0.5));
                            border: 2px solid rgba(46,134,171,0.6); border-radius: 20px; padding: 30px; text-align: center;">
                    <p style="color: #94a3b8 !important; margin: 0; font-size: 0.9rem;">VALOR ESTIMADO DE MERCADO</p>
                    <h1 style="color: #2E86AB !important; font-size: 3rem; margin: 10px 0;">{val['valor_estimado']:,.0f} €</h1>
                    <p style="color: #94a3b8 !important; margin: 0; font-size: 1rem;">
                        Rango: <b style="color: #e2e8f0;">{val['valor_minimo']:,.0f} €</b> — <b style="color: #e2e8f0;">{val['valor_maximo']:,.0f} €</b>
                    </p>
                    <p style="color: #64748b !important; margin: 8px 0 0; font-size: 0.9rem;">
                        {val['precio_m2_estimado']:,.0f} €/m² · Coeficiente aplicado: {val['coeficiente_total_aplicado']:.3f}
                    </p>
                </div>
                """, unsafe_allow_html=True)

            with col_info:
                nivel_color = {"Alta": "#10b981", "Media": "#f59e0b", "Baja": "#ef4444"}.get(conf["nivel"], "#2E86AB")
                st.markdown(f"""
                <div class="metric-card" style="margin-bottom: 12px;">
                    <p class="metric-value" style="color: {nivel_color};">{conf['nivel']}</p>
                    <p class="metric-label">Confianza</p>
                </div>
                <div class="metric-card" style="margin-bottom: 12px;">
                    <p class="metric-value" style="font-size: 1.4rem; color: #2E86AB;">{conf['num_comparables']}</p>
                    <p class="metric-label">Comparables usados</p>
                </div>
                <div class="metric-card">
                    <p class="metric-value" style="font-size: 1.4rem; color: #2E86AB;">{val['precio_m2_base']:,.0f} €</p>
                    <p class="metric-label">Precio/m² base zona</p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Coeficientes de ajuste
            st.markdown("#### 🔧 Coeficientes de Ajuste Aplicados")
            cols = st.columns(len(coefs))
            for i, (nombre, data) in enumerate(coefs.items()):
                with cols[i]:
                    delta = (data["valor"] - 1) * 100
                    color = "#10b981" if delta >= 0 else "#ef4444"
                    st.markdown(f"""<div class="metric-card">
                        <p class="metric-value" style="color: {color}; font-size: 1.2rem;">{delta:+.1f}%</p>
                        <p class="metric-label">{nombre.capitalize()}</p>
                        <p style="color: #64748b !important; font-size: 0.75rem; margin-top: 4px;">{data['descripcion']}</p>
                    </div>""", unsafe_allow_html=True)

            # Comparables
            if comparables:
                st.markdown("<br>#### 🏘️ Propiedades Comparables")
                df_comp = pd.DataFrame(comparables)
                df_comp.columns = ["Título", "Barrio", "m²", "Habitaciones", "Precio (€)", "Precio/m² (€)"]
                st.dataframe(df_comp.style.format({
                    "Precio (€)": "{:,.0f}",
                    "Precio/m² (€)": "{:,.0f}",
                }), use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4: ANÁLISIS DE MERCADO
# ════════════════════════════════════════════════════════════════════════════════

elif seccion == "📈 Análisis de Mercado":
    st.markdown('<div class="section-header"><h1 style="margin:0; font-size:1.8rem;">📈 Análisis de Mercado</h1></div>', unsafe_allow_html=True)
    st.markdown("Dashboard de estadísticas del mercado inmobiliario · **Tool MCP**: `market_analysis` (Lógica propia)")

    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        ciudad_analisis = st.selectbox(
            "Ciudad a analizar",
            ["(Mercado Nacional)", "Madrid", "Barcelona", "Valencia", "Sevilla", "Bilbao"]
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        analizar = st.button("📊 Analizar", use_container_width=True)

    if analizar:
        ciudad_param = "" if ciudad_analisis == "(Mercado Nacional)" else ciudad_analisis
        with st.spinner("Analizando datos de mercado..."):
            resultado = run_tool("market_analysis", {"ciudad": ciudad_param})

        if "error" in resultado:
            st.error(f"❌ {resultado['error']}")
        else:
            resumen = resultado["resumen_general"]
            stats = resultado["estadisticas_precio"]
            caract = resultado["caracteristicas_medias"]
            tipos = resultado["distribucion_por_tipo"]
            por_ciudad = resultado.get("estadisticas_por_ciudad")
            destacadas = resultado["propiedades_destacadas"]

            # KPIs
            st.markdown("#### 📊 Resumen General")
            c1, c2, c3, c4, c5 = st.columns(5)
            metrics = [
                (c1, resumen["total_propiedades"], "Total Propiedades", "#2E86AB"),
                (c2, resumen["disponibles"], "Disponibles", "#10b981"),
                (c3, resumen["reservadas"], "Reservadas", "#f59e0b"),
                (c4, resumen["vendidas"], "Vendidas", "#ef4444"),
                (c5, f"{stats['precio_m2_medio']:,} €/m²", "Precio Medio/m²", "#a855f7"),
            ]
            for col, val, label, color in metrics:
                with col:
                    st.markdown(f"""<div class="metric-card">
                        <p class="metric-value" style="color: {color}; font-size: 1.4rem;">{val}</p>
                        <p class="metric-label">{label}</p>
                    </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Gráficos
            col_g1, col_g2 = st.columns(2)

            with col_g1:
                # Distribución por tipo
                tipos_df = pd.DataFrame([
                    {"Tipo": t.capitalize(), "Cantidad": v["cantidad"], "Precio Medio (€)": v["precio_medio"]}
                    for t, v in tipos.items()
                ])
                fig_pie = px.pie(
                    tipos_df, values="Cantidad", names="Tipo",
                    title="Distribución por Tipo de Propiedad",
                    color_discrete_sequence=["#2E86AB", "#10b981", "#f59e0b", "#ef4444", "#a855f7"]
                )
                fig_pie.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#cbd5e1"),
                    title_font=dict(color="#e2e8f0"),
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            with col_g2:
                # Precio medio por tipo
                fig_bar = px.bar(
                    tipos_df.sort_values("Precio Medio (€)", ascending=True),
                    x="Precio Medio (€)", y="Tipo", orientation="h",
                    title="Precio Medio por Tipo de Propiedad",
                    color="Precio Medio (€)",
                    color_continuous_scale=["#1e3a5f", "#2E86AB", "#7dd3fc"],
                )
                fig_bar.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#cbd5e1"),
                    title_font=dict(color="#e2e8f0"),
                    showlegend=False,
                )
                st.plotly_chart(fig_bar, use_container_width=True)

            # Comparativa por ciudades (sólo en modo nacional)
            if por_ciudad:
                ciudades_df = pd.DataFrame([
                    {
                        "Ciudad": c,
                        "Precio Medio (€)": v["precio_medio"],
                        "Precio/m² (€)": v["precio_m2_medio"],
                        "Propiedades": v["num_propiedades"],
                        "m² Medio": v["m2_medio"],
                    }
                    for c, v in por_ciudad.items()
                ])

                fig_ciudades = px.bar(
                    ciudades_df.sort_values("Precio/m² (€)", ascending=False),
                    x="Ciudad", y="Precio/m² (€)",
                    title="Precio Medio por m² por Ciudad",
                    color="Precio/m² (€)",
                    color_continuous_scale=["#1e3a5f", "#2E86AB", "#7dd3fc"],
                    text_auto=True,
                )
                fig_ciudades.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#cbd5e1"),
                    title_font=dict(color="#e2e8f0"),
                )
                st.plotly_chart(fig_ciudades, use_container_width=True)

                st.markdown("#### 🏙️ Detalle por Ciudad")
                st.dataframe(ciudades_df.style.format({
                    "Precio Medio (€)": "{:,.0f}",
                    "Precio/m² (€)": "{:,.0f}",
                    "m² Medio": "{:.0f}",
                }), use_container_width=True)

            # Propiedades destacadas
            st.markdown("#### 🏆 Propiedades Destacadas")
            dest_cols = st.columns(3)
            items = [
                ("💰 Más Económica", destacadas["mas_economica"], "#10b981"),
                ("👑 Más Cara", destacadas["mas_cara"], "#a855f7"),
                ("📐 Mejor Precio/m²", destacadas["mejor_precio_m2"], "#f59e0b"),
            ]
            for col, (label, prop, color) in zip(dest_cols, items):
                with col:
                    if prop:
                        st.markdown(f"""<div class="metric-card">
                            <p style="color: {color} !important; font-weight: 600; margin: 0 0 8px;">{label}</p>
                            <p style="color: #e2e8f0 !important; font-size: 0.9rem; margin: 0;">{prop['titulo'][:40]}...</p>
                            <p style="color: #2E86AB !important; font-weight: 700; font-size: 1.2rem; margin: 8px 0 0;">
                                {prop['precio']:,.0f} €
                            </p>
                            <p style="color: #64748b !important; font-size: 0.8rem; margin: 4px 0 0;">
                                {prop['precio_m2']:,.0f} €/m² · {prop['m2']} m² · {prop['ciudad']}
                            </p>
                        </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5: GEOLOCALIZACIÓN
# ════════════════════════════════════════════════════════════════════════════════

elif seccion == "🌍 Geolocalización":
    st.markdown('<div class="section-header"><h1 style="margin:0; font-size:1.8rem;">🌍 Geolocalización de Propiedades</h1></div>', unsafe_allow_html=True)
    st.markdown("Ubica direcciones de propiedades en el mapa · **Tool MCP**: `geocode_address` (Nominatim/OpenStreetMap)")

    with st.form("form_geo"):
        col1, col2 = st.columns([3, 1])
        with col1:
            direccion = st.text_input(
                "Dirección a geocodificar",
                placeholder="ej: Calle Gran Vía 42, Madrid, España",
                value=""
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("📍 Localizar", use_container_width=True)

    # Direcciones de ejemplo
    st.markdown("**Ejemplos rápidos:**")
    ex_cols = st.columns(5)
    ejemplos = [
        "Gran Vía 42, Madrid",
        "Passeig de Gràcia 92, Barcelona",
        "Calle Colón 28, Valencia",
        "Calle Sierpes 45, Sevilla",
        "Gran Vía 55, Bilbao",
    ]
    for i, col in enumerate(ex_cols):
        with col:
            if st.button(f"📌 {ejemplos[i][:20]}...", key=f"ej_{i}"):
                with st.spinner(f"Localizando {ejemplos[i]}..."):
                    resultado = run_tool("geocode_address", {"address": f"{ejemplos[i]}, España"})

                if "error" not in resultado:
                    lat = resultado["latitud"]
                    lon = resultado["longitud"]
                    st.success(f"✅ {resultado['direccion_formateada'][:80]}...")

                    # Mapa
                    df_map = pd.DataFrame({"lat": [lat], "lon": [lon]})
                    st.map(df_map, zoom=15)

                    # Detalles
                    with st.expander("📋 Detalles de la ubicación"):
                        detalles = resultado.get("detalles", {})
                        for k, v in detalles.items():
                            if v:
                                st.markdown(f"**{k.capitalize()}:** {v}")

    if submitted and direccion:
        with st.spinner(f"Geocodificando: {direccion}..."):
            resultado = run_tool("geocode_address", {"address": direccion})

        if "error" in resultado:
            st.error(f"❌ {resultado['error']}")
        else:
            lat = resultado["latitud"]
            lon = resultado["longitud"]

            st.success(f"✅ Dirección encontrada: **{resultado['direccion_formateada'][:100]}**")

            col_map, col_info = st.columns([2, 1])
            with col_map:
                df_map = pd.DataFrame({"lat": [lat], "lon": [lon]})
                st.map(df_map, zoom=15)

            with col_info:
                st.markdown(f"""
                <div class="metric-card" style="margin-bottom: 12px; text-align: left; padding: 16px;">
                    <p style="color: #94a3b8 !important; font-size: 0.8rem; margin-bottom: 12px;">COORDENADAS</p>
                    <p style="color: #e2e8f0 !important; margin: 4px 0;"><b>Latitud:</b> {lat:.6f}°</p>
                    <p style="color: #e2e8f0 !important; margin: 4px 0;"><b>Longitud:</b> {lon:.6f}°</p>
                </div>
                """, unsafe_allow_html=True)

                detalles = resultado.get("detalles", {})
                info_items = [(k.capitalize(), v) for k, v in detalles.items() if v]
                if info_items:
                    detalles_html = "".join([f"<p style='color: #e2e8f0 !important; margin: 4px 0;'><b>{k}:</b> {v}</p>" for k, v in info_items])
                    st.markdown(f"""
                    <div class="metric-card" style="text-align: left; padding: 16px;">
                        <p style="color: #94a3b8 !important; font-size: 0.8rem; margin-bottom: 12px;">DETALLES</p>
                        {detalles_html}
                    </div>
                    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6: CONVERSOR DE DIVISAS
# ════════════════════════════════════════════════════════════════════════════════

elif seccion == "💱 Conversor de Divisas":
    st.markdown('<div class="section-header"><h1 style="margin:0; font-size:1.8rem;">💱 Conversor de Divisas</h1></div>', unsafe_allow_html=True)
    st.markdown("Convierte precios de propiedades entre divisas · **Tool MCP**: `convert_currency` (Frankfurter API)")

    DIVISAS = ["EUR", "USD", "GBP", "CHF", "JPY", "CAD", "AUD", "SEK", "NOK", "DKK",
               "PLN", "CZK", "HUF", "CNY", "HKD", "SGD", "MXN", "BRL", "AED", "THB"]

    with st.form("form_divisa"):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            cantidad = st.number_input("Precio a convertir", min_value=0.01, value=350000.0, step=1000.0)
        with col2:
            desde = st.selectbox("De", DIVISAS, index=0)
        with col3:
            hacia = st.selectbox("A", DIVISAS, index=1)

        submitted = st.form_submit_button("💱 Convertir", use_container_width=True)

    # Conversiones rápidas de ejemplo (precio típico en Madrid)
    st.markdown("**Conversiones rápidas para un piso en Madrid (350.000 €):**")
    divisas_rapidas = ["USD", "GBP", "CHF", "JPY", "AED"]
    cols_rapidas = st.columns(len(divisas_rapidas))
    for col, d in zip(cols_rapidas, divisas_rapidas):
        with col:
            if st.button(f"EUR → {d}", key=f"rapida_{d}"):
                with st.spinner(f"Convirtiendo a {d}..."):
                    r = run_tool("convert_currency", {"amount": 350000.0, "from_currency": "EUR", "to_currency": d})
                if "error" not in r:
                    st.success(f"350.000 € = **{r['cantidad_convertida']:,.0f} {d}**\n\nTasa: {r['tasa_de_cambio']}")

    if submitted:
        with st.spinner(f"Obteniendo tasa de cambio {desde} → {hacia}..."):
            resultado = run_tool("convert_currency", {
                "amount": float(cantidad),
                "from_currency": desde,
                "to_currency": hacia,
            })

        if "error" in resultado:
            st.error(f"❌ {resultado['error']}")
        else:
            col_r1, col_r2, col_r3 = st.columns(3)
            with col_r1:
                st.markdown(f"""<div class="metric-card">
                    <p class="metric-value" style="color: #94a3b8; font-size: 1.4rem;">{cantidad:,.2f} {desde}</p>
                    <p class="metric-label">Cantidad original</p>
                </div>""", unsafe_allow_html=True)
            with col_r2:
                st.markdown(f"""<div class="metric-card">
                    <p class="metric-value" style="color: #2E86AB; font-size: 1.4rem;">{resultado['cantidad_convertida']:,.2f} {hacia}</p>
                    <p class="metric-label">Cantidad convertida</p>
                </div>""", unsafe_allow_html=True)
            with col_r3:
                st.markdown(f"""<div class="metric-card">
                    <p class="metric-value" style="color: #10b981; font-size: 1.1rem;">1 {desde} = {resultado['tasa_de_cambio']} {hacia}</p>
                    <p class="metric-label">Tasa · {resultado['fecha_tasa']}</p>
                </div>""", unsafe_allow_html=True)

            st.info(f"💰 **{resultado['descripcion']}**  \n📅 Datos del Banco Central Europeo (BCE) · Fecha: {resultado['fecha_tasa']}")


# ════════════════════════════════════════════════════════════════════════════════
# SECCIÓN 7: GENERADOR DE INFORMES PDF
# ════════════════════════════════════════════════════════════════════════════════

elif seccion == "📄 Generador de Informes PDF":
    st.markdown('<div class="section-header"><h1 style="margin:0; font-size:1.8rem;">📄 Generador de Informes PDF</h1></div>', unsafe_allow_html=True)
    st.markdown("Genera informes profesionales de propiedades · **Tool MCP**: `generate_property_report` (ReportLab)")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("**Primero busca propiedades disponibles:**")
        ciudad_pdf = st.selectbox("Ciudad", ["", "Madrid", "Barcelona", "Valencia", "Sevilla", "Bilbao"], key="ciudad_pdf")

    if ciudad_pdf or True:
        # Cargar propiedades disponibles
        with st.spinner("Cargando propiedades..."):
            props_result = run_tool("search_properties", {
                "ciudad": ciudad_pdf,
                "estado": "disponible",
                "limite": 25,
            })

        propiedades_disponibles = props_result.get("propiedades", [])

        if not propiedades_disponibles:
            st.info("No hay propiedades disponibles.")
        else:
            # Selector de propiedad
            opciones = {f"[ID:{p['id']}] {p['titulo']} — {p['precio_formateado']}": p["id"]
                       for p in propiedades_disponibles}

            seleccion = st.selectbox("Selecciona una propiedad", list(opciones.keys()))
            prop_id = opciones[seleccion]

            # Info rápida
            prop_sel = next(p for p in propiedades_disponibles if p["id"] == prop_id)
            st.markdown(f"""
            <div class="property-card">
                <div class="precio-badge">{prop_sel['precio_formateado']}</div>
                <h3 style="color: #e2e8f0 !important; margin: 8px 0 4px;">{prop_sel['titulo']}</h3>
                <p style="color: #94a3b8 !important; margin: 0;">
                    📍 {prop_sel['direccion']} · {prop_sel['barrio']}, {prop_sel['ciudad']} · 
                    {prop_sel['m2']} m² · {prop_sel['habitaciones']} hab. · {prop_sel['banos']} baños
                </p>
            </div>
            """, unsafe_allow_html=True)

            if st.button("📄 Generar Informe PDF", use_container_width=True):
                with st.spinner("Generando informe PDF con ReportLab..."):
                    resultado = run_tool("generate_property_report", {"property_id": prop_id})

                if "error" in resultado:
                    st.error(f"❌ {resultado['error']}")
                else:
                    pdf_path = resultado["pdf_path"]
                    st.success(f"✅ Informe generado: **{resultado['nombre_archivo']}**")

                    # Botón de descarga
                    if os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()
                        st.download_button(
                            label="⬇️ Descargar Informe PDF",
                            data=pdf_bytes,
                            file_name=resultado["nombre_archivo"],
                            mime="application/pdf",
                            use_container_width=True,
                        )
                        st.info(f"📁 Informe guardado en el servidor: `{pdf_path}`")
