-- =============================================================================
-- 02_limpieza.sql
-- Un único precio de catálogo para toda la tabla.
--
-- Criterio principal: PRECIO DE CATÁLOGO SIN REBAJA. Si un producto está
-- rebajado, precio_actual se sustituye por su precio original.
--   · En las 5 marcas originales solo había 1 producto rebajado de 1.211
--     (JEANS Z1975 WIDE LEG JOGGER TIRO ALTO, 15,99 € → 27,95 €).
--   · En las 11 marcas nuevas hay 156 rebajados de 486 (Springfield 45 de 50,
--     Women'secret 13 de 13, descuentos medios del 30–49 %).
--
-- Antes de borrar precio_original se guarda lo que costaba el producto ese día
-- en dos columnas nuevas, para el análisis de sensibilidad (¿cambia algo si se
-- compara el precio rebajado?):
--   · precio_venta: lo que marcaba la web el 10/10/2026 (con rebaja si la había)
--   · rebajado:     1 si el producto tenía precio original, 0 si no
-- Las vistas de 05 y 06 siguen usando precio_actual (= precio de catálogo).
-- =============================================================================

ALTER TABLE catalogo ADD COLUMN precio_venta REAL;
ALTER TABLE catalogo ADD COLUMN rebajado INTEGER;

UPDATE catalogo
SET precio_venta = precio_actual,
    rebajado     = (precio_original IS NOT NULL AND precio_original <> '');

UPDATE catalogo
SET precio_actual = CAST(precio_original AS REAL)   -- estaba guardado como texto
WHERE rebajado = 1;

ALTER TABLE catalogo DROP COLUMN precio_original;    -- requiere SQLite ≥ 3.35

-- Comprobación 1: debe devolver 27.95 (precio de catálogo) y 15.99 (precio de venta)
SELECT nombre, precio_actual, precio_venta
FROM catalogo
WHERE nombre = 'JEANS Z1975 WIDE LEG JOGGER TIRO ALTO';

-- Comprobación 2: % del catálogo rebajado por marca (todas las filas, antes de clasificar)
SELECT marca, COUNT(*) AS filas, SUM(rebajado) AS rebajados,
       ROUND(100.0 * AVG(rebajado), 0) AS pct_rebajado
FROM catalogo
GROUP BY marca
ORDER BY pct_rebajado DESC;
