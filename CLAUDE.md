# Proyecto 4 · Posicionamiento de precio en la moda rápida en España

> Archivo de traspaso desde la conversación en claude.ai. Léelo entero antes de tocar nada.
> Todo lo que aparece aquí como "validado" se comprobó paso a paso con Javi en SQLite.

---

## 1. Quién es Javi y cómo trabajar con él

- **Javi**, 23 años, último curso de Marketing e Investigación de Mercados (UGR), vive en Alhama de Granada.
- Está construyendo un **portfolio de análisis de datos** para conseguir prácticas curriculares en Granada y Málaga. En octubre de 2027 empieza el Máster en Big Data y Business Analytics de ESIC.
- **Su ventaja diferencial es el criterio de negocio, no el código.** Cada entregable tiene que demostrar que sabe qué preguntar a los datos y qué hacer con la respuesta.
- Partió de cero. Sabe SQL (SQLite, DB Browser) y Looker Studio. **Python todavía es nuevo para él.**

**Cómo trabajar:**
1. **Siempre en español.** Tono cercano y directo.
2. **En este proyecto, el análisis y la presentación los haces tú**, pero Javi tiene que poder entender y defender cada decisión. Explica brevemente los porqués. Comenta el código Python en español y explica cualquier técnica nueva la primera vez que aparezca.
3. **Enséñale a dudar.** Ante cada hallazgo llamativo, plantea qué otra explicación podría tener y qué métrica independiente lo confirmaría o lo desmentiría.
4. **Sé honesto cuando algo no da para tanto.** Si un dato no sostiene una conclusión, dilo. Prefiere un hallazgo modesto y sólido a uno inflado.
5. **Avísale de los errores señalando la causa**, no solo la solución.
6. Antes de dar por terminado un paso largo (gráficos, deck), **enséñale un borrador** y espera su visto bueno.

---

## 2. La pregunta de negocio

> **¿Dónde se posiciona en precio cada gran cadena de moda en España y con quién se solapa?**
> En concreto: ¿escalona Inditex sus marcas sin pisarse, y dónde chocan con sus rivales?

- **Para quién:** un equipo de marketing o una agencia que tiene que posicionar una marca de moda y decidir su precio de entrada y contra quién compararse.
- **Qué es este análisis:** un análisis de **posicionamiento de precio** a partir del catálogo online.
- **Qué NO es:** no mide ventas, cuota de mercado, clientes reales, calidad ni márgenes. No demuestra una "estrategia" de Inditex: describe dónde se sitúan los precios. **Esta frontera no se cruza en ningún texto.**

---

## 3. Datos

| | |
|---|---|
| Fichero | `data/moda_catalogo_2026-10-10.csv` |
| Recogida | 10/10/2026, web española de cada marca, sección **mujer** |
| Marcas | Primark, Lefties, H&M, Zara, Massimo Dutti (Lefties, Zara y Massimo Dutti son de **Inditex**) |
| Categorías | camiseta de **manga larga** y **vaquero** |
| Unidad | **modelo** (deduplicado por referencia; cada variante de color NO es una fila) |
| Filas | 1.211 |

**Columnas:** `marca, categoria, nombre, precio_actual, precio_original, referencia_modelo, clasificacion_web, n_colores, url, fecha_recogida`

**Notas por marca** (importantes para no interpretar mal):
- **Zara:** datos de su API de catálogo. `clasificacion_web` es su familia interna (`C.CTAS BASICAS`, `C.CTAS POSICIO`, `L. TOP PIJAMA`…). Su etiqueta "básica" **no** coincide con nuestra definición (p. ej., "RAYAS ANCHAS" aparece como básica).
- **Lefties:** API de Inditex. La categoría "camisetas manga larga" es pequeña.
- **H&M:** solo marca **H&M**. Se excluyeron COS, ARKET, & Other Stories, Monki y Weekday, que se venden en la misma web y tienen precios más altos. Sin URL de producto (solo referencia del modelo). H&M llama "Top" a lo que Zara llama "Camiseta".
- **Massimo Dutti:** sin `n_colores`. 3 productos sin precio (no cargaron en la web).
- **Primark:** no vende online en España, pero su web muestra el catálogo con precios. Los vaqueros se deduplicaron por los 9 primeros dígitos del código.
- `data/raw/` guarda los ficheros brutos de la recogida y `scripts/unificar_raw.py` los convierte en el CSV. **No hace falta volver a ejecutarlo.**

