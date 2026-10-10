# Ampliación del Proyecto 4: de 5 a 16 marcas

> Para Claude Code. Lee esto **después** de `CLAUDE.md`. Todo lo que dice `CLAUDE.md` sigue en vigor
> (cómo trabajar con Javi, la frontera "posicionamiento, no estrategia", criterios de visualización,
> lo que no hay que hacer), salvo lo que este documento cambia de forma explícita.

---

## 0. Qué ha cambiado y qué te pide Javi

Javi ha autorizado añadir **11 marcas** al análisis. Los datos se recogieron el mismo día (10/10/2026),
con el mismo método (web española, sección mujer, camiseta de manga larga y vaquero, una fila por modelo):

| Grupo | Marcas nuevas |
|---|---|
| Mango (grupo propio) | Mango |
| Tendam | Springfield, Cortefiel, Pedro del Hierro, Women'secret |
| Gama media-alta / premium española | Desigual, Adolfo Domínguez, Bimba y Lola, Scalpers, El Ganso, Silbon |

**Tu tarea:** integrar estas marcas en la base, ampliar las reglas de clasificación, y **rehacer el
análisis completo** (resumen, solapamiento, robustez, gráficos, deck) con las 16 marcas.

**Lo que no cambia:** la unidad (modelo), la definición de prenda básica, las dos métricas, la regla de
coherencia SQL = Python y el estándar de entregables.

---

## 1. Ficheros nuevos

| Fichero | Qué es |
|---|---|
| `data/moda_catalogo_ampliacion_2026-10-10.csv` | 486 filas, **mismo esquema** que el CSV original |
| `data/raw_ampliacion/*.json` | Brutos de la recogida, uno por marca, cada uno con una `nota` de método |
| `scripts/unificar_raw_ampliacion.py` | Convierte los brutos en el CSV. No hace falta volver a ejecutarlo |

Filas brutas por marca (antes de clasificar):

