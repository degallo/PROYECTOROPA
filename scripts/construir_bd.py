"""
Reconstruye la base de datos desde los CSV aplicando, en orden, los SQL de la carpeta sql/.

Uso:
    python scripts/construir_bd.py                  # 16 marcas  → data/moda.db
    python scripts/construir_bd.py --solo-5-marcas  # 5 marcas   → data/moda_5marcas.db

Siempre se construyen y comprueban las DOS versiones:
  · data/moda_5marcas.db: solo el CSV original. Tiene que reproducir EXACTAMENTE las
    cifras validadas de CLAUDE.md (sección 6). Es la prueba de que la ampliación no ha
    roto nada.
  · data/moda.db: los dos CSV (original + ampliación). Además se comprueba que ninguna
    fila de las 5 marcas originales cambia de clasificación al cargar las nuevas (las
    reglas nuevas no pueden "pisar" a las antiguas).
Si alguna comprobación falla, el script se para con un error que dice qué no cuadra.
"""
import csv, os, sqlite3, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_ORIGINAL = os.path.join(BASE, 'data', 'moda_catalogo_2026-10-10.csv')
CSV_AMPLIACION = os.path.join(BASE, 'data', 'moda_catalogo_ampliacion_2026-10-10.csv')
DB_16 = os.path.join(BASE, 'data', 'moda.db')
DB_5 = os.path.join(BASE, 'data', 'moda_5marcas.db')
SQL = os.path.join(BASE, 'sql')

# Cifras validadas con Javi (CLAUDE.md, sección 6) para las 5 marcas originales.
# (categoria, marca): (n, p25, mediana, p75, media)
ESPERADO_RESUMEN = {
    ('camiseta', 'Primark'): (23, 4.50, 7.00, 8.00, 6.50),
    ('camiseta', 'Lefties'): (9, 7.99, 7.99, 7.99, 8.10),
    ('camiseta', 'H&M'): (87, 9.99, 14.99, 19.99, 16.90),
    ('camiseta', 'Zara'): (50, 12.95, 15.95, 17.95, 16.39),
    ('camiseta', 'Massimo Dutti'): (14, 29.95, 29.95, 39.95, 33.52),
    ('vaquero', 'Primark'): (45, 14.00, 18.00, 18.00, 17.20),
    ('vaquero', 'Lefties'): (28, 17.99, 19.99, 19.99, 19.24),
    ('vaquero', 'H&M'): (289, 29.99, 34.99, 39.99, 36.38),
    ('vaquero', 'Zara'): (101, 29.95, 35.95, 39.95, 34.41),
    ('vaquero', 'Massimo Dutti'): (32, 49.95, 59.95, 59.95, 56.51),
}
# (categoria, marca_a, marca_b): % de solapamiento por tramos (orden alfabético de la pareja)
ESPERADO_SOLAPE = {
    ('camiseta', 'Lefties', 'Primark'): 52, ('camiseta', 'H&M', 'Zara'): 47,
    ('camiseta', 'H&M', 'Primark'): 35, ('camiseta', 'H&M', 'Lefties'): 31,
    ('camiseta', 'Lefties', 'Zara'): 8, ('camiseta', 'Massimo Dutti', 'Zara'): 2,
    ('vaquero', 'Lefties', 'Primark'): 97, ('vaquero', 'H&M', 'Zara'): 87,
    ('vaquero', 'H&M', 'Primark'): 20, ('vaquero', 'H&M', 'Lefties'): 17,
    ('vaquero', 'Lefties', 'Zara'): 14, ('vaquero', 'Massimo Dutti', 'Zara'): 5,
}
MARCAS_ORIGINALES = ('Primark', 'Lefties', 'H&M', 'Zara', 'Massimo Dutti')


def leer_csv(ruta):
    with open(ruta, encoding='utf-8') as f:
        return [(r['marca'], r['categoria'], r['nombre'],
                 float(r['precio_actual']) if r['precio_actual'] else None,
                 r['precio_original'] or None, r['referencia_modelo'], r['clasificacion_web'],
                 int(r['n_colores']) if r['n_colores'] else None, r['url'], r['fecha_recogida'])
                for r in csv.DictReader(f)]


def construir(db, csvs):
    if os.path.exists(db):
        os.remove(db)
    con = sqlite3.connect(db)
    con.executescript(open(os.path.join(SQL, '00_crear_tabla.sql'), encoding='utf-8').read())
    for ruta in csvs:
        con.executemany('INSERT INTO catalogo VALUES (?,?,?,?,?,?,?,?,?,?)', leer_csv(ruta))
    for nombre in ['02_limpieza.sql', '03_reglas_clasificacion.sql', '04_clasificar.sql',
                   '05_resumen_precios.sql', '06_solapamiento.sql']:
        con.executescript(open(os.path.join(SQL, nombre), encoding='utf-8').read())
    con.commit()
    return con


