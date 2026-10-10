"""
Gráficos de la ampliación a 16 marcas (criterios de la sección 8 de CLAUDE.md).

Mismo estilo que scripts/graficos.py (versión de 5 marcas), con dos cambios:
  - Dos colores de acento con significado fijo en todo el deck:
      azul    = Inditex (Lefties, Zara, Massimo Dutti)
      naranja = Tendam  (Springfield, Cortefiel, Pedro del Hierro)
    El resto de marcas, en gris. Validado con el comprobador de paleta: azul y
    naranja se distinguen también con daltonismo (ΔE 21 en protanopía).
  - El eje de precio va en ESCALA LOGARÍTMICA en las escaleras: los precios van de
    4 € a 135 € y en escala normal la zona de 5–40 €, donde está la competencia, se
    aplastaría. En escala logarítmica cada línea de la cuadrícula duplica el precio,
    así que un escalón "×2" mide siempre lo mismo. Se avisa en cada gráfico.

Decisiones de Javi aplicadas (10/10/2026):
  - Precio de catálogo (sin rebaja) como criterio principal.
  - n ≥ 15 normal; 5–14 "muestra pequeña" (con trama); n < 5 fuera de las métricas:
    se dibujan sus modelos como puntos sueltos, sin franja ni mediana destacada.
  - Women'secret fuera del análisis.

Fuente: data/moda.db (vistas) y output/tablas/ampliacion/ (scripts/analisis_ampliacion.py).
Salida: PNG a 300 ppp en output/graficos/16_marcas/.

Uso:  python scripts/construir_bd.py && python scripts/analisis_ampliacion.py && python scripts/graficos_ampliacion.py
"""
import os
import sqlite3

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FixedLocator, NullLocator

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, 'data', 'moda.db')
TABLAS = os.path.join(BASE, 'output', 'tablas', 'ampliacion')
SALIDA = os.path.join(BASE, 'output', 'graficos', '16_marcas')
os.makedirs(SALIDA, exist_ok=True)

# ---------------------------------------------------------------------------
# Estilo común
# ---------------------------------------------------------------------------
AZUL, AZUL_CLARO = '#2A64A8', '#A9C1E2'          # Inditex
NARANJA, NARANJA_CLARO = '#C8571B', '#EFC2A6'    # Tendam
GRIS, GRIS_CLARO = '#7A7A7A', '#D3D3D3'          # resto
TEXTO, TEXTO_SEC = '#333333', '#6B6B6B'
FONDO_HUECO = '#F3F3F3'
DESTACADO = '#333333'

INDITEX = {'Lefties', 'Zara', 'Massimo Dutti'}
TENDAM = {'Springfield', 'Cortefiel', 'Pedro del Hierro'}
PRENDAS = {'camiseta': 'Camiseta de manga larga', 'vaquero': 'Vaquero'}

FUENTE = ('Fuente: catálogo online de cada marca en España (sección mujer), 10/10/2026. Precio de catálogo '
          '(sin rebaja). Solo prendas básicas; cada modelo cuenta una vez.')

plt.rcParams.update({
    'font.family': 'Inter', 'font.size': 10, 'text.color': TEXTO,
    'axes.labelcolor': TEXTO_SEC, 'xtick.color': TEXTO_SEC, 'ytick.color': TEXTO_SEC,
    'axes.edgecolor': GRIS_CLARO, 'figure.facecolor': 'white', 'axes.facecolor': 'white',
    'savefig.dpi': 300, 'hatch.color': 'white', 'hatch.linewidth': 1.2,
})


def euros(x, decimales=2):
    return f'{x:.{decimales}f}'.replace('.', ',') + ' €'


def color_marca(marca, claro=False):
    if marca in INDITEX:
        return AZUL_CLARO if claro else AZUL
    if marca in TENDAM:
        return NARANJA_CLARO if claro else NARANJA
    return GRIS_CLARO if claro else GRIS


def limpiar_ejes(ax, cuadricula='x'):
    for lado in ['top', 'right', 'left', 'bottom']:
        ax.spines[lado].set_visible(False)
    ax.tick_params(length=0)
    if cuadricula:
        ax.grid(axis=cuadricula, color='#EDEDED', linewidth=0.8)
        ax.set_axisbelow(True)