**Excluidos y por qué:**
- **Shein:** su web bloquea el acceso con un CAPTCHA. No se intentó saltarlo. Va en limitaciones: *"excluida por inaccesibilidad de los datos (protección anti-bot)"*.
- **Composición del tejido:** se descartó a propósito, así que **no se puede controlar por calidad o material**.

---

## 4. Pipeline reproducible

```bash
python scripts/construir_bd.py              # crea data/moda.db desde el CSV y ejecuta sql/02 → sql/06
python scripts/analisis_complementario.py   # tablas del paso 1
python scripts/graficos.py                  # gráficos del paso 2
python scripts/crear_deck.py                # deck del paso 3
```

| Fichero | Qué hace |
|---|---|
| `sql/00_crear_tabla.sql` | Estructura de `catalogo` |
| `sql/01_exploracion.sql` | Comprobaciones de tipos y totales (no modifica datos) |
| `sql/02_limpieza.sql` | Normaliza el único producto rebajado a su precio original y elimina `precio_original` |
| `sql/03_reglas_clasificacion.sql` | Tabla `reglas_clasificacion`: 191 patrones LIKE que excluyen prendas no básicas |
| `sql/04_clasificar.sql` | Columna `motivo` (motivo de exclusión o `7_basica`) |
| `sql/05_resumen_precios.sql` | Vista `v_resumen_precios`: n, mínimo, P25, mediana, P75, máximo, media, grupo, fiabilidad |
| `sql/06_solapamiento.sql` | Vistas `v_solape_franja` (métrica 1) y `v_solape_pares` (métrica 2) |
| `scripts/analisis_complementario.py` | Paso 1: arquitectura de precios, hueco de la escalera, ratios y "H&M rodea a Zara" → `output/tablas/*.csv` |
| `scripts/graficos.py` | Paso 2: gráficos PNG a 300 ppp → `output/graficos/` |
| `scripts/crear_deck.py` | Paso 3: `output/posicionamiento_precio_moda.pptx` (python-pptx, Calibri; cifras leídas de la base y de `output/tablas/`) |

**Regla de coherencia:** todo lo que calcules en Python tiene que coincidir con estas vistas. Si no coincide, es un error tuyo de configuración, no un hallazgo nuevo. Usa las vistas como fuente o verifica contra ellas.

### Definición de "prenda básica" (validada con Javi)
- **Camiseta:** manga larga, lisa o de canalé, sin estampado ni adornos. Que sea realmente una camiseta (no polo, blusa, sudadera, top de pijama ni prenda deportiva o técnica). Se excluyen también los tejidos de vestir (seda, satén, velour, terciopelo, acetato) y los crop. Se **mantienen** el algodón, la lana, el lino y el modal, y cualquier tipo de cuello.
- **Vaquero:** pantalón largo de tela vaquera, **cualquier corte** (recto, wide leg, barrel, flare, mom, cropped…). Se excluyen vestidos, faldas, bermudas, capri, jeggings, chinos, cargo, cintura elástica o con cordón, lino o "efecto denim", líneas especiales (premamá MAMA de H&M, Adaptive de Primark), estampados y adornos o acabados (tachas, strass, rotos, encerado, costuras de contraste…).
- La clasificación se hace **solo por el nombre del producto** (y `clasificacion_web` en algunos casos). El cajón de sastre se revisó a mano.

