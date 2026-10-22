"""
integration_tools.py
--------------------
Tools del MCP Server que se integran con herramientas existentes:

    1. search_properties       -> SQLite (base de datos local de propiedades)
    2. generate_property_report -> ReportLab (generación de informes PDF)
"""

import json
import os
import sys
from datetime import datetime

# Asegurar que el paquete raíz es accesible
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server.fastmcp import FastMCP
from mcp_server.utils.db import fetch_all_sync, fetch_one_sync

mcp = FastMCP("InmobiliariaServer-Integration")

# Directorio donde se guardarán los informes PDF
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 3: Búsqueda de propiedades (SQLite)
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def search_properties(
    ciudad: str = "",
    tipo: str = "",
    precio_min: float = 0,
    precio_max: float = 9999999,
    habitaciones_min: int = 0,
    m2_min: int = 0,
    garaje: bool = False,
    piscina: bool = False,
    estado: str = "disponible",
    limite: int = 10
) -> str:
    """
    Busca propiedades en la base de datos aplicando múltiples filtros.

    Integra con SQLite para consultar el catálogo de propiedades inmobiliarias.
    Permite filtrar por ciudad, tipo, precio, tamaño y características.

    Args:
        ciudad:          Ciudad donde buscar (Madrid, Barcelona, Valencia, Sevilla, Bilbao).
                         Vacío para buscar en todas.
        tipo:            Tipo de propiedad: piso, casa, chalet, estudio, local.
                         Vacío para todos los tipos.
        precio_min:      Precio mínimo en euros.
        precio_max:      Precio máximo en euros.
        habitaciones_min: Número mínimo de habitaciones.
        m2_min:          Superficie mínima en metros cuadrados.
        garaje:          Si True, solo propiedades con garaje.
        piscina:         Si True, solo propiedades con piscina.
        estado:          Estado de la propiedad: disponible, reservado, vendido.
                         Vacío para todos los estados.
        limite:          Número máximo de resultados (por defecto 10, máximo 25).

    Returns:
        JSON con lista de propiedades que cumplen los criterios y total encontrado.
    """
    limite = min(limite, 25)

    query = "SELECT * FROM propiedades WHERE 1=1"
    params = []

    if ciudad:
        query += " AND LOWER(ciudad) = LOWER(?)"
        params.append(ciudad)
    if tipo:
        query += " AND LOWER(tipo) = LOWER(?)"
        params.append(tipo)
    if precio_min > 0:
        query += " AND precio >= ?"
        params.append(precio_min)
    if precio_max < 9999999:
        query += " AND precio <= ?"
        params.append(precio_max)
    if habitaciones_min > 0:
        query += " AND habitaciones >= ?"
        params.append(habitaciones_min)
    if m2_min > 0:
        query += " AND m2 >= ?"
        params.append(m2_min)
    if garaje:
        query += " AND garaje = 1"
    if piscina:
        query += " AND piscina = 1"
    if estado:
        query += " AND LOWER(estado) = LOWER(?)"
        params.append(estado)

    query += " ORDER BY precio ASC LIMIT ?"
    params.append(limite)

    try:
        rows = fetch_all_sync(query, tuple(params))

        if not rows:
            return json.dumps({
                "total": 0,
                "propiedades": [],
                "mensaje": "No se encontraron propiedades con los criterios indicados."
            }, ensure_ascii=False, indent=2)

        # Formatear las propiedades para mejor legibilidad
        propiedades_fmt = []
        for p in rows:
            propiedades_fmt.append({
                "id": p["id"],
                "titulo": p["titulo"],
                "tipo": p["tipo"],
                "direccion": p["direccion"],
                "ciudad": p["ciudad"],
                "barrio": p["barrio"],
                "m2": p["m2"],
                "habitaciones": p["habitaciones"],
                "banos": p["banos"],
                "precio": p["precio"],
                "precio_formateado": f"{p['precio']:,.0f} €",
                "precio_m2": round(p["precio"] / p["m2"], 2),
                "antiguedad": p["antiguedad"],
                "garaje": bool(p["garaje"]),
                "piscina": bool(p["piscina"]),
                "descripcion": p["descripcion"],
                "estado": p["estado"],
            })

        return json.dumps({
            "total": len(propiedades_fmt),
            "propiedades": propiedades_fmt,
            "filtros_aplicados": {
                "ciudad": ciudad or "todas",
                "tipo": tipo or "todos",
                "precio_min": precio_min,
                "precio_max": precio_max,
                "habitaciones_min": habitaciones_min,
                "m2_min": m2_min,
                "garaje": garaje,
                "piscina": piscina,
                "estado": estado or "todos",
            }
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Error al consultar la base de datos: {str(e)}"}, ensure_ascii=False)


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 4: Generación de informes PDF (ReportLab)
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def generate_property_report(property_id: int) -> str:
    """
    Genera un informe PDF profesional con todos los datos de una propiedad.

    Utiliza ReportLab para crear un documento estructurado que incluye:
    ficha técnica, descripción, análisis de precio por m², características
    destacadas y datos de contacto simulados.

    Args:
        property_id: ID de la propiedad en la base de datos.

    Returns:
        JSON con la ruta del archivo PDF generado y un resumen de la propiedad.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    except ImportError:
        return json.dumps({"error": "ReportLab no está instalado. Ejecute: pip install reportlab"}, ensure_ascii=False)

    # Obtener datos de la propiedad
    propiedad = fetch_one_sync("SELECT * FROM propiedades WHERE id = ?", (property_id,))
    if not propiedad:
        return json.dumps({"error": f"No se encontró ninguna propiedad con ID {property_id}."}, ensure_ascii=False)

    # Ruta del PDF
    nombre_archivo = f"informe_propiedad_{property_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = os.path.join(REPORTS_DIR, nombre_archivo)

    # ── Configuración del documento ──────────────────────────────────────────
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm
    )

    # Colores corporativos
    COLOR_PRIMARIO = colors.HexColor("#1E3A5F")
    COLOR_ACENTO = colors.HexColor("#2E86AB")
    COLOR_CLARO = colors.HexColor("#F0F4F8")
    COLOR_TEXTO = colors.HexColor("#2D3748")

    # Estilos
    styles = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        "Titulo",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=COLOR_PRIMARIO,
        spaceAfter=6,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
    )
    estilo_subtitulo = ParagraphStyle(
        "Subtitulo",
        parent=styles["Normal"],
        fontSize=11,
        textColor=COLOR_ACENTO,
        spaceAfter=4,
        fontName="Helvetica",
    )
    estilo_seccion = ParagraphStyle(
        "Seccion",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=COLOR_PRIMARIO,
        spaceBefore=14,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    estilo_normal = ParagraphStyle(
        "Normal2",
        parent=styles["Normal"],
        fontSize=10,
        textColor=COLOR_TEXTO,
        fontName="Helvetica",
        leading=15,
    )
    estilo_footer = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER,
    )

    # ── Construcción del contenido ───────────────────────────────────────────
    story = []

    # --- Cabecera ---
    story.append(Paragraph("🏢 INMOBILIARIA DIGITAL", estilo_subtitulo))
    story.append(Paragraph(propiedad["titulo"], estilo_titulo))
    story.append(Paragraph(
        f"📍 {propiedad['direccion']} · {propiedad['barrio']}, {propiedad['ciudad']}",
        estilo_subtitulo
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=COLOR_PRIMARIO))
    story.append(Spacer(1, 0.3 * cm))

    # --- Precio destacado ---
    precio_formateado = f"{propiedad['precio']:,.0f} €"
    precio_m2 = f"{propiedad['precio'] / propiedad['m2']:,.0f} €/m²"
    precio_data = [
        [Paragraph(f"<b><font size=18 color='#{COLOR_PRIMARIO.hexval()[2:]}'>PRECIO: {precio_formateado}</font></b>",
                   styles["Normal"]),
         Paragraph(f"<b>{precio_m2}</b>", estilo_normal)],
    ]
    precio_tabla = Table(precio_data, colWidths=["70%", "30%"])
    precio_tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CLARO),
        ("ROUNDEDCORNERS", [5]),
        ("PADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(precio_tabla)
    story.append(Spacer(1, 0.4 * cm))

    # --- Ficha técnica ---
    story.append(Paragraph("FICHA TÉCNICA", estilo_seccion))

    si_no = lambda v: "Sí" if v else "No"
    ficha_data = [
        ["Tipo de inmueble", propiedad["tipo"].capitalize(),
         "Superficie", f"{propiedad['m2']} m²"],
        ["Habitaciones", str(propiedad["habitaciones"]),
         "Baños", str(propiedad["banos"])],
        ["Antigüedad", f"{propiedad['antiguedad']} años",
         "Estado", propiedad["estado"].capitalize()],
        ["Garaje", si_no(propiedad["garaje"]),
         "Piscina", si_no(propiedad["piscina"])],
        ["Ciudad", propiedad["ciudad"],
         "Barrio", propiedad["barrio"]],
    ]

    ficha_tabla = Table(ficha_data, colWidths=["25%", "25%", "25%", "25%"])
    ficha_tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), COLOR_PRIMARIO),
        ("BACKGROUND", (2, 0), (2, -1), COLOR_PRIMARIO),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (1, 0), (1, -1), [colors.white, COLOR_CLARO]),
        ("ROWBACKGROUNDS", (3, 0), (3, -1), [colors.white, COLOR_CLARO]),
    ]))
    story.append(ficha_tabla)
    story.append(Spacer(1, 0.3 * cm))

    # --- Descripción ---
    story.append(Paragraph("DESCRIPCIÓN", estilo_seccion))
    story.append(Paragraph(propiedad.get("descripcion", "Sin descripción disponible."), estilo_normal))
    story.append(Spacer(1, 0.3 * cm))

    # --- Análisis de precio ---
    story.append(Paragraph("ANÁLISIS DE PRECIO", estilo_seccion))

    # Obtener precio medio de la ciudad
    comparables = fetch_all_sync(
        "SELECT precio, m2 FROM propiedades WHERE ciudad = ? AND tipo = ? AND id != ? AND estado != 'vendido'",
        (propiedad["ciudad"], propiedad["tipo"], property_id)
    )
    if comparables:
        precios_m2 = [p["precio"] / p["m2"] for p in comparables]
        precio_medio_m2 = sum(precios_m2) / len(precios_m2)
        precio_m2_prop = propiedad["precio"] / propiedad["m2"]
        diferencia_pct = ((precio_m2_prop - precio_medio_m2) / precio_medio_m2) * 100
        valoracion = "por encima" if diferencia_pct > 0 else "por debajo"

        analisis_text = (
            f"El precio por m² de esta propiedad es de <b>{precio_m2_prop:,.0f} €/m²</b>, "
            f"mientras que el precio medio de {propiedad['tipo']}s en {propiedad['ciudad']} es de "
            f"<b>{precio_medio_m2:,.0f} €/m²</b>. "
            f"Esta propiedad se sitúa un <b>{abs(diferencia_pct):.1f}%</b> {valoracion} del precio medio de mercado. "
            f"Análisis basado en {len(comparables)} propiedades comparables."
        )
    else:
        analisis_text = "No hay suficientes comparables en la base de datos para realizar el análisis de precio."

    story.append(Paragraph(analisis_text, estilo_normal))
    story.append(Spacer(1, 0.3 * cm))

    # --- Simulación de hipoteca ---
    story.append(Paragraph("SIMULACIÓN DE HIPOTECA (orientativa)", estilo_seccion))
    precio = propiedad["precio"]
    entrada = precio * 0.20
    capital = precio - entrada
    tasa_mensual = 0.035 / 12  # 3.5% TIN
    n_cuotas = 360  # 30 años
    cuota = capital * (tasa_mensual * (1 + tasa_mensual) ** n_cuotas) / ((1 + tasa_mensual) ** n_cuotas - 1)

    hipoteca_data = [
        ["Precio de la vivienda", f"{precio:,.0f} €"],
        ["Entrada estimada (20%)", f"{entrada:,.0f} €"],
        ["Capital a financiar", f"{capital:,.0f} €"],
        ["Cuota mensual aprox.*", f"{cuota:,.0f} €/mes"],
        ["Plazo", "30 años"],
        ["TIN estimado", "3,5%"],
    ]
    hip_tabla = Table(hipoteca_data, colWidths=["50%", "50%"])
    hip_tabla.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, COLOR_CLARO]),
        ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#E8F5E9")),
        ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
    ]))
    story.append(hip_tabla)
    story.append(Paragraph("*Simulación orientativa. Consulte con su entidad financiera.", estilo_footer))

    # --- Footer ---
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Paragraph(
        f"Informe generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')} · "
        f"Referencia: REF-{property_id:04d} · "
        f"Inmobiliaria Digital S.L. · Tel: +34 900 123 456",
        estilo_footer
    ))

    # ── Generar PDF ────────────────────────────────────────────────────────────
    doc.build(story)

    return json.dumps({
        "exito": True,
        "pdf_path": pdf_path,
        "nombre_archivo": nombre_archivo,
        "propiedad": {
            "id": property_id,
            "titulo": propiedad["titulo"],
            "ciudad": propiedad["ciudad"],
            "precio": propiedad["precio"],
        },
        "mensaje": f"Informe PDF generado correctamente en: {pdf_path}"
    }, ensure_ascii=False, indent=2)