def eje_log(ax, ticks, eje='x'):
    """Escala logarítmica con etiquetas en euros (sin notación científica)."""
    setter = ax.set_xscale if eje == 'x' else ax.set_yscale
    setter('log')
    axis = ax.xaxis if eje == 'x' else ax.yaxis
    axis.set_major_locator(FixedLocator(ticks))
    axis.set_minor_locator(NullLocator())
    axis.set_major_formatter(plt.FuncFormatter(lambda v, _: euros(v, 0)))


def nota_pie(fig, texto_extra='', fuente=FUENTE):
    fig.text(0.01, 0.01, fuente + ('\n' + texto_extra if texto_extra else ''), ha='left', va='bottom',
             fontsize=7.5, color=TEXTO_SEC)


def guardar(fig, nombre):
    ruta = os.path.join(SALIDA, nombre)
    fig.savefig(ruta, bbox_inches='tight', pad_inches=0.15)
    plt.close(fig)
    print('  ', os.path.relpath(ruta, BASE))


# ---------------------------------------------------------------------------
# Datos (todo sale de las vistas o de las tablas que las leen)
# ---------------------------------------------------------------------------
con = sqlite3.connect(DB)
resumen = pd.read_sql('SELECT * FROM v_resumen_precios', con).set_index(['categoria', 'marca'])
basicas = pd.read_sql("""SELECT c.marca, c.categoria, c.precio_actual AS precio, c.precio_venta
                         FROM catalogo AS c JOIN marcas AS m USING (marca)
                         WHERE c.motivo = '7_basica' AND c.precio_actual IS NOT NULL
                           AND m.en_analisis = 1""", con)
marcas = pd.read_sql('SELECT * FROM marcas WHERE en_analisis = 1', con)
con.close()
solape = pd.read_csv(os.path.join(TABLAS, 'solapamiento_16_marcas.csv'))
hueco_total = pd.read_csv(os.path.join(TABLAS, 'hueco_total.csv')).set_index('categoria')
rebajas = pd.read_csv(os.path.join(TABLAS, 'rebajas_por_marca.csv'))
ratios = pd.read_csv(os.path.join(TABLAS, 'ratios_escaleras.csv'))


def estado(cat, marca):
    """'ok', 'pequena' (5–14), 'fuera' (n < 5) o 'sin' (ninguna básica)."""
    if (cat, marca) not in resumen.index:
        return 'sin'
    r = resumen.loc[(cat, marca)]
    if not r['en_metricas']:
        return 'fuera'
    return 'pequena' if r['fiabilidad'] != 'OK' else 'ok'


def mediana_orden(marca):
    """Orden de las filas: mediana del vaquero (si no hay, la de la camiseta)."""
    for cat in ['vaquero', 'camiseta']:
        if (cat, marca) in resumen.index:
            return resumen.loc[(cat, marca), 'mediana']
    return 1e9


# Mismo orden de filas en los dos paneles (múltiplos pequeños: misma estructura).
ORDEN = sorted(marcas['marca'], key=mediana_orden)
LIM = (3.2, 260)
TICKS = [5, 10, 20, 40, 80, 160]
AVISO_LOG = ('Eje en escala logarítmica: cada línea de la cuadrícula duplica el precio '
             '(un salto ×2 mide siempre lo mismo).')

print('Gráficos (16 marcas):')


