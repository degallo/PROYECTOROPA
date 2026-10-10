-- =============================================================================
-- 02_limpieza.sql
-- Un único precio de catálogo para toda la tabla.
--
-- La recogida se hizo sin rebajas activas: solo 1 de 1.211 productos estaba
-- rebajado (JEANS Z1975 WIDE LEG JOGGER TIRO ALTO, 15,99 € → 27,95 €).
-- Se normaliza a su precio original ANTES de borrar la columna; si no, ese
-- producto se compararía con precio de rebaja sin dejar rastro.
-- =============================================================================

UPDATE catalogo
SET precio_actual = CAST(precio_original AS REAL)   -- estaba guardado como texto
WHERE precio_original IS NOT NULL AND precio_original <> '';

ALTER TABLE catalogo DROP COLUMN precio_original;    -- requiere SQLite ≥ 3.35

-- Comprobación: debe devolver 27.95
SELECT nombre, precio_actual
FROM catalogo
WHERE nombre = 'JEANS Z1975 WIDE LEG JOGGER TIRO ALTO';
