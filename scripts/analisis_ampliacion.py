"""
Ampliación a 16 marcas · tablas para tomar decisiones con Javi y comprobar las conclusiones.

Qué calcula (docs/INSTRUCCIONES_AMPLIACION.md, secciones 3, 5 y 6):
  1. Rebajas: % del catálogo rebajado y descuento medio por marca.
  2. Muestras: n de básicas por marca y prenda, tramo de fiabilidad y concentración
     de precios (si casi todo está a un precio, la mediana es más fiable de lo que
     sugiere el n).
  3. Resumen de precios de las 16 marcas (vista v_resumen_precios).
  4. Sensibilidad: el mismo resumen y el mismo solapamiento con el precio REBAJADO
     (precio_venta). ¿Cambia el orden de la escalera o alguna pareja?
  5. Solapamiento por tramos entre las marcas que entran en las métricas, con la
     prueba de robustez (4 € / 8 €).
  6. Ancla de control: ninguna marca premium debería solaparse con Primark o Lefties.
  7. Conclusiones originales, escalera de Tendam frente a Inditex, Mango y el hueco
     entre Zara y Massimo Dutti.

Regla de coherencia: los cuartiles y el solapamiento con tramos de 5 € / 10 € se leen
de las vistas SQL. Lo único que se recalcula en Python (tramos de 4 € / 8 €) se
comprueba antes contra v_solape_pares con los anchos originales.

Uso:  python scripts/construir_bd.py && python scripts/analisis_ampliacion.py
Salida: output/tablas/ampliacion/*.csv y un resumen por pantalla.
"""
import os
import shutil
import sqlite3
import tempfile

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, 'data', 'moda.db')
SALIDA = os.path.join(BASE, 'output', 'tablas', 'ampliacion')
os.makedirs(SALIDA, exist_ok=True)

ANCHO = {'camiseta': 5, 'vaquero': 10}          # tramos de la métrica principal
ANCHO_ROBUSTEZ = {'camiseta': 4, 'vaquero': 8}  # prueba de robustez
N_MIN_METRICAS = 5      # solo para rotular la tabla de muestras; el corte real está en v_resumen_precios
N_FIABLE = 15
PREMIUM = ['Desigual', 'Adolfo Domínguez', 'Bimba y Lola', 'Scalpers', 'El Ganso', 'Silbon',
           'Pedro del Hierro', 'Massimo Dutti']

pd.set_option('display.width', 220)
pd.set_option('display.max_columns', 30)
pd.set_option('display.max_colwidth', 90)


def euros(x):
    return f'{x:.2f}'.replace('.', ',') + ' €'


def leer(con):
    """Básicas con precio y vistas, tal como las deja el SQL."""
    basicas = pd.read_sql("""SELECT marca, categoria, nombre, precio_actual AS precio
                             FROM catalogo WHERE motivo = '7_basica' AND precio_actual IS NOT NULL""", con)
    resumen = pd.read_sql('SELECT * FROM v_resumen_precios', con)
    pares = pd.read_sql('SELECT categoria, marca_a, marca_b, solape_pct FROM v_solape_pares', con)
    return basicas, resumen, pares