# ---------------------------------------------------------------------------
# 1. La escalera completa (múltiplos pequeños, escala log)
# ---------------------------------------------------------------------------
def dibujar_escalera(ax, cat, nombres=True, hueco=False):
    for i, marca in enumerate(ORDEN):
        e = estado(cat, marca)
        col, col_claro = color_marca(marca), color_marca(marca, claro=True)
        if e == 'sin':
            ax.text(LIM[0] * 1.1, i, 'sin básicas en esta prenda', va='center', fontsize=8,
                    color=TEXTO_SEC, style='italic')
            continue
        r = resumen.loc[(cat, marca)]
        if e == 'fuera':
            # n < 5: cada modelo como punto hueco, sin franja ni mediana.
            precios = basicas.query('categoria == @cat and marca == @marca')['precio']
            ax.scatter(precios, [i] * len(precios), s=34, facecolor='white', edgecolor=col,
                       linewidth=1.3, zorder=3)
            ax.annotate(f'n = {int(r["n"])} · sin métrica', (precios.max(), i), xytext=(8, 0),
                        textcoords='offset points', va='center', fontsize=7.5, color=TEXTO_SEC,
                        style='italic')
            continue
        pequena = e == 'pequena'
        # Barra flotante P25–P75. Si P25 = P75 (casi todo a un precio), se le da una
        # anchura mínima visible centrada en ese precio.
        p25, p75 = r['p25'], r['p75']
        if p75 / p25 < 1.08:
            centro = (p25 * p75) ** 0.5
            p25, p75 = centro / 1.04, centro * 1.04
        ax.barh(i, p75 - p25, left=p25, height=0.56, color=col_claro, edgecolor='white',
                hatch='////' if pequena else None, linewidth=0, zorder=2)
        ax.scatter(r['mediana'], i, s=62, color=col, edgecolor='white', linewidth=1.5, zorder=3)
        x_texto = max(r['p75'], r['mediana'])
        ax.annotate(euros(r['mediana']), (x_texto, i), xytext=(8, 0.5), textcoords='offset points',
                    va='bottom', ha='left', fontsize=9.5, fontweight='bold', color=col)
        ax.annotate(f'n = {int(r["n"])}' + (' · muestra pequeña' if pequena else ''), (x_texto, i),
                    xytext=(8, -0.5), textcoords='offset points', va='top', ha='left', fontsize=7,
                    color=TEXTO_SEC, style='italic' if pequena else 'normal')
    ax.set_yticks(range(len(ORDEN)))
    ax.set_yticklabels(ORDEN, fontsize=10, fontweight='bold')
    for t, marca in zip(ax.get_yticklabels(), ORDEN):
        t.set_color(color_marca(marca))
    ax.tick_params(axis='y', labelleft=nombres)
    ax.set_ylim(-0.6, len(ORDEN) - 0.4)
    eje_log(ax, TICKS)
    ax.set_xlim(*LIM)
    limpiar_ejes(ax)
    if hueco:
        lo, hi = resumen.loc[(cat, 'Zara'), 'p75'], resumen.loc[(cat, 'Massimo Dutti'), 'p25']
        ax.axvspan(lo, hi, color=FONDO_HUECO, zorder=0)
        pct = int(hueco_total.loc[cat, 'pct'])
        # Rótulo como subtítulo del panel: dentro del gráfico pisaba los datos.
        ax.text(0, 1.012, f'En gris, el hueco ({euros(lo)} – {euros(hi)}): {pct} % de los modelos',
                transform=ax.transAxes, ha='left', va='bottom', fontsize=8.5, color=TEXTO_SEC)


def titulo_panel(ax, texto, pad=10):
    ax.set_title(texto, loc='left', fontsize=12, fontweight='bold', color=TEXTO, pad=pad)


LEYENDA = ('Barra: 50 % central de los modelos (P25–P75). Punto: mediana. Azul: Inditex. Naranja: Tendam. '
           'Gris: resto. Con trama: muestra pequeña (5–14 modelos).\nPuntos huecos: marcas con menos de 5 '
           'modelos básicos, cada punto es un modelo (no entran en las métricas). Women\'secret, fuera del '
           'análisis (lencería y homewear). ' + AVISO_LOG)

for nombre, hueco in [('01_escalera_16_marcas.png', False), ('06_hueco_16_marcas.png', True)]:
    fig, axes = plt.subplots(1, 2, figsize=(13, 7.2))
    for ax, cat in zip(axes, PRENDAS):
        dibujar_escalera(ax, cat, nombres=(cat == 'camiseta'), hueco=hueco)
        titulo_panel(ax, PRENDAS[cat], pad=24 if hueco else 10)
    fig.subplots_adjust(wspace=0.06, bottom=0.14, left=0.12)
    extra = LEYENDA
    if hueco:
        extra = ('Hueco: por encima del P75 de Zara y por debajo del P25 de Massimo Dutti, con precios '
                 'redondeados al euro. Porcentaje sobre los modelos de las marcas que entran en las métricas.\n'
                 + LEYENDA)
    nota_pie(fig, extra)
    guardar(fig, nombre)


# ---------------------------------------------------------------------------
# 2. Dos escaleras: Inditex y Tendam (ratios entre escalones)
# ---------------------------------------------------------------------------
# Un eje de precio (log) por prenda y dos filas: Inditex y Tendam. Así se ve a la vez
# el multiplicador de cada escalón y que la escalera de Tendam empieza un peldaño
# más arriba (Springfield ≈ Zara; Cortefiel ≈ Massimo Dutti).
ESCALERAS = [('Inditex', ['Lefties', 'Zara', 'Massimo Dutti'], AZUL),
             ('Tendam', ['Springfield', 'Cortefiel', 'Pedro del Hierro'], NARANJA)]
