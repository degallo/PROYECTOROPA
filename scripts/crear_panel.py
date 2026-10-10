"""
Panel web interactivo: output/panel/escalera_precios.html

Genera una página web autónoma (un solo fichero HTML) con el catálogo completo y
las 191 reglas de clasificación dentro. En el navegador se puede:
  - activar o quitar cadenas y ver al instante la escalera, el solapamiento por
    parejas, los escalones de Inditex, el hueco entre dos cadenas y la tabla;
  - cambiar el ancho de los tramos (prueba de robustez);
  - añadir una cadena nueva desde un CSV, que se clasifica con las mismas reglas.

Los cálculos están en scripts/panel/calc.js. Antes de escribir la página, este
script los ejecuta con Node y comprueba que dan lo mismo que las vistas SQL
(regla de coherencia de CLAUDE.md). Si algo no coincide, se para.

Uso:  python scripts/crear_panel.py
"""
import itertools
import json
import os
import shutil
import sqlite3
import subprocess
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, 'data', 'moda_5marcas.db')  # versión de 5 marcas (antes de la ampliación)
PANEL = os.path.join(BASE, 'scripts', 'panel')
SALIDA = os.path.join(BASE, 'output', 'panel', 'escalera_precios.html')
INDITEX = ['Lefties', 'Zara', 'Massimo Dutti']

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

# Catálogo tras la limpieza (precio_actual ya es el precio de catálogo). La
# clasificación NO se exporta: la hace el panel con las reglas, igual que el SQL.
catalogo = [dict(marca=r['marca'], categoria=r['categoria'], nombre=r['nombre'],
                 precio=r['precio_actual'], clasificacion_web=r['clasificacion_web'] or '')
            for r in con.execute('SELECT * FROM catalogo ORDER BY rowid')]
reglas = [dict(r) for r in con.execute(
    'SELECT categoria, prioridad, motivo, campo, patron FROM reglas_clasificacion ORDER BY rowid')]
datos = {'catalogo': catalogo, 'reglas': reglas, 'inditex': INDITEX}

# ---------------------------------------------------------------------------
# Comprobación con Node: el motor JS tiene que dar lo mismo que el SQL
# ---------------------------------------------------------------------------
esperado_motivo = [r[0] for r in con.execute('SELECT motivo FROM catalogo ORDER BY rowid')]
esperado_resumen = {(r['categoria'], r['marca']): dict(r) for r in con.execute('SELECT * FROM v_resumen_precios')}
esperado_solape = {(r['categoria'], r['marca_a'], r['marca_b']): r['solape_pct']
                   for r in con.execute('SELECT * FROM v_solape_pares')}
con.close()

prueba = r"""
const C = require(process.argv[2]);
const D = JSON.parse(require('fs').readFileSync(process.argv[3], 'utf8'));
const R = C.prepararReglas(D.reglas);
const motivos = D.catalogo.map(f => C.clasificar(f, R));
const precios = {};
D.catalogo.forEach((f, i) => {
  if (motivos[i] !== '7_basica' || f.precio == null) return;
  const k = f.categoria + '|' + f.marca; (precios[k] = precios[k] || []).push(f.precio);
});
const resumen = {}, solape = {};
Object.keys(precios).forEach(k => { resumen[k] = C.resumen(precios[k]); });
const marcas = [...new Set(D.catalogo.map(f => f.marca))].sort();
for (const [cat, anchos] of [['camiseta', [5, 4]], ['vaquero', [10, 8]]])
  for (let i = 0; i < marcas.length; i++) for (let j = i + 1; j < marcas.length; j++)
    for (const w of anchos)
      solape[[cat, marcas[i], marcas[j], w].join('|')] =
        C.solape(precios[cat + '|' + marcas[i]], precios[cat + '|' + marcas[j]], w);
const hueco = {};
for (const cat of ['camiseta', 'vaquero']) {
  const lo = resumen[cat + '|Zara'].p75, hi = resumen[cat + '|Massimo Dutti'].p25;
  marcas.forEach(m => { hueco[cat + '|' + m] = C.enHueco(precios[cat + '|' + m], lo, hi); });
}
console.log(JSON.stringify({ motivos, resumen, solape, hueco }));
"""

