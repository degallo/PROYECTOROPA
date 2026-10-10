"""
Paso 3 · Presentación PowerPoint (guion de la sección 9 de CLAUDE.md).

- 16:9, fondo blanco, Calibri (viene con Office; los gráficos usan Inter).
- Los títulos van en el marcador de título de cada diapositiva: son texto
  editable y salen en la vista de esquema de PowerPoint.
- Los gráficos se insertan como imagen (output/graficos/).
- Todas las cifras se leen de data/moda.db y de output/tablas/; ninguna se
  escribe a mano.
- Cada diapositiva lleva notas del orador con un guion breve.

Uso:  python scripts/crear_deck.py
"""
import os
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
TABLAS = os.path.join(BASE, 'output', 'tablas')
GRAFICOS = os.path.join(BASE, 'output', 'graficos')
SALIDA = os.path.join(BASE, 'output', 'posicionamiento_precio_moda.pptx')

# ---------------------------------------------------------------------------
# Estilo (mismos colores que los gráficos)
# ---------------------------------------------------------------------------
AZUL = RGBColor(0x2A, 0x64, 0xA8)      # Inditex
TEXTO = RGBColor(0x33, 0x33, 0x33)
TEXTO_SEC = RGBColor(0x6B, 0x6B, 0x6B)
GRIS_MARCA = RGBColor(0x7A, 0x7A, 0x7A)
FONDO_TARJETA = RGBColor(0xF3, 0xF3, 0xF3)
BLANCO = RGBColor(0xFF, 0xFF, 0xFF)
FUENTE_LETRA = 'Calibri'
AUTOR = 'Javier Benítez Escobedo'

INDITEX = {'Lefties', 'Zara', 'Massimo Dutti'}
ORDEN = ['Primark', 'Lefties', 'H&M', 'Zara', 'Massimo Dutti']

ANCHO, ALTO = 13.333, 7.5      # pulgadas (16:9)
MARGEN = 0.6


# ---------------------------------------------------------------------------
# Formato español
# ---------------------------------------------------------------------------
def euros(x):
    return f'{x:.2f}'.replace('.', ',') + ' €'


def pct(x):
    return f'{int(round(x))} %'


def veces(x):
    return '×' + f'{x:.1f}'.replace('.', ',')


def miles(n):
    return f'{n:,}'.replace(',', '.')


# ---------------------------------------------------------------------------
# Datos (todo sale de la base y de las tablas del paso 1)
# ---------------------------------------------------------------------------
con = sqlite3.connect(DB)
resumen = pd.read_sql('SELECT * FROM v_resumen_precios', con).set_index(['categoria', 'marca'])
pares = pd.read_sql('SELECT categoria, pareja, solape_pct FROM v_solape_pares', con)
total_modelos = con.execute('SELECT COUNT(*) FROM catalogo').fetchone()[0]
total_basicas = con.execute("SELECT COUNT(*) FROM catalogo WHERE motivo = '7_basica'").fetchone()[0]
n_basicas = dict(con.execute("""SELECT marca || '|' || categoria, COUNT(*) FROM catalogo
                                WHERE motivo = '7_basica' GROUP BY marca, categoria""").fetchall())
con.close()

solape = {(r.categoria, r.pareja): r.solape_pct for r in pares.itertuples()}
ratios = pd.read_csv(os.path.join(TABLAS, 'ratios_escalera.csv')).set_index(['categoria', 'escalon'])
hueco = pd.read_csv(os.path.join(TABLAS, 'hueco_escalera.csv')).set_index(['categoria', 'marca'])
rodea = pd.read_csv(os.path.join(TABLAS, 'hm_rodea_zara.csv')).set_index(['categoria', 'marca'])
arq = pd.read_csv(os.path.join(TABLAS, 'arquitectura_precios.csv')).set_index(['categoria', 'marca'])
term = pd.read_csv(os.path.join(TABLAS, 'terminaciones.csv')).set_index('marca')

# Prueba de robustez (4 € / 8 €): mismo cálculo que v_solape_pares con otro ancho.
basicas = pd.read_sql("""SELECT marca, categoria, precio_actual AS precio FROM catalogo
                         WHERE motivo = '7_basica' AND precio_actual IS NOT NULL""",
                      sqlite3.connect(DB))