fig, axes = plt.subplots(2, 1, figsize=(12, 6.4), sharex=True, gridspec_kw={'hspace': 0.45})
for ax, cat in zip(axes, PRENDAS):
    for fila, (grupo, escalera, col) in enumerate(ESCALERAS):
        y = 1.2 - 1.3 * fila
        puntos = []
        for marca in escalera:
            e = estado(cat, marca)
            if e in ('ok', 'pequena'):
                m = resumen.loc[(cat, marca), 'mediana']
                puntos.append((marca, m))
                ax.scatter(m, y, s=90, color=col, edgecolor='white', linewidth=1.5, zorder=3,
                           hatch=None)
                etiqueta = f'{marca}\n{euros(m)}' + ('*' if e == 'pequena' else '')
                ax.annotate(etiqueta, (m, y), xytext=(0, -11), textcoords='offset points', ha='center',
                            va='top', fontsize=8.5, color=col, linespacing=1.15)
            elif e == 'fuera':
                n = int(resumen.loc[(cat, marca), 'n'])
                m = resumen.loc[(cat, marca), 'mediana']
                ax.scatter(m, y, s=70, facecolor='white', edgecolor=col, linewidth=1.3, zorder=3)
                ax.annotate(f'{marca}\nn = {n}, sin métrica', (m, y), xytext=(0, -11),
                            textcoords='offset points', ha='center', va='top', fontsize=8,
                            color=TEXTO_SEC, style='italic', linespacing=1.15)
        # Flechas y multiplicadores entre escalones consecutivos con métrica.
        for (m1, v1), (m2, v2) in zip(puntos, puntos[1:]):
            ax.annotate('', xy=(v2 / 1.07, y), xytext=(v1 * 1.07, y),
                        arrowprops=dict(arrowstyle='->', color=col, lw=1.2))
            ax.text((v1 * v2) ** 0.5, y + 0.13, f'×{v2 / v1:.1f}'.replace('.', ','), ha='center',
                    va='bottom', fontsize=12, fontweight='bold', color=TEXTO)
        ax.text(LIM[0] * 1.02, y, grupo, ha='left', va='center', fontsize=11, fontweight='bold', color=col)
    ax.set_ylim(-0.75, 1.75)
    ax.set_yticks([])
    eje_log(ax, TICKS)
    ax.set_xlim(*LIM)
    limpiar_ejes(ax)
    titulo_panel(ax, PRENDAS[cat])
fig.subplots_adjust(bottom=0.16)
nota_pie(fig, 'Punto: precio mediano de cada marca. Multiplicador = mediana del escalón superior / mediana '
              'del inferior. * Muestra pequeña (5–14 modelos). Punto hueco: menos de 5 modelos,\nno se calcula '
              'el escalón. ' + AVISO_LOG)
guardar(fig, '02_escaleras_inditex_tendam.png')


# ---------------------------------------------------------------------------
# 3. Solapamiento por parejas (pares con ≥ 30 % en la métrica principal)
# ---------------------------------------------------------------------------
# Parejas destacadas: los choques frontales que defiende el análisis. Se eligen a mano,
# no por un umbral fijo (decisión 8 de CLAUDE.md: con un corte en el 50 %, H&M–Zara en
# camisetas, con un 47 %, habría quedado fuera). Frágil: cae 20 puntos o más con el
# otro ancho de tramo o con el precio rebajado; se avisa junto a la barra.
DESTACADAS = {('Lefties', 'Primark'), ('H&M', 'Zara'), ('Mango', 'Zara'), ('H&M', 'Mango'),
              ('Cortefiel', 'Massimo Dutti')}