| Marca | Camisetas | Vaqueros | Rebajados | Notas de recogida |
|---|---|---|---|---|
| Mango | 28 | 177 | 45 | Incluye líneas premamá, tallas plus, pana y cargo, que las reglas tienen que excluir. `clasificacion_web` = ruta de la web (`vaqueros/premama`, `camisetas/basicas`…) |
| Springfield | 27 | 23 | **45 de 50** | Solo marca propia (la web vende marcas invitadas). Descuentos casi permanentes: ver sección 3 |
| Cortefiel | 19 | 18 | 15 | Solo marca propia |
| Pedro del Hierro | 15 | 15 | 15 | Sin subcategoría de manga larga: se filtró leyendo cada ficha |
| Women'secret | 13 | **0** | 13 | Lencería/homewear: **no vende vaqueros**. Cada color es un código distinto, y hay camisetas de pijama y de deporte (`clasificacion_web`) |
| Desigual | 5 | 42 | 11 | La categoría de manga larga tiene 5 productos, todos estampados o camisas |
| Adolfo Domínguez | 4 | 9 | 1 | Catálogo muy corto. Solo línea Mujer |
| Bimba y Lola | 19 | 13 | 11 | Vaqueros = pantalones "denim" (no hay categoría propia) |
| Scalpers | 15 | 32 | 0 | Solo marca propia (excluidas Lacoste, Levi's, Samsøe…). Agrupado por código de modelo |
| El Ganso | **0** | 3 | 0 | **No tiene camisetas de manga larga de mujer.** Se excluyó un vaquero de hombre que aparecía en Mujer |
| Silbon | 4 | 5 | 0 | Agrupado por nombre sin color |

Comprobado: 0 duplicados por `(marca, categoria, referencia_modelo)` y 0 precios vacíos.

---

## 2. Paso 1 · Integrar los datos

1. Modifica `scripts/construir_bd.py` para que cargue **los dos CSV** (original + ampliación) en `catalogo`.
   Total esperado: **1.697 filas** (1.211 + 486).
2. **Conserva la versión de 5 marcas reproducible** (por ejemplo, un parámetro `--solo-5-marcas` o una
   vista filtrada). La comprobación de `CLAUDE.md`, sección 6, tiene que seguir cuadrando exactamente: es la
   prueba de que no has roto nada.
3. Actualiza `sql/00_crear_tabla.sql` (comentarios de marcas y filas) y `sql/02_limpieza.sql` (ver sección 3:
   ya no hay "un solo producto rebajado").
4. Amplía el `grupo` de `v_resumen_precios` (hoy es Inditex / Otros) a:
   `Inditex` (Lefties, Zara, Massimo Dutti) · `Tendam` (Springfield, Cortefiel, Pedro del Hierro, Women'secret) ·
   `Mango` · `H&M` · `Primark` · `Premium española` (Desigual, Adolfo Domínguez, Bimba y Lola, Scalpers, El Ganso, Silbon).
   Para no romper la vista, es más limpio crear una tabla `marcas(marca, grupo)` y hacer JOIN que alargar el CASE.

---

## 3. Paso 2 · Decidir el criterio de precio (consúltalo con Javi)

En las 5 marcas originales solo había 1 producto rebajado y se normalizó a su precio original. **Con las
nuevas marcas eso cambia:** 156 de las 486 filas tienen precio rebajado, con descuentos medios del 30–49 %.
`sql/02_limpieza.sql` tal como está **ya sustituye el precio actual por el original** cuando existe, así que
por defecto se compara precio de catálogo sin rebaja, que es coherente con la decisión de Javi.

El problema: en **Springfield** 45 de 50 productos están rebajados, y en Women'secret, 13 de 13. Cuando casi
todo el catálogo está siempre "rebajado", el precio "original" puede ser un precio de referencia que casi
nadie paga. Entonces el precio de catálogo **sobreestimaría** su posición.

Qué hacer:
- Mantén el precio original como criterio principal (coherente con las 5 marcas originales).
- Haz un **análisis de sensibilidad** con `precio_actual`: ¿cambia el orden de la escalera o alguna pareja de
  solapamiento? Recuerda que habrá que guardar ambos precios antes de que `02_limpieza.sql` borre la columna.
- Enséñale a Javi la tabla de % de catálogo rebajado por marca y el resultado de la sensibilidad, y **que
  decida él**. Va en limitaciones sea cual sea la decisión.

---

## 4. Paso 3 · Ampliar las reglas de clasificación

Con las 191 reglas actuales, una prueba rápida ya deja pasar como "básicas" prendas que claramente no lo son.
Ejemplos reales que hoy salen como `7_basica`:

- **Camisetas:** "CAMISA FLOCADA" (Desigual), "Camiseta guipur bajo", "Camiseta fluida floral", "Camiseta
  chenilla escote pico" (Cortefiel), "Jersey faldón bimateria lace", "Camiseta animal print", "Camiseta
  plumeti", "Top cuello perking lace" (Springfield), "CAMISETA FLUIDA STUDS", "CAMISETA LÚREX MANGA LARGA",
  "SCNET SMOCK LS TEE" (Scalpers), "Top de punto lurex", "Camiseta romántica", "Camiseta envolvente"
  (Pedro del Hierro), "Camiseta jacquard lana", "Camiseta lana nudo" (Bimba y Lola), y las camisetas de
  pijama y de deporte de Women'secret.
- **Vaqueros:** revisa los "BARREL - … rayas / hebilla / Snake / pony" de Bimba y Lola, los estampados y
  bordados de Desigual ("Mariposas", "flores", "paisley", "M. C. Lacroix", "Ottolinger", "Mickey™"), los de
  Scalpers ("strass", "glitter", "studs", "animal print", "tiras laterales", "volante", "apliques"), los
  capri/cropped de Pedro del Hierro, el "jogger" y el "fluido" de Bimba y Lola, y las líneas de Mango
  (premamá, tallas plus, pana, cargo) usando `clasificacion_web` cuando haga falta.

Procedimiento (el mismo que validó Javi):
1. Añade los patrones nuevos como `INSERT` en `sql/03_reglas_clasificacion.sql`, en el motivo y la prioridad
   que correspondan. No toques `04_clasificar.sql`.
2. Ojo con los patrones demasiado amplios: comprueba que cada uno nuevo **no cambia** la clasificación de
   ninguna fila de las 5 marcas originales (la comprobación del paso 1.2 lo garantiza).
3. **Revisa el cajón de sastre a mano:** lista todas las `7_basica` de las marcas nuevas y léelas. Es la regla
   metodológica de Javi.
4. Comprueba que los totales cuadran: básicas + excluidas = filas, por marca y prenda.

---

## 5. Paso 4 · Muestras pequeñas: qué hacer con cada marca

Antes de ampliar las reglas, las básicas por marca ya son pocas en muchos casos (y bajarán al afinarlas):

| | Camisetas básicas (prueba) | Vaqueros básicos (prueba) |
|---|---|---|
| ≥ 15 | Springfield (18) | Mango (134), Desigual (21), Scalpers (20), Springfield (20), Cortefiel (17) |
| 5–14 | Mango (13), Cortefiel (13), Pedro del Hierro (7), Women'secret (7), Scalpers (6) | Pedro del Hierro (10), Adolfo Domínguez (8), Bimba y Lola (6) |
| < 5 | Bimba y Lola (4), Adolfo Domínguez (1), Desigual (1), Silbon (1), El Ganso (0) | Silbon (4), El Ganso (1), Women'secret (0) |

Propuesta (confírmala con Javi):
- **n ≥ 15:** entran normal.
- **5 ≤ n < 15:** entran marcadas como **baja fiabilidad**, igual que Lefties y Massimo Dutti en camisetas.
- **n < 5:** **no se calculan cuartiles ni solapamiento** (con 1–4 modelos un P25 no significa nada). Se
  pueden enseñar como puntos individuales en el gráfico, o mencionar en el texto, pero no entran en las métricas.
- **Women'secret** no es una cadena de moda comparable (lencería y homewear) y no tiene vaqueros: propón
  dejarla fuera del análisis principal o, como mucho, como referencia aparte en camisetas.
- **Desigual en camisetas:** su catálogo de manga larga es todo estampado; es un dato en sí (no tiene básico),
  no un error.

Atenuante a comprobar: si una marca con n bajo tiene precios muy concentrados (p. ej., Scalpers casi todo a
49,99 €), la mediana es más fiable de lo que sugiere el n. Dilo con datos.

---

## 6. Paso 5 · Rehacer el análisis

Con la base nueva, en este orden:

1. `v_resumen_precios` con las 16 marcas (o las que pasen el corte) y `v_solape_pares`.
2. **Prueba de robustez** de los tramos (los dos anchos, como en el original).
3. **Ancla de control:** con la ampliación hay varias marcas premium. Ninguna de ellas debería solaparse con
   Primark o Lefties. Si alguna sale solapada, revisa el método antes de seguir.
4. **Comprueba si las conclusiones originales siguen en pie** al añadir marcas (Lefties–Primark y Zara–H&M
   como choques frontales; escalones ×2 en Inditex). Es lo primero que Javi va a preguntar.
5. **Preguntas nuevas que permite la ampliación** (sin cruzar la frontera de "posicionamiento"):
   - ¿Quién ocupa ahora **el hueco entre Zara y Massimo Dutti** que señalaba el análisis original? Una prueba
     rápida apunta a Mango y Springfield en camiseta (~16–18 €) y a Cortefiel en ese tramo, y en vaquero a
     Springfield (35,99 €) y Cortefiel (~60 €, a la altura de Massimo Dutti). Cuantifícalo con las básicas
     finales; si el hueco se llena, la recomendación del deck cambia y hay que decirlo.
   - **Tendam frente a Inditex:** ¿escalona Tendam sus marcas (Springfield → Cortefiel → Pedro del Hierro)
     igual que Inditex (Lefties → Zara → Massimo Dutti)? Calcula los ratios entre escalones con el mismo método.
   - ¿Con quién choca **Mango**? Con las cifras de la prueba, en vaquero parece estar en la franja Zara/H&M.
   - El tramo premium (Scalpers, Desigual, Pedro del Hierro, Adolfo Domínguez, Bimba y Lola): ¿hay escalones
     claros o es una franja difusa?
6. Arquitectura de precios (x,95 / x,99 / enteros) con las marcas nuevas: Tendam usa x,99 y las premium
   españolas mezclan (65, 95, 135 en Bimba y Lola; x,9 en Silbon y El Ganso).

---

## 7. Paso 6 · Gráficos y deck

- La escalera tiene ahora hasta 16 filas por panel: sigue siendo legible si ordenas por mediana y
  **agrupas por color de grupo** (Inditex con acento, Tendam con un segundo color, el resto en gris).
  Más de dos colores de acento rompe el criterio de Knaflic: si hace falta, haz un gráfico por historia
  (Inditex vs. Tendam, Mango vs. Zara/H&M) en vez de colorearlo todo.
- Las marcas de baja fiabilidad se distinguen visualmente (trazo más claro o etiqueta), como en el original.
  Las de n < 5 van como puntos sueltos o fuera.
- El eje de precio llega ahora a ~170 €: considera escala logarítmica o paneles separados para que no se
  aplaste la zona de 5–40 €, donde está la competencia más densa. Si usas escala log, dilo en el gráfico.
- Revisa el guion de `CLAUDE.md`, sección 9: el titular de la diapositiva 2 y las cifras grandes (×2 · 97 % ·
  87 %) pueden cambiar. **Ningún titular se mantiene si los datos nuevos no lo sostienen.**
- Añade una diapositiva de "qué cambió al añadir 11 marcas" si alguna conclusión se mueve: es buen material
  de criterio para el portfolio.
- Sustituye "1.211 modelos de 5 cadenas" por las cifras finales tras clasificar.

---

## 8. Limitaciones nuevas (añádelas a la lista de `CLAUDE.md`)

- **Rebajas activas** en 8 de las 11 marcas nuevas. Se usa el precio de catálogo (original); en Springfield
  y Women'secret casi todo el catálogo estaba rebajado, por lo que su precio de catálogo puede no ser
  representativo del precio real de venta.
- **Muestras muy pequeñas** en las marcas premium y en camisetas en general.
- **Filtrado de manga larga por la descripción** en Pedro del Hierro, Adolfo Domínguez, Bimba y Lola,
  Scalpers y Silbon (no tienen subcategoría). Puede dejar fuera productos cuya ficha no lo diga.
- **Vaqueros por nombre** ("denim") en Bimba y Lola, Adolfo Domínguez, Silbon y El Ganso, porque no tienen
  categoría propia.
- **Marcas invitadas excluidas** en Springfield, Cortefiel, Pedro del Hierro y Scalpers (mismo criterio que
  COS/ARKET en H&M).
- **Women'secret y El Ganso** no son comparables en una o en las dos prendas.

## 9. Registro de errores evitados en la recogida (para el deck y LinkedIn)

1. Mango solo servía 12 productos en el HTML de la categoría; el catálogo completo estaba en su API.
2. Las webs de Tendam y Scalpers venden **marcas invitadas** junto a la propia: sin filtrarlas, Scalpers
   habría incluido Levi's y Lacoste.
3. En Scalpers, Silbon y Women'secret **cada color es un producto distinto**: contarlos así inflaba el
   catálogo (Scalpers: 80 fichas de camiseta → 15 modelos de manga larga).
4. La categoría "Mujer" de El Ganso incluía un vaquero de hombre (se detectó por el prefijo del código).
5. Pedro del Hierro y otras no tienen filtro de manga larga: se tuvo que leer la ficha de cada producto.
6. En Springfield, 45 de 50 productos estaban "rebajados": un precio de catálogo que casi nadie paga.

---

## 10. Checklist antes de enseñarle nada a Javi

- [ ] La versión de 5 marcas reproduce exactamente las cifras de `CLAUDE.md`, sección 6.
- [ ] 1.697 filas cargadas; básicas + excluidas = total, por marca y prenda.
- [ ] Cajón de sastre de las marcas nuevas revisado a mano.
- [ ] Decisión sobre rebajas tomada con Javi, con la sensibilidad calculada.
- [ ] Decisión sobre marcas con n < 5 y sobre Women'secret tomada con Javi.
- [ ] Ninguna marca premium se solapa con Primark/Lefties (ancla de control).
- [ ] Cada cifra del deck sale de `data/moda.db`.
- [ ] Gráficos enseñados a Javi antes de montar el deck.
