-- =============================================================================
-- 00_crear_tabla.sql
-- Estructura de la tabla de partida.
--
-- Datos: catálogo online de 5 cadenas de moda en España (Primark, Lefties, H&M,
-- Zara, Massimo Dutti), sección mujer, recogido el 10/10/2026.
-- Dos categorías: camiseta de manga larga y vaquero. 1.211 modelos (no variantes
-- de color). Fichero: data/moda_catalogo_2026-10-10.csv
--
-- Importación:
--   · DB Browser for SQLite: Archivo > Importar > Tabla desde CSV (nombre: catalogo)
--   · sqlite3 (terminal):    .mode csv
--                            .import --skip 1 data/moda_catalogo_2026-10-10.csv catalogo
-- =============================================================================

DROP TABLE IF EXISTS catalogo;
CREATE TABLE catalogo (
    marca              TEXT,     -- Primark | Lefties | H&M | Zara | Massimo Dutti
    categoria          TEXT,     -- camiseta | vaquero
    nombre             TEXT,     -- nombre comercial tal como aparece en la web
    precio_actual      REAL,     -- precio en euros el día de la recogida
    precio_original    TEXT,     -- precio antes de rebaja (solo 1 producto; se elimina en 02)
    referencia_modelo  TEXT,     -- TEXT para conservar ceros a la izquierda (H&M: '0999727')
    clasificacion_web  TEXT,     -- familia interna de la web (solo Zara, Lefties y H&M)
    n_colores          INTEGER,  -- nº de colores del modelo (no disponible en Massimo Dutti)
    url                TEXT,
    fecha_recogida     TEXT
);