---

## 5. Decisiones tomadas y por qué

1. **Pregunta B** entre tres opciones: "¿compiten de verdad por el mismo cliente o solo lo parece?". Se eligió por equilibrar interés, viabilidad y criterio de negocio.
2. **Marcas por papel en el abanico de precios:** Primark (low cost físico), Lefties (low cost de Inditex), H&M y Zara (gama media), Massimo Dutti (gama media-alta y **ancla de control**: si sale solapada con Primark, el método está mal).
3. **Prendas básicas y no de temporada:** son las más comparables entre marcas y no dependen del calendario de colección de cada una. Camiseta de manga larga y no corta: en octubre, Massimo Dutti apenas tenía manga corta.
4. **Sin composición:** Javi lo decidió dos veces. Consecuencia: se habla de **posicionamiento de precio**, no de prima de marca ni de estrategia demostrada.
5. **Rebajas:** solo 1 de 1.211 productos estaba rebajado. Se normalizó a su precio original y se eliminó la columna.
6. **Mínimo de 15 modelos por marca y categoría.** Lefties camisetas (9) y Massimo Dutti camisetas (14) no llegan. **No se eliminan:** se marcan como **baja fiabilidad**. Atenuante: sus precios apenas varían (Lefties 6,99–9,99 €; Massimo Dutti 29,95–39,95 €).
7. **Métrica principal de solapamiento = métrica 2 (tramos).** La métrica 1 se rompe en los bordes con precios redondos (ver sección 6).
8. **Sin etiquetas automáticas** de "competencia directa" o "contacto parcial" por umbrales fijos: con un corte en el 50 %, H&M–Zara en camisetas (47 %) habría quedado como "parcial", contradiciendo el análisis. Las interpretaciones van en el texto.
9. **"Muestra pequeña", no "baja fiabilidad"**, en todo texto que vea el lector (gráficos, deck, resumen). Lo pidió Javi: dice lo mismo sin sonar a dato erróneo. Internamente (vista SQL) se mantiene `fiabilidad`.
10. **Aprobado tras el paso 1 (10/10/2026):**
    - El **hueco** de la escalera se mide con precios **redondeados al euro** (39,95 € y 39,99 € = mismo precio). Sin redondear, el 22 % de H&M en vaqueros parecía estar en el hueco; con redondeo es el 7 %. Camiseta: 15 % de los modelos en el hueco (H&M 23 %, Zara 14 %); vaquero: 4 % (H&M 7 %, Zara 2 %). Se presenta como **oportunidad a validar**.
    - **"H&M rodea a Zara" se matiza:** claro en camisetas (H&M 31 % por debajo / 37 % dentro / 32 % por encima de la franja de Zara) y suave en vaqueros (15 % / 70 % / 16 %).
    - La **arquitectura de precios** va como **apoyo**, no como hallazgo central (la dispersión de H&M se explica en parte por su tamaño de catálogo). Las terminaciones: x,95 = Zara y Massimo Dutti; x,99 = H&M **y Lefties**; Primark, enteros o x,50.
    - **Mango** (y COS / & Other Stories) podrían ocupar el hueco: va **solo como limitación**, sin añadir datos.

---

## 6. Resultados validados

### Distribución de precios (`v_resumen_precios`, ordenado por mediana)

