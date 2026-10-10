-- =============================================================================
-- 03_reglas_clasificacion.sql
-- Tabla de reglas para decidir qué es una prenda "básica".
--
-- En lugar de un CASE WHEN con 190 condiciones, las reglas se guardan como datos:
-- una fila por patrón. Añadir o quitar un criterio es un INSERT o un DELETE,
-- y el código de clasificación (04_clasificar.sql) no cambia.
--
-- Lógica: se buscan MOTIVOS PARA EXCLUIR. Una prenda que no encaja en ninguna
-- regla se considera básica ('7_basica'). Si encaja en varias, gana la de menor
-- prioridad (1 = se evalúa primero).
--
-- Nota sobre los patrones: lower() de SQLite no convierte letras acentuadas,
-- por eso las vocales con tilde se sustituyen por '_' (un carácter cualquiera):
-- '%t_rmica%' encuentra "térmica" y "TÉRMICA".
-- =============================================================================

DROP TABLE IF EXISTS reglas_clasificacion;
CREATE TABLE reglas_clasificacion (
    categoria  TEXT    NOT NULL,   -- 'camiseta' o 'vaquero'
    prioridad  INTEGER NOT NULL,   -- orden de evaluación
    motivo     TEXT    NOT NULL,   -- etiqueta que se asigna
    campo      TEXT    NOT NULL CHECK (campo IN ('nombre', 'clasificacion_web')),
    patron     TEXT    NOT NULL    -- patrón LIKE (sobre lower(nombre) o sobre clasificacion_web)
);


-- -----------------------------------------------------------------------------
-- CAMISETAS
-- -----------------------------------------------------------------------------

-- 1_no_es_camiseta: No es una camiseta (polo, sudadera, blusa, pack, pijama…)
INSERT INTO reglas_clasificacion (categoria, prioridad, motivo, campo, patron) VALUES
    ('camiseta', 1, '1_no_es_camiseta', 'nombre', '%polo%'),
    ('camiseta', 1, '1_no_es_camiseta', 'nombre', '%sudadera%'),
    ('camiseta', 1, '1_no_es_camiseta', 'nombre', '%chaqueta%'),
    ('camiseta', 1, '1_no_es_camiseta', 'nombre', '%rdigan%'),
    ('camiseta', 1, '1_no_es_camiseta', 'nombre', '%bolero%'),
    ('camiseta', 1, '1_no_es_camiseta', 'nombre', '%blusa%'),
    ('camiseta', 1, '1_no_es_camiseta', 'nombre', '%conjunto%'),
    ('camiseta', 1, '1_no_es_camiseta', 'nombre', '%pack%'),
    ('camiseta', 1, '1_no_es_camiseta', 'nombre', '%maillot%'),
    ('camiseta', 1, '1_no_es_camiseta', 'nombre', '%capucha%'),
    ('camiseta', 1, '1_no_es_camiseta', 'nombre', '%denim%'),
    ('camiseta', 1, '1_no_es_camiseta', 'nombre', '%al codo%'),
    ('camiseta', 1, '1_no_es_camiseta', 'clasificacion_web', '%PIJAMA%');

-- 2_deporte_funcional: Prenda deportiva o técnica
INSERT INTO reglas_clasificacion (categoria, prioridad, motivo, campo, patron) VALUES
    ('camiseta', 2, '2_deporte_funcional', 'nombre', '%dry%'),
    ('camiseta', 2, '2_deporte_funcional', 'nombre', '%softmove%'),
    ('camiseta', 2, '2_deporte_funcional', 'nombre', '%deporte%'),
    ('camiseta', 2, '2_deporte_funcional', 'nombre', '%running%'),
    ('camiseta', 2, '2_deporte_funcional', 'nombre', '%warming%'),
    ('camiseta', 2, '2_deporte_funcional', 'nombre', '%cooling%'),
    ('camiseta', 2, '2_deporte_funcional', 'nombre', '%t_rmica%'),
    ('camiseta', 2, '2_deporte_funcional', 'nombre', '%sculpting%'),
    ('camiseta', 2, '2_deporte_funcional', 'nombre', '%heat iq%');