def solape_python(basicas, cat, ancho):
    """Coeficiente de solapamiento por tramos: el mismo cálculo que v_solape_pares."""
    d = basicas[basicas['categoria'] == cat].copy()
    d['tramo'] = (d['precio'] // ancho).astype(int)
    cuota = d.groupby(['marca', 'tramo']).size().unstack(fill_value=0)
    cuota = cuota.div(cuota.sum(axis=1), axis=0)        # reparto de cada marca (suma 1)
    marcas = sorted(cuota.index)
    filas = []
    for i, a in enumerate(marcas):
        for b in marcas[i + 1:]:
            filas.append({'categoria': cat, 'marca_a': a, 'marca_b': b,
                          'solape_pct': round(100 * cuota.loc[[a, b]].min().sum())})
    return pd.DataFrame(filas)


def todas_las_parejas(pares, resumen):
    """v_solape_pares omite las parejas sin ningún tramo en común: se rellenan con 0 %."""
    filas = []
    for cat, g in resumen[resumen['en_metricas'] == 1].groupby('categoria'):
        marcas = sorted(g['marca'])
        for i, a in enumerate(marcas):
            for b in marcas[i + 1:]:
                filas.append((cat, a, b))
    todo = pd.DataFrame(filas, columns=['categoria', 'marca_a', 'marca_b'])
    return todo.merge(pares, how='left').fillna({'solape_pct': 0}).astype({'solape_pct': int})


# =============================================================================
con = sqlite3.connect(DB)
basicas, resumen, pares = leer(con)
grupos = dict(con.execute('SELECT marca, grupo FROM marcas').fetchall())

# 1. Rebajas -------------------------------------------------------------------
rebajas = pd.read_sql("""
    SELECT marca,
           COUNT(*)                                                  AS filas,
           SUM(rebajado)                                             AS rebajadas,
           ROUND(100.0 * AVG(rebajado))                              AS pct_rebajado,
           SUM(CASE WHEN motivo = '7_basica' THEN 1 ELSE 0 END)      AS basicas,
           SUM(CASE WHEN motivo = '7_basica' THEN rebajado ELSE 0 END) AS basicas_rebajadas,
           ROUND(100.0 * AVG(CASE WHEN rebajado = 1
                                  THEN 1 - precio_venta / precio_actual END)) AS dto_medio_pct
    FROM catalogo
    GROUP BY marca
    ORDER BY pct_rebajado DESC, marca""", con)
rebajas.insert(1, 'grupo', rebajas['marca'].map(grupos))
rebajas.to_csv(os.path.join(SALIDA, 'rebajas_por_marca.csv'), index=False)

# 2. Muestras y concentración de precios ---------------------------------------
filas = []
for (cat, marca), g in basicas.groupby(['categoria', 'marca']):
    frec = g['precio'].value_counts()
    n = len(g)
    tramo = 'n ≥ 15' if n >= N_FIABLE else ('5–14 (muestra pequeña)' if n >= N_MIN_METRICAS else 'n < 5')
    filas.append({'categoria': cat, 'grupo': grupos[marca], 'marca': marca, 'n': n, 'tramo_n': tramo,
                  'precios_distintos': len(frec), 'precio_mas_frecuente': frec.index[0],
                  'pct_precio_mas_frecuente': round(100 * frec.iloc[0] / n),
                  'min': g['precio'].min(), 'max': g['precio'].max()})
muestras = pd.DataFrame(filas)
# Marcas sin ninguna básica en una prenda (no salen en groupby)
for cat in ['camiseta', 'vaquero']:
    for marca in grupos:
        if not ((muestras['categoria'] == cat) & (muestras['marca'] == marca)).any():
            muestras.loc[len(muestras)] = {'categoria': cat, 'grupo': grupos[marca], 'marca': marca, 'n': 0,
                                           'tramo_n': 'n < 5'}
muestras = muestras.sort_values(['categoria', 'n'], ascending=[True, False])
muestras.to_csv(os.path.join(SALIDA, 'muestras_por_marca.csv'), index=False)

# Decisión de Javi: n ≥ 5 y Women'secret fuera. El corte vive en la vista (columna en_metricas).
en_metricas = {(c, m) for c, m, e in zip(resumen['categoria'], resumen['marca'], resumen['en_metricas']) if e}

# 3. Resumen de las 16 marcas ---------------------------------------------------
resumen['en_metricas'] = resumen['en_metricas'].astype(bool)
resumen = resumen.sort_values(['categoria', 'mediana', 'marca'])
resumen.to_csv(os.path.join(SALIDA, 'resumen_16_marcas.csv'), index=False)

# 4. Sensibilidad con el precio rebajado -----------------------------------------
# Se copia la base, se pone el precio rebajado en precio_actual y se leen las MISMAS
# vistas: así el método es idéntico y solo cambia el precio.
tmp = os.path.join(tempfile.mkdtemp(), 'moda_precio_venta.db')
shutil.copy(DB, tmp)
con_v = sqlite3.connect(tmp)
con_v.execute('UPDATE catalogo SET precio_actual = precio_venta')
con_v.commit()
basicas_v, resumen_v, pares_v = leer(con_v)
con_v.close()

sens = resumen[['categoria', 'marca', 'n', 'p25', 'mediana', 'p75', 'en_metricas']].merge(
    resumen_v[['categoria', 'marca', 'p25', 'mediana', 'p75']], on=['categoria', 'marca'],
    suffixes=('', '_rebajado'))
sens['cambia_mediana'] = (sens['mediana'] - sens['mediana_rebajado']).abs() > 0.005
# Puesto en la escalera (por mediana) de cada marca que entra en las métricas, con los dos precios
for col in ['mediana', 'mediana_rebajado']:
    sens['puesto_' + col] = (sens[sens['en_metricas']].groupby('categoria')[col]
                             .rank(method='min').reindex(sens.index))
sens.to_csv(os.path.join(SALIDA, 'sensibilidad_rebajas_resumen.csv'), index=False)

pares_cat = todas_las_parejas(pares, resumen)
pares_cat_v = todas_las_parejas(pares_v, resumen_v)
sens_pares = pares_cat.merge(pares_cat_v, on=['categoria', 'marca_a', 'marca_b'], suffixes=('', '_rebajado'))
sens_pares['diferencia'] = sens_pares['solape_pct_rebajado'] - sens_pares['solape_pct']

# 5. Solapamiento entre las marcas que entran en las métricas ---------------------
# Coherencia: el cálculo en Python con los anchos originales tiene que dar lo mismo que la vista.
basicas_m = basicas[[(c, m) in en_metricas for c, m in zip(basicas['categoria'], basicas['marca'])]]
for cat in ['camiseta', 'vaquero']:
    py = solape_python(basicas_m, cat, ANCHO[cat])
    sq = pares_cat[pares_cat['categoria'] == cat]
    comp = py.merge(sq, on=['categoria', 'marca_a', 'marca_b'], suffixes=('_py', '_sql'))
    assert len(comp) == len(py) and (comp['solape_pct_py'] == comp['solape_pct_sql']).all(), \
        f'El solapamiento en Python no coincide con v_solape_pares ({cat})'
robustez = pd.concat([solape_python(basicas_m, c, ANCHO_ROBUSTEZ[c]) for c in ['camiseta', 'vaquero']])
solape = (pares_cat.merge(robustez, on=['categoria', 'marca_a', 'marca_b'], suffixes=('', '_robustez'))
          .merge(sens_pares[['categoria', 'marca_a', 'marca_b', 'solape_pct_rebajado']]))
solape['en_metricas'] = True    # la vista ya solo incluye marcas con en_metricas = 1
solape['pareja'] = solape['marca_a'] + ' – ' + solape['marca_b']
solape = solape.sort_values(['categoria', 'solape_pct'], ascending=[True, False])
solape.to_csv(os.path.join(SALIDA, 'solapamiento_16_marcas.csv'), index=False)
sol_m = solape[solape['en_metricas']]

# 6. Ancla de control -----------------------------------------------------------
ancla = sol_m[(sol_m['marca_a'].isin(PREMIUM) & sol_m['marca_b'].isin(['Primark', 'Lefties'])) |
              (sol_m['marca_b'].isin(PREMIUM) & sol_m['marca_a'].isin(['Primark', 'Lefties']))]

# 7. Escaleras (ratios de medianas) ------------------------------------------------
med = resumen.set_index(['categoria', 'marca'])['mediana']
filas = []
for grupo, escalera in [('Inditex', ['Lefties', 'Zara', 'Massimo Dutti']),
                        ('Tendam', ['Springfield', 'Cortefiel', 'Pedro del Hierro'])]:
    for cat in ['camiseta', 'vaquero']:
        for baja, alta in zip(escalera, escalera[1:]):
            if (cat, baja) in med and (cat, alta) in med:
                filas.append({'grupo': grupo, 'categoria': cat, 'escalon': f'{baja} → {alta}',
                              'mediana_baja': med[(cat, baja)], 'mediana_alta': med[(cat, alta)],
                              'ratio': round(med[(cat, alta)] / med[(cat, baja)], 1),
                              'calculo': f'{euros(med[(cat, alta)])} / {euros(med[(cat, baja)])}',
                              'n_baja': int(resumen.set_index(['categoria', 'marca']).loc[(cat, baja), 'n']),
                              'n_alta': int(resumen.set_index(['categoria', 'marca']).loc[(cat, alta), 'n'])})
ratios = pd.DataFrame(filas)
ratios.to_csv(os.path.join(SALIDA, 'ratios_escaleras.csv'), index=False)

# Hueco entre el P75 de Zara y el P25 de Massimo Dutti (precios redondeados al euro,
# criterio aprobado por Javi: 39,95 € y 39,99 € cuentan como el mismo precio).
def redondear_euro(x):
    return int(x + 0.5)


r = resumen.set_index(['categoria', 'marca'])
filas = []
for cat in ['camiseta', 'vaquero']:
    lo, hi = redondear_euro(r.loc[(cat, 'Zara'), 'p75']), redondear_euro(r.loc[(cat, 'Massimo Dutti'), 'p25'])
    d = basicas[basicas['categoria'] == cat].copy()
    d['en_hueco'] = d['precio'].map(redondear_euro).between(lo + 1, hi - 1)
    for marca, g in d.groupby('marca'):
        dentro = g[g['en_hueco']]
        filas.append({'categoria': cat, 'hueco': f'{euros(r.loc[(cat, "Zara"), "p75"])} – '
                                                 f'{euros(r.loc[(cat, "Massimo Dutti"), "p25"])}',
                      'marca': marca, 'grupo': grupos[marca], 'n': len(g),
                      'en_metricas': (cat, marca) in en_metricas,
                      'n_hueco': int(g['en_hueco'].sum()), 'pct_hueco': round(100 * g['en_hueco'].mean()),
                      'precios_en_hueco': ' · '.join(f'{euros(p)} ({k})' for p, k in
                                                     dentro['precio'].value_counts().sort_index().items())})
hueco = pd.DataFrame(filas).sort_values(['categoria', 'n_hueco'], ascending=[True, False])
hueco.to_csv(os.path.join(SALIDA, 'hueco_16_marcas.csv'), index=False)
# Peso del hueco en la oferta de las marcas que entran en las métricas (modelos, no ventas)
hm = hueco[hueco['en_metricas']]
hueco_total = hm.groupby('categoria')[['n', 'n_hueco']].sum()
hueco_total['pct'] = (100 * hueco_total['n_hueco'] / hueco_total['n']).round().astype(int)
# Sensibilidad: el mismo hueco (mismos límites de Zara y Massimo Dutti, que no tienen
# rebajas) contando cada modelo con el precio que marcaba la web ese día.
filas = []
for cat in ['camiseta', 'vaquero']:
    lo, hi = redondear_euro(r.loc[(cat, 'Zara'), 'p75']), redondear_euro(r.loc[(cat, 'Massimo Dutti'), 'p25'])
    d = basicas_v[basicas_v['categoria'] == cat]
    d = d[d['marca'].map(lambda m: (cat, m) in en_metricas)]
    filas.append({'categoria': cat, 'pct_rebajado': round(100 * d['precio'].map(redondear_euro)
                                                          .between(lo + 1, hi - 1).mean())})
hueco_total = hueco_total.join(pd.DataFrame(filas).set_index('categoria'))
hueco_total.to_csv(os.path.join(SALIDA, 'hueco_total.csv'))

# 8. Arquitectura de precios: céntimos finales y concentración ------------------------
# Céntimos con enteros (precio × 100) para evitar errores de redondeo (7.99 * 100 = 798.999…).
bm = basicas_m.copy()
bm['centimos'] = (bm['precio'] * 100).round().astype(int) % 100
bm['terminacion'] = bm['centimos'].map(lambda c: ',00' if c == 0 else f',{c:02d}')
terminaciones = (pd.crosstab(bm['marca'], bm['terminacion'], normalize='index').mul(100).round().astype(int))
terminaciones.insert(0, 'grupo', terminaciones.index.map(grupos))
terminaciones.insert(1, 'n', bm.groupby('marca').size())
terminaciones = terminaciones.sort_values(['grupo', 'n'], ascending=[True, False])
terminaciones.to_csv(os.path.join(SALIDA, 'terminaciones_16_marcas.csv'))
filas = []
for (cat, marca), g in bm.groupby(['categoria', 'marca']):
    frec = g['precio'].value_counts()
    filas.append({'categoria': cat, 'grupo': grupos[marca], 'marca': marca, 'n': len(g),
                  'precios_distintos': len(frec), 'pct_top3': round(100 * frec.head(3).sum() / len(g)),
                  'precios_top3': ' · '.join(euros(p) for p in frec.head(3).index)})
arquitectura = pd.DataFrame(filas).sort_values(['categoria', 'pct_top3'], ascending=[True, False])
arquitectura.to_csv(os.path.join(SALIDA, 'arquitectura_16_marcas.csv'), index=False)
con.close()

# =============================================================================
# Resumen por pantalla
# =============================================================================
print('1. REBAJAS POR MARCA (todas las filas; el análisis usa el precio de catálogo)')
print(rebajas.to_string(index=False))

print('\n2. MUESTRAS DE BÁSICAS Y CONCENTRACIÓN DE PRECIOS')
print(muestras[['categoria', 'marca', 'n', 'tramo_n', 'precios_distintos', 'precio_mas_frecuente',
                'pct_precio_mas_frecuente', 'min', 'max']].to_string(index=False))

print('\n3. ESCALERA POR MEDIANA (solo marcas que entran en las métricas)')
print(resumen[resumen['en_metricas']][['categoria', 'grupo', 'marca', 'n', 'p25', 'mediana', 'p75',
                                       'maximo', 'media']].to_string(index=False))

print('\n4. SENSIBILIDAD: PRECIO DE CATÁLOGO vs PRECIO REBAJADO')
print(sens[sens['cambia_mediana']][['categoria', 'marca', 'n', 'p25', 'mediana', 'p75', 'p25_rebajado',
                                    'mediana_rebajado', 'p75_rebajado', 'puesto_mediana',
                                    'puesto_mediana_rebajado']].to_string(index=False))
cambios = sens_pares[(sens_pares['diferencia'].abs() >= 10)].merge(
    solape[['categoria', 'marca_a', 'marca_b', 'en_metricas']])
print('\nParejas cuyo solapamiento cambia 10 puntos o más con el precio rebajado:')
print(cambios[cambios['en_metricas']].sort_values('diferencia').to_string(index=False))

print('\n5. SOLAPAMIENTO ≥ 30 % (marcas en las métricas) · principal / robustez / con precio rebajado')
print(sol_m[sol_m['solape_pct'] >= 30][['categoria', 'pareja', 'solape_pct', 'solape_pct_robustez',
                                        'solape_pct_rebajado']].to_string(index=False))

print('\n6. ANCLA DE CONTROL: premium frente a Primark / Lefties (máximo de cada prenda)')
print(ancla.groupby('categoria')[['solape_pct', 'solape_pct_robustez', 'solape_pct_rebajado']].max())
print(ancla[ancla['solape_pct'] > 0][['categoria', 'pareja', 'solape_pct']].to_string(index=False) or '  (ninguna > 0 %)')

print('\n7a. RATIOS DE LAS ESCALERAS (medianas)')
print(ratios.to_string(index=False))
print('\n7b. HUECO ENTRE ZARA (P75) Y MASSIMO DUTTI (P25), precios redondeados al euro')
print(hueco[hueco['n_hueco'] > 0].to_string(index=False))
print('\nPeso del hueco en la oferta de las marcas en métricas (pct_rebajado: con el precio rebajado):')
print(hueco_total.to_string())
print('\n8. ARQUITECTURA DE PRECIOS')
print(arquitectura.to_string(index=False))
print('\nTerminaciones (% de modelos, camiseta + vaquero):')
print(terminaciones.to_string())
print('\nTablas guardadas en', SALIDA)