| Prenda | Marca | n | P25 | **Mediana** | P75 | Máx | Media |
|---|---|---|---|---|---|---|---|
| camiseta | Primark | 23 | 4,50 | **7,00** | 8,00 | 10,00 | 6,50 |
| camiseta | Lefties | 9 ⚠ | 7,99 | **7,99** | 7,99 | 9,99 | 8,10 |
| camiseta | H&M | 87 | 9,99 | **14,99** | 19,99 | 49,99 | 16,90 |
| camiseta | Zara | 50 | 12,95 | **15,95** | 17,95 | 29,95 | 16,39 |
| camiseta | Massimo Dutti | 14 ⚠ | 29,95 | **29,95** | 39,95 | 39,95 | 33,52 |
| vaquero | Primark | 45 | 14,00 | **18,00** | 18,00 | 24,00 | 17,20 |
| vaquero | Lefties | 28 | 17,99 | **19,99** | 19,99 | 25,99 | 19,24 |
| vaquero | H&M | 289 | 29,99 | **34,99** | 39,99 | 89,99 | 36,38 |
| vaquero | Zara | 101 | 29,95 | **35,95** | 39,95 | 59,95 | 34,41 |
| vaquero | Massimo Dutti | 32 | 49,95 | **59,95** | 59,95 | 59,95 | 56,51 |

### Solapamiento por tramos (`v_solape_pares`, métrica principal)

| Pareja | Camiseta (tramos 5 €) | Vaquero (tramos 10 €) | Robustez (4 € / 8 €) |
|---|---|---|---|
| Lefties – Primark | 52 % | **97 %** | 72 % / 82 % ✅ |
| H&M – Zara | 47 % | **87 %** | 60 % / 86 % ✅ |
| H&M – Primark | 35 % | 20 % | 31 % / 12 % (moderado) |
| H&M – Lefties | 31 % | 17 % | **12 %** / 7 % ❌ frágil |
| Lefties – Zara | 8 % | 14 % | 8 % / 4 % |
| Zara – Massimo Dutti | 2 % | 5 % | 2 % / 3 % |

### Métrica 1 (franja central P25–P75, asimétrica): solo como apoyo
- Camiseta: el 86 % de las básicas de Zara cae en la franja de H&M, pero solo el 37 % de las de H&M cae en la de Zara.
- Camiseta: Lefties → Primark 89 %, Primark → Lefties 0 %. **Es un fallo de la métrica, no un hallazgo**: la franja de Lefties tiene anchura cero (7,99–7,99).
- Vaquero: H&M–Zara solo da 54 % / 46 % a pesar de tener franjas casi idénticas. **Trampa de los 4 céntimos:** Zara tiene muchos vaqueros a 29,95 €, justo por debajo del P25 de H&M (29,99 €), y H&M muchos a 39,99 €, justo por encima del P75 de Zara (39,95 €).

### Conclusiones que se sostienen (dos métricas, dos anchos de tramo, dos prendas)
1. **Inditex escalona sus tres marcas sin solaparse.** Cada escalón cuesta aproximadamente el doble que el anterior, en las dos prendas:
   - Camiseta: Lefties 7,99 → Zara 15,95 (**×2,0**) → Massimo Dutti 29,95 (**×1,9**)
   - Vaquero: Lefties 19,99 → Zara 35,95 (**×1,8**) → Massimo Dutti 59,95 (**×1,7**)
2. **Solo hay dos enfrentamientos frontales de precio:** Lefties–Primark en la gama baja y Zara–H&M en la gama media.
3. **H&M rodea a Zara.** Casi toda la oferta de Zara cae en la franja central de H&M, pero H&M tiene mucha oferta por debajo y por encima. Para Zara, H&M es su competidor directo; para H&M, Zara es uno de varios.
4. **El "H&M es más cara que Zara" es un espejismo de la media.** H&M tiene más media pero menos mediana, en las dos prendas, por una cola de productos caros dentro de la propia marca H&M (líneas premium, lana merino, algodón pima, vaqueros de hasta 89,99 €).
5. **H&M asoma a la gama baja:** su precio de entrada (7,99–9,99 € en camiseta) toca la parte alta de Primark. Es un contacto parcial, no una competencia frontal.
6. **Massimo Dutti está aislado.** El control funciona: 0 % de solapamiento con Primark.