ANCHO = {'camiseta': (5, 4), 'vaquero': (10, 8)}
fig, axes = plt.subplots(1, 2, figsize=(13, 6.2))
for ax, cat in zip(axes, PRENDAS):
    d = solape[(solape['categoria'] == cat) & (solape['solape_pct'] >= 30)].sort_values('solape_pct')
    for i, r in enumerate(d.itertuples()):
        destacada = (r.marca_a, r.marca_b) in DESTACADAS
        ax.barh(i, r.solape_pct, height=0.62, color=DESTACADO if destacada else GRIS_CLARO, zorder=2)
        ax.plot([r.solape_pct_robustez] * 2, [i - 0.4, i + 0.4], color=TEXTO, lw=1.3, zorder=3)
        avisos = []
        if r.solape_pct - r.solape_pct_robustez >= 20:
            avisos.append(f'tramos de {ANCHO[cat][1]} €: {r.solape_pct_robustez} %')
        if r.solape_pct - r.solape_pct_rebajado >= 20:
            avisos.append(f'con rebajas: {r.solape_pct_rebajado} %')
        texto = f'{r.solape_pct} %' + ('   ' + ' · '.join(avisos) if avisos else '')
        ax.text(max(r.solape_pct, r.solape_pct_robustez) + 1.5, i, texto, va='center', fontsize=8.5,
                fontweight='bold' if destacada else 'normal', color=TEXTO if destacada else TEXTO_SEC)
    ax.set_yticks(range(len(d)))
    ax.set_yticklabels(d['pareja'], fontsize=9.5)
    ax.tick_params(axis='y', pad=6)
    for t, r in zip(ax.get_yticklabels(), d.itertuples()):
        if (r.marca_a, r.marca_b) in DESTACADAS:
            t.set_color(TEXTO)
            t.set_fontweight('bold')
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(['0 %', '25 %', '50 %', '75 %', '100 %'])
    limpiar_ejes(ax)
    titulo_panel(ax, f'{PRENDAS[cat]} · tramos de {ANCHO[cat][0]} €')
fig.subplots_adjust(wspace=0.9, bottom=0.17, left=0.13, right=0.9)
nota_pie(fig, 'Solapamiento: parte del catálogo que dos marcas reparten igual por tramos de precio (0 % = no '
              'comparten ningún tramo; 100 % = mismo reparto). Solo parejas con 30 % o más.\nLínea vertical: '
              'mismo cálculo con tramos de 4 € / 8 € (robustez). Se avisa cuando la cifra cae 20 puntos o más con '
              'esos tramos o con el precio rebajado. En negro: los choques frontales.')
guardar(fig, '03_solapamiento_16_marcas.png')


# ---------------------------------------------------------------------------
# 4 y 5. Repartos de precio: la gama media a tres y Cortefiel frente a Massimo Dutti
# ---------------------------------------------------------------------------
def reparto(nombre, filas, franja_de, lims, ticks, nota):
    """Para cada precio, % de los modelos de la marca con ese precio. Fondo: franja P25–P75 de `franja_de`.

    `filas`: lista de (marca, columna de precio, rótulo extra). La columna es 'precio'
    (catálogo) o 'precio_venta' (lo que marcaba la web ese día, con rebaja si la había).
    """
    fig, axes = plt.subplots(len(filas), 2, figsize=(12, 1.55 * len(filas) + 1.4), sharex='col',
                             gridspec_kw={'hspace': 0.18, 'wspace': 0.14})
    ancho_barra = {'camiseta': 0.55, 'vaquero': 1.1}
    for col, cat in enumerate(PRENDAS):
        cuotas = [basicas.query('categoria == @cat and marca == @m')[c].value_counts(normalize=True).mul(100)
                  for m, c, _ in filas]
        tope = max(c.max() for c in cuotas)       # misma escala vertical en todas las filas
        f = resumen.loc[(cat, franja_de)]
        for fila, ((marca, columna, rotulo), cuota) in enumerate(zip(filas, cuotas)):
            ax = axes[fila, col]
            color = DESTACADO if marca == 'Mango' else color_marca(marca, claro=(columna == 'precio_venta'))
            ax.axvspan(f['p25'] - ancho_barra[cat] / 2, f['p75'] + ancho_barra[cat] / 2, color=FONDO_HUECO, zorder=0)
            ax.bar(cuota.index, cuota.values, width=ancho_barra[cat], color=color, zorder=2)
            ax.set_ylim(0, tope * 1.3)
            ax.set_yticks([])
            pequena = estado(cat, marca) == 'pequena'
            ax.text(-0.01, 0.4, f'{marca}{rotulo}\nn = {int(resumen.loc[(cat, marca), "n"])}'
                    + (' · muestra pequeña' if pequena else ''), transform=ax.transAxes, ha='right',
                    va='center', fontsize=9.5, fontweight='bold',
                    color=DESTACADO if marca == 'Mango' else color_marca(marca))
            for lado in ['top', 'right', 'left']:
                ax.spines[lado].set_visible(False)
            ax.spines['bottom'].set_color(GRIS_CLARO)
            ax.tick_params(length=0)
        axes[0, col].text((f['p25'] + f['p75']) / 2, tope * 1.28,
                          f'Franja central de {franja_de}\n{euros(f["p25"])} – {euros(f["p75"])}', ha='center',
                          va='top', fontsize=8, color=TEXTO_SEC)
        axes[0, col].set_title(PRENDAS[cat], loc='left', fontsize=12, fontweight='bold', color=TEXTO, pad=10)
        axes[-1, col].set_xlim(*lims[cat])
        axes[-1, col].set_xticks(ticks[cat])
        axes[-1, col].set_xticklabels([euros(t, 0) for t in ticks[cat]])
    fig.subplots_adjust(bottom=0.2, left=0.13)
    nota_pie(fig, nota)
    guardar(fig, nombre)


