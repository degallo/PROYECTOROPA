"""
Deck de la ampliación a 16 marcas → output/posicionamiento_precio_moda_16_marcas.pptx

El deck de 5 marcas (scripts/crear_deck.py) se conserva aparte, como pidió Javi.
Mismo estilo que ese deck: 16:9, fondo blanco, Calibri, títulos de acción en el marcador
de título (texto editable), gráficos como imagen y notas del orador en cada diapositiva.
Colores con significado fijo: azul = Inditex, naranja = Tendam, gris = resto.

Todas las cifras se leen de data/moda.db y de output/tablas/ (ampliacion/ y, para
"H&M rodea a Zara", la tabla de la versión de 5 marcas, que no cambia porque H&M y Zara
son las mismas). Ninguna cifra se escribe a mano.

Uso:  python scripts/construir_bd.py && python scripts/analisis_ampliacion.py \
      && python scripts/graficos_ampliacion.py && python scripts/crear_deck_ampliacion.py
"""
import os
import re
import sqlite3

import pandas as pd
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, 'data', 'moda.db')
TABLAS = os.path.join(BASE, 'output', 'tablas', 'ampliacion')
TABLAS_5 = os.path.join(BASE, 'output', 'tablas')
GRAFICOS = os.path.join(BASE, 'output', 'graficos')
SALIDA = os.path.join(BASE, 'output', 'posicionamiento_precio_moda_16_marcas.pptx')

# ---------------------------------------------------------------------------
# Estilo (mismos colores que los gráficos)
# ---------------------------------------------------------------------------
AZUL = RGBColor(0x2A, 0x64, 0xA8)        # Inditex
NARANJA = RGBColor(0xC8, 0x57, 0x1B)     # Tendam
TEXTO = RGBColor(0x33, 0x33, 0x33)
TEXTO_SEC = RGBColor(0x6B, 0x6B, 0x6B)
GRIS_MARCA = RGBColor(0x7A, 0x7A, 0x7A)
GRIS_PELDANO = RGBColor(0xD3, 0xD3, 0xD3)
FONDO_TARJETA = RGBColor(0xF3, 0xF3, 0xF3)
BLANCO = RGBColor(0xFF, 0xFF, 0xFF)
VERDE_OK = RGBColor(0x2E, 0x7D, 0x4F)    # solo para la etiqueta "Se mantiene" (diapositiva 14)
FUENTE_LETRA = 'Calibri'
AUTOR = 'Javier Benítez Escobedo'

INDITEX = ['Lefties', 'Zara', 'Massimo Dutti']
TENDAM = ['Springfield', 'Cortefiel', 'Pedro del Hierro']
ANCHO, ALTO = 13.333, 7.5
MARGEN = 0.6
FUENTE_DATOS = ('Fuente: catálogo online de cada marca en España (sección mujer), 10/10/2026. '
                'Precio de catálogo, prendas básicas.')


def color_marca(marca):
    if marca in INDITEX:
        return AZUL
    if marca in TENDAM or marca == "Women'secret":
        return NARANJA
    return GRIS_MARCA


# ---------------------------------------------------------------------------
# Formato español
# ---------------------------------------------------------------------------
def euros(x):
    return f'{x:.2f}'.replace('.', ',') + '\u00a0€'     # \u00a0 = espacio que no se parte


def pct(x):
    return f'{int(round(x))}\u00a0%'


def no_partir(txt):
    """Une con un espacio duro cada cifra con su unidad (7,99 €, 47 %), para que
    PowerPoint no deje el número en una línea y la unidad en la siguiente."""
    return re.sub(r'(\d) ([%€])', '\\1\u00a0\\2', txt)


def veces(x):
    return '×' + f'{x:.1f}'.replace('.', ',')


def miles(n):
    return f'{n:,}'.replace(',', '.')


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------
con = sqlite3.connect(DB)
resumen = pd.read_sql('SELECT * FROM v_resumen_precios', con).set_index(['categoria', 'marca'])
marcas = pd.read_sql('SELECT * FROM marcas', con)
total_modelos = con.execute('SELECT COUNT(*) FROM catalogo').fetchone()[0]
n_marcas = len(marcas)
basicas_analisis = con.execute("""SELECT COUNT(*) FROM catalogo JOIN marcas USING (marca)
                                  WHERE motivo = '7_basica' AND en_analisis = 1""").fetchone()[0]
basicas_metricas = con.execute("""SELECT SUM(n) FROM v_resumen_precios WHERE en_metricas = 1""").fetchone()[0]
n_basicas = dict(con.execute("""SELECT marca || '|' || categoria, COUNT(*) FROM catalogo
                                WHERE motivo = '7_basica' GROUP BY marca, categoria""").fetchall())
con.close()

solape = pd.read_csv(os.path.join(TABLAS, 'solapamiento_16_marcas.csv'))
S = {(r.categoria, r.pareja): r for r in solape.itertuples()}
ratios = pd.read_csv(os.path.join(TABLAS, 'ratios_escaleras.csv')).set_index(['categoria', 'escalon'])
hueco = pd.read_csv(os.path.join(TABLAS, 'hueco_16_marcas.csv')).set_index(['categoria', 'marca'])
hueco_total = pd.read_csv(os.path.join(TABLAS, 'hueco_total.csv')).set_index('categoria')
rebajas = pd.read_csv(os.path.join(TABLAS, 'rebajas_por_marca.csv')).set_index('marca')
muestras = pd.read_csv(os.path.join(TABLAS, 'muestras_por_marca.csv')).set_index(['categoria', 'marca'])
sens = pd.read_csv(os.path.join(TABLAS, 'sensibilidad_rebajas_resumen.csv')).set_index(['categoria', 'marca'])
term = pd.read_csv(os.path.join(TABLAS, 'terminaciones_16_marcas.csv')).set_index('marca')
arq = pd.read_csv(os.path.join(TABLAS, 'arquitectura_16_marcas.csv'))
rodea = pd.read_csv(os.path.join(TABLAS_5, 'hm_rodea_zara.csv')).set_index(['categoria', 'marca'])


def med(cat, marca):
    return resumen.loc[(cat, marca), 'mediana']


def sol(cat, pareja, col='solape_pct'):
    return getattr(S[(cat, pareja)], col)


def en_metricas(cat, marca):
    return (cat, marca) in resumen.index and bool(resumen.loc[(cat, marca), 'en_metricas'])


def rat(cat, escalon):
    return ratios.loc[(cat, escalon), 'ratio']


ESC_I = ['Lefties → Zara', 'Zara → Massimo Dutti']
ESC_T = ['Springfield → Cortefiel', 'Cortefiel → Pedro del Hierro']
ratios_inditex = [rat(c, e) for c in ['camiseta', 'vaquero'] for e in ESC_I]
# Escalones de Tendam con las dos marcas en las métricas (Pedro del Hierro no llega a 5 camisetas)
ratios_tendam = sorted({rat(c, e) for c in ['camiseta', 'vaquero'] for e in ESC_T
                        if (c, e) in ratios.index and all(
                            (c, m) in resumen.index and bool(resumen.loc[(c, m), 'en_metricas'])
                            for m in e.split(' → '))})