def comprobar_5_marcas(con, etiqueta):
    """Las 5 marcas originales tienen que dar las cifras validadas, estén solas o con las 11 nuevas."""
    errores = []
    for (cat, marca), esp in ESPERADO_RESUMEN.items():
        fila = con.execute('SELECT n, p25, mediana, p75, media FROM v_resumen_precios '
                           'WHERE categoria = ? AND marca = ?', (cat, marca)).fetchone()
        if fila is None or any(abs(a - b) > 0.005 for a, b in zip(fila, esp)):
            errores.append(f'resumen {cat} {marca}: {fila} ≠ {esp}')
    for (cat, a, b), esp in ESPERADO_SOLAPE.items():
        fila = con.execute('SELECT solape_pct FROM v_solape_pares WHERE categoria = ? AND marca_a = ? '
                           'AND marca_b = ?', (cat, a, b)).fetchone()
        if fila is None or fila[0] != esp:
            errores.append(f'solape {cat} {a}–{b}: {fila} ≠ {esp}')
    if errores:
        sys.exit(f'✗ [{etiqueta}] Las 5 marcas originales NO cuadran con CLAUDE.md:\n  ' + '\n  '.join(errores))
    print(f'✓ [{etiqueta}] Las 5 marcas originales reproducen exactamente CLAUDE.md §6 '
          f'({len(ESPERADO_RESUMEN)} filas de resumen y {len(ESPERADO_SOLAPE)} parejas).')


def main():
    solo_5 = '--solo-5-marcas' in sys.argv

    con5 = construir(DB_5, [CSV_ORIGINAL])
    n5 = con5.execute('SELECT COUNT(*) FROM catalogo').fetchone()[0]
    assert n5 == 1211, f'La versión de 5 marcas tiene {n5} filas (esperado 1.211)'
    comprobar_5_marcas(con5, '5 marcas')
    if solo_5:
        con5.close()
        print('Base de 5 marcas creada en', DB_5)
        return

    con = construir(DB_16, [CSV_ORIGINAL, CSV_AMPLIACION])
    n = con.execute('SELECT COUNT(*) FROM catalogo').fetchone()[0]
    assert n == 1697, f'La versión de 16 marcas tiene {n} filas (esperado 1.697)'
    print(f'✓ [16 marcas] {n} filas cargadas (1.211 + 486).')
    comprobar_5_marcas(con, '16 marcas')

    # Ninguna fila de las 5 marcas originales puede cambiar de motivo entre las dos bases.
    con.execute('ATTACH DATABASE ? AS b5', (DB_5,))
    cambios = con.execute("""
        SELECT c.marca, c.categoria, c.nombre, o.motivo, c.motivo
        FROM catalogo AS c
        JOIN b5.catalogo AS o
          ON o.marca = c.marca AND o.categoria = c.categoria AND o.referencia_modelo = c.referencia_modelo
         AND o.nombre = c.nombre
        WHERE c.motivo <> o.motivo""").fetchall()
    if cambios:
        sys.exit('✗ Reglas nuevas que cambian filas originales:\n  ' + '\n  '.join(map(str, cambios)))
    print('✓ [16 marcas] Ninguna fila de las 5 marcas originales cambia de clasificación.')

    # Toda marca sin fila en la tabla `marcas` se quedaría sin grupo en v_resumen_precios.
    sin_grupo = con.execute('SELECT DISTINCT marca FROM catalogo WHERE marca NOT IN (SELECT marca FROM marcas)').fetchall()
    assert not sin_grupo, f'Marcas sin grupo en la tabla marcas: {sin_grupo}'

    # Básicas + excluidas = filas, por marca y prenda (comprobación 4 de las instrucciones).
    descuadre = con.execute("""
        SELECT marca, categoria FROM catalogo GROUP BY marca, categoria
        HAVING SUM(motivo = '7_basica') + SUM(motivo <> '7_basica') <> COUNT(*)""").fetchall()
    assert not descuadre, f'Básicas + excluidas ≠ total en {descuadre}'

    print('\nBásicas / total por prenda y marca (16 marcas):')
    for r in con.execute("""SELECT categoria, m.grupo, c.marca, SUM(motivo = '7_basica'), COUNT(*)
                            FROM catalogo AS c JOIN marcas AS m USING (marca)
                            GROUP BY categoria, c.marca ORDER BY categoria, m.grupo, c.marca"""):
        print('   {:<9} {:<17} {:<17} {:>4} / {:>4}'.format(*r))
    con.close()
    print('\nBases creadas en', DB_16, 'y', DB_5)


if __name__ == '__main__':
    main()
