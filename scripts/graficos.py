"""
Paso 2 · Gráficos del proyecto (criterios de la sección 8 de CLAUDE.md).

Reglas que se aplican en todos:
  - Fondo blanco, tipografía Inter, texto en gris oscuro (#333).
  - Inditex (Lefties, Zara, Massimo Dutti) en un único azul; el resto en gris.
    El azul significa "Inditex" en todos los gráficos del deck.
  - Etiquetas directas en lugar de leyenda, sin bordes ni cuadrícula fuerte.
  - Números en formato español (7,99 €, 47 %).
  - Muestra pequeña (n < 15) marcada con trama y nota (en los textos para el lector
    se dice "muestra pequeña", no "baja fiabilidad").
  - Nota al pie con fuente, fecha y tamaño de muestra.

Fuente: data/moda_5marcas.db (vistas v_resumen_precios y v_solape_pares) y las tablas
de output/tablas/ que genera scripts/analisis_complementario.py.
Salida: PNG a 300 ppp en output/graficos/.

Uso:  python scripts/graficos.py
"""
import itertools
import os
import sqlite3

import matplotlib
matplotlib.use('Agg')  # dibuja en fichero, sin abrir ventanas
import matplotlib.pyplot as plt
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, 'data', 'moda_5marcas.db')  # versión de 5 marcas (antes de la ampliación)
TABLAS = os.path.join(BASE, 'output', 'tablas')
SALIDA = os.path.join(BASE, 'output', 'graficos')
os.makedirs(SALIDA, exist_ok=True)

# ---------------------------------------------------------------------------
# Estilo común
# ---------------------------------------------------------------------------
AZUL = '#2A64A8'          # Inditex
AZUL_CLARO = '#A9C1E2'    # franja P25–P75 de Inditex
GRIS = '#7A7A7A'          # resto de marcas (marcas y etiquetas)
GRIS_CLARO = '#D3D3D3'    # franja P25–P75 del resto
TEXTO = '#333333'
TEXTO_SEC = '#6B6B6B'
FONDO_HUECO = '#F3F3F3'
DESTACADO = '#333333'     # pareja destacada en el gráfico de solapamiento

INDITEX = {'Lefties', 'Zara', 'Massimo Dutti'}
# Orden por mediana (es el mismo en las dos prendas): se usa en todo el deck.
ORDEN = ['Primark', 'Lefties', 'H&M', 'Zara', 'Massimo Dutti']
PRENDAS = {'camiseta': 'Camiseta de manga larga', 'vaquero': 'Vaquero'}

FUENTE = ('Fuente: catálogo online de cada marca en España (sección mujer), 10/10/2026. '
          'Solo prendas básicas; cada modelo cuenta una vez, sin variantes de color.')

plt.rcParams.update({
    'font.family': 'Inter',
    'font.size': 10,
    'text.color': TEXTO,
    'axes.labelcolor': TEXTO_SEC,
    'xtick.color': TEXTO_SEC,
    'ytick.color': TEXTO_SEC,
    'axes.edgecolor': GRIS_CLARO,
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'savefig.dpi': 300,
})


def euros(x, decimales=2):
    """7.99 -> '7,99 €'; con decimales=0, 10 -> '10 €'."""
    return f'{x:.{decimales}f}'.replace('.', ',') + ' €'


def color_marca(marca, claro=False):
    if marca in INDITEX:
        return AZUL_CLARO if claro else AZUL
    return GRIS_CLARO if claro else GRIS


def limpiar_ejes(ax, eje_x=True):
    """Quita la 'chatarra gráfica': bordes, marcas de los ejes y cuadrícula fuerte."""
    for lado in ['top', 'right', 'left', 'bottom']:
        ax.spines[lado].set_visible(False)
    ax.tick_params(length=0)
    if eje_x:
        ax.grid(axis='x', color='#EDEDED', linewidth=0.8)
        ax.set_axisbelow(True)  # la cuadrícula queda detrás de los datos
    else:
        ax.set_xticks([])


