import json, csv, re, sys
import os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(BASE, 'data', 'raw') + '/'
FECHA = '2026-10-10'
rows = []
def add(marca, cat, nombre, pa, po, ref, clasif, ncol, url):
    rows.append(dict(marca=marca, categoria=cat, nombre=nombre.strip(), precio_actual=pa, precio_original=po,
                     referencia_modelo=ref, clasificacion_web=clasif, n_colores=ncol, url=url, fecha_recogida=FECHA))
def num(x):
    x = (x or '').strip()
    return float(x) if x else ''
def psv(f, ncampos=None):
    out=[]
    for l in open(R+f, encoding='utf-8'):
        l=l.rstrip('\n')
        if not l.strip(): continue
        if ncampos:
            # el nombre puede contener '|': partimos desde la derecha
            out.append(l.rsplit('|', ncampos-1))
        else:
            out.append(l.split('|'))
    return out

# ZARA
for r in json.load(open(R+'zara_camiseta.json', encoding='utf-8')):
    add('Zara','camiseta',r[0],r[1],r[2] if r[2] else '',r[4],r[5]+' / '+r[6],r[8],'https://www.zara.com/es/es/'+r[7])
for f in psv('zara_vaquero.psv'):
    add('Zara','vaquero',f[0],num(f[1]),num(f[2]),f[3],f[4]+' / '+f[5],int(f[6]),'https://www.zara.com/es/es/'+f[7])
# LEFTIES  (nombre|precio|orig|ref|familia|subfamilia|ncolores|slug|n_tarjetas)
for fn,cat in [('lefties_camiseta.psv','camiseta'),('lefties_vaquero.psv','vaquero')]:
    for f in psv(fn):
        add('Lefties',cat,f[0],num(f[1]),num(f[2]),f[3],f[4]+' / '+f[5],int(f[6]),'lefties.com/es (slug: '+f[7]+')')
# MASSIMO DUTTI (nombre|precio|slug)
for fn,cat in [('massimo_camiseta.psv','camiseta'),('massimo_vaquero.psv','vaquero')]:
    for f in psv(fn):
        ref = re.search(r'l(\d+)$', f[2]).group(1)
        add('Massimo Dutti',cat,f[0],num(f[1]),'',ref,'','', 'https://www.massimodutti.com/es/'+f[2])
# H&M (nombre|precio|orig|modelo7|categoria|n_articulos)
for fn,cat in [('hm_camiseta.psv','camiseta'),('hm_vaquero.psv','vaquero')]:
    for f in psv(fn):
        clas = f[4].replace('j_','ladies_jeans_') if f[4].startswith('j') else f[4]
        if clas=='j': clas='ladies_jeans'
        add('H&M',cat,f[0],num(f[1]),num(f[2]),f[3],clas,int(f[5]),'')
# PRIMARK camisetas (nombre|precio|colores|modelo9|n_var|n_disp|slug)
def nombre_slug(slug):
    s = re.sub(r'-\d{12}$','',slug)
    return s.replace('-',' ').capitalize()
for f in psv('primark_camiseta.psv',7):
    nombre = f[0] if f[0] else nombre_slug(f[6])
    add('Primark','camiseta',nombre,num(f[1]),'',f[3],'',int(f[2] or f[4]),'https://www.primark.com/es-es/p/'+f[6])
# PRIMARK vaqueros: variantes por color -> modelo (9 primeros dígitos)
mods = {}
for f in psv('primark_vaquero_variantes.psv',5):
    slug=f[4]; code=re.search(r'(\d{12})$',slug).group(1); k=code[:9]
    nombre = f[0] if not f[0].startswith('Valor ic') else nombre_slug(slug)
    if k not in mods:
        mods[k]=dict(nombre=nombre, p=num(f[1]), col=int(f[2] or 1), n=1, slug=slug)
    else:
        mods[k]['n']+=1; mods[k]['p']=min(mods[k]['p'], num(f[1]))
for k,m in mods.items():
    add('Primark','vaquero',m['nombre'],m['p'],'',k,'',m['col'],'https://www.primark.com/es-es/p/'+m['slug'])

out=os.path.join(BASE, 'data', 'moda_catalogo_2026-10-10.csv')
with open(out,'w',newline='',encoding='utf-8') as fh:
    w=csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
from collections import Counter
c=Counter((r['marca'],r['categoria']) for r in rows)
for k in sorted(c): print(k, c[k])
print('total', len(rows))
print('sin precio', sum(1 for r in rows if r['precio_actual']==''))
print('con precio original', sum(1 for r in rows if r['precio_original']!=''))
