-- =============================================================================
-- 04_clasificar.sql
-- Asigna a cada prenda un motivo de exclusión o '7_basica', usando las reglas
-- de 03_reglas_clasificacion.sql.
--
-- Definición de "básica":
--   · Camiseta: manga larga, lisa o de canalé, sin estampado ni adornos, que sea
--     realmente una camiseta (no polo, blusa, sudadera, top de pijama ni deporte).
--   · Vaquero: pantalón largo de tela vaquera, cualquier corte, sin estampados
--     ni adornos/acabados especiales, fuera de líneas especiales (premamá, adaptada).
-- =============================================================================

ALTER TABLE catalogo ADD COLUMN motivo TEXT;

-- Subconsulta correlacionada: para cada prenda, busca la primera regla que
-- encaja (menor prioridad). Si ninguna encaja, COALESCE devuelve '7_basica'.
UPDATE catalogo
SET motivo = COALESCE(
    (SELECT r.motivo
     FROM reglas_clasificacion AS r
     WHERE r.categoria = catalogo.categoria
       AND (   (r.campo = 'nombre'            AND lower(catalogo.nombre) LIKE r.patron)
            OR (r.campo = 'clasificacion_web' AND catalogo.clasificacion_web LIKE r.patron))
     ORDER BY r.prioridad
     LIMIT 1),
    '7_basica');

-- Comprobación 1: básicas por marca (los totales deben cuadrar con 01_exploracion)
SELECT categoria, marca,
       SUM(motivo = '7_basica') AS basicas,   -- una comparación vale 1 o 0
       COUNT(*)                 AS total
FROM catalogo
GROUP BY categoria, marca
ORDER BY categoria, marca;
-- camiseta: H&M 87 · Lefties 9 · Massimo Dutti 14 · Primark 23 · Zara 50   (183)
-- vaquero:  H&M 289 · Lefties 28 · Massimo Dutti 33 · Primark 45 · Zara 101 (496)

-- Comprobación 2: revisar el cajón de sastre. Si aparece algo que no es básico,
-- falta una regla en 03_reglas_clasificacion.sql.
SELECT categoria, marca, nombre, precio_actual
FROM catalogo
WHERE motivo = '7_basica'
ORDER BY categoria, marca, precio_actual;