txt_tendam = ' y '.join(veces(x) for x in ratios_tendam)
txt_inditex = f'{veces(min(ratios_inditex))} a {veces(max(ratios_inditex))}'.replace('×', '')
pct_hueco = hueco_total['pct'].to_dict()
pct_hueco_reb = hueco_total['pct_rebajado'].to_dict()

# ---------------------------------------------------------------------------
# Utilidades de maquetación (las mismas que en crear_deck.py)
# ---------------------------------------------------------------------------
prs = Presentation()
prs.slide_width = Inches(ANCHO)
prs.slide_height = Inches(ALTO)
LAYOUT_PORTADA = prs.slide_layouts[0]
LAYOUT_TITULO = prs.slide_layouts[5]


def estilo_runs(parrafo, tam, color=TEXTO, negrita=False, cursiva=False):
    for run in parrafo.runs:
        run.font.name = FUENTE_LETRA
        run.font.size = Pt(tam)
        run.font.bold = negrita
        run.font.italic = cursiva
        run.font.color.rgb = color


def nueva_diapositiva(titulo, notas, numero=True):
    """Diapositiva con el título de acción en el marcador de título (editable)."""
    s = prs.slides.add_slide(LAYOUT_TITULO)
    t = s.shapes.title
    t.left, t.top, t.width, t.height = Inches(MARGEN), Inches(0.35), Inches(ANCHO - 2 * MARGEN), Inches(1.0)
    tf = t.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = tf.margin_right = 0
    tf.text = no_partir(titulo)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    estilo_runs(p, 28, negrita=True)
    s.notes_slide.notes_text_frame.text = notas
    if numero:
        caja(s, f'{len(prs.slides)}', ANCHO - MARGEN - 0.6, ALTO - 0.45, 0.6, 0.3, tam=10,
             color=TEXTO_SEC, alinear=PP_ALIGN.RIGHT)
    return s


def forma_plana(s, x, y, w, h, color):
    """Rectángulo de color sin borde ni sombra (se borra el estilo heredado del tema)."""
    forma = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    forma.fill.solid()
    forma.fill.fore_color.rgb = color
    forma.line.fill.background()
    forma.shadow.inherit = False
    estilo = forma._element.find('{http://schemas.openxmlformats.org/presentationml/2006/main}style')
    if estilo is not None:
        forma._element.remove(estilo)
    return forma


def caja(s, texto, x, y, w, h, tam=14, color=TEXTO, negrita=False, cursiva=False,
         alinear=PP_ALIGN.LEFT, anclaje=MSO_ANCHOR.TOP, fondo=None, margen=0.0):
    """Cuadro de texto. 'texto' puede ser una cadena o una lista de párrafos;
    cada párrafo puede ser una cadena o una lista de (texto, opciones)."""
    forma = forma_plana(s, x, y, w, h, fondo) if fondo is not None else \
        s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = forma.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anclaje
    for lado in ['left', 'right', 'top', 'bottom']:
        setattr(tf, f'margin_{lado}', Inches(margen))
    parrafos = texto if isinstance(texto, list) else [texto]
    for i, par in enumerate(parrafos):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = alinear
        trozos = par if isinstance(par, list) else [(par, {})]
        for txt, op in trozos:
            r = p.add_run()
            r.text = no_partir(txt)
            r.font.name = FUENTE_LETRA
            r.font.size = Pt(op.get('tam', tam))
            r.font.bold = op.get('negrita', negrita)
            r.font.italic = op.get('cursiva', cursiva)
            r.font.color.rgb = op.get('color', color)
        if i < len(parrafos) - 1:
            p.space_after = Pt(op.get('espacio', 8))
    return forma


def imagen(s, nombre, x, y, w=None, h=None):
    """Inserta un gráfico manteniendo sus proporciones dentro de la caja w × h."""
    ruta = os.path.join(GRAFICOS, nombre)
    ancho_px, alto_px = Image.open(ruta).size
    proporcion = ancho_px / alto_px
    if w is not None and h is not None:
        if w / h > proporcion:
            w = h * proporcion
        else:
            h = w / proporcion
    elif w is not None:
        h = w / proporcion
    else:
        w = h * proporcion
    s.shapes.add_picture(ruta, Inches(x), Inches(y), Inches(w), Inches(h))
    return w, h


def imagen_centrada(s, nombre, w, arriba=1.45, abajo=ALTO - 0.55):
    """Gráfico a la izquierda, centrado en vertical en la zona de contenido."""
    ancho_px, alto_px = Image.open(os.path.join(GRAFICOS, nombre)).size
    h = w * alto_px / ancho_px
    return imagen(s, nombre, MARGEN, arriba + max(0, (abajo - arriba - h) / 2), w=w)


def cifra_grande(s, cifra, texto, x, y, w, color):
    caja(s, cifra, x, y, w, 1.2, tam=66, color=color, negrita=True)
    caja(s, texto, x, y + 1.3, w, 1.6, tam=15, color=TEXTO)


def tabla(s, datos, x, y, w, anchos, tam=10, alto_fila=0.25, colores_col0=None):
    filas, cols = len(datos), len(datos[0])
    forma = s.shapes.add_table(filas, cols, Inches(x), Inches(y), Inches(w), Inches(alto_fila * filas))
    t = forma.table
    for j, a in enumerate(anchos):
        t.columns[j].width = Inches(a)
    for i, fila in enumerate(datos):
        t.rows[i].height = Inches(alto_fila)
        for j, valor in enumerate(fila):
            celda = t.cell(i, j)
            celda.fill.solid()
            celda.fill.fore_color.rgb = FONDO_TARJETA if i == 0 else BLANCO
            celda.margin_left = celda.margin_right = Inches(0.06)
            celda.margin_top = celda.margin_bottom = Inches(0.01)
            celda.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = celda.text_frame
            tf.text = str(valor)
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.RIGHT
            color = TEXTO
            if j == 0 and i > 0 and colores_col0:
                color = colores_col0(valor)
            estilo_runs(p, tam, color=color, negrita=(i == 0 or (j == 0 and colores_col0 is not None)))
    return forma


def nota_fuente(s, texto=FUENTE_DATOS):
    caja(s, texto, MARGEN, ALTO - 0.5, 10.5, 0.3, tam=10, color=TEXTO_SEC)


