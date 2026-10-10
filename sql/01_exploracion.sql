-- =============================================================================
-- 01_exploracion.sql
-- Comprobaciones antes de calcular nada. No modifica datos.
-- =============================================================================

-- 1. Primeras filas, a ojo
SELECT * FROM catalogo LIMIT 10;

-- 2. ¿Con qué tipo se ha guardado cada columna?
--    Un precio guardado como texto se ordena alfabéticamente ("9.99" > "12.95")
--    y un vacío guardado como '' en lugar de NULL contaría en COUNT().
SELECT marca,
       typeof(precio_actual)     AS tipo_precio,
       typeof(precio_original)   AS tipo_original,
       typeof(referencia_modelo) AS tipo_ref,
       COUNT(*)                  AS n
FROM catalogo
GROUP BY marca, tipo_precio, tipo_original, tipo_ref;
-- Resultado validado: la suma de n = 1.211. Hallazgos:
--   · 3 productos de Massimo Dutti sin precio (no cargaron en la web)
--   · 1 producto de Zara con precio_original guardado como texto (el único rebajado)

-- 3. Recuento por marca y categoría (totales de referencia)
SELECT marca, categoria, COUNT(*) AS n
FROM catalogo
GROUP BY marca, categoria
ORDER BY categoria, marca;
-- camiseta: H&M 219 · Lefties 28 · Massimo Dutti 34 · Primark 42 · Zara 135
-- vaquero:  H&M 355 · Lefties 65 · Massimo Dutti 53 · Primark 61 · Zara 219
