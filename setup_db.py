"""
setup_db.py
-----------
Script para crear y poblar la base de datos SQLite con datos simulados
de propiedades inmobiliarias en España.

Ejecutar con: python setup_db.py
"""

import sqlite3
import os
import random

DB_PATH = os.path.join(os.path.dirname(__file__), "inmobiliaria.db")


def create_tables(conn: sqlite3.Connection):
    """Crea las tablas necesarias en la base de datos."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS propiedades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            tipo TEXT NOT NULL,               -- piso, casa, chalet, local, estudio
            direccion TEXT NOT NULL,
            ciudad TEXT NOT NULL,
            barrio TEXT NOT NULL,
            m2 INTEGER NOT NULL,
            habitaciones INTEGER NOT NULL,
            banos INTEGER NOT NULL,
            precio REAL NOT NULL,
            antiguedad INTEGER NOT NULL,       -- años de antigüedad
            garaje INTEGER NOT NULL DEFAULT 0, -- 0 = no, 1 = sí
            piscina INTEGER NOT NULL DEFAULT 0,
            descripcion TEXT,
            estado TEXT NOT NULL DEFAULT 'disponible' -- disponible, reservado, vendido
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            propiedad_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            precio_venta REAL NOT NULL,
            tipo_operacion TEXT NOT NULL,      -- venta, alquiler
            FOREIGN KEY (propiedad_id) REFERENCES propiedades(id)
        )
    """)
    conn.commit()
    print("[OK] Tablas creadas correctamente.")


