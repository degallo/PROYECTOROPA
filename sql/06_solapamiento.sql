-- =============================================================================
-- 06_solapamiento.sql
-- ¿Qué marcas compiten en el mismo territorio de precio? Dos métricas independientes.
--
-- Métrica 1 (franja central): % de las prendas de A cuyo precio cae entre el
--   p25 y el p75 de B. Asimétrica. Se ROMPE en los bordes cuando las marcas usan
--   precios redondos casi iguales (29,95 € vs 29,99 € queda "fuera") o cuando la
--   franja de una marca tiene anchura cero (Lefties camisetas: 7,99–7,99).
--   Sirve para ver quién se toca y quién no; sus porcentajes no son fiables.
--
-- Métrica 2 (tramos, MÉTRICA PRINCIPAL): coeficiente de solapamiento. Se reparte
--   el catálogo de cada marca en tramos de precio y se suma, tramo a tramo, la
--   menor de las dos cuotas. 0 % = no comparten ningún tramo; 100 % = mismo reparto.
--   Simétrica. Tramos proporcionales al precio de la prenda: 5 € en camisetas y
--   10 € en vaqueros (los vaqueros cuestan ~2,2 veces más).
--   Prueba de robustez: con 4 € / 8 € los dos pares principales se mantienen.
--
-- Las dos métricas solo usan las marcas con en_metricas = 1 en v_resumen_precios
-- (n ≥ 5 y dentro del análisis). Las 5 marcas originales entran todas.
-- =============================================================================

-- Métrica 1 -------------------------------------------------------------------
DROP VIEW IF EXISTS v_solape_franja;
CREATE VIEW v_solape_franja AS
WITH cruce AS (
    SELECT c.categoria, c.marca AS de, r.marca AS en,
           ROUND(100.0 * AVG(c.precio_actual BETWEEN r.p25 AND r.p75), 0) AS pct
    FROM catalogo AS c
    JOIN v_resumen_precios AS r ON r.categoria = c.categoria AND r.en_metricas = 1
    JOIN v_resumen_precios AS m ON m.categoria = c.categoria AND m.marca = c.marca AND m.en_metricas = 1
    WHERE c.motivo = '7_basica' AND c.precio_actual IS NOT NULL
    GROUP BY c.categoria, c.marca, r.marca
)
SELECT x.categoria,
       x.de  AS marca_a,
       x.en  AS marca_b,
       x.pct AS pct_a_en_franja_b,
       y.pct AS pct_b_en_franja_a
FROM cruce AS x
JOIN cruce AS y                       -- autounión: empareja A→B con B→A
  ON y.categoria = x.categoria AND y.de = x.en AND y.en = x.de
WHERE x.de < x.en;                    -- cada pareja una sola vez

-- Métrica 2 -------------------------------------------------------------------
DROP VIEW IF EXISTS v_solape_pares;
CREATE VIEW v_solape_pares AS
WITH tramos AS (
    SELECT c.categoria, c.marca,
           CAST(c.precio_actual / (CASE WHEN c.categoria = 'camiseta' THEN 5 ELSE 10 END) AS INTEGER) AS tramo
    FROM catalogo AS c
    JOIN v_resumen_precios AS m        -- solo marcas con n ≥ 5 y dentro del análisis
      ON m.categoria = c.categoria AND m.marca = c.marca AND m.en_metricas = 1
    WHERE c.motivo = '7_basica' AND c.precio_actual IS NOT NULL
),
reparto AS (
    SELECT categoria, marca, tramo,
           COUNT(*) * 1.0 / SUM(COUNT(*)) OVER (PARTITION BY categoria, marca) AS cuota
    FROM tramos
    GROUP BY categoria, marca, tramo
)
SELECT a.categoria,
       a.marca                         AS marca_a,
       b.marca                         AS marca_b,
       a.marca || ' – ' || b.marca     AS pareja,
       ROUND(100 * SUM(MIN(a.cuota, b.cuota)), 0) AS solape_pct   -- MIN(x, y): el menor de dos valores
FROM reparto AS a
JOIN reparto AS b
  ON b.categoria = a.categoria AND b.tramo = a.tramo AND a.marca < b.marca
GROUP BY a.categoria, a.marca, b.marca;
-- Las parejas que no aparecen tienen 0 % (no comparten ningún tramo).

-- Resultados validados --------------------------------------------------------
SELECT * FROM v_solape_pares ORDER BY categoria, solape_pct DESC;
-- camiseta: Lefties–Primark 52 · H&M–Zara 47 · H&M–Primark 35 · H&M–Lefties 31*
--           Primark–Zara 12 · H&M–Massimo Dutti 8 · Lefties–Zara 8 · Massimo Dutti–Zara 2
-- vaquero:  Lefties–Primark 97 · H&M–Zara 87 · H&M–Primark 20 · Primark–Zara 18
--           H&M–Lefties 17 · Lefties–Zara 14 · H&M–Massimo Dutti 13 · Massimo Dutti–Zara 5
-- * Frágil: con tramos de 4 € baja al 12 %. Era un efecto de dónde caen los cortes.

SELECT * FROM v_solape_franja ORDER BY categoria, MAX(pct_a_en_franja_b, pct_b_en_franja_a) DESC;