def nota_pie(fig, texto_extra=''):
    texto = FUENTE + ('\n' + texto_extra if texto_extra else '')
    fig.text(0.01, 0.01, texto, ha='left', va='bottom', fontsize=7.5, color=TEXTO_SEC)


def guardar(fig, nombre):
    ruta = os.path.join(SALIDA, nombre)
    fig.savefig(ruta, bbox_inches='tight', pad_inches=0.15)
    plt.close(fig)
    print('  ', os.path.relpath(ruta, BASE))


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------
con = sqlite3.connect(DB)
resumen = pd.read_sql('SELECT * FROM v_resumen_precios', con).set_index(['categoria', 'marca'])
pares = pd.read_sql('SELECT categoria, marca_a, marca_b, solape_pct FROM v_solape_pares', con)
basicas = pd.read_sql("""SELECT marca, categoria, precio_actual AS precio FROM catalogo
                         WHERE motivo = '7_basica' AND precio_actual IS NOT NULL""", con)
con.close()
arquitectura = pd.read_csv(os.path.join(TABLAS, 'arquitectura_precios.csv')).set_index(['categoria', 'marca'])
hueco = pd.read_csv(os.path.join(TABLAS, 'hueco_escalera.csv'))

# Escala de cada panel: cada prenda tiene la suya (los vaqueros cuestan ~2 veces más).
LIMITE_X = {'camiseta': 50, 'vaquero': 80}


# ---------------------------------------------------------------------------
# 1. La escalera (barra flotante P25–P75 + mediana)
# ---------------------------------------------------------------------------
def dibujar_escalera(ax, cat, sombrear_hueco=False, nombres=True):
    for i, marca in enumerate(ORDEN):
        r = resumen.loc[(cat, marca)]
        baja = r['fiabilidad'] != 'OK'
        # Barra flotante: empieza en el P25 y mide P75 − P25.
        ax.barh(i, r['p75'] - r['p25'], left=r['p25'], height=0.5,
                color=color_marca(marca, claro=True), edgecolor='white',
                hatch='////' if baja else None, linewidth=0, zorder=2)
        # Mediana: punto en el color fuerte con un aro blanco para separarlo de la barra.
        ax.scatter(r['mediana'], i, s=70, color=color_marca(marca), edgecolor='white',
                   linewidth=1.5, zorder=3)
        # Etiqueta directa de la mediana a la derecha de la franja. annotate() con
        # 'offset points' la separa una distancia fija en puntos, sea cual sea la escala,
        # para que no pise el punto cuando la mediana coincide con el P75.
        x_texto = max(r['p75'], r['mediana'])
        ax.annotate(euros(r['mediana']), (x_texto, i), xytext=(9, 1), textcoords='offset points',
                    va='bottom', ha='left', fontsize=10, fontweight='bold', color=color_marca(marca))
        # Debajo, en pequeño, la n (y el aviso de muestra pequeña si toca).
        nota = f'n = {int(r["n"])}' + (' · muestra pequeña' if baja else '')
        ax.annotate(nota, (x_texto, i), xytext=(9, -1), textcoords='offset points', va='top',
                    ha='left', fontsize=7.5, color=TEXTO_SEC, style='italic' if baja else 'normal')
    # Nombre de la marca en su color (solo en el primer panel de los múltiplos pequeños).
    ax.set_yticks(range(len(ORDEN)))
    ax.set_yticklabels(ORDEN if nombres else [], fontsize=10.5, fontweight='bold')
    for t, marca in zip(ax.get_yticklabels(), ORDEN):
        t.set_color(color_marca(marca))
    ax.set_xlim(0, LIMITE_X[cat])
    ax.set_ylim(-0.6, len(ORDEN) - 0.4)
    paso = 10
    ax.set_xticks(range(0, LIMITE_X[cat] + 1, paso))
    ax.set_xticklabels([euros(x, 0) for x in range(0, LIMITE_X[cat] + 1, paso)])
    limpiar_ejes(ax)
    if sombrear_hueco:
        lo = resumen.loc[(cat, 'Zara'), 'p75']
        hi = resumen.loc[(cat, 'Massimo Dutti'), 'p25']
        ax.axvspan(lo, hi, color=FONDO_HUECO, zorder=0)
        h = hueco.query('categoria == @cat')
        pct = round(100 * h['n_hueco'].sum() / h['n'].sum())
        ax.text((lo + hi) / 2, -0.5, f'Hueco\n{euros(lo)} – {euros(hi)}\n'
                f'{pct} % de los modelos', ha='center', va='bottom', fontsize=8.5, color=TEXTO_SEC)


