"""
Paso 1 · Análisis complementario (sección 7 de CLAUDE.md).

Tres preguntas que completan la historia de la escalera de precios:
  1. Arquitectura de precios: ¿cuántos precios distintos usa cada marca y cuánto
     catálogo concentran los más frecuentes? ¿En qué céntimos terminan?
  2. El hueco de la escalera: ¿quién ocupa los precios entre el P75 de Zara y el
     P25 de Massimo Dutti?
  3. Ratios de la escalera de Inditex (medianas), con el cálculo explícito.

Fuente: data/moda.db (hay que ejecutar antes scripts/construir_bd.py).
Los cuartiles y medianas se leen de la vista v_resumen_precios para que todo
coincida con el SQL (regla de coherencia).
Salida: tablas CSV en output/tablas/ y un resumen por pantalla.

Uso:  python scripts/analisis_complementario.py
"""
import os
import sqlite3

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, 'data', 'moda.db')
SALIDA = os.path.join(BASE, 'output', 'tablas')
os.makedirs(SALIDA, exist_ok=True)

con = sqlite3.connect(DB)

# Prendas básicas con precio: la misma población que usan las vistas.
basicas = pd.read_sql("""
    SELECT marca, categoria, nombre, precio_actual AS precio
    FROM catalogo
    WHERE motivo = '7_basica' AND precio_actual IS NOT NULL
""", con)

# Cuartiles y medianas tal como los calcula el SQL (NTILE(4)).
resumen = pd.read_sql('SELECT * FROM v_resumen_precios', con).set_index(['categoria', 'marca'])


def euros(x):
    """Formato español: 7.99 -> '7,99 €'."""
    return f'{x:.2f}'.replace('.', ',') + ' €'


# =============================================================================
# 1. Arquitectura de precios
# =============================================================================
# Los céntimos se calculan con números enteros (precio × 100) para evitar los
# errores de redondeo de los decimales en el ordenador (7.99 * 100 = 798.9999…).
basicas['centimos'] = (basicas['precio'] * 100).round().astype(int) % 100
basicas['terminacion'] = basicas['centimos'].map(
    lambda c: 'entero (,00)' if c == 0 else f',{c:02d}')

filas = []
for (cat, marca), g in basicas.groupby(['categoria', 'marca']):
    # value_counts() cuenta cuántos modelos hay en cada precio, de más a menos.
    frecuencias = g['precio'].value_counts()
    n = len(g)
    top = frecuencias.head(3)
    term = g['terminacion'].value_counts(normalize=True)
    filas.append({
        'categoria': cat,
        'marca': marca,
        'n': n,
        'precios_distintos': len(frecuencias),
        # Normalizamos por tamaño: una marca con más modelos tiende a tener más
        # precios distintos solo por tener más productos.
        'precios_por_10_modelos': round(10 * len(frecuencias) / n, 1),
        'precio_1': top.index[0],
        'pct_precio_1': round(100 * top.iloc[0] / n),
        'pct_top2': round(100 * top.head(2).sum() / n),
        'pct_top3': round(100 * top.sum() / n),
        'precios_top3': ' · '.join(euros(p) for p in top.index),
        'escalones': ' → '.join(euros(p) for p in sorted(frecuencias.index)),
        'terminacion_principal': term.index[0],
        'pct_terminacion_principal': round(100 * term.iloc[0]),
    })
arquitectura = pd.DataFrame(filas).sort_values(['categoria', 'pct_top3'], ascending=[True, False])
arquitectura.to_csv(os.path.join(SALIDA, 'arquitectura_precios.csv'), index=False)

# Terminaciones por marca (las dos prendas juntas).
terminaciones = pd.crosstab(basicas['marca'], basicas['terminacion'], normalize='index').mul(100).round()
terminaciones.to_csv(os.path.join(SALIDA, 'terminaciones.csv'))


# =============================================================================
# 2. El hueco de la escalera
# =============================================================================
# Hueco = precios por encima del P75 de Zara y por debajo del P25 de Massimo Dutti.
# Ojo con la "trampa de los 4 céntimos": un vaquero de H&M a 39,99 € está
# técnicamente por encima del P75 de Zara (39,95 €), pero en la práctica es el
# mismo precio. Por eso calculamos el hueco de dos maneras:
#   - estricto: comparando en céntimos;
#   - redondeado: comparando precios redondeados al euro (39,95 y 39,99 -> 40 €).
# La definición buena es la redondeada; la estricta se guarda para enseñar la trampa.
def redondear_euro(x):
    # Redondeo "de toda la vida" (0,5 sube). round() de Python redondea 0,5 al par.
    return int(x + 0.5)


filas = []
for cat in ['camiseta', 'vaquero']:
    limite_inf = resumen.loc[(cat, 'Zara'), 'p75']
    limite_sup = resumen.loc[(cat, 'Massimo Dutti'), 'p25']
    d = basicas[basicas['categoria'] == cat].copy()
    d['en_hueco_estricto'] = (d['precio'] > limite_inf) & (d['precio'] < limite_sup)
    d['en_hueco'] = (d['precio'].map(redondear_euro) > redondear_euro(limite_inf)) & \
                    (d['precio'].map(redondear_euro) < redondear_euro(limite_sup))
    for marca, g in d.groupby('marca'):
        dentro = g[g['en_hueco']]
        filas.append({
            'categoria': cat,
            'limite_inferior_zara_p75': limite_inf,
            'limite_superior_md_p25': limite_sup,
            'marca': marca,
            'n': len(g),
            'n_hueco': int(g['en_hueco'].sum()),
            'pct_hueco': round(100 * g['en_hueco'].mean()),
            'n_hueco_estricto': int(g['en_hueco_estricto'].sum()),
            'pct_hueco_estricto': round(100 * g['en_hueco_estricto'].mean()),
            'precios_en_hueco': ' · '.join(
                f'{euros(p)} ({k})' for p, k in dentro['precio'].value_counts().sort_index().items()),
        })
