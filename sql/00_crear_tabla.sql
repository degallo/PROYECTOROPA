-- =============================================================================
-- 00_crear_tabla.sql
-- Estructura de la tabla de partida.
--
-- Datos: catálogo online de 16 cadenas de moda en España, sección mujer,
-- recogido el 10/10/2026. Dos categorías: camiseta de manga larga y vaquero.
-- Una fila por modelo (no por variante de color). Dos ficheros, mismo esquema:
--   · data/moda_catalogo_2026-10-10.csv            1.211 filas · 5 marcas originales
--     (Primark, Lefties, H&M, Zara, Massimo Dutti)
--   · data/moda_catalogo_ampliacion_2026-10-10.csv   486 filas · 11 marcas nuevas
--     (Mango; Springfield, Cortefiel, Pedro del Hierro, Women'secret; Desigual,
--      Adolfo Domínguez, Bimba y Lola, Scalpers, El Ganso, Silbon)
--   Total: 1.697 filas. scripts/construir_bd.py carga los dos (o solo el original
--   con --solo-5-marcas).
--
-- Importación:
--   · DB Browser for SQLite: Archivo > Importar > Tabla desde CSV (nombre: catalogo)
--   · sqlite3 (terminal):    .mode csv
--                            .import --skip 1 data/moda_catalogo_2026-10-10.csv catalogo
--                            .import --skip 1 data/moda_catalogo_ampliacion_2026-10-10.csv catalogo
-- =============================================================================

DROP TABLE IF EXISTS catalogo;
CREATE TABLE catalogo (
    marca              TEXT,     -- una de las 16 de la tabla `marcas`
    categoria          TEXT,     -- camiseta | vaquero
    nombre             TEXT,     -- nombre comercial tal como aparece en la web
    precio_actual      REAL,     -- precio en euros el día de la recogida
    precio_original    TEXT,     -- precio antes de rebaja, si lo hay (se elimina en 02)
    referencia_modelo  TEXT,     -- TEXT para conservar ceros a la izquierda (H&M: '0999727')
    clasificacion_web  TEXT,     -- familia o ruta de la web (Zara, Lefties, H&M, Mango, Tendam…)
    n_colores          INTEGER,  -- nº de colores del modelo (no disponible en Massimo Dutti)
    url                TEXT,
    fecha_recogida     TEXT
);

-- -----------------------------------------------------------------------------
-- Grupo empresarial o segmento de cada marca. Se usa con JOIN en v_resumen_precios
-- (antes era un CASE Inditex / Otros dentro de la vista).
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS marcas;
CREATE TABLE marcas (
    marca  TEXT PRIMARY KEY,
    grupo  TEXT NOT NULL
);
INSERT INTO marcas (marca, grupo) VALUES
    ('Lefties',          'Inditex'),
    ('Zara',             'Inditex'),
    ('Massimo Dutti',    'Inditex'),
    ('Springfield',      'Tendam'),
    ('Cortefiel',        'Tendam'),
    ('Pedro del Hierro', 'Tendam'),
    ('Women''secret',    'Tendam'),
    ('Mango',            'Mango'),
    ('H&M',              'H&M'),
    ('Primark',          'Primark'),
    ('Desigual',         'Premium española'),
    ('Adolfo Domínguez', 'Premium española'),
    ('Bimba y Lola',     'Premium española'),
    ('Scalpers',         'Premium española'),
    ('El Ganso',         'Premium española'),
    ('Silbon',           'Premium española');
