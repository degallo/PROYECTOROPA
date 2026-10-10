"""
Convierte los ficheros brutos de data/raw_ampliacion/ (11 marcas añadidas) en
data/moda_catalogo_ampliacion_2026-10-10.csv, con el MISMO esquema que el CSV original.
Uso:  python scripts/unificar_raw_ampliacion.py
Formato bruto: {"nota": ..., "camiseta": [[nombre, precio_actual, precio_original|"", referencia, n_colores, slug]], "vaquero": [...]}
(Mango lleva además la familia web en la posición 4.)
"""
import csv, json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, 'data', 'raw_ampliacion')
OUT = os.path.join(BASE, 'data', 'moda_catalogo_ampliacion_2026-10-10.csv')
FECHA = '2026-10-10'

MARCAS = {  # fichero: (marca, url base, cómo sacar clasificacion_web del slug)
    'mango.json':           ('Mango',            'https://shop.mango.com/es/es/p/mujer/', 'mango'),
    'springfield.json':     ('Springfield',      'https://myspringfield.com/es/es/mujer/', 'dir'),
    'cortefiel.json':       ('Cortefiel',        'https://cortefiel.com/es/es/mujer/', 'dir'),
    'pedrodelhierro.json':  ('Pedro del Hierro', 'https://pedrodelhierro.com/es/es/mujer/', 'dir'),
    'womensecret.json':     ("Women'secret",     'https://womensecret.com/es/es/', 'dir'),
    'desigual.json':        ('Desigual',         'https://www.desigual.com', None),
    'adolfodominguez.json': ('Adolfo Domínguez', 'https://www.adolfodominguez.com', None),
    'bimbaylola.json':      ('Bimba y Lola',     'https://www.bimbaylola.com/es_es/', None),
    'scalpers.json':        ('Scalpers',         'https://scalperscompany.com/es/products/', None),
    'elganso.json':         ('El Ganso',         'https://www.elganso.com/es/', None),
    'silbon.json':          ('Silbon',           'https://www.silbonshop.com/products/', None),
}

filas, vistos, resumen = [], set(), []
for fichero, (marca, base, modo) in MARCAS.items():
    d = json.load(open(os.path.join(RAW, fichero), encoding='utf-8'))
    for categoria in ('camiseta', 'vaquero'):
        n_in = n_dup = 0
        for r in d.get(categoria, []):
            n_in += 1
            if modo == 'mango':
                nombre, pa, po, ref, _familia, ncol, slug = r
            else:
                nombre, pa, po, ref, ncol, slug = r
            clave = (marca, categoria, str(ref))
            if clave in vistos:
                n_dup += 1
                continue
            vistos.add(clave)
            if modo == 'mango':
                clas = '/'.join(slug.split('/')[:-2])          # p. ej. camisetas/manga-larga, vaqueros/premama
            elif modo == 'dir':
                clas = '/'.join(slug.split('/')[:-2])          # p. ej. camisetas-y-tops, mujer/dormir-y-homewear/pijamas
            else:
                clas = ''
            url = (base + slug.lstrip('/')) if slug else ''
            if marca in ('El Ganso',) and slug and not slug.endswith('.html'):
                url += '.html'
            filas.append([marca, categoria, ' '.join(str(nombre).split()), pa, po if po != '' else '',
                          ref, clas, ncol if ncol else '', url, FECHA])
        resumen.append((marca, categoria, n_in, n_dup))

with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['marca', 'categoria', 'nombre', 'precio_actual', 'precio_original', 'referencia_modelo',
                'clasificacion_web', 'n_colores', 'url', 'fecha_recogida'])
    w.writerows(filas)

print(f'{len(filas)} filas escritas en {OUT}')
for m, c, n, dup in resumen:
    print(f'  {m:18} {c:9} {n:4} brutas  {dup:3} duplicadas')
