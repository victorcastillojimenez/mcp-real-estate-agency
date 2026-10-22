"""
logic_tools.py
--------------
Tools del MCP Server con lógica propia implementada:

    1. calculate_mortgage     -> Calculadora de hipoteca (sistema francés)
    2. estimate_property_value -> Estimador de valor por comparables + coeficientes
    3. market_analysis         -> Análisis estadístico del mercado inmobiliario (EXTRA)
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server.fastmcp import FastMCP
from mcp_server.utils.db import fetch_all_sync

mcp = FastMCP("InmobiliariaServer-Logic")


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 5: Calculadora de hipoteca (lógica propia)
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def calculate_mortgage(
    precio_vivienda: float,
    porcentaje_entrada: float = 20.0,
    tasa_anual_pct: float = 3.5,
    anos: int = 30,
    ingresos_mensuales: float = 0.0
) -> str:
    """
    Calcula todos los parámetros de una hipoteca usando el sistema de amortización francés.

    Implementa la fórmula estándar de amortización francesa donde las cuotas son
    constantes y la composición entre capital e intereses varía en cada período.
    También genera una tabla de amortización resumida anual.

    Args:
        precio_vivienda:      Precio total de la vivienda en euros.
        porcentaje_entrada:   Porcentaje de entrada inicial (por defecto 20%).
                              Mínimo recomendado: 20% (más gastos ~10%).
        tasa_anual_pct:       Tipo de interés nominal anual en % (por defecto 3.5%).
        anos:                 Plazo de la hipoteca en años (típicamente 15-30).
        ingresos_mensuales:   Ingresos mensuales netos del solicitante (opcional).
                              Si se proporciona, calcula el ratio de endeudamiento.

    Returns:
        JSON con: cuota mensual, total pagado, total intereses, tabla de amortización
                  anual resumida y análisis de viabilidad financiera.
    """
    if precio_vivienda <= 0:
        return json.dumps({"error": "El precio de la vivienda debe ser mayor que 0."}, ensure_ascii=False)
    if not (0 < porcentaje_entrada < 100):
        return json.dumps({"error": "El porcentaje de entrada debe estar entre 1 y 99."}, ensure_ascii=False)
    if tasa_anual_pct <= 0:
        return json.dumps({"error": "La tasa de interés debe ser mayor que 0."}, ensure_ascii=False)
    if anos <= 0 or anos > 40:
        return json.dumps({"error": "El plazo debe estar entre 1 y 40 años."}, ensure_ascii=False)

    # ── Cálculos base ────────────────────────────────────────────────────────
    entrada = round(precio_vivienda * (porcentaje_entrada / 100), 2)
    capital = round(precio_vivienda - entrada, 2)
    gastos_estimados = round(precio_vivienda * 0.10, 2)  # ~10% (ITP/AJD + notaría + registro)

    n = anos * 12  # número de cuotas
    r = (tasa_anual_pct / 100) / 12  # tasa mensual

    # Fórmula de amortización francesa: M = C * [r(1+r)^n] / [(1+r)^n - 1]
    cuota_mensual = capital * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    cuota_mensual = round(cuota_mensual, 2)

    total_pagado = round(cuota_mensual * n, 2)
    total_intereses = round(total_pagado - capital, 2)

    # ── Tabla de amortización anual resumida ─────────────────────────────────
    tabla_anual = []
    saldo_pendiente = capital

    for ano in range(1, anos + 1):
        capital_amortizado_ano = 0
        intereses_ano = 0
        cuotas_ano = min(12, n - (ano - 1) * 12)  # últimos años pueden tener menos

        for _ in range(cuotas_ano):
            interes_mes = saldo_pendiente * r
            capital_mes = cuota_mensual - interes_mes
            saldo_pendiente -= capital_mes
            capital_amortizado_ano += capital_mes
            intereses_ano += interes_mes

        saldo_pendiente = max(0, saldo_pendiente)
        tabla_anual.append({
            "ano": ano,
            "cuota_total_ano": round(cuota_mensual * cuotas_ano, 2),
            "capital_amortizado": round(capital_amortizado_ano, 2),
            "intereses_pagados": round(intereses_ano, 2),
            "saldo_pendiente": round(saldo_pendiente, 2),
        })

    # ── Análisis de viabilidad ───────────────────────────────────────────────
    analisis_viabilidad = {}
    if ingresos_mensuales > 0:
        ratio_endeudamiento = (cuota_mensual / ingresos_mensuales) * 100
        if ratio_endeudamiento <= 30:
            semaforo = "🟢 VIABLE"
            consejo = "El ratio de endeudamiento es saludable (≤30%). La hipoteca es financieramente viable."
        elif ratio_endeudamiento <= 40:
            semaforo = "🟡 ACEPTABLE"
            consejo = "El ratio está en el límite aceptable (30-40%). Considera reducir el plazo o buscar tipo fijo."
        else:
            semaforo = "🔴 RIESGO ALTO"
            consejo = "El ratio supera el 40%, lo que puede dificultar la aprobación bancaria. Considera un importe menor."

        analisis_viabilidad = {
            "ingresos_mensuales": ingresos_mensuales,
            "ratio_endeudamiento_pct": round(ratio_endeudamiento, 1),
            "valoracion": semaforo,
            "consejo": consejo,
            "cuota_maxima_recomendada": round(ingresos_mensuales * 0.30, 2),
        }

    return json.dumps({
        "resumen": {
            "precio_vivienda": precio_vivienda,
            "entrada": entrada,
            "porcentaje_entrada": porcentaje_entrada,
            "gastos_estimados_compra": gastos_estimados,
            "ahorro_total_necesario": round(entrada + gastos_estimados, 2),
            "capital_financiado": capital,
            "tasa_anual_pct": tasa_anual_pct,
            "anos": anos,
            "n_cuotas": n,
        },
        "resultado": {
            "cuota_mensual": cuota_mensual,
            "total_pagado": total_pagado,
            "total_intereses": total_intereses,
            "coste_total_vivienda": round(precio_vivienda + total_intereses + gastos_estimados, 2),
            "ratio_intereses_capital_pct": round((total_intereses / capital) * 100, 1),
        },
        "tabla_amortizacion_anual": tabla_anual,
        "analisis_viabilidad": analisis_viabilidad if analisis_viabilidad else None,
    }, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 6: Estimador de valor de propiedad (lógica propia)
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def estimate_property_value(
    ciudad: str,
    tipo: str,
    m2: int,
    habitaciones: int,
    banos: int,
    antiguedad: int,
    garaje: bool = False,
    piscina: bool = False,
    barrio: str = ""
) -> str:
    """
    Estima el valor de mercado de una propiedad usando comparables y coeficientes de ajuste.

    Algoritmo propio que:
    1. Obtiene propiedades similares de la BD (misma ciudad, mismo tipo).
    2. Calcula el precio base por m² del vecindario o ciudad.
    3. Aplica coeficientes de ajuste por antigüedad, extras y características.
    4. Genera un rango de valoración (mínimo, estimado, máximo).

    Args:
        ciudad:      Ciudad de la propiedad a valorar.
        tipo:        Tipo de propiedad (piso, casa, chalet, estudio, local).
        m2:          Superficie en metros cuadrados.
        habitaciones: Número de habitaciones.
        banos:       Número de baños.
        antiguedad:  Años de antigüedad de la construcción.
        garaje:      Si dispone de plaza de garaje.
        piscina:     Si dispone de piscina.
        barrio:      Barrio concreto (opcional, mejora la precisión).

    Returns:
        JSON con: valor estimado, rango (min-max), precio/m², comparables usados,
                  desglose de coeficientes aplicados y nivel de confianza.
    """
    # ── Obtener comparables de la BD ─────────────────────────────────────────
    comparables = fetch_all_sync(
        "SELECT * FROM propiedades WHERE LOWER(ciudad) = LOWER(?) AND LOWER(tipo) = LOWER(?) AND estado != 'vendido'",
        (ciudad, tipo)
    )

    if len(comparables) < 2:
        # Fallback: todos los tipos de la ciudad
        comparables = fetch_all_sync(
            "SELECT * FROM propiedades WHERE LOWER(ciudad) = LOWER(?) AND estado != 'vendido'",
            (ciudad,)
        )

    if not comparables:
        return json.dumps({
            "error": f"Sin datos suficientes para valorar en {ciudad}. Ciudad no encontrada en la base de datos.",
            "ciudades_disponibles": ["Madrid", "Barcelona", "Valencia", "Sevilla", "Bilbao"]
        }, ensure_ascii=False)

    # Precio base: mediana del precio/m² de los comparables
    precios_m2 = sorted([c["precio"] / c["m2"] for c in comparables])
    mediana_idx = len(precios_m2) // 2
    precio_base_m2 = precios_m2[mediana_idx]

    # ── Coeficientes de ajuste ───────────────────────────────────────────────
    coeficientes = {}

    # 1. Antigüedad: penalización progresiva
    if antiguedad == 0:
        coef_antiguedad = 1.10    # nueva construcción: +10%
    elif antiguedad <= 5:
        coef_antiguedad = 1.05
    elif antiguedad <= 15:
        coef_antiguedad = 1.00
    elif antiguedad <= 30:
        coef_antiguedad = 0.95
    elif antiguedad <= 50:
        coef_antiguedad = 0.88
    else:
        coef_antiguedad = 0.80    # más de 50 años: -20%
    coeficientes["antiguedad"] = {"valor": coef_antiguedad, "descripcion": f"{antiguedad} años de antigüedad"}

    # 2. Garaje: bonus
    coef_garaje = 1.05 if garaje else 1.00
    coeficientes["garaje"] = {"valor": coef_garaje, "descripcion": "Con garaje" if garaje else "Sin garaje"}

    # 3. Piscina: bonus (más relevante en casas/chalets)
    bonus_piscina = 0.08 if tipo in ["chalet", "casa"] else 0.03
    coef_piscina = 1.0 + bonus_piscina if piscina else 1.00
    coeficientes["piscina"] = {"valor": coef_piscina, "descripcion": "Con piscina" if piscina else "Sin piscina"}

    # 4. Ratio habitaciones/m²: ajuste por distribución
    ratio_hab = habitaciones / m2 if m2 > 0 else 0
    if 0.03 <= ratio_hab <= 0.05:
        coef_distribucion = 1.02  # distribución óptima
    elif ratio_hab < 0.03:
        coef_distribucion = 0.98  # pocas habitas para el tamaño → menos funcional
    else:
        coef_distribucion = 0.97  # muy compartimentado
    coeficientes["distribucion"] = {"valor": coef_distribucion, "descripcion": f"{habitaciones} hab / {m2} m²"}

    # Coeficiente total compuesto
    coeficiente_total = coef_antiguedad * coef_garaje * coef_piscina * coef_distribucion

    # ── Cálculo del valor estimado ───────────────────────────────────────────
    precio_m2_ajustado = precio_base_m2 * coeficiente_total
    valor_estimado = round(precio_m2_ajustado * m2, 0)

    # Rango de incertidumbre: ±10% si hay >5 comparables, ±15% si hay menos
    margen = 0.10 if len(comparables) >= 5 else 0.15
    valor_minimo = round(valor_estimado * (1 - margen), 0)
    valor_maximo = round(valor_estimado * (1 + margen), 0)

    # Nivel de confianza según nº de comparables
    if len(comparables) >= 8:
        confianza = "Alta"
        confianza_pct = 85
    elif len(comparables) >= 4:
        confianza = "Media"
        confianza_pct = 70
    else:
        confianza = "Baja"
        confianza_pct = 50

    # Comparables resumidos
    comparables_fmt = [
        {
            "titulo": c["titulo"],
            "barrio": c["barrio"],
            "m2": c["m2"],
            "habitaciones": c["habitaciones"],
            "precio": c["precio"],
            "precio_m2": round(c["precio"] / c["m2"], 0),
        }
        for c in comparables[:5]
    ]

    return json.dumps({
        "propiedad_consultada": {
            "ciudad": ciudad,
            "tipo": tipo,
            "m2": m2,
            "habitaciones": habitaciones,
            "banos": banos,
            "antiguedad": antiguedad,
            "garaje": garaje,
            "piscina": piscina,
        },
        "valoracion": {
            "valor_estimado": valor_estimado,
            "valor_minimo": valor_minimo,
            "valor_maximo": valor_maximo,
            "precio_m2_base": round(precio_base_m2, 2),
            "precio_m2_estimado": round(precio_m2_ajustado, 2),
            "coeficiente_total_aplicado": round(coeficiente_total, 4),
            "rango_descripcion": f"{valor_minimo:,.0f} € – {valor_maximo:,.0f} €",
        },
        "coeficientes_aplicados": coeficientes,
        "confianza": {
            "nivel": confianza,
            "porcentaje": confianza_pct,
            "num_comparables": len(comparables),
        },
        "comparables_usados": comparables_fmt,
    }, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 7: Análisis de mercado (lógica propia - EXTRA)
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def market_analysis(ciudad: str = "") -> str:
    """
    Genera un análisis estadístico completo del mercado inmobiliario.

    Calcula métricas clave como precio medio por ciudad/zona, distribución
    de tipos de propiedad, precio por m² por ciudad y estado de las propiedades.
    Permite filtrar por ciudad o analizar el mercado global.

    Args:
        ciudad: Ciudad a analizar (Madrid, Barcelona, Valencia, Sevilla, Bilbao).
                Si está vacío, analiza el mercado nacional completo.

    Returns:
        JSON con estadísticas de mercado: precios medios, distribución por tipo,
        precio/m² por zona, ranking de ciudades y propiedades destacadas.
    """
    query_base = "SELECT * FROM propiedades"
    params = ()
    scope = "nacional"

    if ciudad:
        query_base += " WHERE LOWER(ciudad) = LOWER(?)"
        params = (ciudad,)
        scope = ciudad

    propiedades = fetch_all_sync(query_base, params)

    if not propiedades:
        return json.dumps({
            "error": f"No se encontraron datos para: {ciudad or 'España'}",
            "ciudades_disponibles": ["Madrid", "Barcelona", "Valencia", "Sevilla", "Bilbao"]
        }, ensure_ascii=False)

    total = len(propiedades)
    disponibles = [p for p in propiedades if p["estado"] == "disponible"]
    reservadas = [p for p in propiedades if p["estado"] == "reservado"]
    vendidas = [p for p in propiedades if p["estado"] == "vendido"]

    precios = [p["precio"] for p in disponibles] if disponibles else [p["precio"] for p in propiedades]
    m2_vals = [p["m2"] for p in disponibles] if disponibles else [p["m2"] for p in propiedades]
    precios_m2 = [p["precio"] / p["m2"] for p in propiedades]

    def media(lst): return sum(lst) / len(lst) if lst else 0
    def mediana(lst):
        s = sorted(lst)
        n = len(s)
        return (s[n // 2 - 1] + s[n // 2]) / 2 if n % 2 == 0 else s[n // 2]

    # ── Estadísticas por tipo ─────────────────────────────────────────────────
    tipos = {}
    for p in propiedades:
        t = p["tipo"]
        if t not in tipos:
            tipos[t] = {"count": 0, "precios": [], "m2": []}
        tipos[t]["count"] += 1
        tipos[t]["precios"].append(p["precio"])
        tipos[t]["m2"].append(p["m2"])

    distribucion_tipos = {}
    for t, data in tipos.items():
        distribucion_tipos[t] = {
            "cantidad": data["count"],
            "porcentaje": round(data["count"] / total * 100, 1),
            "precio_medio": round(media(data["precios"]), 0),
            "precio_m2_medio": round(media([pr / m for pr, m in zip(data["precios"], data["m2"])]), 0),
            "m2_medio": round(media(data["m2"]), 0),
        }

    # ── Estadísticas por ciudad (si análisis nacional) ────────────────────────
    estadisticas_ciudad = {}
    if not ciudad:
        ciudades_data = {}
        for p in propiedades:
            c = p["ciudad"]
            if c not in ciudades_data:
                ciudades_data[c] = {"precios": [], "m2": []}
            ciudades_data[c]["precios"].append(p["precio"])
            ciudades_data[c]["m2"].append(p["m2"])

        for c, data in ciudades_data.items():
            estadisticas_ciudad[c] = {
                "num_propiedades": len(data["precios"]),
                "precio_medio": round(media(data["precios"]), 0),
                "precio_m2_medio": round(media([pr / m for pr, m in zip(data["precios"], data["m2"])]), 0),
                "precio_minimo": round(min(data["precios"]), 0),
                "precio_maximo": round(max(data["precios"]), 0),
                "m2_medio": round(media(data["m2"]), 0),
            }

    # ── Propiedades destacadas ────────────────────────────────────────────────
    disponibles_sort = sorted(disponibles, key=lambda x: x["precio"])
    mas_economica = disponibles_sort[0] if disponibles_sort else None
    mas_cara = disponibles_sort[-1] if disponibles_sort else None
    mejor_precio_m2 = min(disponibles, key=lambda x: x["precio"] / x["m2"]) if disponibles else None

    def fmt_prop(p):
        if not p:
            return None
        return {"id": p["id"], "titulo": p["titulo"], "ciudad": p["ciudad"],
                "precio": p["precio"], "m2": p["m2"],
                "precio_m2": round(p["precio"] / p["m2"], 0)}

    return json.dumps({
        "ambito": scope,
        "resumen_general": {
            "total_propiedades": total,
            "disponibles": len(disponibles),
            "reservadas": len(reservadas),
            "vendidas": len(vendidas),
            "tasa_disponibilidad_pct": round(len(disponibles) / total * 100, 1),
        },
        "estadisticas_precio": {
            "precio_medio": round(media(precios), 0),
            "precio_mediano": round(mediana(precios), 0),
            "precio_minimo": round(min(precios), 0),
            "precio_maximo": round(max(precios), 0),
            "precio_m2_medio": round(media(precios_m2), 0),
            "precio_m2_mediano": round(mediana(precios_m2), 0),
        },
        "caracteristicas_medias": {
            "m2_medio": round(media(m2_vals), 1),
            "pct_con_garaje": round(sum(1 for p in propiedades if p["garaje"]) / total * 100, 1),
            "pct_con_piscina": round(sum(1 for p in propiedades if p["piscina"]) / total * 100, 1),
            "antiguedad_media": round(media([p["antiguedad"] for p in propiedades]), 1),
        },
        "distribucion_por_tipo": distribucion_tipos,
        "estadisticas_por_ciudad": estadisticas_ciudad if estadisticas_ciudad else None,
        "propiedades_destacadas": {
            "mas_economica": fmt_prop(mas_economica),
            "mas_cara": fmt_prop(mas_cara),
            "mejor_precio_m2": fmt_prop(mejor_precio_m2),
        },
    }, ensure_ascii=False, indent=2)