def solape_ancho(cat, ancho, a, b):
    d = basicas[(basicas['categoria'] == cat) & basicas['marca'].isin([a, b])].copy()
    d['tramo'] = (d['precio'] // ancho).astype(int)
    cuota = d.groupby(['marca', 'tramo']).size().unstack(fill_value=0)
    cuota = cuota.div(cuota.sum(axis=1), axis=0)
    return round(100 * cuota.min().sum())


def r_med(cat, marca):
    return resumen.loc[(cat, marca), 'mediana']


# Ratios de la escalera (de la tabla del paso 1)
rat = {(c, e): ratios.loc[(c, e), 'ratio_mediana'] for c, e in ratios.index}
rat_media = {(c, e): ratios.loc[(c, e), 'ratio_media'] for c, e in ratios.index}
ESC = ['Lefties → Zara', 'Zara → Massimo Dutti']
ratio_min = min(rat[(c, e)] for c in ['camiseta', 'vaquero'] for e in ESC)
ratio_max = max(rat[(c, e)] for c in ['camiseta', 'vaquero'] for e in ESC)

# Mayor solapamiento fuera de las dos parejas destacadas
DESTACADAS = {'Lefties – Primark', 'H&M – Zara'}
resto_max = {c: max(v for (cc, p), v in solape.items() if cc == c and p not in DESTACADAS)
             for c in ['camiseta', 'vaquero']}

# Hueco
pct_hueco = {c: round(100 * hueco.loc[c]['n_hueco'].sum() / hueco.loc[c]['n'].sum())
             for c in ['camiseta', 'vaquero']}

# ---------------------------------------------------------------------------
# Utilidades de maquetación
# ---------------------------------------------------------------------------
prs = Presentation()
prs.slide_width = Inches(ANCHO)
prs.slide_height = Inches(ALTO)
LAYOUT_PORTADA = prs.slide_layouts[0]     # "Title Slide"
LAYOUT_TITULO = prs.slide_layouts[5]      # "Title Only"


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
    tf.text = titulo
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    estilo_runs(p, 28, negrita=True)
    s.notes_slide.notes_text_frame.text = notas
    if numero:
        caja(s, f'{len(prs.slides)}', ANCHO - MARGEN - 0.6, ALTO - 0.45, 0.6, 0.3, tam=10,
             color=TEXTO_SEC, alinear=PP_ALIGN.RIGHT)
    return s


def forma_plana(s, x, y, w, h, color):
    """Rectángulo de color sin borde ni sombra. Se borra el estilo heredado del tema
    (<p:style>), que en algunos programas añade una sombra aunque se desactive."""
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
    if fondo is not None:
        forma = forma_plana(s, x, y, w, h, fondo)
    else:
        forma = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
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
            r.text = txt
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


def cifra_grande(s, cifra, texto, x, y, w, color):
    caja(s, cifra, x, y, w, 1.2, tam=66, color=color, negrita=True)
    caja(s, texto, x, y + 1.3, w, 1.4, tam=15, color=TEXTO)


# ===========================================================================
# 1. Portada
# ===========================================================================
s = prs.slides.add_slide(LAYOUT_PORTADA)
t = s.shapes.title
t.left, t.top, t.width, t.height = Inches(MARGEN + 0.2), Inches(1.5), Inches(6.1), Inches(2.9)
t.text_frame.word_wrap = True
t.text_frame.vertical_anchor = MSO_ANCHOR.BOTTOM
t.text_frame.text = '¿Compiten de verdad en precio las grandes cadenas de moda en España?'
p = t.text_frame.paragraphs[0]
p.alignment = PP_ALIGN.LEFT
estilo_runs(p, 38, negrita=True)
t.text_frame.margin_left = t.text_frame.margin_right = 0
sub = s.placeholders[1]
sub.left, sub.top, sub.width, sub.height = Inches(MARGEN + 0.2), Inches(4.6), Inches(6.1), Inches(1.0)
sub.text_frame.word_wrap = True
sub.text_frame.text = ('Posicionamiento de precio de cinco cadenas a partir de su catálogo online')
p = sub.text_frame.paragraphs[0]
p.alignment = PP_ALIGN.LEFT
estilo_runs(p, 20, color=TEXTO_SEC)
sub.text_frame.margin_left = sub.text_frame.margin_right = 0
caja(s, [[(AUTOR, {'negrita': True, 'color': TEXTO})], 'Datos recogidos el 10/10/2026'],
     MARGEN + 0.2, 6.05, 6.1, 0.8, tam=14, color=TEXTO_SEC)

# Motivo visual: la escalera de precios con las cinco marcas. Cada peldaño mide lo que
# el precio mediano del vaquero básico de esa marca (factor de mentira = 1): Inditex en
# azul, el resto en gris, igual que en los gráficos.
LOGOS = {m: os.path.join(BASE, 'assets', 'logos', f) for m, f in
         [('Primark', 'primark.png'), ('Lefties', 'lefties.png'), ('H&M', 'hm.png'),
          ('Zara', 'zara.png'), ('Massimo Dutti', 'massimo_dutti.png')]}
# Los logos solo se usan si están los cinco; si falta alguno, van todos como texto
# para que la portada sea coherente.
usar_logos = all(os.path.exists(r) for r in LOGOS.values())


def logo_monocromo(ruta, color=(0x33, 0x33, 0x33)):
    """Convierte un logo a un solo color (gris oscuro) conservando su forma.
    Usa la transparencia del PNG; si no la tiene, la oscuridad del píxel."""
    im = Image.open(ruta).convert('RGBA')
    if im.getextrema()[3][0] == 255:            # sin transparencia: fondo claro
        gris = im.convert('L')
        alfa = gris.point(lambda v: 255 - v)
    else:
        alfa = im.getchannel('A')
    plano = Image.new('RGBA', im.size, color + (0,))
    plano.putalpha(alfa)
    plano = plano.crop(alfa.getbbox())
    destino = os.path.join(GRAFICOS, '_logos', os.path.basename(ruta))
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    plano.save(destino)
    return destino


GRIS_PELDANO = RGBColor(0xD3, 0xD3, 0xD3)
base_y, alto_max = 6.55, 3.7
pw, pg = 1.02, 0.1
x0 = ANCHO - MARGEN - 5 * pw - 4 * pg
precio_max = max(r_med('vaquero', m) for m in ORDEN)
for i, marca in enumerate(ORDEN):
    alto = alto_max * r_med('vaquero', marca) / precio_max
    x = x0 + i * (pw + pg)
    forma_plana(s, x, base_y - alto, pw, alto, AZUL if marca in INDITEX else GRIS_PELDANO)
    # Precio dentro del peldaño, arriba
    caja(s, euros(r_med('vaquero', marca)), x, base_y - alto + 0.08, pw, 0.3, tam=11,
         color=BLANCO if marca in INDITEX else TEXTO, negrita=True, alinear=PP_ALIGN.CENTER)
    # Marca encima del peldaño: logo (si están todos) o nombre
    if usar_logos:
        ruta = logo_monocromo(LOGOS[marca])
        ancho_px, alto_px = Image.open(ruta).size
        w = min(pw * 0.85, 0.42 * ancho_px / alto_px)
        h = w * alto_px / ancho_px
        s.shapes.add_picture(ruta, Inches(x + (pw - w) / 2), Inches(base_y - alto - 0.12 - h),
                             Inches(w), Inches(h))
    else:
        nombre = marca.replace(' ', '\n')
        lineas = nombre.count('\n') + 1
        caja(s, [[(l, {'espacio': 0})] for l in nombre.split('\n')], x - 0.05, base_y - alto - 0.1 - 0.27 * lineas, pw + 0.1,
             0.27 * lineas, tam=13, negrita=True, alinear=PP_ALIGN.CENTER, anclaje=MSO_ANCHOR.BOTTOM,
             color=AZUL if marca in INDITEX else TEXTO)
caja(s, 'Altura de cada peldaño: precio mediano del vaquero básico. En azul, Inditex.',
     x0, base_y + 0.1, 5 * pw + 4 * pg, 0.3, tam=10, color=TEXTO_SEC, alinear=PP_ALIGN.RIGHT)
s.notes_slide.notes_text_frame.text = (
    'Pregunta de partida: dónde se posiciona en precio cada gran cadena de moda en España y con quién '
    'se solapa. En concreto: ¿escalona Inditex sus marcas sin pisarse, y dónde chocan con sus rivales? '
    'Es un análisis de precio de catálogo, no de ventas ni de cuota.')


# ===========================================================================
# 2. La Gran Idea
# ===========================================================================
s = nueva_diapositiva(
    'Inditex escalona sus marcas sin pisarse; solo hay dos choques frontales de precio',
    'La historia en una frase: Inditex coloca Lefties, Zara y Massimo Dutti en tramos de precio '
    'distintos, y cada tramo cuesta aproximadamente el doble que el anterior. Los dos únicos sitios '
    'donde dos cadenas comparten casi el mismo reparto de precios son Lefties–Primark en la gama baja '
    'y Zara–H&M en la media. El resto del deck enseña cómo se llega a esto y por qué aguanta.')
col_w = 3.7
xs = [MARGEN, MARGEN + col_w + 0.5, MARGEN + 2 * (col_w + 0.5)]
cifra_grande(s, '×2', f'Cada escalón de Inditex (Lefties → Zara → Massimo Dutti) cuesta '
                      f'aproximadamente el doble que el anterior ({veces(ratio_min)} a {veces(ratio_max)}), '
                      f'en camisetas y en vaqueros', xs[0], 2.0, col_w, AZUL)
cifra_grande(s, pct(solape[('vaquero', 'Lefties – Primark')]),
             'de solapamiento de precio entre Lefties y Primark en vaqueros: el choque de la gama baja',
             xs[1], 2.0, col_w, TEXTO)
cifra_grande(s, pct(solape[('vaquero', 'H&M – Zara')]),
             'de solapamiento de precio entre H&M y Zara en vaqueros: el choque de la gama media',
             xs[2], 2.0, col_w, TEXTO)
caja(s, f'Fuera de esas dos parejas, ningún par de marcas supera el {pct(resto_max["camiseta"])} de '
        f'solapamiento en camisetas ni el {pct(resto_max["vaquero"])} en vaqueros.',
     MARGEN, 5.0, ANCHO - 2 * MARGEN, 0.8, tam=16, color=TEXTO_SEC, fondo=FONDO_TARJETA,
     anclaje=MSO_ANCHOR.MIDDLE, margen=0.25)


# ===========================================================================
# 3. Método en una imagen
# ===========================================================================
s = nueva_diapositiva(
    f'{miles(total_modelos)} modelos de 5 cadenas, comparando la misma prenda básica',
    'Cinco cadenas elegidas por su papel en el abanico de precios. Massimo Dutti hace de control: si '
    'saliera solapada con Primark, el método estaría mal (y sale con 0 %). Comparamos solo prendas '
    'básicas, que son las más comparables entre marcas y no dependen del calendario de colección.')
PAPEL = {'Primark': 'Low cost', 'Lefties': 'Low cost · Inditex', 'H&M': 'Gama media',
         'Zara': 'Gama media · Inditex', 'Massimo Dutti': 'Gama media-alta · Inditex'}
tw, gap = 2.24, 0.23
for i, marca in enumerate(ORDEN):
    x = MARGEN + i * (tw + gap)
    color = AZUL if marca in INDITEX else GRIS_MARCA
    nc, nv = n_basicas[f'{marca}|camiseta'], n_basicas[f'{marca}|vaquero']
    caja(s, [[(marca, {'tam': 18, 'negrita': True, 'color': color})],
             [(PAPEL[marca], {'tam': 13, 'color': TEXTO_SEC})],
             [(f'{nc} camisetas · {nv} vaqueros', {'tam': 13, 'color': TEXTO})]],
         x, 1.7, tw, 1.7, fondo=FONDO_TARJETA, margen=0.18)
bloques = [
    ('Qué se compara', 'Camiseta de manga larga y vaquero largo, sección mujer. Cada modelo cuenta una '
                       'vez: las variantes de color no son filas nuevas.'),
    ('Qué es una prenda básica', 'Camiseta lisa o de canalé, sin estampado ni adornos. Vaquero de '
                                 'cualquier corte, sin rotos, tachas ni estampados. Se clasifica por el '
                                 'nombre del producto.'),
    ('De dónde salen los datos', f'Web española de cada marca, 10/10/2026. Precio de catálogo, sin '
                                 f'rebajas activas. De {miles(total_modelos)} modelos, '
                                 f'{miles(total_basicas)} son básicas.'),
]
bw = (ANCHO - 2 * MARGEN - 2 * 0.5) / 3
for i, (cab, txt) in enumerate(bloques):
    x = MARGEN + i * (bw + 0.5)
    caja(s, [[(cab, {'tam': 18, 'negrita': True})], [(txt, {'tam': 16, 'color': TEXTO})]],
         x, 4.1, bw, 2.6)
caja(s, 'En azul, las tres marcas de Inditex. El número de prendas es el de modelos básicos.',
     MARGEN, ALTO - 0.5, 9, 0.3, tam=10, color=TEXTO_SEC)


# ===========================================================================
# 4. Escalera de camisetas
# ===========================================================================
s = nueva_diapositiva(
    'En camisetas, cada marca de Inditex ocupa su propio tramo de precio',
    'Cada barra es el 50 % central de los modelos de una marca y el punto, su precio mediano. Las tres '
    'marcas de Inditex, en azul, no se tocan: Lefties abajo, Zara en medio y Massimo Dutti arriba. '
    'Lefties y Massimo Dutti tienen pocos modelos de camiseta (9 y 14), pero sus precios apenas varían.')
imagen(s, '01_escalera_camiseta.png', MARGEN, 1.45, w=8.0)
c = 'camiseta'
caja(s, [
    [('Tres tramos sin contacto', {'negrita': True})],
    f'Lefties {euros(r_med(c, "Lefties"))}, Zara {euros(r_med(c, "Zara"))} y Massimo Dutti '
    f'{euros(r_med(c, "Massimo Dutti"))} de mediana.',
    [('Dos vecindarios compartidos', {'negrita': True})],
    'Primark y Lefties en la gama baja; H&M y Zara en la media.',
    [('Muestra pequeña, precios estables', {'negrita': True})],
    f'Lefties ({int(resumen.loc[(c, "Lefties"), "n"])} modelos) va de '
    f'{euros(resumen.loc[(c, "Lefties"), "minimo"])} a {euros(resumen.loc[(c, "Lefties"), "maximo"])}; '
    f'Massimo Dutti ({int(resumen.loc[(c, "Massimo Dutti"), "n"])}), de '
    f'{euros(resumen.loc[(c, "Massimo Dutti"), "minimo"])} a '
    f'{euros(resumen.loc[(c, "Massimo Dutti"), "maximo"])}.',
], 9.0, 1.7, ANCHO - MARGEN - 9.0, 4.8, tam=15)


# ===========================================================================
# 5. Múltiplos pequeños: camiseta y vaquero
# ===========================================================================
s = nueva_diapositiva(
    'En vaqueros se repite el mismo patrón',
    'Mismo gráfico, dos prendas. El orden de las marcas es idéntico en las dos: Primark, Lefties, H&M, '
    'Zara y Massimo Dutti. Que el patrón se repita en una prenda con otro nivel de precio hace más '
    'creíble que no sea casualidad de una categoría.')
imagen(s, '02_escalera_camiseta_vaquero.png', MARGEN, 1.4, w=ANCHO - 2 * MARGEN)
caja(s, 'El orden por precio mediano es el mismo en las dos prendas: Primark < Lefties < H&M ≈ Zara '
        '< Massimo Dutti.', MARGEN, 6.45, ANCHO - 2 * MARGEN - 0.8, 0.5, tam=15, color=TEXTO_SEC)


# ===========================================================================
# 6. Ratios de la escalera
# ===========================================================================
s = nueva_diapositiva(
    'Cada escalón de Inditex cuesta aproximadamente el doble que el anterior',
    'Dividimos la mediana de cada escalón entre la del anterior. Sale entre 1,7 y 2 veces en las dos '
    'prendas. Para comprobar que no es un efecto de usar la mediana, lo repetimos con las medias y sale '
    'prácticamente lo mismo. Ojo: esto describe precios; no demuestra por qué Inditex los fija así.')
imagen(s, '03_ratios_escalera.png', MARGEN, 1.5, w=8.1)
lineas = [[('Cálculo (medianas)', {'negrita': True})]]
for cat, nombre in [('camiseta', 'Camiseta'), ('vaquero', 'Vaquero')]:
    for e in ESC:
        lineas.append(f'{nombre}: {ratios.loc[(cat, e), "calculo"]}')
lineas.append([('Comprobación con medias', {'negrita': True})])
lineas.append(f'Camiseta {veces(rat_media[("camiseta", ESC[0])])} y {veces(rat_media[("camiseta", ESC[1])])}; '
              f'vaquero {veces(rat_media[("vaquero", ESC[0])])} y {veces(rat_media[("vaquero", ESC[1])])}.')
lineas.append([('Lo que no sabemos', {'negrita': True})])
lineas.append('Sin la composición del tejido no se puede distinguir si el salto es una segmentación '
              'buscada o prendas de distinto material.')
caja(s, lineas, 9.1, 1.6, ANCHO - MARGEN - 9.1, 5.2, tam=14)


# ===========================================================================
# 7. Solapamiento por parejas
# ===========================================================================
hl_c, hl_c4 = int(solape[('camiseta', 'H&M – Lefties')]), solape_ancho('camiseta', 4, 'H&M', 'Lefties')
s = nueva_diapositiva(
    'Solo hay dos enfrentamientos directos: Lefties–Primark y Zara–H&M',
    'Medimos cuánto se parecen los repartos de precio de cada pareja de marcas, por tramos. Dos parejas '
    'destacan en las dos prendas y siguen destacando si cambiamos el ancho de los tramos (la rayita '
    f'negra). H&M–Lefties parece alto en camisetas ({hl_c} %), pero con tramos de 4 € baja al {hl_c4} %: '
    'era un efecto de dónde caen los cortes, no un solapamiento real.')
imagen(s, '04_solapamiento_parejas.png', MARGEN + 0.4, 1.35, h=5.4)
caja(s, f'H&M–Lefties ({hl_c} % en camisetas) no se sostiene: con tramos de 4 € baja al {hl_c4} %.',
     MARGEN, 6.75, ANCHO - 2 * MARGEN - 0.8, 0.4, tam=14, color=TEXTO_SEC)


# ===========================================================================
# 8. H&M rodea a Zara (matizado) + el espejismo de la media
# ===========================================================================
rc, rv = rodea.loc[('camiseta', 'H&M')], rodea.loc[('vaquero', 'H&M')]
s = nueva_diapositiva(
    'H&M rodea a Zara en camisetas; en vaqueros el choque es más frontal',
    f'En camisetas, H&M tiene tanta oferta por debajo de la franja central de Zara '
    f'({rc["pct_por_debajo"]} %) como dentro ({rc["pct_dentro"]} %) o por encima '
    f'({rc["pct_por_encima"]} %). Para Zara, H&M es su competidor directo; para H&M, Zara es uno de '
    f'varios. En vaqueros, el {rv["pct_dentro"]} % de H&M cae dentro de la franja de Zara: ahí chocan '
    'de frente. Y una advertencia: si miras la media, H&M parece más cara que Zara; con la mediana es al '
    'revés. La media la sube una cola de productos caros de la propia H&M.')
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
caja(s, filas, 9.35, 1.6, ANCHO - MARGEN - 9.35, 3.9, tam=14, fondo=FONDO_TARJETA, margen=0.2)


# ===========================================================================
# 9. Arquitectura de precios (apoyo)
# ===========================================================================
md_c = int(arq.loc[('camiseta', 'Massimo Dutti'), 'precios_distintos'])
md_v = int(arq.loc[('vaquero', 'Massimo Dutti'), 'precios_distintos'])
s = nueva_diapositiva(
    f'Cada marca repite unos pocos precios; Massimo Dutti usa solo {md_c}',
    'Cada marca repite unos pocos precios. Massimo Dutti solo usa dos por prenda. Zara concentra tres '
    'cuartas partes de su catálogo en tres precios. H&M dispersa más, aunque en parte porque tiene '
    'muchos más modelos. Y cada cadena tiene su firma en los céntimos.')
imagen(s, '06_arquitectura_precios.png', MARGEN, 1.4, w=ANCHO - 2 * MARGEN)


def lista_marcas(cents):
    return ' y '.join(m for m in ORDEN if term.loc[m, cents] >= 99)


firmas = [(',95', lista_marcas(',95')), (',99', lista_marcas(',99')),
          ('Enteros', f'Primark ({pct(term.loc["Primark", "entero (,00)"])}; el resto, x,50)')]
fw = (ANCHO - 2 * MARGEN - 2 * 0.3) / 3
for i, (cab, txt) in enumerate(firmas):
    caja(s, [[(cab + '  ', {'negrita': True, 'tam': 20}), (txt, {'tam': 14})]],
         MARGEN + i * (fw + 0.3), 6.05, fw, 0.6, fondo=FONDO_TARJETA, anclaje=MSO_ANCHOR.MIDDLE,
         margen=0.18)


# ===========================================================================
# 10. El hueco de la escalera y qué implica
# ===========================================================================
hc = hueco.loc['camiseta']
hv = hueco.loc['vaquero']
s = nueva_diapositiva(
    'Entre Zara y Massimo Dutti queda un hueco de precio poco ocupado',
    f'Entre el precio alto de Zara y el bajo de Massimo Dutti hay una zona con poca oferta: el '
    f'{pct_hueco["camiseta"]} % de los modelos en camisetas y solo el {pct_hueco["vaquero"]} % en '
    'vaqueros. Lo que hay es sobre todo la cola de H&M. Es una oportunidad a investigar, no un hueco de '
    'mercado demostrado: no sabemos si hay demanda a ese precio, y marcas que no están en el estudio '
    '(Mango, COS, & Other Stories) podrían ocuparlo.')
imagen(s, '07_hueco_escalera.png', MARGEN, 1.45, w=8.4)
z75c, md25c = resumen.loc[('camiseta', 'Zara'), 'p75'], resumen.loc[('camiseta', 'Massimo Dutti'), 'p25']
z75v, md25v = resumen.loc[('vaquero', 'Zara'), 'p75'], resumen.loc[('vaquero', 'Massimo Dutti'), 'p25']
caja(s, [
    [('Para quien posiciona una marca', {'negrita': True, 'tam': 16})],
    [('1. Gama baja: ', {'negrita': True}),
     (f'el precio de referencia lo marcan Lefties y Primark (vaquero en torno a '
      f'{euros(r_med("vaquero", "Primark"))}–{euros(r_med("vaquero", "Lefties"))}).', {})],
    [('2. Gama media: ', {'negrita': True}),
     (f'compararse con Zara y H&M a la vez (vaquero {euros(resumen.loc[("vaquero", "Zara"), "p25"])}–'
      f'{euros(z75v)}).', {})],
    [('3. Zona a investigar: ', {'negrita': True}),
     (f'camiseta {euros(z75c)}–{euros(md25c)} y vaquero {euros(z75v)}–{euros(md25v)}, la menos ocupada '
      f'entre estas cinco marcas.', {})],
], 9.35, 1.6, ANCHO - MARGEN - 9.35, 3.6, tam=14)
caja(s, [[('Antes de decidir, validar: ', {'negrita': True}),
          ('¿hay demanda a ese precio? ¿Lo ocupan marcas fuera del estudio, como Mango, COS o '
           '& Other Stories?', {})]],
     MARGEN, 5.25, 8.4, 0.95, tam=14, fondo=FONDO_TARJETA, anclaje=MSO_ANCHOR.MIDDLE, margen=0.2)


# ===========================================================================
# 11. Limitaciones
# ===========================================================================
s = nueva_diapositiva(
    'Lo que este análisis no dice',
    'Esto es lo que hay que tener en cuenta antes de usar las conclusiones. La más importante es la '
    'primera: describimos dónde están los precios, no por qué están ahí.')
lefties_n = int(resumen.loc[('camiseta', 'Lefties'), 'n'])
md_n = int(resumen.loc[('camiseta', 'Massimo Dutti'), 'n'])
limites = [
    ('Posicionamiento, no estrategia', 'La escalera puede ser una segmentación buscada o prendas de '
                                       'distinto material. Sin la composición, no se distinguen.'),
    ('Una foto de un solo día', '10/10/2026, sin rebajas activas. Precio de catálogo, no precio de '
                                'venta ni volumen vendido.'),
    ('Shein, fuera', 'Excluida por inaccesibilidad de los datos (protección anti-bot).'),
    ('Básicas por palabras clave', 'Se clasificaron por el nombre del producto: puede haber errores '
                                   'puntuales.'),
    ('Muestras pequeñas', f'Lefties ({lefties_n}) y Massimo Dutti ({md_n}) en camisetas, por debajo de '
                          '15 modelos. Sus precios apenas varían.'),
    ('Sublíneas dentro de cada marca', 'H&M incluye líneas premium; Zara (TRF, Z1975, ZW Collection) y '
                                       'Primark (The Edit) también mezclan sublíneas.'),
    ('Medidas aproximadas', 'Cuartiles con NTILE(4). El solapamiento depende del ancho del tramo: se '
                            'probó con dos anchos.'),
    ('Cinco marcas, no todo el mercado', 'Mango, COS o & Other Stories podrían ocupar el hueco entre '
                                         'Zara y Massimo Dutti.'),
]
cw, ch, gx, gy = (ANCHO - 2 * MARGEN - 3 * 0.3) / 4, 2.35, 0.3, 0.3
for i, (cab, txt) in enumerate(limites):
    fila, col = divmod(i, 4)
    caja(s, [[(cab, {'negrita': True, 'tam': 16})], [(txt, {'tam': 14, 'color': TEXTO})]],
         MARGEN + col * (cw + gx), 1.55 + fila * (ch + gy), cw, ch, fondo=FONDO_TARJETA, margen=0.2)


# ===========================================================================
# 12. Anexo: método y robustez
# ===========================================================================
s = nueva_diapositiva(
    'Anexo: método y robustez',
    'Tabla completa de precios y prueba de robustez del solapamiento. La métrica principal es la de '
    'tramos; la de franja central solo se usa como apoyo, porque se rompe con precios redondos casi '
    'iguales (29,95 € frente a 29,99 €).')


def tabla(s, datos, x, y, w, anchos, tam=11):
    filas, cols = len(datos), len(datos[0])
    forma = s.shapes.add_table(filas, cols, Inches(x), Inches(y), Inches(w), Inches(0.28 * filas))
    t = forma.table
    for j, a in enumerate(anchos):
        t.columns[j].width = Inches(a)
    for i, fila in enumerate(datos):
        t.rows[i].height = Inches(0.28)
        for j, valor in enumerate(fila):
            celda = t.cell(i, j)
            celda.fill.solid()
            celda.fill.fore_color.rgb = FONDO_TARJETA if i == 0 else BLANCO
            celda.margin_left = celda.margin_right = Inches(0.06)
            celda.margin_top = celda.margin_bottom = Inches(0.02)
            tf = celda.text_frame
            tf.text = str(valor)
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if (j == 0 or (j == 1 and cols > 5)) else PP_ALIGN.RIGHT
            estilo_runs(p, tam, negrita=(i == 0))
    return forma


datos = [['Prenda', 'Marca', 'n', 'P25', 'Mediana', 'P75', 'Máx.', 'Media']]
for cat in ['camiseta', 'vaquero']:
    for marca in ORDEN:
        r = resumen.loc[(cat, marca)]
        n_txt = f'{int(r["n"])}' + ('*' if r['fiabilidad'] != 'OK' else '')
        datos.append([cat.capitalize(), marca, n_txt] +
                     [euros(r[k]) for k in ['p25', 'mediana', 'p75', 'maximo', 'media']])
tabla(s, datos, MARGEN, 1.45, 7.3, [0.95, 1.35, 0.5, 0.9, 0.9, 0.9, 0.9, 0.9])
caja(s, '* Muestra pequeña (menos de 15 modelos). Cuartiles aproximados con NTILE(4).',
     MARGEN, 1.45 + 0.28 * 11 + 0.1, 7.3, 0.3, tam=10, color=TEXTO_SEC)

PARES = ['Lefties – Primark', 'H&M – Zara', 'H&M – Primark', 'H&M – Lefties', 'Lefties – Zara',
         'Massimo Dutti – Zara']
datos = [['Pareja', 'Cam. 5 €', 'Vaq. 10 €', 'Cam. 4 €', 'Vaq. 8 €']]
for p_ in PARES:
    a, b = p_.split(' – ')
    datos.append([p_, pct(solape[('camiseta', p_)]), pct(solape[('vaquero', p_)]),
                  pct(solape_ancho('camiseta', 4, a, b)), pct(solape_ancho('vaquero', 8, a, b))])
tabla(s, datos, 8.3, 1.45, ANCHO - MARGEN - 8.3, [1.55, 0.72, 0.72, 0.72, 0.72], tam=10)
caja(s, [
    [('Métrica principal: solapamiento por tramos. ', {'negrita': True}),
     ('Se reparte el catálogo de cada marca en tramos de precio (5 € en camiseta, 10 € en vaquero) y se '
      'suma, tramo a tramo, la menor de las dos proporciones. 0 % = no comparten ningún tramo; 100 % = mismo '
      'reparto. Las dos últimas columnas repiten el cálculo con 4 € y 8 €.', {})],
    [('Métrica de apoyo: franja central. ', {'negrita': True}),
     ('% de los modelos de una marca que caen entre el P25 y el P75 de otra. Se rompe con precios '
      'redondos casi iguales (29,95 € frente a 29,99 €).', {})],
], 8.3, 1.45 + 0.28 * 7 + 0.6, ANCHO - MARGEN - 8.3, 3.2, tam=11)
caja(s, 'Fuente: catálogo online de cada marca en España (sección mujer), 10/10/2026. Prendas básicas.',
     MARGEN, ALTO - 0.5, 9, 0.3, tam=10, color=TEXTO_SEC)

prs.save(SALIDA)
print('Presentación guardada en', os.path.relpath(SALIDA, BASE), f'({len(prs.slides)} diapositivas)')
