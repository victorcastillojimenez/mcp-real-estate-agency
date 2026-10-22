"""
db.py
-----
Utilidades de conexión y consulta a la base de datos SQLite.
"""

import os
import sqlite3
import aiosqlite
from typing import Any

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "inmobiliaria.db")
DB_PATH = os.path.normpath(DB_PATH)


def get_db_path() -> str:
    """Retorna la ruta absoluta a la base de datos."""
    return DB_PATH


async def fetch_all(query: str, params: tuple = ()) -> list[dict]:
    """Ejecuta una consulta SELECT y devuelve todos los resultados como lista de dicts."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def fetch_one(query: str, params: tuple = ()) -> dict | None:
    """Ejecuta una consulta SELECT y devuelve el primer resultado como dict."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


def fetch_all_sync(query: str, params: tuple = ()) -> list[dict]:
    """Versión síncrona de fetch_all."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def fetch_one_sync(query: str, params: tuple = ()) -> dict | None:
    """Versión síncrona de fetch_one."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