**Titular para el deck y el resumen ejecutivo:**
> *Inditex escalona sus tres marcas sin canibalizarse: cada escalón cuesta aproximadamente el doble que el anterior, en camisetas y en vaqueros. Los únicos enfrentamientos frontales de precio son Lefties–Primark en la gama baja y Zara–H&M en la media.*

### Limitaciones (tienen que aparecer en todos los entregables)
- **Posicionamiento, no estrategia.** La escalera puede reflejar una segmentación deliberada o simplemente productos de distinta calidad. Sin la composición, **no se pueden distinguir**.
- Foto de **un único día** (10/10/2026), sin rebajas activas. Es precio de catálogo, no precio de venta ni volumen vendido.
- **Shein excluida** por inaccesibilidad de los datos.
- La clasificación de "básica" se hizo por **palabras clave en el nombre**. Puede haber errores puntuales.
- **Lefties (9) y Massimo Dutti (14) en camisetas**, por debajo del mínimo de 15: baja fiabilidad.
- H&M incluye líneas premium dentro de su marca. Otras sublíneas (Zara TRF / Z1975 / ZW Collection; Primark The Edit) también conviven dentro de cada marca.
- Los cuartiles se aproximan con `NTILE(4)`.
- La métrica de tramos depende del ancho elegido; se hizo una prueba de robustez.

### Registro de errores evitados (material para el deck y LinkedIn)
1. La página visible de Zara solo cargaba 40 tarjetas de camisetas; la API tenía 135 modelos. Si me hubiera fiado de lo visible, el catálogo de Zara habría parecido tres veces más pequeño.
2. hm.com mezcla 6 marcas del grupo. Sin filtrarlas, H&M habría parecido más cara.
3. Contar variantes de color como productos inflaba el catálogo de H&M (1.076 fichas frente a 556 modelos en manga larga).
4. El nombre de producto "The Primark Scene | …" rompía el separador `|` al unificar los datos.
5. Una rebaja aislada habría quedado camuflada al borrar la columna de precio original.
6. La métrica 1 inventaba asimetrías por precios redondos (Lefties → Primark 89 % / 0 %; la trampa de los 4 céntimos).
7. El 31 % de solapamiento H&M–Lefties desaparecía al cambiar el ancho de los tramos: era un efecto del corte.

---

## 7. Tu tarea en Claude Code

### Paso 0 · Reproducir y verificar
- Ejecuta `python scripts/construir_bd.py` y comprueba que la salida coincide con la sección 6. Si algo no cuadra, para y avisa a Javi antes de seguir.
- Instala lo necesario: `pip install pandas matplotlib python-pptx` (y `--break-system-packages` si hace falta).

### Paso 1 · Análisis complementario (solo lo que aporte a la historia)
1. **Arquitectura de precios.** Ya se vio de forma cualitativa que Massimo Dutti solo usa **dos precios** en camisetas (29,95 € y 39,95 €), que Lefties concentra casi todo en **7,99 €** y que Zara sube en escalones fijos (9,95 → 12,95 → 15,95 → 17,95). Cuantifícalo: nº de precios distintos por marca y prenda, y % del catálogo que concentran los 2–3 precios más frecuentes. Termina de puntos: x,95 (Inditex) frente a x,99 (H&M, Lefties) frente a enteros (Primark).
2. **Los huecos de la escalera.** Entre el P75 de Zara y el P25 de Massimo Dutti hay un hueco (camiseta 17,95 → 29,95; vaquero 39,95 → 49,95). ¿Quién ocupa ese hueco? (Parece que la cola de H&M.) Cuantifica qué % de cada marca cae en él. Es la base de la recomendación para quien posicione una marca. Formúlalo como **oportunidad a investigar**, no como hueco de mercado demostrado: no sabemos si hay demanda.
3. **Ratios de la escalera** con su cálculo explícito (medianas), para el gráfico de "×2".
4. **No abras líneas nuevas** (composición, más marcas, reseñas, rotación…) sin preguntar a Javi.