# ===========================================================================
# 1. Portada
# ===========================================================================
s = prs.slides.add_slide(LAYOUT_PORTADA)
t = s.shapes.title
t.left, t.top, t.width, t.height = Inches(MARGEN + 0.2), Inches(1.5), Inches(5.6), Inches(2.9)
t.text_frame.word_wrap = True
t.text_frame.vertical_anchor = MSO_ANCHOR.BOTTOM
t.text_frame.text = '¿Compiten de verdad en precio las grandes cadenas de moda en España?'
p = t.text_frame.paragraphs[0]
p.alignment = PP_ALIGN.LEFT
estilo_runs(p, 38, negrita=True)
t.text_frame.margin_left = t.text_frame.margin_right = 0
sub = s.placeholders[1]
sub.left, sub.top, sub.width, sub.height = Inches(MARGEN + 0.2), Inches(4.6), Inches(5.6), Inches(1.0)
sub.text_frame.word_wrap = True
sub.text_frame.text = f'Posicionamiento de precio de {n_marcas} cadenas a partir de su catálogo online'
p = sub.text_frame.paragraphs[0]
p.alignment = PP_ALIGN.LEFT
estilo_runs(p, 20, color=TEXTO_SEC)
sub.text_frame.margin_left = sub.text_frame.margin_right = 0
caja(s, [[(AUTOR, {'negrita': True, 'color': TEXTO})], 'Datos recogidos el 10/10/2026'],
     MARGEN + 0.2, 6.05, 5.6, 0.8, tam=14, color=TEXTO_SEC)

# Motivo visual: la escalera del vaquero con las marcas de 15 modelos o más. La altura de
# cada peldaño es proporcional a su precio mediano (factor de mentira = 1).
PORTADA = [m for (c, m), r in resumen.iterrows() if c == 'vaquero' and r['fiabilidad'] == 'OK']
PORTADA.sort(key=lambda m: med('vaquero', m))
base_y, alto_max = 6.55, 3.9
pw, pg = 0.74, 0.06
x0 = ANCHO - MARGEN - len(PORTADA) * pw - (len(PORTADA) - 1) * pg
precio_max = max(med('vaquero', m) for m in PORTADA)
for i, marca in enumerate(PORTADA):
    alto = alto_max * med('vaquero', marca) / precio_max
    x = x0 + i * (pw + pg)
    acento = marca in INDITEX or marca in TENDAM
    forma_plana(s, x, base_y - alto, pw, alto, color_marca(marca) if acento else GRIS_PELDANO)
    caja(s, euros(med('vaquero', marca)), x, base_y - alto + 0.06, pw, 0.3, tam=10,
         color=BLANCO if acento else TEXTO, negrita=True, alinear=PP_ALIGN.CENTER)
    partes = marca.split(' ')
    caja(s, [[(l, {'espacio': 0})] for l in partes], x - 0.1, base_y - alto - 0.08 - 0.24 * len(partes),
         pw + 0.2, 0.24 * len(partes), tam=11, negrita=True, alinear=PP_ALIGN.CENTER,
         anclaje=MSO_ANCHOR.BOTTOM, color=color_marca(marca) if acento else TEXTO)
caja(s, 'Altura de cada peldaño: precio mediano del vaquero básico (marcas con 15 modelos o más). '
        'Azul: Inditex. Naranja: Tendam.',
     x0 - 0.4, base_y + 0.1, ANCHO - MARGEN - x0 + 0.4, 0.5, tam=10, color=TEXTO_SEC, alinear=PP_ALIGN.RIGHT)
s.notes_slide.notes_text_frame.text = (
    f'Pregunta de partida: dónde se posiciona en precio cada gran cadena de moda en España y con quién se '
    f'solapa. Esta versión amplía el análisis de 5 a {n_marcas} cadenas: se añaden Mango, Tendam (Springfield, '
    'Cortefiel, Pedro del Hierro, Women\'secret) y seis marcas españolas de gama media-alta. Es un análisis de '
    'precio de catálogo, no de ventas ni de cuota.')


# ===========================================================================
# 2. La Gran Idea
# ===========================================================================
mz_v, mz_c = sol('vaquero', 'Mango – Zara'), sol('camiseta', 'Mango – Zara')
cm_v, cm_v_reb = sol('vaquero', 'Cortefiel – Massimo Dutti'), sol('vaquero', 'Cortefiel – Massimo Dutti', 'solape_pct_rebajado')
s = nueva_diapositiva(
    'Inditex y Tendam escalonan sus marcas; los choques de precio están en la gama baja y en la media',
    'La historia en una frase: Inditex coloca Lefties, Zara y Massimo Dutti en tramos de precio distintos, '
    'cada uno aproximadamente al doble del anterior, y Tendam hace lo mismo un peldaño más arriba. La gama '
    'baja sigue siendo un duelo entre Lefties y Primark. La gama media, en cambio, deja de ser un cara a cara: '
    'Mango entra de lleno entre Zara y H&M. Y Massimo Dutti ya no está solo: Cortefiel marca sus mismos '
    'precios de catálogo, aunque con muchas rebajas.')
col_w = 3.7
xs = [MARGEN, MARGEN + col_w + 0.5, MARGEN + 2 * (col_w + 0.5)]
cifra_grande(s, '×2', f'Cada escalón de Inditex cuesta aproximadamente el doble ({veces(min(ratios_inditex))} '
                      f'a {veces(max(ratios_inditex))}). Tendam repite el patrón un peldaño más arriba.',
             xs[0], 1.9, col_w, AZUL)
cifra_grande(s, pct(sol('vaquero', 'Lefties – Primark')),
             'de solapamiento entre Lefties y Primark en vaqueros: el choque de la gama baja. '
             'Ninguna de las marcas nuevas entra ahí.', xs[1], 1.9, col_w, TEXTO)
cifra_grande(s, pct(mz_v), f'entre Mango y Zara en vaqueros. La gama media pasa a ser un choque a tres, con '
                           f'H&M ({pct(sol("vaquero", "H&M – Zara"))} con Zara).', xs[2], 1.9, col_w, TEXTO)
caja(s, f'Massimo Dutti ya no está solo: Cortefiel coincide con él en precio de catálogo ({pct(cm_v)} en '
        f'vaqueros), aunque con el precio rebajado baja al {pct(cm_v_reb)}.',
     MARGEN, 5.25, ANCHO - 2 * MARGEN, 0.8, tam=16, color=TEXTO_SEC, fondo=FONDO_TARJETA,
     anclaje=MSO_ANCHOR.MIDDLE, margen=0.25)


# ===========================================================================
# 3. Método
# ===========================================================================
s = nueva_diapositiva(
    f'{miles(total_modelos)} modelos de {n_marcas} cadenas, comparando la misma prenda básica',
    'Dieciséis cadenas agrupadas por grupo empresarial o segmento. Comparamos solo prendas básicas, que son '
    'las más comparables entre marcas. Con menos de 5 modelos básicos no calculamos cuartiles ni '
    'solapamiento; esas marcas solo aparecen como puntos sueltos. Women\'secret queda fuera porque es '
    'lencería y homewear y no vende vaqueros.')