-- 3_estampado_rayas: Estampado, rayas, texto, licencias o colaboraciones
INSERT INTO reglas_clasificacion (categoria, prioridad, motivo, campo, patron) VALUES
    ('camiseta', 3, '3_estampado_rayas', 'nombre', '%raya%'),
    ('camiseta', 3, '3_estampado_rayas', 'nombre', '%estampa%'),
    ('camiseta', 3, '3_estampado_rayas', 'nombre', '%texto%'),
    ('camiseta', 3, '3_estampado_rayas', 'nombre', '%cuadros%'),
    ('camiseta', 3, '3_estampado_rayas', 'nombre', '%tigre%'),
    ('camiseta', 3, '3_estampado_rayas', 'nombre', '%fruit of%'),
    ('camiseta', 3, '3_estampado_rayas', 'nombre', '%acdc%'),
    ('camiseta', 3, '3_estampado_rayas', 'nombre', '%eclipse%'),
    ('camiseta', 3, '3_estampado_rayas', 'nombre', '%tricolor%'),
    ('camiseta', 3, '3_estampado_rayas', 'nombre', '%berenson%'),
    ('camiseta', 3, '3_estampado_rayas', 'clasificacion_web', '%POSICIO%'),
    ('camiseta', 3, '3_estampado_rayas', 'clasificacion_web', '%Licencias%');

-- 4_adornos_diseno: Adornos o detalles de diseño
INSERT INTO reglas_clasificacion (categoria, prioridad, motivo, campo, patron) VALUES
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%encaje%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%malla%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%transparente%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%lentejuela%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%brill%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%tachuela%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%tachas%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%cuentas%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%crochet%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%bordad%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%volante%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%frunc%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%peplum%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%drapead%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%asim_tric%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%hombro%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%off-the%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%cut%out%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%botones%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%botonadura%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%henley%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%snaps%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%cremallera%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%cadena%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%bolsillo%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%pa_uelo%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%fular%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%twist%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%girado%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%capa%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%layering%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%superpos%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%doble%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%triple%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%combinad%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%contraste%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%murci%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%globo%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%campana%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%acampanad%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%abullonad%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%mangas abiertas%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%hombreras%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%cascada%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%cruzad%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%efecto%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%plisad%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%pleated%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%smocked%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%nido de abeja%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%detalle%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%picot%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%sin rematar%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%faj_n%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%banda lateral%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%bajo el_stico%'),
    ('camiseta', 4, '4_adornos_diseno', 'nombre', '%textur%');

-- 5_tejido_de_vestir: Tejido de vestir (seda, satén, velour…)
INSERT INTO reglas_clasificacion (categoria, prioridad, motivo, campo, patron) VALUES
    ('camiseta', 5, '5_tejido_de_vestir', 'nombre', '%seda%'),
    ('camiseta', 5, '5_tejido_de_vestir', 'nombre', '%sat_n%'),
    ('camiseta', 5, '5_tejido_de_vestir', 'nombre', '%velour%'),
    ('camiseta', 5, '5_tejido_de_vestir', 'nombre', '%terciopelo%'),
    ('camiseta', 5, '5_tejido_de_vestir', 'nombre', '%acetato%');

-- 6_crop: Corte crop
INSERT INTO reglas_clasificacion (categoria, prioridad, motivo, campo, patron) VALUES
    ('camiseta', 6, '6_crop', 'nombre', '%crop%');

-- -----------------------------------------------------------------------------
-- VAQUEROS
-- -----------------------------------------------------------------------------