### Paso 2 · Gráficos
- Hazlos con **matplotlib**, exportados en PNG a 300 ppp en `output/graficos/`, siguiendo la sección 8.
- **Gráfico principal, la escalera:** para cada marca, la franja P25–P75 como barra flotante y la mediana como marca destacada, ordenadas por mediana. Dos paneles (camiseta y vaquero) como **múltiplos pequeños**, cada uno con su escala. Inditex en un color de acento y el resto en gris.
- Enséñale los gráficos a Javi antes de montar el deck.

### Paso 3 · Presentación PowerPoint
- `output/posicionamiento_precio_moda.pptx`, creada con **python-pptx**. 16:9.
- Guion propuesto en la sección 9. Ajústalo si el análisis complementario lo pide, pero explica por qué.
- Los gráficos van como imagen y el texto como texto editable, para que Javi pueda retocar los títulos.

### Paso 4 · Cierre (pregunta a Javi antes)
- Su estándar de proyecto incluye además: **resumen ejecutivo de 1 página** (Principio de la Pirámide: conclusión primero, hallazgos con cifras, recomendaciones accionables, limitaciones, metodología), **README de GitHub que empiece por el resultado, no por el código**, y un post de LinkedIn. Ofrécelo cuando el deck esté aprobado.

---

## 8. Criterios de visualización (de los libros de referencia del proyecto)

Javi ha leído *Storytelling with Data* (Cole Nussbaumer Knaflic), *La representación visual de información cuantitativa* (Edward Tufte) y *Good Charts* (Scott Berinato). Estos son los criterios que hay que aplicar **siempre**:

**Contexto antes que gráfico (Knaflic, cap. 1; Berinato).**
- Antes de diseñar, hay que saber **quién** (un equipo de marketing que posiciona una marca), **qué** quieres que sepa o haga y **cómo** se lo vas a contar.
- Escribe la **Gran Idea** en una frase (el titular de la sección 6) y comprueba que **la historia se puede contar en 3 minutos**.
- Esto es una visualización **declarativa** (Berinato: *everyday dataviz*). El objetivo es comunicar una conclusión, no explorar. Cada gráfico afirma **una sola cosa**.

**Elegir el gráfico adecuado (Knaflic, cap. 2).**
- Barras horizontales o flotantes para comparar rangos entre categorías. Puntos o tiras para distribuciones. Texto simple para una o dos cifras clave (un número grande vale más que un gráfico con dos barras).
- **Prohibido:** tartas, anillos, 3D, ejes dobles y gráficos de área.
- Las barras empiezan en cero. En las barras flotantes de rango, el eje puede no empezar en cero, pero tiene que estar claramente rotulado.

**El desorden es el enemigo (Knaflic, cap. 3; Tufte, proporción de tinta de datos).**
- Cada elemento añade carga cognitiva. **Maximiza la tinta dedicada a los datos** y elimina la "chatarra gráfica" (Tufte): sin bordes de gráfico, sin cuadrícula (o muy tenue y gris), sin marcadores innecesarios, sin decimales que no aporten (7,99 € sí; 7,990 no) y sin texto en diagonal.
- **Etiqueta los datos directamente** en lugar de usar leyenda (principio de proximidad de la Gestalt) y con el mismo color que su serie (principio de semejanza).
- Alinea los elementos y deja espacio en blanco.

**Dirigir la atención (Knaflic, caps. 4–5).**
- Usa atributos preatentivos con intención: **todo en gris** y **un único color de acento** para lo que importa (Inditex o la pareja de la diapositiva).
- El color tiene que significar lo mismo en todo el deck: si Inditex es azul en una diapositiva, lo es en todas.
- Jerarquía visual: el título dice la conclusión; el gráfico la demuestra; la nota al pie da la fuente y la n.