reparto('04_gama_media_zara_hm_mango.png', [('Zara', 'precio', ''), ('H&M', 'precio', ''), ('Mango', 'precio', '')],
        'Zara', {'camiseta': (0, 52), 'vaquero': (15, 92)},
        {'camiseta': range(0, 51, 10), 'vaquero': range(20, 91, 10)},
        'Altura de cada barra: % de los modelos de la marca con ese precio (misma escala en las tres filas). '
        'Fondo gris: 50 % central de los modelos de Zara (P25–P75).\nEl eje del vaquero empieza en 15 €.')

reparto('05_cortefiel_massimo_dutti.png',
        [('Massimo Dutti', 'precio', ''), ('Cortefiel', 'precio', '\nprecio de catálogo'),
         ('Cortefiel', 'precio_venta', '\nprecio rebajado')],
        'Massimo Dutti', {'camiseta': (10, 45), 'vaquero': (15, 75)},
        {'camiseta': range(10, 46, 5), 'vaquero': range(20, 71, 10)},
        'Altura de cada barra: % de los modelos de la marca con ese precio (misma escala en las tres filas). Fondo '
        'gris: 50 % central de Massimo Dutti (P25–P75).\nÚltima fila: Cortefiel con el precio que marcaba la web '
        'ese día (con rebaja si la había; el 41 % de su catálogo estaba rebajado). Los ejes empiezan en 10 € y 15 €.')


# ---------------------------------------------------------------------------
# 7. Rebajas por marca (por qué Tendam se interpreta con cautela)
# ---------------------------------------------------------------------------
r = rebajas[rebajas['marca'].isin(marcas['marca'])].sort_values('pct_rebajado')
fig, ax = plt.subplots(figsize=(8, 5.2))
for i, f in enumerate(r.itertuples()):
    col = color_marca(f.marca)
    ax.barh(i, f.pct_rebajado, height=0.6, color=col, zorder=2)
    txt = f'{int(f.pct_rebajado)} %'
    if f.pct_rebajado > 0:
        txt += f'  ·  descuento medio {int(f.dto_medio_pct)} %'
    ax.text(f.pct_rebajado + 1.5, i, txt, va='center', fontsize=9, color=TEXTO if f.pct_rebajado >= 40 else TEXTO_SEC,
            fontweight='bold' if f.pct_rebajado >= 40 else 'normal')
ax.set_yticks(range(len(r)))
ax.set_yticklabels(r['marca'], fontsize=10, fontweight='bold')
for t, m in zip(ax.get_yticklabels(), r['marca']):
    t.set_color(color_marca(m))
ax.set_xlim(0, 100)
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xticklabels(['0 %', '25 %', '50 %', '75 %', '100 %'])
limpiar_ejes(ax)
titulo_panel(ax, '% del catálogo recogido con precio rebajado')
fig.subplots_adjust(bottom=0.16, left=0.22)
nota_pie(fig, 'Camisetas de manga larga y vaqueros, todas las fichas recogidas (antes de clasificar). '
              'Zara: 1 producto de 354 (0,3 %).',
         fuente='Fuente: catálogo online de cada marca en España (sección mujer), 10/10/2026. Women\'secret '
                '(100 % rebajado) queda fuera del análisis.')
guardar(fig, '07_rebajas_por_marca.png')