GRUPOS = ['Inditex', 'Tendam', 'Mango', 'H&M', 'Primark', 'Premium española']
COLOR_GRUPO = {'Inditex': AZUL, 'Tendam': NARANJA}
cw, chh, gx, gy = (ANCHO - 2 * MARGEN - 2 * 0.25) / 3, 1.3, 0.25, 0.2
for i, g in enumerate(GRUPOS):
    fila, col = divmod(i, 3)
    ms = marcas[marcas['grupo'] == g]
    nombres = ', '.join(m + (' (fuera)' if not e else '') for m, e in zip(ms['marca'], ms['en_analisis']))
    nc = sum(n_basicas.get(f'{m}|camiseta', 0) for m, e in zip(ms['marca'], ms['en_analisis']) if e)
    nv = sum(n_basicas.get(f'{m}|vaquero', 0) for m, e in zip(ms['marca'], ms['en_analisis']) if e)
    caja(s, [[(g, {'tam': 16, 'negrita': True, 'color': COLOR_GRUPO.get(g, GRIS_MARCA), 'espacio': 2})],
             [(nombres, {'tam': 13, 'color': TEXTO, 'espacio': 2})],
             [(f'{nc} camisetas · {nv} vaqueros básicos', {'tam': 12, 'color': TEXTO_SEC})]],
         MARGEN + col * (cw + gx), 1.5 + fila * (chh + gy), cw, chh, fondo=FONDO_TARJETA, margen=0.15)
bloques = [
    ('Qué se compara', 'Camiseta de manga larga y vaquero largo, sección mujer. Cada modelo cuenta una vez: '
                       'las variantes de color no son filas nuevas.'),
    ('Qué es una prenda básica', 'Camiseta lisa o de canalé, sin estampado ni adornos. Vaquero de cualquier '
                                 'corte, sin rotos, tachas ni estampados. Se clasifica por el nombre.'),
    ('Qué entra en las métricas', f'Precio de catálogo, sin rebaja. Marcas con 5 modelos o más por prenda '
                                  f'(de 5 a 14, muestra pequeña): {miles(basicas_metricas)} de las '
                                  f'{miles(basicas_analisis)} básicas.'),
]
bw = (ANCHO - 2 * MARGEN - 2 * 0.5) / 3
for i, (cab, txt) in enumerate(bloques):
    caja(s, [[(cab, {'tam': 18, 'negrita': True})], [(txt, {'tam': 15, 'color': TEXTO})]],
         MARGEN + i * (bw + 0.5), 4.55, bw, 2.3)
nota_fuente(s, 'Azul: Inditex. Naranja: Tendam. El número de prendas es el de modelos básicos de las marcas '
               'que entran en el análisis.')


# ===========================================================================
# 4. Escalera completa
# ===========================================================================
ad_v = med('vaquero', 'Adolfo Domínguez')
s = nueva_diapositiva(
    f'Cada cadena ocupa su tramo: el vaquero mediano va de {euros(med("vaquero", "Primark"))} en Primark '
    f'a {euros(ad_v)} en Adolfo Domínguez',
    'Cada barra es el 50 % central de los modelos de una marca y el punto, su precio mediano. El eje está en '
    'escala logarítmica: cada línea de la cuadrícula duplica el precio, así que la zona barata no se aplasta '
    'y un salto "×2" mide siempre lo mismo. Las marcas premium solo tienen muestra suficiente en vaqueros; en '
    'camisetas aparecen como puntos sueltos.')
imagen(s, '16_marcas/01_escalera_16_marcas.png', MARGEN + 0.3, 1.45, w=ANCHO - 2 * MARGEN - 0.6, h=5.55)


# ===========================================================================
# 5. Dos escaleras: Inditex y Tendam
# ===========================================================================
sp_v_reb = sens.loc[('vaquero', 'Springfield'), 'mediana_rebajado']
co_v_reb = sens.loc[('vaquero', 'Cortefiel'), 'mediana_rebajado']
s = nueva_diapositiva(
    'Cada escalón de Inditex cuesta casi el doble; Tendam repite el patrón un peldaño más arriba',
    f'Dividimos la mediana de cada escalón entre la del anterior. En Inditex sale de {txt_inditex} veces en las '
    f'dos prendas. Tendam escalona igual ({txt_tendam}), pero empieza más arriba: Springfield cuesta lo que '
    'Zara y Cortefiel lo que Massimo Dutti. Ojo: casi todo Springfield y buena parte de Cortefiel estaban '
    'rebajados; con el precio rebajado, la escalera de Tendam baja.')
imagen_centrada(s, '16_marcas/02_escaleras_inditex_tendam.png', w=8.3)
lineas = [[('Cálculo (medianas)', {'negrita': True, 'tam': 16})]]
for cat in ['camiseta', 'vaquero']:
    lineas.append([(cat.capitalize(), {'negrita': True})])
    for g, esc in [('Inditex', ESC_I), ('Tendam', ESC_T)]:
        for e in esc:
            a, b = e.split(' → ')
            if (cat, e) in ratios.index and en_metricas(cat, a) and en_metricas(cat, b):
                calc = ratios.loc[(cat, e), 'calculo'].replace(' €', '')
                lineas.append([(f'{e}  ', {'color': AZUL if g == 'Inditex' else NARANJA}),
                               (f'{veces(rat(cat, e))}', {'negrita': True}),
                               (f'  ({calc})', {'color': TEXTO_SEC, 'tam': 12})])
lineas.append([('Con el precio rebajado ', {'negrita': True}),
               (f'el vaquero de Springfield baja a {euros(sp_v_reb)} y el de Cortefiel a {euros(co_v_reb)}.', {})])
caja(s, lineas, 9.1, 1.6, ANCHO - MARGEN - 9.1, 5.3, tam=13)


# ===========================================================================
# 6. Solapamiento
# ===========================================================================
s = nueva_diapositiva(
    'Hay cinco choques frontales de precio, y en la gama baja sigue habiendo solo uno',
    'Medimos cuánto se parecen los repartos de precio de cada pareja de marcas, por tramos. En negro, los '
    'choques que defendemos: aguantan al cambiar el ancho de los tramos (la rayita vertical). Los textos junto '
    'a las barras avisan cuando una cifra cae mucho con otros tramos o con el precio rebajado: Mango–Springfield '
    'o Springfield–Zara en camisetas parecen altos, pero son efecto del corte, como pasaba con H&M–Lefties. '
    'Cortefiel–Massimo Dutti es real a precio de catálogo, pero depende de las rebajas.')
imagen(s, '16_marcas/03_solapamiento_16_marcas.png', MARGEN, 1.4, w=ANCHO - 2 * MARGEN, h=5.6)


# ===========================================================================
# 7. Gama media a tres
# ===========================================================================
mango_v = muestras.loc[('vaquero', 'Mango')]
s = nueva_diapositiva(
    'La gama media es un choque a tres: Zara, H&M y Mango',
    f'Mango entra de lleno en la franja central de Zara. En vaqueros, el {pct(mango_v["pct_precio_mas_frecuente"])} '
    f'de sus modelos básicos está a {euros(mango_v["precio_mas_frecuente"])}, justo en el borde bajo de esa '
    f'franja. El solapamiento con Zara es del {pct(mz_v)} y aguanta con tramos de 8 €. Quien posicione una '
    'marca en la gama media ya no puede compararse solo con Zara y H&M.')