def insert_properties(conn: sqlite3.Connection):
    """Inserta propiedades simuladas realistas en la base de datos."""
    cursor = conn.cursor()

    propiedades = [
        # Madrid
        ("Piso luminoso en el centro de Madrid", "piso", "Calle Gran Vía 42", "Madrid", "Centro", 75, 2, 1, 320000, 25, 0, 0,
         "Espectacular piso en pleno centro de Madrid, reformado completamente en 2022. Suelos de parquet, cocina moderna equipada y grandes ventanales.", "disponible"),
        ("Ático con terraza en Salamanca", "piso", "Calle Serrano 108", "Madrid", "Salamanca", 130, 3, 2, 780000, 10, 1, 0,
         "Ático de lujo en el exclusivo barrio de Salamanca. Terraza de 40m², vistas panorámicas a la ciudad y acabados premium.", "disponible"),
        ("Chalet adosado en Pozuelo", "chalet", "Urbanización La Finca Calle Roble 7", "Madrid", "Pozuelo de Alarcón", 280, 5, 4, 950000, 5, 2, 1,
         "Impresionante chalet adosado en la mejor urbanización de Pozuelo. Jardín privado, piscina comunitaria y seguridad 24h.", "disponible"),
        ("Estudio reformado en Malasaña", "estudio", "Calle Fuencarral 98", "Madrid", "Malasaña", 40, 1, 1, 185000, 40, 0, 0,
         "Estudio completamente reformado en el corazón de Malasaña. Ideal para inversión o jóvenes profesionales.", "disponible"),
        ("Piso familiar en Alcobendas", "piso", "Avenida de España 15", "Madrid", "Alcobendas", 100, 4, 2, 290000, 20, 1, 0,
         "Amplio piso familiar en zona residencial tranquila. Cerca de colegios internacionales y zonas verdes.", "reservado"),
        ("Local comercial en Retiro", "local", "Calle Menéndez Pelayo 55", "Madrid", "Retiro", 120, 0, 1, 450000, 15, 0, 0,
         "Excelente local comercial con amplio escaparate en zona de alto tránsito peatonal.", "disponible"),
        ("Piso con garaje en Chamberí", "piso", "Calle Almagro 22", "Madrid", "Chamberí", 90, 3, 2, 420000, 30, 1, 0,
         "Clásico piso madrileño en Chamberí con garaje incluido. Techos altos, molduras originales y mucha luz.", "vendido"),

        # Barcelona
        ("Piso modernista en el Eixample", "piso", "Carrer de Provença 210", "Barcelona", "Eixample", 110, 3, 2, 520000, 100, 0, 0,
         "Maravilloso piso en edificio modernista del Eixample. Conserva elementos originales: suelos hidráulicos, techos ornamentados.", "disponible"),
        ("Apartamento con vistas al mar", "piso", "Passeig de Gràcia 45", "Barcelona", "Barceloneta", 65, 2, 1, 390000, 15, 0, 0,
         "Apartamento con vistas al Mediterráneo en la zona más cotizada de Barcelona. Reformado con materiales de alta gama.", "disponible"),
        ("Chalet con jardín en Pedralbes", "chalet", "Carrer de Montevideo 22", "Barcelona", "Pedralbes", 350, 6, 4, 1850000, 30, 1, 1,
         "Villa de lujo en la exclusiva zona de Pedralbes. Jardín de 600m², piscina infinity y vistas a la ciudad.", "disponible"),
        ("Estudio en el barrio Gótico", "estudio", "Carrer del Bisbe 8", "Barcelona", "Gótico", 35, 1, 1, 210000, 80, 0, 0,
         "Encantador estudio en pleno barrio Gótico con mucho carácter. Ideal para alquiler turístico.", "disponible"),
        ("Piso en Sant Martí", "piso", "Carrer de Roc Boronat 120", "Barcelona", "Sant Martí", 80, 3, 2, 310000, 8, 1, 0,
         "Moderno piso en el nuevo 22@ de Barcelona. Edificio de diseño con zonas comunes premium.", "reservado"),

        # Valencia
        ("Piso céntrico en Valencia", "piso", "Calle Colón 28", "Valencia", "Centro", 85, 3, 2, 210000, 35, 0, 0,
         "Magnífico piso en la calle más comercial de Valencia. Totalmente reformado, listo para entrar a vivir.", "disponible"),
        ("Chalet en La Eliana", "chalet", "Urbanización Los Pinos Calle Cedro 4", "Valencia", "La Eliana", 220, 4, 3, 380000, 12, 1, 1,
         "Fantástico chalet con gran jardín y piscina propia en La Eliana. Zona tranquila y con todos los servicios.", "disponible"),
        ("Ático en la playa de Valencia", "piso", "Paseo Neptuno 60", "Valencia", "Malvarrosa", 90, 2, 2, 350000, 5, 1, 0,
         "Ático de nueva construcción con impresionantes vistas al mar. Terraza de 60m² y plaza de garaje.", "disponible"),
        ("Piso en el Carmen", "piso", "Carrer de les Barques 12", "Valencia", "El Carmen", 70, 2, 1, 175000, 50, 0, 0,
         "Piso con mucho encanto en el histórico barrio del Carmen. Ideal para reforma o inversión.", "vendido"),

        # Sevilla
        ("Piso en el centro histórico", "piso", "Calle Sierpes 45", "Sevilla", "Centro", 80, 3, 1, 195000, 60, 0, 0,
         "Piso histórico en pleno centro de Sevilla a pocos metros de la Catedral. Patio interior andaluz.", "disponible"),
        ("Casa unifamiliar en Triana", "casa", "Calle Betis 33", "Sevilla", "Triana", 160, 4, 3, 320000, 40, 0, 1,
         "Auténtica casa andaluza en el popular barrio de Triana con patio de flores y azulejos típicos.", "disponible"),
        ("Piso moderno en Los Bermejales", "piso", "Avenida de la Raza 24", "Sevilla", "Los Bermejales", 95, 3, 2, 245000, 15, 1, 0,
         "Luminoso piso en zona residencial de Los Bermejales, cerca del parque. Comunidad con piscina.", "disponible"),
        ("Chalet en Mairena del Aljarafe", "chalet", "Urbanización Entrenúcleos Calle Mimosa 8", "Sevilla", "Mairena del Aljarafe", 200, 4, 3, 290000, 18, 1, 1,
         "Chalet pareado en urbanización privada con zonas comunes. A 10 minutos del centro de Sevilla.", "disponible"),

        # Bilbao
        ("Piso en el Ensanche", "piso", "Gran Vía Don Diego López de Haro 55", "Bilbao", "Ensanche", 95, 3, 2, 310000, 20, 1, 0,
         "Magnifico piso en la Gran Vía de Bilbao. Reformado con materiales de calidad, garaje incluido.", "disponible"),
        ("Loft en Abandoibarra", "estudio", "Calle Uribitarte 14", "Bilbao", "Abandoibarra", 55, 1, 1, 235000, 3, 0, 0,
         "Moderno loft frente al Museo Guggenheim. Diseño contemporáneo con vistas a la ría.", "disponible"),
        ("Casa en Getxo", "casa", "Avenida Los Chopos 18", "Bilbao", "Getxo", 180, 5, 3, 495000, 25, 1, 1,
         "Espléndida casa en la exclusiva zona de Getxo a 200 metros del mar. Jardín con piscina.", "disponible"),
        ("Piso en Deusto", "piso", "Calle Iturribide 40", "Bilbao", "Deusto", 75, 3, 1, 185000, 35, 0, 0,
         "Piso bien distribuido en la zona universitaria de Deusto. Excelente comunicación con el centro.", "reservado"),
        ("Local en el Casco Viejo", "local", "Calle Somera 22", "Bilbao", "Casco Viejo", 80, 0, 1, 220000, 45, 0, 0,
         "Local comercial céntrico en el animado Casco Viejo de Bilbao. Bajo nivel con mucho tráfico peatonal.", "disponible"),
    ]

    cursor.executemany("""
        INSERT INTO propiedades 
        (titulo, tipo, direccion, ciudad, barrio, m2, habitaciones, banos, precio, 
         antiguedad, garaje, piscina, descripcion, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, propiedades)

    # Insertar algunas transacciones históricas
    transacciones = [
        (7, "2024-03-15", 418000, "venta"),
        (16, "2024-07-20", 172000, "venta"),
    ]
    cursor.executemany("""
        INSERT INTO transacciones (propiedad_id, fecha, precio_venta, tipo_operacion)
        VALUES (?, ?, ?, ?)
    """, transacciones)

    conn.commit()
    print(f"[OK] Insertadas {len(propiedades)} propiedades y {len(transacciones)} transacciones.")


def main():
    """Función principal para crear e inicializar la base de datos."""
    print(f"[INFO] Creando base de datos en: {DB_PATH}")

    # Eliminar BD existente si la hay (para empezar limpio)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("[INFO] Base de datos anterior eliminada.")

    conn = sqlite3.connect(DB_PATH)
    try:
        create_tables(conn)
        insert_properties(conn)
        print("\n[OK] Base de datos creada y poblada correctamente.")
        print(f"   Ubicacion: {DB_PATH}")

        # Verificación rápida
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM propiedades")
        count = cursor.fetchone()[0]
        print(f"   Total propiedades: {count}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