-- 1_no_es_vaquero_clasico: No es un vaquero clásico (vestido, falda, capri, chino, cintura elástica…)
INSERT INTO reglas_clasificacion (categoria, prioridad, motivo, campo, patron) VALUES
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%vestido%'),
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%chaqueta%'),
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%chaleco%'),
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%bermuda%'),
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%falda%'),
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%capri%'),
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%jegging%'),
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%chino%'),
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%parachute%'),
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%sarga%'),
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%efecto denim%'),
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%lino%'),
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%fluido%'),
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%jogger%'),
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%cord_n de ajuste%'),
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%drawstring%'),
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%cintura el_stica%'),
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%kw%'),
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%pinzas%'),
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%paper bag%'),
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%cargo%'),
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%carpintero%'),
    ('vaquero', 1, '1_no_es_vaquero_clasico', 'nombre', '%goma%');

-- 2_linea_especial: Línea especial (premamá, adaptada)
INSERT INTO reglas_clasificacion (categoria, prioridad, motivo, campo, patron) VALUES
    ('vaquero', 2, '2_linea_especial', 'nombre', 'mama %'),
    ('vaquero', 2, '2_linea_especial', 'nombre', '%adaptive%');

-- 3_estampado_rayas: Estampado, rayas, texto, licencias o colaboraciones
INSERT INTO reglas_clasificacion (categoria, prioridad, motivo, campo, patron) VALUES
    ('vaquero', 3, '3_estampado_rayas', 'nombre', '%raya%'),
    ('vaquero', 3, '3_estampado_rayas', 'nombre', '%estampad%'),
    ('vaquero', 3, '3_estampado_rayas', 'nombre', '%animal%'),
    ('vaquero', 3, '3_estampado_rayas', 'nombre', '%flor%'),
    ('vaquero', 3, '3_estampado_rayas', 'nombre', '%paisley%'),
    ('vaquero', 3, '3_estampado_rayas', 'nombre', '%lunares%'),
    ('vaquero', 3, '3_estampado_rayas', 'nombre', '%jacquard%'),
    ('vaquero', 3, '3_estampado_rayas', 'nombre', '%estrella%'),
    ('vaquero', 3, '3_estampado_rayas', 'nombre', '%fruit of%'),
    ('vaquero', 3, '3_estampado_rayas', 'nombre', '%bicolor%'),
    ('vaquero', 3, '3_estampado_rayas', 'nombre', '%pintura%'),
    ('vaquero', 3, '3_estampado_rayas', 'nombre', '%salpicadura%'),
    ('vaquero', 3, '3_estampado_rayas', 'nombre', '%franjas%'),
    ('vaquero', 3, '3_estampado_rayas', 'nombre', '%bandas laterales%');

-- 4_adornos_acabado: Adornos o acabados especiales (tachas, rotos, encerado…)
INSERT INTO reglas_clasificacion (categoria, prioridad, motivo, campo, patron) VALUES
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%tachas%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%tachuela%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%strass%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%stras%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%brill%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%lentejuela%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%perlas%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%abalorio%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%bordad%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%encaje%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%patchwork%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%combinad%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%decorativ%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%cremallera%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%cordones%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%ojales%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%alamares%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%lazada%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%cintur_n%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%belted%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%fular%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%trenzad%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%flock%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%terciopelo%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%afelpad%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%bouc%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%revestido%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%coated%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%encerado%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%craquelad%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%efecto%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%textura%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%plisad%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%pliegue%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%costura%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%pespunte%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%contraste%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%raya planchada%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%con raya%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%rotos%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%desgastado%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%deshilachado%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%sin cintura%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%cintura cruzada%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%cintura doblada%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%cintura plegada%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%doble%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%abertura%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%bolsillos de parche%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%bolsillo delantero%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%nervio%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%detalle%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%total look%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%selvedge%'),
    ('vaquero', 4, '4_adornos_acabado', 'nombre', '%split seam%');

-- Comprobación: reglas por categoría y motivo (camiseta 97, vaquero 94; total 191)
SELECT categoria, motivo, COUNT(*) AS n_patrones
FROM reglas_clasificacion
GROUP BY categoria, motivo
ORDER BY categoria, motivo;