imagen_centrada(s, '16_marcas/04_gama_media_zara_hm_mango.png', w=8.3)
caja(s, [
    [('Solapamiento en vaqueros', {'negrita': True, 'tam': 16})],
    [('Mango – Zara  ', {'negrita': True}), (f'{pct(mz_v)} (tramos de 8 €: {pct(sol("vaquero", "Mango – Zara", "solape_pct_robustez"))})', {})],
    [('H&M – Mango  ', {'negrita': True}), (f'{pct(sol("vaquero", "H&M – Mango"))} ({pct(sol("vaquero", "H&M – Mango", "solape_pct_robustez"))})', {})],
    [('H&M – Zara  ', {'negrita': True}), (f'{pct(sol("vaquero", "H&M – Zara"))} ({pct(sol("vaquero", "H&M – Zara", "solape_pct_robustez"))})', {})],
    [('En camisetas', {'negrita': True, 'tam': 16})],
    f'Mango – Zara {pct(mz_c)} (tramos de 4 €: {pct(sol("camiseta", "Mango – Zara", "solape_pct_robustez"))}), con '
    f'solo {int(resumen.loc[("camiseta", "Mango"), "n"])} camisetas de Mango: muestra pequeña.',
    [('Mango, el más barato de los tres ', {'negrita': True}),
     (f'en vaquero: mediana {euros(med("vaquero", "Mango"))}, frente a {euros(med("vaquero", "H&M"))} de H&M '
      f'y {euros(med("vaquero", "Zara"))} de Zara.', {})],
], 9.2, 1.6, ANCHO - MARGEN - 9.2, 5.3, tam=14)


# ===========================================================================
# 8. H&M rodea a Zara (no cambia con la ampliación)
# ===========================================================================
rc, rv = rodea.loc[('camiseta', 'H&M')], rodea.loc[('vaquero', 'H&M')]
s = nueva_diapositiva(
    'H&M rodea a Zara en camisetas; en vaqueros el choque es más frontal',
    f'Esta conclusión no cambia con la ampliación (H&M y Zara son los mismos datos). En camisetas, H&M tiene '
    f'tanta oferta por debajo de la franja central de Zara ({rc["pct_por_debajo"]} %) como dentro '
    f'({rc["pct_dentro"]} %) o por encima ({rc["pct_por_encima"]} %). En vaqueros, el {rv["pct_dentro"]} % de '
    'H&M cae dentro de la franja de Zara. Y una advertencia: por la media, H&M parece más cara que Zara; por la '
    'mediana es al revés. La media la sube una cola de productos caros de la propia H&M.')
imagen(s, '05_hm_rodea_zara.png', MARGEN, 1.5, w=8.4)
filas = [[('El espejismo de la media', {'negrita': True, 'tam': 16})],
         'H&M parece más cara que Zara por la media, pero no por la mediana:']
for cat, nombre in [('camiseta', 'Camiseta'), ('vaquero', 'Vaquero')]:
    h, z = resumen.loc[(cat, 'H&M')], resumen.loc[(cat, 'Zara')]
    filas.append([(f'{nombre}  ', {'negrita': True}),
                  (f'media H&M {euros(h["media"])} > Zara {euros(z["media"])}; '
                   f'mediana H&M {euros(h["mediana"])} < Zara {euros(z["mediana"])}', {})])
filas.append(f'La cola cara de H&M (camisetas de hasta {euros(resumen.loc[("camiseta", "H&M"), "maximo"])}, '
             f'vaqueros de hasta {euros(resumen.loc[("vaquero", "H&M"), "maximo"])}) sube su media.')
caja(s, filas, 9.35, 1.6, ANCHO - MARGEN - 9.35, 4.1, tam=14, fondo=FONDO_TARJETA, margen=0.2)


# ===========================================================================
# 9. Cortefiel frente a Massimo Dutti (la duda y su descarte)
# ===========================================================================
cm_c, cm_c_reb = sol('camiseta', 'Cortefiel – Massimo Dutti'), sol('camiseta', 'Cortefiel – Massimo Dutti', 'solape_pct_rebajado')
reb_co = rebajas.loc['Cortefiel']
s = nueva_diapositiva(
    'Cortefiel coincide con Massimo Dutti en precio de catálogo, pero con la rebaja se separa',
    f'A precio de catálogo, Cortefiel cae justo encima de Massimo Dutti: {euros(med("vaquero", "Cortefiel"))} '
    f'frente a {euros(med("vaquero", "Massimo Dutti"))} en vaquero y {euros(med("camiseta", "Cortefiel"))} frente a '
    f'{euros(med("camiseta", "Massimo Dutti"))} en camiseta (medianas). Pero el {pct(reb_co["pct_rebajado"])} de su catálogo estaba '
    f'rebajado, con un descuento medio del {pct(reb_co["dto_medio_pct"])}. Con el precio que marcaba la web '
    f'ese día, el solapamiento en vaqueros baja del {pct(cm_v)} al {pct(cm_v_reb)}. No sabemos a qué precio se '
    'vende de verdad: solo vemos el catálogo.')
imagen_centrada(s, '16_marcas/05_cortefiel_massimo_dutti.png', w=8.3)
caja(s, [
    [('A precio de catálogo', {'negrita': True, 'tam': 16})],
    f'Solapamiento {pct(cm_v)} en vaqueros y {pct(cm_c)} en camisetas. Aguanta al cambiar los tramos.',
    [('Con el precio rebajado', {'negrita': True, 'tam': 16})],
    f'{pct(cm_v_reb)} en vaqueros y {pct(cm_c_reb)} en camisetas: Cortefiel se separa hacia abajo.',
    [('Lo que no sabemos', {'negrita': True, 'tam': 16})],
    'A qué precio se vende cada prenda. Si casi todo se vende rebajado, el precio de catálogo exagera la '
    'posición de Cortefiel.',
], 9.2, 1.6, ANCHO - MARGEN - 9.2, 5.3, tam=14)


# ===========================================================================
# 10. Tramo premium del vaquero
# ===========================================================================
s = nueva_diapositiva(
    'Por encima de 60 € el vaquero se ordena en dos niveles, aunque con muestras pequeñas',
    f'Entre las marcas de gama media-alta hay dos niveles: Scalpers (mediana {euros(med("vaquero", "Scalpers"))}), '
    f'junto a Silbon y El Ganso, que tienen muy pocos modelos; y por encima Desigual '
    f'({euros(med("vaquero", "Desigual"))}), Pedro del Hierro ({euros(med("vaquero", "Pedro del Hierro"))}) y '
    f'Adolfo Domínguez ({euros(ad_v)}). Todas con menos de 15 modelos: es una tendencia, no una conclusión '
    'firme. En camisetas ninguna de estas marcas llega a 5 modelos básicos.')
imagen_centrada(s, '16_marcas/08_vaquero_premium.png', w=8.3)
caja(s, [
    [('Nivel 1 · en torno a 60–80 €', {'negrita': True, 'tam': 16})],
    f'Scalpers ({euros(med("vaquero", "Scalpers"))}). Toca a Cortefiel ({pct(sol("vaquero", "Cortefiel – Scalpers"))} '
    f'de solapamiento) y a Massimo Dutti ({pct(sol("vaquero", "Massimo Dutti – Scalpers"))}).',
    [('Nivel 2 · en torno a 90–135 €', {'negrita': True, 'tam': 16})],
    f'Desigual, Pedro del Hierro y Adolfo Domínguez. Desigual – Pedro del Hierro: '
    f'{pct(sol("vaquero", "Desigual – Pedro del Hierro"))} (con rebajas, '
    f'{pct(sol("vaquero", "Desigual – Pedro del Hierro", "solape_pct_rebajado"))}).',
    [('Ancla de control', {'negrita': True, 'tam': 16})],
    '0 % de solapamiento entre cualquier marca de este tramo y Primark o Lefties: el método separa bien.',
], 9.2, 1.6, ANCHO - MARGEN - 9.2, 5.3, tam=14)