def titulo_panel(ax, cat):
    ax.set_title(PRENDAS[cat], loc='left', fontsize=12, fontweight='bold', color=TEXTO, pad=12)


LEYENDA_ESCALERA = ('Barra: 50 % central de los modelos (de P25 a P75). Punto: mediana. '
                    'En azul, las marcas de Inditex. Con trama: muestra pequeña (menos de 15 modelos).')

print('Gráficos:')

# 1a. Solo camisetas (diapositiva 4)
fig, ax = plt.subplots(figsize=(8, 4.2))
dibujar_escalera(ax, 'camiseta')
titulo_panel(ax, 'camiseta')
nota_pie(fig, LEYENDA_ESCALERA)
fig.subplots_adjust(bottom=0.2, left=0.17)
guardar(fig, '01_escalera_camiseta.png')

# 1b. Múltiplos pequeños: camiseta y vaquero (diapositiva 5)
fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
for ax, cat in zip(axes, PRENDAS):
    dibujar_escalera(ax, cat, nombres=(cat == 'camiseta'))
    titulo_panel(ax, cat)
fig.subplots_adjust(wspace=0.18, bottom=0.2, left=0.1)
nota_pie(fig, LEYENDA_ESCALERA + ' Cada panel tiene su escala.')
guardar(fig, '02_escalera_camiseta_vaquero.png')

# 1c. La escalera con el hueco sombreado (diapositiva 10)
fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
for ax, cat in zip(axes, PRENDAS):
    dibujar_escalera(ax, cat, sombrear_hueco=True, nombres=(cat == 'camiseta'))
    titulo_panel(ax, cat)
fig.subplots_adjust(wspace=0.18, bottom=0.2, left=0.1)
nota_pie(fig, 'Hueco: precios por encima del P75 de Zara y por debajo del P25 de Massimo Dutti, '
              'redondeados al euro (39,95 € y 39,99 € cuentan como el mismo precio). '
              'Porcentaje sobre los modelos de las 5 marcas.')
guardar(fig, '07_hueco_escalera.png')


# ---------------------------------------------------------------------------
# 2. Ratios de la escalera de Inditex (diapositiva 6)
# ---------------------------------------------------------------------------
# Barras verticales desde cero: así el doble de altura es el doble de precio
# (factor de mentira = 1).
fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
escalera_inditex = ['Lefties', 'Zara', 'Massimo Dutti']
for ax, cat in zip(axes, PRENDAS):
    medianas = [resumen.loc[(cat, m), 'mediana'] for m in escalera_inditex]
    baja = [resumen.loc[(cat, m), 'fiabilidad'] != 'OK' for m in escalera_inditex]
    ax.bar(range(3), medianas, width=0.55, color=AZUL, zorder=2,
           hatch=['////' if b else None for b in baja], edgecolor='white', linewidth=0)
    for i, v in enumerate(medianas):
        ax.text(i, v + max(medianas) * 0.02, euros(v), ha='center', va='bottom',
                fontsize=11, fontweight='bold', color=AZUL)
    # Multiplicador entre escalones, a media altura entre las dos barras.
    for i in range(2):
        ratio = medianas[i + 1] / medianas[i]
        y = (medianas[i] + medianas[i + 1]) / 2
        ax.annotate('', xy=(i + 0.72, medianas[i + 1] * 0.92), xytext=(i + 0.28, medianas[i] * 1.02),
                    arrowprops=dict(arrowstyle='->', color=TEXTO_SEC, lw=1))
        ax.text(i + 0.46, y, f'×{ratio:.1f}'.replace('.', ','),
                ha='right', va='bottom', fontsize=14, fontweight='bold', color=TEXTO)
    ax.set_xticks(range(3))
    ax.set_xticklabels([f'{m}\nn = {int(resumen.loc[(cat, m), "n"])}' +
                        ('\nmuestra pequeña' if b else '') for m, b in zip(escalera_inditex, baja)],
                       fontsize=9.5)
    ax.set_ylim(0, max(medianas) * 1.25)
    ax.set_yticks([])
    for lado in ['top', 'right', 'left']:
        ax.spines[lado].set_visible(False)
    ax.spines['bottom'].set_color(GRIS_CLARO)
    ax.tick_params(length=0)
    titulo_panel(ax, cat)