**Integridad gráfica (Tufte).**
- El **factor de mentira** tiene que ser 1: el tamaño visual tiene que ser proporcional al dato.
- Muestra la variación de los datos, no la del diseño. Indica siempre la fuente, la fecha y el tamaño de muestra.
- Marca visiblemente la **baja fiabilidad** (Lefties y Massimo Dutti en camisetas), por ejemplo con trama, transparencia o una nota junto a la barra.
- **Múltiplos pequeños** (Tufte): mismos ejes y misma estructura para comparar camiseta y vaquero.

**Contar la historia (Knaflic, cap. 7; Berinato; Minto).**
- **Títulos de acción:** cada título de diapositiva es una frase con la conclusión ("Inditex escalona sus marcas: cada salto duplica el precio"), no un tema ("Precios por marca").
- **Lógica horizontal:** leyendo solo los títulos de las diapositivas en orden, se tiene que entender la historia completa.
- Estructura **planteamiento → nudo → desenlace**: el contexto y la pregunta, los hallazgos con su tensión (la duda y su descarte), y qué significa para el público y qué hacer.
- **Persuasión honesta (Berinato):** las limitaciones se dicen; no se insinúa causalidad ni estrategia.

**Estilo visual.**
- Fondo blanco. Una tipografía sans serif limpia. Gris oscuro (#333) para el texto y grises claros para el contexto.
- Inditex en un único azul sobrio y el resto de marcas en gris. Como mucho, un segundo color para resaltar una pareja concreta.
- Formato de números en **español**: coma decimal (7,99 €), símbolo € detrás y porcentajes sin decimales.

---

## 9. Guion propuesto del deck (10–12 diapositivas)

| # | Título de acción (borrador) | Contenido |
|---|---|---|
| 1 | ¿Compiten de verdad las grandes cadenas de moda por el mismo cliente? | Portada: pregunta, autor (Javi), fecha de los datos |
| 2 | Inditex escalona sus marcas sin pisarse; solo hay dos choques frontales | La Gran Idea + 3 cifras grandes: ×2 · 97 % · 87 % |
| 3 | 1.211 modelos de 5 cadenas, comparando la misma prenda básica | Método en una imagen: marcas, prendas, definición de básica, fecha |
| 4 | En camisetas, cada marca de Inditex ocupa su propio tramo de precio | Escalera de camisetas (barras flotantes P25–P75 + mediana) |
| 5 | En vaqueros se repite el mismo patrón | Múltiplos pequeños: camiseta y vaquero |
| 6 | Cada escalón de Inditex cuesta aproximadamente el doble | Ratios ×2,0 / ×1,9 y ×1,8 / ×1,7 |
| 7 | Solo hay dos enfrentamientos directos: Lefties–Primark y Zara–H&M | Barras horizontales del solapamiento por pareja, con las dos destacadas |
| 8 | H&M rodea a Zara y alarga su oferta por arriba | Asimetría 86 % / 37 % + media frente a mediana (el espejismo) |
| 9 | Las marcas trabajan con unos pocos precios cerrados | Arquitectura de precios (paso 1.1) |
| 10 | Entre Zara y Massimo Dutti queda un hueco de precio | Qué implica para quien posiciona una marca (paso 1.2), como oportunidad a validar |
| 11 | Lo que este análisis no dice | Limitaciones (sección 6) |
| 12 | Anexo: método y robustez | Definiciones, las dos métricas, prueba de 4 € / 8 €, tabla completa |

---

## 10. Lo que no hay que hacer
- No volver a extraer datos de las webs ni añadir marcas sin permiso de Javi.
- No usar las palabras "estrategia", "canibalización demostrada", "cuota", "ventas", "clientes" ni "calidad" como conclusiones. Se habla de **precio de catálogo** y **posicionamiento**.
- No usar la métrica 1 como prueba principal.
- No presentar el H&M–Lefties (31 %) como competencia.
- No inventar cifras. Toda cifra del deck tiene que salir de `data/moda.db` o de un cálculo reproducible en el repositorio.
