-- =============================================================================
-- 05_resumen_precios.sql
-- Distribución de precios de las prendas básicas por categoría y marca.
--
-- SQLite no tiene función de mediana: se aproxima con NTILE(4).
--   p25 ≈ máximo del cuartil 1 · mediana ≈ máximo del cuartil 2 · p75 ≈ máximo del cuartil 3
-- Con muestras pequeñas (Lefties camisetas, n = 9) la aproximación es tosca.
-- =============================================================================

DROP VIEW IF EXISTS v_resumen_precios;
CREATE VIEW v_resumen_precios AS
WITH basicas AS (
    SELECT categoria, marca, precio_actual,
           NTILE(4) OVER (PARTITION BY categoria, marca ORDER BY precio_actual) AS cuartil
    FROM catalogo
    WHERE motivo = '7_basica'
      AND precio_actual IS NOT NULL            -- excluye 1 vaquero de Massimo Dutti sin precio
),
resumen AS (
    SELECT categoria, marca,
           COUNT(*)                                          AS n,
           MIN(precio_actual)                                AS minimo,
           MAX(CASE WHEN cuartil = 1 THEN precio_actual END) AS p25,
           MAX(CASE WHEN cuartil = 2 THEN precio_actual END) AS mediana,
           MAX(CASE WHEN cuartil = 3 THEN precio_actual END) AS p75,
           MAX(precio_actual)                                AS maximo,
           ROUND(AVG(precio_actual), 2)                      AS media
    FROM basicas
    GROUP BY categoria, marca
)
SELECT resumen.*,
       ROUND(p75 - p25, 2) AS ancho_franja,
       CASE WHEN marca IN ('Lefties', 'Zara', 'Massimo Dutti') THEN 'Inditex' ELSE 'Otros' END AS grupo,
       CASE WHEN n < 15 THEN 'Baja fiabilidad (n<15)' ELSE 'OK' END AS fiabilidad
FROM resumen;

-- Resultado validado
SELECT categoria, marca, n, minimo, p25, mediana, p75, maximo, media, fiabilidad
FROM v_resumen_precios
ORDER BY categoria, mediana;
-- camiseta  Primark        23   4.00   4.50   7.00   8.00  10.00   6.50
-- camiseta  Lefties         9   6.99   7.99   7.99   7.99   9.99   8.10  (baja fiabilidad)
-- camiseta  H&M            87   7.99   9.99  14.99  19.99  49.99  16.90
-- camiseta  Zara           50   9.95  12.95  15.95  17.95  29.95  16.39
-- camiseta  Massimo Dutti  14  29.95  29.95  29.95  39.95  39.95  33.52  (baja fiabilidad)
-- vaquero   Primark        45  10.00  14.00  18.00  18.00  24.00  17.20
-- vaquero   Lefties        28  12.99  17.99  19.99  19.99  25.99  19.24
-- vaquero   H&M           289  19.99  29.99  34.99  39.99  89.99  36.38
-- vaquero   Zara          101  25.95  29.95  35.95  39.95  59.95  34.41
-- vaquero   Massimo Dutti  32  49.95  49.95  59.95  59.95  59.95  56.51