# ===========================================================================
# 11. Arquitectura de precios (apoyo)
# ===========================================================================
total_combis = len(arq)
combis_3 = int((arq['precios_distintos'] <= 3).sum())
s = nueva_diapositiva(
    'Las marcas repiten unos pocos precios; el x,95 lo usan sobre todo Zara y Massimo Dutti',
    f'En {combis_3} de las {total_combis} combinaciones de marca y prenda que entran en las métricas, tres '
    'precios o menos cubren todo el catálogo de básicas. Y cada cadena tiene su firma en los céntimos: Zara y '
    'Massimo Dutti terminan en ,95; H&M, Lefties, Mango y Tendam en ,99; Primark y Adolfo Domínguez usan '
    'precios enteros. Es un dato de apoyo, no un hallazgo central.')
caja(s, [[(f'{combis_3} de {total_combis}', {'tam': 54, 'negrita': True})],
         [(f'combinaciones de marca y prenda en las que 3 precios o menos cubren todo su catálogo de básicas',
           {'tam': 15})]], MARGEN, 1.7, 3.6, 3.5)
FIRMAS = [(',95', ',95'), (',99', ',99'), ('Enteros (,00)', ',00'), (',90', ',90')]
fx, fw = MARGEN + 4.1, (ANCHO - 2 * MARGEN - 4.1 - 0.3) / 2
for i, (cab, col) in enumerate(FIRMAS):
    fila, c = divmod(i, 2)
    lista = term[term[col] >= 20].sort_values(col, ascending=False)
    runs = [(cab, {'tam': 26, 'negrita': True})]
    par2 = []
    for j, (m, v) in enumerate(lista[col].items()):
        par2.append((m, {'negrita': True, 'color': color_marca(m)}))
        par2.append((f' {pct(v)}' + (' · ' if j < len(lista) - 1 else ''), {'color': TEXTO_SEC}))
    caja(s, [runs, par2], fx + c * (fw + 0.3), 1.6 + fila * 2.55, fw, 2.3, tam=14, fondo=FONDO_TARJETA, margen=0.2)
nota_fuente(s, 'Porcentaje de los modelos básicos de cada marca (camiseta y vaquero) con esa terminación. Solo '
               'se listan las marcas en las que la terminación pesa un 20 % o más.')


# ===========================================================================
# 12. El hueco de la escalera
# ===========================================================================
hc, hv = hueco.loc['camiseta'], hueco.loc['vaquero']
s = nueva_diapositiva(
    'Entre Zara y Massimo Dutti el hueco sigue casi vacío, ahora con vecinos a los dos lados',
    f'Entre el precio alto de Zara y el bajo de Massimo Dutti hay poca oferta: el {pct_hueco["camiseta"]} % de '
    f'los modelos en camisetas y el {pct_hueco["vaquero"]} % en vaqueros, sobre todo la cola de H&M y, en '
    f'camisetas, {int(hc.loc["Mango", "n_hueco"])} modelos de Mango. Las marcas nuevas se quedan a los lados: '
    f'Springfield por debajo y Cortefiel a la altura de Massimo Dutti. Ni siquiera con el precio rebajado se '
    f'llena ({pct_hueco_reb["camiseta"]} % y {pct_hueco_reb["vaquero"]} %): las rebajas lo saltan hacia abajo.')
imagen(s, '16_marcas/06_hueco_16_marcas.png', MARGEN + 0.3, 1.45, w=ANCHO - 2 * MARGEN - 0.6, h=5.55)


# ===========================================================================
# 13. Qué implica para quien posiciona una marca
# ===========================================================================
r = resumen
z75c, md25c = r.loc[('camiseta', 'Zara'), 'p75'], r.loc[('camiseta', 'Massimo Dutti'), 'p25']
z75v, md25v = r.loc[('vaquero', 'Zara'), 'p75'], r.loc[('vaquero', 'Massimo Dutti'), 'p25']
s = nueva_diapositiva(
    'Para posicionar una marca: elegir primero el tramo y después contra quién compararse',
    'Traducción práctica para un equipo de marketing. Primero decidir el tramo de precio de entrada; después, '
    'qué marcas son la referencia en ese tramo. La zona entre Zara y Massimo Dutti es la menos ocupada, pero '
    'es una oportunidad a investigar, no un hueco de mercado demostrado: no sabemos si hay demanda a ese precio.')
TARJETAS = [
    ('Gama baja', f'Vaquero {euros(med("vaquero", "Primark"))}–{euros(med("vaquero", "Lefties"))} · camiseta '
                  f'{euros(med("camiseta", "Primark"))}–{euros(med("camiseta", "Lefties"))}',
     'La referencia son Lefties y Primark. Ninguna de las 11 marcas nuevas entra en este tramo.'),
    ('Gama media', f'Vaquero {euros(med("vaquero", "Mango"))}–{euros(med("vaquero", "Zara"))} · camiseta '
                   f'{euros(med("camiseta", "H&M"))}–{euros(med("camiseta", "Zara"))}',
     'Compararse con Zara, H&M y Mango a la vez. Springfield asoma por arriba, con rebajas casi permanentes.'),
    ('Gama media-alta', f'Vaquero {euros(med("vaquero", "Massimo Dutti"))} · camiseta '
                        f'{euros(med("camiseta", "Massimo Dutti"))}',
     'Massimo Dutti y Cortefiel. Con Cortefiel, mirar también su precio rebajado.'),
    ('Zona a investigar', f'Camiseta {euros(z75c)}–{euros(md25c)} · vaquero {euros(z75v)}–{euros(md25v)}',
     'La menos ocupada entre estas cadenas. Antes de decidir: ¿hay demanda a ese precio? ¿La ocupan marcas '
     'fuera del estudio, como COS o & Other Stories?'),
]
tw, th = (ANCHO - 2 * MARGEN - 0.3) / 2, 2.45
for i, (cab, precio, txt) in enumerate(TARJETAS):
    fila, col = divmod(i, 2)
    caja(s, [[(f'{i + 1}. {cab}', {'tam': 20, 'negrita': True})],
             [(precio, {'tam': 14, 'negrita': True, 'color': TEXTO_SEC})],
             [(txt, {'tam': 15})]],
         MARGEN + col * (tw + 0.3), 1.55 + fila * (th + 0.3), tw, th, fondo=FONDO_TARJETA, margen=0.25)
nota_fuente(s, 'Precios: medianas de catálogo de las prendas básicas, salvo la zona a investigar (P75 de Zara '
               '– P25 de Massimo Dutti).')