hueco = pd.DataFrame(filas)
hueco.to_csv(os.path.join(SALIDA, 'hueco_escalera.csv'), index=False)

# Peso del hueco dentro de toda la oferta de las 5 marcas (modelos, no ventas).
hueco_total = hueco.groupby('categoria')[['n', 'n_hueco']].sum()
hueco_total['pct'] = (100 * hueco_total['n_hueco'] / hueco_total['n']).round()


# =============================================================================
# 3. Ratios de la escalera de Inditex
# =============================================================================
# Ratio = mediana del escalón superior / mediana del escalón inferior.
# Comprobación independiente: el mismo ratio con las medias. Si la escalera solo
# existiera en la mediana, con las medias se desharía.
escalones = [('Lefties', 'Zara'), ('Zara', 'Massimo Dutti'), ('Lefties', 'Massimo Dutti')]
filas = []
for cat in ['camiseta', 'vaquero']:
    for baja, alta in escalones:
        med_b, med_a = resumen.loc[(cat, baja), 'mediana'], resumen.loc[(cat, alta), 'mediana']
        mb, ma = resumen.loc[(cat, baja), 'media'], resumen.loc[(cat, alta), 'media']
        filas.append({
            'categoria': cat,
            'escalon': f'{baja} → {alta}',
            'mediana_baja': med_b,
            'mediana_alta': med_a,
            'ratio_mediana': round(med_a / med_b, 1),
            'calculo': f'{euros(med_a)} / {euros(med_b)} = {med_a / med_b:.2f}'.replace('.', ','),
            'ratio_media': round(ma / mb, 1),
        })
ratios = pd.DataFrame(filas)
ratios.to_csv(os.path.join(SALIDA, 'ratios_escalera.csv'), index=False)

# =============================================================================
# 4. ¿H&M rodea a Zara? (apoyo a la conclusión 3)
# =============================================================================
# Reparto de cada marca respecto a la franja central (P25–P75) de la otra.
# Se compara con precios redondeados al euro por la trampa de los 4 céntimos
# (29,95 € de Zara y 29,99 € de H&M cuentan como el mismo precio).
filas = []
for cat in ['camiseta', 'vaquero']:
    for marca, otra in [('H&M', 'Zara'), ('Zara', 'H&M')]:
        p = basicas.query('categoria == @cat and marca == @marca')['precio'].map(redondear_euro)
        lo = redondear_euro(resumen.loc[(cat, otra), 'p25'])
        hi = redondear_euro(resumen.loc[(cat, otra), 'p75'])
        filas.append({
            'categoria': cat, 'marca': marca, 'franja_de': otra,
            'franja': f'{euros(resumen.loc[(cat, otra), "p25"])} – {euros(resumen.loc[(cat, otra), "p75"])}',
            'pct_por_debajo': round(100 * (p < lo).mean()),
            'pct_dentro': round(100 * ((p >= lo) & (p <= hi)).mean()),
            'pct_por_encima': round(100 * (p > hi).mean()),
        })
rodea = pd.DataFrame(filas)
rodea.to_csv(os.path.join(SALIDA, 'hm_rodea_zara.csv'), index=False)

# Comprobación: ¿la mediana exacta (pandas) coincide con la de NTILE(4)?
mediana_exacta = basicas.groupby(['categoria', 'marca'])['precio'].median()
diferencias = (mediana_exacta - resumen['mediana']).abs()
assert diferencias.max() < 0.01, f'Medianas distintas:\n{diferencias[diferencias >= 0.01]}'

con.close()

# =============================================================================
# Resumen por pantalla
# =============================================================================
pd.set_option('display.width', 200)
pd.set_option('display.max_colwidth', 80)
print('1. ARQUITECTURA DE PRECIOS')
print(arquitectura[['categoria', 'marca', 'n', 'precios_distintos', 'precios_por_10_modelos',
                    'pct_precio_1', 'pct_top2', 'pct_top3', 'precios_top3']].to_string(index=False))
print('\nTerminaciones (% de modelos, camiseta + vaquero):')
print(terminaciones.to_string())
print('\nEscalones de Zara:')
for cat in ['camiseta', 'vaquero']:
    print(f'  {cat}:', arquitectura.query('marca == "Zara" and categoria == @cat')['escalones'].iloc[0])

print('\n2. HUECO ENTRE EL P75 DE ZARA Y EL P25 DE MASSIMO DUTTI (precios redondeados al euro)')
print(hueco[['categoria', 'marca', 'n', 'n_hueco', 'pct_hueco', 'n_hueco_estricto',
             'pct_hueco_estricto', 'precios_en_hueco']].to_string(index=False))
print('\nPeso del hueco en la oferta total de las 5 marcas:')
print(hueco_total.to_string())

print('\n3. RATIOS DE LA ESCALERA DE INDITEX')
print(ratios[['categoria', 'escalon', 'calculo', 'ratio_mediana', 'ratio_media']].to_string(index=False))
print('\n4. H&M FRENTE A LA FRANJA CENTRAL DE ZARA (y al revés), precios redondeados al euro')
print(rodea.to_string(index=False))
print('\nMediana exacta = mediana NTILE(4) en todas las marcas: OK')
print('Tablas guardadas en', SALIDA)
