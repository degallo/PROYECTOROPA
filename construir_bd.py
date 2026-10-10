"""
Reconstruye data/moda.db desde el CSV original aplicando, en orden, los SQL de la carpeta sql/.
Uso:  python scripts/construir_bd.py
Al final imprime las comprobaciones que deben coincidir con la tabla de CLAUDE.md (sección 6).
"""
import csv, os, sqlite3

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(BASE, 'data', 'moda_catalogo_2026-10-10.csv')
DB = os.path.join(BASE, 'data', 'moda.db')
SQL = os.path.join(BASE, 'sql')

if os.path.exists(DB):
    os.remove(DB)
con = sqlite3.connect(DB)
con.executescript(open(os.path.join(SQL, '00_crear_tabla.sql'), encoding='utf-8').read())
with open(CSV, encoding='utf-8') as f:
    filas = []
    for r in csv.DictReader(f):
        filas.append((r['marca'], r['categoria'], r['nombre'],
                      float(r['precio_actual']) if r['precio_actual'] else None,
                      r['precio_original'] or None, r['referencia_modelo'], r['clasificacion_web'],
                      int(r['n_colores']) if r['n_colores'] else None, r['url'], r['fecha_recogida']))
con.executemany('INSERT INTO catalogo VALUES (?,?,?,?,?,?,?,?,?,?)', filas)

for nombre in ['02_limpieza.sql', '03_reglas_clasificacion.sql', '04_clasificar.sql',
               '05_resumen_precios.sql', '06_solapamiento.sql']:
    con.executescript(open(os.path.join(SQL, nombre), encoding='utf-8').read())
con.commit()

print('Filas totales:', con.execute('SELECT COUNT(*) FROM catalogo').fetchone()[0], '(esperado 1211)')
print('\nBásicas por prenda y marca:')
for r in con.execute("""SELECT categoria, marca, SUM(motivo='7_basica'), COUNT(*)
                        FROM catalogo GROUP BY categoria, marca ORDER BY categoria, marca"""):
    print('  ', r)
print('\nv_resumen_precios:')
for r in con.execute('SELECT categoria, marca, n, p25, mediana, p75, media FROM v_resumen_precios ORDER BY categoria, mediana'):
    print('  ', r)
print('\nv_solape_pares (>=20 %):')
for r in con.execute('SELECT categoria, pareja, solape_pct FROM v_solape_pares WHERE solape_pct >= 20 ORDER BY categoria, solape_pct DESC'):
    print('  ', r)
con.close()
print('\nBase creada en', DB)