# ===========================================================================
# 14. Qué cambió al añadir 11 marcas
# ===========================================================================
CAMBIOS = [
    ('Se mantiene', 'Inditex escalona sus marcas: cada escalón cuesta aproximadamente el doble.'),
    ('Se mantiene', f'Lefties–Primark es el único choque de la gama baja ({pct(sol("vaquero", "Lefties – Primark"))} en vaqueros).'),
    ('Se mantiene', 'H&M rodea a Zara en camisetas y choca de frente con ella en vaqueros.'),
    ('Se mantiene', f'Hay un hueco entre Zara y Massimo Dutti ({pct(pct_hueco["camiseta"])} y {pct(pct_hueco["vaquero"])} '
                    'de los modelos).'),
    ('Se mantiene', 'El ancla de control funciona: 0 % entre las marcas premium y Primark o Lefties.'),
    ('Cambia', f'"Solo dos choques frontales" → cinco. Mango entra en la gama media ({pct(mz_v)} con Zara en vaqueros).'),
    ('Cambia', f'"Massimo Dutti está aislado" → Cortefiel coincide con él a precio de catálogo ({pct(cm_v)}; '
               f'{pct(cm_v_reb)} con rebajas).'),
    ('Nuevo', f'Tendam también escalona ({txt_tendam}), un peldaño por encima de Inditex.'),
]
NUMEROS = {1: 'una', 2: 'dos', 3: 'tres', 4: 'cuatro', 5: 'cinco', 6: 'seis'}
n_mantiene = sum(e == 'Se mantiene' for e, _ in CAMBIOS)
n_cambia = sum(e == 'Cambia' for e, _ in CAMBIOS)
s = nueva_diapositiva(
    f'Al añadir 11 marcas, {NUMEROS[n_mantiene]} conclusiones se mantienen y {NUMEROS[n_cambia]} cambian',
    'Material de criterio: antes de dar por buena una conclusión, ver si aguanta al ampliar la muestra. Con 16 '
    'cadenas, la escalera de Inditex, el duelo de la gama baja, "H&M rodea a Zara" y el hueco siguen en pie. '
    'Cambian dos cosas: ya no hay solo dos choques frontales (Mango entra en la gama media) y Massimo Dutti ya '
    'no está aislado (Cortefiel, a precio de catálogo). Y aparece algo nuevo: Tendam también escalona.')
COLOR_ETIQ = {'Se mantiene': VERDE_OK, 'Cambia': NARANJA, 'Nuevo': AZUL}
fh = 0.58
for i, (etq, txt) in enumerate(CAMBIOS):
    y = 1.5 + i * (fh + 0.09)
    caja(s, etq, MARGEN, y, 1.7, fh, tam=14, negrita=True, color=BLANCO, fondo=COLOR_ETIQ[etq],
         alinear=PP_ALIGN.CENTER, anclaje=MSO_ANCHOR.MIDDLE)
    caja(s, txt, MARGEN + 1.85, y, ANCHO - 2 * MARGEN - 1.85, fh, tam=15, fondo=FONDO_TARJETA,
         anclaje=MSO_ANCHOR.MIDDLE, margen=0.18)


# ===========================================================================
# 15. Limitaciones
# ===========================================================================
reb_sp = rebajas.loc['Springfield']
s = nueva_diapositiva(
    'Lo que este análisis no dice',
    'Esto es lo que hay que tener en cuenta antes de usar las conclusiones. La más importante sigue siendo la '
    'primera: describimos dónde están los precios, no por qué están ahí. Con la ampliación se añaden dos '
    'cautelas grandes: las rebajas de Tendam y las muestras pequeñas de las marcas premium.')
limites = [
    ('Posicionamiento, no estrategia', 'La escalera puede ser una segmentación buscada o prendas de distinto '
                                       'material. Sin la composición, no se distinguen.'),
    ('Una foto de un solo día', f'10/10/2026, precio de catálogo. Springfield tenía el {pct(reb_sp["pct_rebajado"])} '
                                f'rebajado y Cortefiel el {pct(reb_co["pct_rebajado"])}: su catálogo puede exagerar su precio real.'),
    ('Muestras pequeñas', 'Las marcas premium solo tienen muestra en vaqueros, y de 7 a 14 modelos. Con menos '
                          'de 5 no se calcula nada.'),
    ('Básicas por palabras clave', 'Por el nombre del producto. En 5 marcas, la manga larga se filtró leyendo '
                                   'la ficha; en 4, el vaquero por la palabra "denim".'),
    ('Marcas fuera', 'Shein (protección anti-bot) y Women\'secret (lencería y homewear, sin vaqueros).'),
    ('Sublíneas y marcas invitadas', 'H&M, Zara y Primark mezclan sublíneas. Se excluyeron las marcas '
                                     'invitadas de Tendam y Scalpers.'),
    ('Qué es un modelo', 'Lo que la web trata como referencia propia. En H&M y Mango, cada lavado de un '
                         'vaquero cuenta como modelo.'),
    ('Medidas aproximadas', 'Cuartiles con NTILE(4). El solapamiento depende del ancho del tramo: se probó '
                            'con dos anchos y con el precio rebajado.'),
]
cw2, ch2, gx2, gy2 = (ANCHO - 2 * MARGEN - 3 * 0.3) / 4, 2.45, 0.3, 0.3
for i, (cab, txt) in enumerate(limites):
    fila, col = divmod(i, 4)
    caja(s, [[(cab, {'negrita': True, 'tam': 16})], [(txt, {'tam': 14, 'color': TEXTO})]],
         MARGEN + col * (cw2 + gx2), 1.5 + fila * (ch2 + gy2), cw2, ch2, fondo=FONDO_TARJETA, margen=0.2)


# ===========================================================================
# 16. Conclusión final: para qué sirve este análisis
# ===========================================================================
s = nueva_diapositiva(
    'Conclusión: un mapa de precios para decidir dónde entrar y contra quién medirse',
    'Para qué ha servido todo esto. Antes, "Zara compite con H&M" o "Massimo Dutti está en otra liga" eran '
    'intuiciones; ahora son cifras comprobadas con dos métricas, dos anchos de tramo y el precio rebajado. Una '
    'marca de ropa puede usarlo para fijar su precio de entrada y saber contra quién se la va a comparar. Una '
    'agencia puede usarlo como base de un informe de precios para las marcas que asesora y repetirlo cada '
    'temporada con el mismo método. Lo que no hace: no dice cuánto se vende ni si hay demanda en un tramo; es el '
    'punto de partida para esas preguntas.')
caja(s, [[('Qué aporta: ', {'negrita': True}),
          (f'un mapa del precio de catálogo de {n_marcas} cadenas, comprobado con dos métricas, dos anchos de tramo '
           'y el precio rebajado, que dice en qué tramo está cada una y con quién comparte precios.', {})]],
     MARGEN, 1.45, ANCHO - 2 * MARGEN, 0.75, tam=16, fondo=FONDO_TARJETA, anclaje=MSO_ANCHOR.MIDDLE, margen=0.22)