fig.subplots_adjust(wspace=0.25, bottom=0.25)
nota_pie(fig, 'Barras: precio mediano de cada marca de Inditex. Multiplicador = mediana del '
              'escalón superior / mediana del inferior.')
guardar(fig, '03_ratios_escalera.png')


# ---------------------------------------------------------------------------
# 3. Solapamiento por parejas (diapositiva 7)
# ---------------------------------------------------------------------------
# Métrica principal (tramos de 5 € / 10 €) y, como marca fina, la prueba de
# robustez con tramos de 4 € / 8 €, recalculada aquí con el mismo método que la
# vista v_solape_pares.
def solape(cat, ancho):
    d = basicas[basicas['categoria'] == cat].copy()
    d['tramo'] = (d['precio'] // ancho).astype(int)       # // = división entera
    cuota = d.groupby(['marca', 'tramo']).size().unstack(fill_value=0)
    cuota = cuota.div(cuota.sum(axis=1), axis=0)            # reparto de cada marca
    return {frozenset((a, b)): round(100 * cuota.loc[[a, b]].min().sum())
            for a, b in itertools.combinations(cuota.index, 2)}


principal = {c: solape(c, a) for c, a in [('camiseta', 5), ('vaquero', 10)]}
robustez = {c: solape(c, a) for c, a in [('camiseta', 4), ('vaquero', 8)]}

# Comprobación de coherencia con la vista SQL.
for _, r in pares.iterrows():
    assert principal[r['categoria']][frozenset((r['marca_a'], r['marca_b']))] == r['solape_pct'], r

todas = list(principal['camiseta'].keys())
# Orden: de más a menos solapamiento medio entre las dos prendas.
todas.sort(key=lambda p: -(principal['camiseta'][p] + principal['vaquero'][p]))
DESTACADAS = {frozenset(('Lefties', 'Primark')), frozenset(('H&M', 'Zara'))}


def nombre_pareja(p):
    # Orden alfabético, igual que la columna 'pareja' de v_solape_pares.
    a, b = sorted(p)
    return f'{a} – {b}'


fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
for ax, (cat, ancho, ancho_rob) in zip(axes, [('camiseta', 5, 4), ('vaquero', 10, 8)]):
    for i, p in enumerate(todas):
        v = principal[cat][p]
        destacada = p in DESTACADAS
        ax.barh(i, v, height=0.6, color=DESTACADO if destacada else GRIS_CLARO, zorder=2)
        ax.text(v + 1.5, i, f'{v} %', va='center', fontsize=9.5,
                fontweight='bold' if destacada else 'normal',
                color=TEXTO if destacada else TEXTO_SEC)
        # Marca fina: valor con el otro ancho de tramo.
        ax.plot([robustez[cat][p]] * 2, [i - 0.38, i + 0.38], color=TEXTO, lw=1.2, zorder=3)
        if p == frozenset(('H&M', 'Lefties')) and cat == 'camiseta':
            ax.annotate(f'frágil: {robustez[cat][p]} % con tramos de {ancho_rob} €', (v, i),
                        xytext=(38, 0), textcoords='offset points', va='center',
                        fontsize=8, style='italic', color=TEXTO_SEC)
    ax.set_yticks(range(len(todas)))
    ax.set_yticklabels([nombre_pareja(p) for p in todas], fontsize=9.5)
    for t, p in zip(ax.get_yticklabels(), todas):
        if p in DESTACADAS:
            t.set_color(TEXTO)
            t.set_fontweight('bold')
    ax.set_xlim(0, 105)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(['0 %', '25 %', '50 %', '75 %', '100 %'])
    limpiar_ejes(ax)
    ax.set_title(f'{PRENDAS[cat]} · tramos de {ancho} €', loc='left', fontsize=12,
                 fontweight='bold', color=TEXTO, pad=12)
axes[0].invert_yaxis()  # una sola vez: el eje y es compartido
fig.subplots_adjust(wspace=0.12, bottom=0.17, left=0.14)
nota_pie(fig, 'Solapamiento: parte del catálogo que dos marcas reparten igual por tramos de precio '
              '(0 % = no comparten ningún tramo; 100 % = mismo reparto).\n'
              'Línea vertical: el mismo cálculo con tramos de 4 € (camiseta) y 8 € (vaquero), '
              'como prueba de robustez.')
guardar(fig, '04_solapamiento_parejas.png')


# ---------------------------------------------------------------------------
# 4. H&M rodea a Zara (diapositiva 8)
# ---------------------------------------------------------------------------
# Para cada precio, % de los modelos de la marca que tienen ese precio.
# Zara arriba (azul) y H&M abajo (gris), con el mismo eje de precio.
# El fondo gris es la franja central de Zara (P25–P75) en las dos filas: así se
# ve qué parte de H&M queda por debajo, dentro y por encima de ella.
rodea = pd.read_csv(os.path.join(TABLAS, 'hm_rodea_zara.csv')).set_index(['categoria', 'marca'])
fig, axes = plt.subplots(2, 2, figsize=(12, 5), sharex='col',
                         gridspec_kw={'hspace': 0.15, 'wspace': 0.12})
ancho_barra = {'camiseta': 0.6, 'vaquero': 1.2}
for col, cat in enumerate(PRENDAS):
    cuotas = {m: basicas.query('categoria == @cat and marca == @m')['precio']
                        .value_counts(normalize=True).mul(100) for m in ['Zara', 'H&M']}
    tope = max(c.max() for c in cuotas.values())   # misma escala vertical en las dos filas
    zara = resumen.loc[(cat, 'Zara')]
    for fila, marca in enumerate(['Zara', 'H&M']):
        ax = axes[fila, col]
        # Media barra de margen a cada lado para que las barras del borde queden dentro.
        ax.axvspan(zara['p25'] - ancho_barra[cat] / 2, zara['p75'] + ancho_barra[cat] / 2,
                   color=FONDO_HUECO, zorder=0)
        ax.bar(cuotas[marca].index, cuotas[marca].values, width=ancho_barra[cat],
               color=color_marca(marca), zorder=2)
        ax.set_ylim(0, tope * 1.4)
        ax.set_yticks([])
        ax.text(-0.01, 0.4, f'{marca}\nn = {int(resumen.loc[(cat, marca), "n"])}',
                transform=ax.transAxes, ha='right', va='center', fontsize=10,
                fontweight='bold', color=color_marca(marca))
        for lado in ['top', 'right', 'left']:
            ax.spines[lado].set_visible(False)
        ax.spines['bottom'].set_color(GRIS_CLARO)
        ax.tick_params(length=0)
    # Rótulo de la franja, arriba.
    axes[0, col].text((zara['p25'] + zara['p75']) / 2, tope * 1.38,
                      f'Franja central de Zara\n{euros(zara["p25"])} – {euros(zara["p75"])}',
                      ha='center', va='top', fontsize=8, color=TEXTO_SEC)
    # Reparto de H&M respecto a esa franja.
    r = rodea.loc[(cat, 'H&M')]
    ax = axes[1, col]
    lim = {'camiseta': (0, 52), 'vaquero': (15, 92)}[cat]
    y = tope * 1.38
    # Cada rótulo, centrado en su zona: por debajo, dentro y por encima de la franja.
    for x, texto in [((lim[0] + zara['p25']) / 2, f'{r["pct_por_debajo"]} %\npor debajo'),
                     ((zara['p25'] + zara['p75']) / 2, f'{r["pct_dentro"]} %\ndentro'),
                     ((zara['p75'] + lim[1]) / 2, f'{r["pct_por_encima"]} %\npor encima')]:
        ax.text(x, y, texto, ha='center', va='top', fontsize=9, fontweight='bold', color=TEXTO,
                linespacing=1.1)
    axes[0, col].set_title(PRENDAS[cat], loc='left', fontsize=12, fontweight='bold',
                           color=TEXTO, pad=10)
    axes[1, col].set_xlim(*lim)
    ticks = range(0, 51, 10) if cat == 'camiseta' else range(20, 91, 10)
    axes[1, col].set_xticks(list(ticks))
    axes[1, col].set_xticklabels([euros(t, 0) for t in ticks])
fig.subplots_adjust(bottom=0.17, left=0.08)
nota_pie(fig, 'Altura de cada barra: % de los modelos de la marca con ese precio (misma escala en las '
              'dos filas). Fondo gris: 50 % central de los modelos de Zara (P25–P75).\n'
              'Por debajo / dentro / por encima: precios redondeados al euro (29,95 € y 29,99 € '
              'cuentan como el mismo precio). El eje del vaquero empieza en 15 €.')
guardar(fig, '05_hm_rodea_zara.png')


# ---------------------------------------------------------------------------
# 5. Arquitectura de precios (diapositiva 9)
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
for ax, cat in zip(axes, PRENDAS):
    for i, marca in enumerate(ORDEN):
        a = arquitectura.loc[(cat, marca)]
        baja = resumen.loc[(cat, marca), 'fiabilidad'] != 'OK'
        ax.barh(i, a['pct_top3'], height=0.55, color=color_marca(marca), zorder=2,
                hatch='////' if baja else None, edgecolor='white', linewidth=0)
        ax.text(a['pct_top3'] + 2, i, f'{int(a["pct_top3"])} %', va='center', fontsize=10,
                fontweight='bold', color=color_marca(marca))
        n_precios = int(a['precios_distintos'])
        # Con 3 precios o menos, el 100 % es automático: lo decimos para no inflarlo.
        detalle = (f'usa solo {n_precios} precios' if n_precios <= 3
                   else f'{n_precios} precios distintos') + f' · {int(a["n"])} modelos'
        ax.text(122, i, detalle, va='center', fontsize=8.5, color=TEXTO_SEC, clip_on=False)
    ax.set_yticks(range(len(ORDEN)))
    ax.set_yticklabels(ORDEN, fontsize=10.5, fontweight='bold')
    for t, marca in zip(ax.get_yticklabels(), ORDEN):
        t.set_color(color_marca(marca))
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 50, 100])
    ax.set_xticklabels(['0 %', '50 %', '100 %'])
    limpiar_ejes(ax)
    titulo_panel(ax, cat)
fig.subplots_adjust(wspace=0.85, bottom=0.2, left=0.1, right=0.8)
nota_pie(fig, 'Barra: % del catálogo de básicas que concentran los 3 precios más frecuentes de cada '
              'marca. Con trama: muestra pequeña (menos de 15 modelos).\nCon más modelos es más fácil tener más precios '
              'distintos: parte de la dispersión de H&M se debe a su tamaño de catálogo.')
guardar(fig, '06_arquitectura_precios.png')