node = shutil.which('node')
if node is None:
    raise SystemExit('Hace falta Node.js para comprobar el panel contra el SQL.')
with tempfile.TemporaryDirectory() as tmp:
    ruta_datos = os.path.join(tmp, 'datos.json')
    ruta_prueba = os.path.join(tmp, 'prueba.js')
    with open(ruta_datos, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False)
    with open(ruta_prueba, 'w', encoding='utf-8') as f:
        f.write(prueba)
    salida = subprocess.run([node, ruta_prueba, os.path.join(PANEL, 'calc.js'), ruta_datos],
                            capture_output=True, text=True, check=True).stdout
js = json.loads(salida)

errores = []
# 1. Clasificación fila a fila
dif = sum(a != b for a, b in zip(js['motivos'], esperado_motivo))
if dif:
    errores.append(f'{dif} filas clasificadas distinto que en SQL')
# 2. Resumen de precios
for (cat, marca), e in esperado_resumen.items():
    r = js['resumen'][f'{cat}|{marca}']
    for campo in ['n', 'minimo', 'p25', 'mediana', 'p75', 'maximo', 'media']:
        if abs(r[campo] - e[campo]) > 1e-9:
            errores.append(f'{cat} {marca} {campo}: JS {r[campo]} / SQL {e[campo]}')
# 3. Solapamiento (tramos principales) contra la vista; los pares sin tramos comunes valen 0
marcas = sorted({f['marca'] for f in catalogo})
for cat, w in [('camiseta', 5), ('vaquero', 10)]:
    for a, b in itertools.combinations(marcas, 2):
        v = js['solape'][f'{cat}|{a}|{b}|{w}']
        e = esperado_solape.get((cat, a, b), 0)
        if v != e:
            errores.append(f'solape {cat} {a}–{b}: JS {v} / SQL {e}')
# 4. Robustez (4 € / 8 €) contra la tabla validada de CLAUDE.md
robustez = {('Lefties', 'Primark'): (72, 82), ('H&M', 'Zara'): (60, 86), ('H&M', 'Primark'): (31, 12),
            ('H&M', 'Lefties'): (12, 7), ('Lefties', 'Zara'): (8, 4), ('Massimo Dutti', 'Zara'): (2, 3)}
for (a, b), (vc, vv) in robustez.items():
    if (js['solape'][f'camiseta|{a}|{b}|4'], js['solape'][f'vaquero|{a}|{b}|8']) != (vc, vv):
        errores.append(f'robustez {a}–{b} no coincide')
# 5. Hueco contra output/tablas/hueco_escalera.csv
import csv
with open(os.path.join(BASE, 'output', 'tablas', 'hueco_escalera.csv'), encoding='utf-8') as f:
    for r in csv.DictReader(f):
        h = js['hueco'][f"{r['categoria']}|{r['marca']}"]
        if (h['enHueco'], h['pct']) != (int(r['n_hueco']), int(r['pct_hueco'])):
            errores.append(f"hueco {r['categoria']} {r['marca']} no coincide")

if errores:
    raise SystemExit('El panel NO coincide con el SQL:\n  ' + '\n  '.join(errores))
print('Comprobación con Node: clasificación, resumen, solapamiento, robustez y hueco coinciden con el SQL.')

# ---------------------------------------------------------------------------
# Página
# ---------------------------------------------------------------------------
with open(os.path.join(PANEL, 'plantilla.html'), encoding='utf-8') as f:
    plantilla = f.read()
with open(os.path.join(PANEL, 'calc.js'), encoding='utf-8') as f:
    calc = f.read()
# '</' dentro de un <script> cerraría la etiqueta antes de tiempo: se escapa.
json_datos = json.dumps(datos, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
pagina = plantilla.replace('/*__CALC__*/', calc).replace('/*__DATOS__*/', json_datos)
os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
with open(SALIDA, 'w', encoding='utf-8') as f:
    f.write(pagina)
print('Panel guardado en', os.path.relpath(SALIDA, BASE), f'({len(pagina) // 1024} KB)')