z25v = r.loc[('vaquero', 'Zara'), 'p25']
# Solapamientos llamativos (> 50 %) que caen 20 puntos o más con otro ancho de tramo o con rebajas
altos = solape[solape['solape_pct'] > 50]
n_altos = len(altos)
# Solo caídas: si la cifra sube con otro ancho (Lefties–Primark en camiseta, 52 % → 72 %), no es fragilidad.
n_fragiles = int(((altos['solape_pct'] - altos['solape_pct_robustez']).ge(20) |
                  (altos['solape_pct'] - altos['solape_pct_rebajado']).ge(20)).sum())
USOS = [
    # Encabezados en gris oscuro: azul y naranja significan Inditex y Tendam en todo el deck.
    ('Una marca de ropa podría…', TEXTO, [
        ('Fijar su precio de entrada con referencia: ',
         f'un vaquero entre {euros(z25v)} y {euros(z75v)} se medirá a la vez con Zara, H&M y Mango; por debajo '
         f'de {euros(med("vaquero", "Lefties"))}, con Lefties y Primark.'),
        ('Separar sus propias líneas sin pisarse: ',
         'Inditex y Tendam separan cada escalón casi al doble de precio; es una referencia de cuánta distancia '
         'dejar entre línea básica y línea premium.'),
        ('Plantear una hipótesis de entrada: ',
         f'la zona entre Zara y Massimo Dutti (vaquero {euros(z75v)}–{euros(md25v)}) es la menos ocupada. Hay '
         'que validar la demanda antes de lanzar nada.'),
    ]),
    ('Una agencia podría…', TEXTO, [
        ('Ofrecer un informe de posicionamiento de precio ',
         'a las marcas que asesora: dónde están, contra quién se comparan y qué huecos quedan, con cifras.'),
        ('Repetir la foto cada temporada: ',
         'el proceso es reproducible (mismas reglas, mismas métricas). Basta un catálogo nuevo para ver quién '
         'sube, quién baja y cómo afectan las rebajas.'),
        ('Exigir pruebas antes de afirmar: ',
         f'un choque de precio solo se da por bueno si aguanta al cambiar los tramos y con el precio rebajado. '
         f'Aquí, {n_fragiles} de los {n_altos} solapamientos por encima del 50 % caían 20 puntos o más.'),
    ]),
]
cw3 = (ANCHO - 2 * MARGEN - 0.4) / 2
for k, (cab, col, items) in enumerate(USOS):
    x = MARGEN + k * (cw3 + 0.4)
    pars = [[(cab, {'tam': 20, 'negrita': True, 'color': col, 'espacio': 10})]]
    for i, (neg, txt) in enumerate(items):
        pars.append([(f'{i + 1}. {neg}', {'negrita': True}), (txt, {'espacio': 10})])
    caja(s, pars, x, 2.45, cw3, 3.95, tam=15)
caja(s, [[('Lo que no sustituye: ', {'negrita': True}),
          ('no mide ventas ni demanda. Es el punto de partida para preguntarlas, no la respuesta.', {})]],
     MARGEN, 6.5, ANCHO - 2 * MARGEN - 0.8, 0.4, tam=14, color=TEXTO_SEC)


# ===========================================================================
# 17. Anexo A: tabla de precios
# ===========================================================================
s = nueva_diapositiva(
    'Anexo A: distribución de precios de las marcas que entran en las métricas',
    'Tabla completa de la vista v_resumen_precios para las marcas con 5 modelos o más. Las marcas con menos '
    'de 5 modelos básicos en una prenda no tienen cuartiles: aparecen como puntos sueltos en los gráficos.')
CAB = ['Marca', 'n', 'P25', 'Mediana', 'P75', 'Máx.', 'Media']
anchos = [1.55, 0.45, 0.72, 0.8, 0.72, 0.72, 0.72]
for k, cat in enumerate(['camiseta', 'vaquero']):
    d = resumen.loc[cat]
    d = d[d['en_metricas'] == 1].sort_values('mediana')
    datos = [CAB]
    for marca, fila in d.iterrows():
        datos.append([marca, f'{int(fila["n"])}' + ('*' if fila['fiabilidad'] != 'OK' else '')] +
                     [euros(fila[c]) for c in ['p25', 'mediana', 'p75', 'maximo', 'media']])
    x = MARGEN + k * (sum(anchos) + 0.5)
    caja(s, 'Camiseta de manga larga' if cat == 'camiseta' else 'Vaquero', x, 1.4, sum(anchos), 0.35,
         tam=14, negrita=True)
    tabla(s, datos, x, 1.8, sum(anchos), anchos, tam=10, colores_col0=color_marca)
nota_fuente(s, '* Muestra pequeña (5–14 modelos). Cuartiles aproximados con NTILE(4). ' + FUENTE_DATOS)


# ===========================================================================
# 18. Anexo B: robustez y sensibilidad
# ===========================================================================
s = nueva_diapositiva(
    'Anexo B: robustez del solapamiento y sensibilidad a las rebajas',
    'Para cada pareja con un 30 % o más de solapamiento: la métrica principal (tramos de 5 € / 10 €), la misma '
    'con tramos de 4 € / 8 € y la misma con el precio rebajado. Una cifra que se hunde en cualquiera de las dos '
    'pruebas no se usa como conclusión.')
pares_tabla = solape[solape['solape_pct'] >= 30].sort_values(['categoria', 'solape_pct'], ascending=[True, False])
datos = [['Pareja', 'Prenda', 'Principal', '4 € / 8 €', 'Rebajado']]
for f in pares_tabla.itertuples():
    datos.append([f.pareja, f.categoria, pct(f.solape_pct), pct(f.solape_pct_robustez), pct(f.solape_pct_rebajado)])
tabla(s, datos, MARGEN, 1.45, 7.3, [3.2, 1.0, 1.0, 1.05, 1.05], tam=10, alto_fila=0.24)
caja(s, [
    [('Métrica principal: solapamiento por tramos. ', {'negrita': True}),
     ('Se reparte el catálogo de cada marca en tramos de precio (5 € en camiseta, 10 € en vaquero) y se suma, '
      'tramo a tramo, la menor de las dos proporciones. 0 % = no comparten ningún tramo; 100 % = mismo reparto.', {})],
    [('Sensibilidad a las rebajas. ', {'negrita': True}),
     ('Se repite todo con el precio que marcaba la web ese día. Inditex, H&M, Primark y Mango no cambian; '
      'Tendam baja: ', {})] +
    [(f'{m} {euros(sens.loc[("vaquero", m), "mediana"])} → {euros(sens.loc[("vaquero", m), "mediana_rebajado"])}'
      + ('; ' if m != 'Cortefiel' else ' (mediana del vaquero).'), {}) for m in ['Springfield', 'Cortefiel']],
    [('Unidad. ', {'negrita': True}),
     ('Un modelo, deduplicado por referencia. Las 5 marcas originales reproducen exactamente las cifras del '
      'primer análisis (lo comprueba scripts/construir_bd.py).', {})],
], 8.3, 1.45, ANCHO - MARGEN - 8.3, 5.4, tam=12)
nota_fuente(s)

prs.save(SALIDA)
print('Presentación guardada en', os.path.relpath(SALIDA, BASE), f'({len(prs.slides)} diapositivas)')
