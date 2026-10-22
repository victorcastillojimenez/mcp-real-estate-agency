"""
api_tools.py
------------
Tools del MCP Server que consumen APIs de terceros (sin API key requerida).

Tools incluidas:
    1. geocode_address   -> Nominatim (OpenStreetMap) - convierte dirección a coordenadas
    2. convert_currency  -> Frankfurter API - convierte divisa a otra en tiempo real
"""

import httpx
import json
from mcp.server.fastmcp import FastMCP

# Esta instancia será registrada en el servidor principal
mcp = FastMCP("InmobiliariaServer-API")


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 1: Geocodificación de direcciones (OpenStreetMap Nominatim)
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
async def geocode_address(address: str) -> str:
    """
    Obtiene las coordenadas geográficas y datos de ubicación de una dirección.
    
    Utiliza la API gratuita de Nominatim (OpenStreetMap) para convertir
    una dirección en texto a coordenadas GPS y metadatos de la ubicación.

    Args:
        address: Dirección completa a geocodificar 
                 (ej: "Calle Gran Vía 42, Madrid, España")

    Returns:
        JSON con: latitud, longitud, dirección formateada, tipo de zona y
                  desglose por componente (ciudad, país, código postal).
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "addressdetails": 1,
        "limit": 1,
        "accept-language": "es",
    }
    headers = {
        "User-Agent": "InmobiliariaApp/1.0 (proyecto-universitario)"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        if not data:
            return json.dumps({
                "error": "No se encontraron resultados para la dirección proporcionada.",
                "address": address
            }, ensure_ascii=False)

        result = data[0]
        addr_details = result.get("address", {})

        return json.dumps({
            "latitud": float(result["lat"]),
            "longitud": float(result["lon"]),
            "direccion_formateada": result.get("display_name", ""),
            "tipo": result.get("type", ""),
            "clase": result.get("class", ""),
            "detalles": {
                "calle": addr_details.get("road", addr_details.get("pedestrian", "")),
                "barrio": addr_details.get("neighbourhood", addr_details.get("suburb", "")),
                "ciudad": addr_details.get("city", addr_details.get("town", addr_details.get("village", ""))),
                "provincia": addr_details.get("state", ""),
                "pais": addr_details.get("country", ""),
                "codigo_postal": addr_details.get("postcode", ""),
            },
            "importancia": float(result.get("importance", 0)),
        }, ensure_ascii=False, indent=2)

    except httpx.TimeoutException:
        return json.dumps({"error": "Timeout al conectar con la API de Nominatim."}, ensure_ascii=False)
    except httpx.HTTPError as e:
        return json.dumps({"error": f"Error HTTP: {str(e)}"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Error inesperado: {str(e)}"}, ensure_ascii=False)


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 2: Conversión de divisas (Frankfurter API)
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
async def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """
    Convierte un precio inmobiliario de una divisa a otra usando tasas en tiempo real.
    
    Utiliza la API gratuita de Frankfurter (datos del Banco Central Europeo)
    para obtener tasas de cambio actualizadas sin necesidad de API key.

    Divisas soportadas: EUR, USD, GBP, CHF, JPY, CAD, AUD, SEK, NOK, DKK,
                        PLN, CZK, HUF, CNY, HKD, SGD, MXN, BRL, AED, entre otras.

    Args:
        amount:        Cantidad a convertir (ej: 350000.0)
        from_currency: Divisa origen en formato ISO 4217 (ej: "EUR")
        to_currency:   Divisa destino en formato ISO 4217 (ej: "USD")

    Returns:
        JSON con: cantidad convertida, tasa de cambio, divisa origen/destino y fecha.
    """
    from_currency = from_currency.upper().strip()
    to_currency = to_currency.upper().strip()

    url = "https://api.frankfurter.dev/v1/latest"
    params = {
        "from": from_currency,
        "to": to_currency,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        if "rates" not in data or to_currency not in data["rates"]:
            return json.dumps({
                "error": f"No se pudo obtener la tasa de cambio de {from_currency} a {to_currency}.",
                "divisas_disponibles": list(data.get("rates", {}).keys())
            }, ensure_ascii=False)

        rate = data["rates"][to_currency]
        converted = round(amount * rate, 2)

        return json.dumps({
            "cantidad_original": amount,
            "divisa_origen": from_currency,
            "cantidad_convertida": converted,
            "divisa_destino": to_currency,
            "tasa_de_cambio": rate,
            "fecha_tasa": data.get("date", ""),
            "descripcion": f"{amount:,.2f} {from_currency} = {converted:,.2f} {to_currency}",
        }, ensure_ascii=False, indent=2)

    except httpx.TimeoutException:
        return json.dumps({"error": "Timeout al conectar con la API de Frankfurter."}, ensure_ascii=False)
    except httpx.HTTPError as e:
        return json.dumps({"error": f"Error HTTP: {str(e)}"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Error inesperado: {str(e)}"}, ensure_ascii=False)
