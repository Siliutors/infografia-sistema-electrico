# -*- coding: utf-8 -*-
"""
Actualiza los datos de la infografía del sistema eléctrico español y la regenera.

Descarga:
  1. ESIOS (REE): UnidadesFisicas (81), UnidadesProgramacion (82), SujetosMercado (83)
  2. Ministerio (MITECO): exportación CSV del registro ELECTRA (RAIPRE)
  3. CNMC: nudos de transporte y subestaciones de distribución con su capacidad de acceso
     (servicios ArcGIS públicos que alimentan los mapas de capacidad de la CNMC)
  4. REE: fichero mensual de capacidad de acceso por nudo de la red de transporte (GRT generación)
y después ejecuta build.py, que reescribe index.html.

Uso:  python actualizar_datos.py
Requisitos: Python 3.8+ (solo librería estándar).
"""
import datetime, io, json, math, os, re, ssl, subprocess, sys, urllib.error, urllib.parse, urllib.request, zipfile

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
UA = {'User-Agent': 'Mozilla/5.0'}

# Token personal de ESIOS (OPCIONAL): las descargas usadas aquí son públicas y no lo requieren.
# Si en el futuro se usan endpoints que sí lo exigen, defínalo SOLO como variable de entorno
# (setx ESIOS_TOKEN "...") — nunca lo escriba en este archivo ni en ningún otro del repositorio.
ESIOS_TOKEN = os.environ.get('ESIOS_TOKEN', '')
if ESIOS_TOKEN:
    UA['x-api-key'] = ESIOS_TOKEN

def descarga(url, data=None, headers=None, timeout=180):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except urllib.error.URLError as e:
        # proxy corporativo con TLS interceptado (p. ej. contra arcgis.com):
        # reintenta sin verificación de certificado, como `curl -k`
        if not isinstance(getattr(e, 'reason', None), ssl.SSLCertVerificationError):
            raise
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.read()

# ---- 1. ESIOS ----
ESIOS = {81: 'uf.json', 82: 'up.json', 83: 'sm.json'}
CLAVES = {81: 'UnidadesFisicas', 82: 'UnidadesProgramacion', 83: 'SujetosMercado'}
for aid, destino in ESIOS.items():
    print(f'Descargando ESIOS archivo {aid} -> {destino} ...')
    raw = descarga(f'https://api.esios.ree.es/archives/{aid}/download?locale=es')
    datos = json.loads(raw.decode('utf-8'))
    n = len(datos[CLAVES[aid]])
    open(destino, 'wb').write(raw)
    print(f'  OK: {n} registros')

# ---- 2. ELECTRA (RAIPRE) ----
print('Descargando registro ELECTRA (RAIPRE) del Ministerio ...')
URL_ELECTRA = 'https://energia.serviciosmin.gob.es/Electra/BuscarDatos.aspx'
pagina = descarga(URL_ELECTRA).decode('utf-8', errors='replace')
def campo(nombre):
    m = re.search('name="' + re.escape(nombre) + '" id="[^"]*" value="([^"]*)"', pagina)
    return m.group(1) if m else ''
form = {
    '__VIEWSTATE': campo('__VIEWSTATE'),
    '__VIEWSTATEGENERATOR': campo('__VIEWSTATEGENERATOR'),
    '__EVENTVALIDATION': campo('__EVENTVALIDATION'),
    'ctl00$ContentPlaceHolder1$mButDescargaCSV': 'CSV',
}
zbytes = descarga(URL_ELECTRA, data=urllib.parse.urlencode(form).encode(),
                  headers={'Content-Type': 'application/x-www-form-urlencoded'}, timeout=300)
with zipfile.ZipFile(io.BytesIO(zbytes)) as z:
    nombre = z.namelist()[0]
    open('ElectraExp.csv', 'wb').write(z.read(nombre))
filas = open('ElectraExp.csv', 'rb').read().count(b'\n')
print(f'  OK: ~{filas} filas del registro')

# ---- 3. CNMC: nudos y capacidad de acceso (servicios ArcGIS de sus mapas de capacidad) ----
CNMC = 'https://services9.arcgis.com/F9FmuOlj5xjEjPRZ/arcgis/rest/services'

def arcgis(servicio, capa):
    """Descarga todos los registros de una capa ArcGIS (paginando con resultOffset)."""
    feats, offset = [], 0
    while True:
        q = urllib.parse.urlencode({'where': '1=1', 'outFields': '*', 'f': 'json',
                                    'resultOffset': offset})
        d = json.loads(descarga(f'{CNMC}/{servicio}/FeatureServer/{capa}/query?{q}'))
        if 'error' in d:
            raise RuntimeError(f'ArcGIS {servicio}: {d["error"]}')
        feats += d['features']
        if not d.get('exceededTransferLimit'):
            return feats
        offset = len(feats)

def lat_lon(g):  # Web Mercator (EPSG:3857) -> grados
    R = 6378137.0
    return (round(math.degrees(2 * math.atan(math.exp(g['y'] / R)) - math.pi / 2), 5),
            round(math.degrees(g['x'] / R), 5))

print('Descargando CNMC: nudos de transporte y distribución (mapas de capacidad de acceso) ...')
per = arcgis('Capacidad_Periodo', 10)
periodo = f"{per[0]['attributes'].get('MES', '')} {per[0]['attributes'].get('ANIO', '')}".strip() if per else ''
nt = []
for f in arcgis('Generacion_en_Transporte', 0):
    a, (la, lo) = f['attributes'], lat_lon(f['geometry'])
    nt.append(dict(n=(a['SUBESTACION'] or '').strip(), kv=a['NIVEL_TENSION'], lat=la, lon=lo,
                   prov=a['PROVINCIA'], muni=a['MUNICIPIO'],
                   ocu=a['CAP_OCUPADA'], dmpe=a['CAP_DISPONIBLE_MPE'], dmges=a['CAP_DISPONIBLE_MGES'],
                   ampe=a['CAP_ALM_DISPONIBLE_MPE'], amges=a['CAP_ALM_DISPONIBLE_MGES'],
                   tram=a['CAP_ADMITIDA_NO_RESUELTA'], plib=a['POSICIONES_LIBRES'],
                   pocu=a['POSICIONES_OCUPADAS']))
json.dump({'periodo': periodo, 'nudos': nt},
          open('nudos_transporte.json', 'w', encoding='utf-8'), ensure_ascii=False)
print(f'  OK: {len(nt)} nudos de transporte (datos de {periodo})')
nd = []
for f in arcgis('Generacion_en_Distribucion', 4):
    a, (la, lo) = f['attributes'], lat_lon(f['geometry'])
    nudo = (a.get('NUDO_AFECCION_RDT') or '').strip()
    if nudo in ('-', '0'):
        nudo = ''
    nd.append(dict(n=(a['SUBESTACION'] or '').strip(), kv=a['NIVEL_TENSION'], lat=la, lon=lo,
                   ges=(a.get('DESCRIPCION') or '').strip(), muni=a['MUNICIPIO'], nudo=nudo))
json.dump({'periodo': periodo, 'subestaciones': nd},
          open('nudos_distribucion.json', 'w', encoding='utf-8'), ensure_ascii=False)
print(f'  OK: {len(nd)} subestaciones de distribución (>1 kV) con su nudo de afección en transporte')

# ---- 4. REE: fichero mensual de capacidad de acceso por nudo (GRT generación) ----
# Se publica dentro de los 5 primeros días de cada mes; se busca el más reciente.
print('Descargando fichero mensual de capacidad por nudo de REE ...')
ree_csv = ree_fecha = None
mes1 = datetime.date.today().replace(day=1)
for _ in range(6):
    for dia in range(1, 6):
        url = (f'https://www.ree.es/sites/default/files/12_CLIENTES/Documentos/'
               f'{mes1.year}_{mes1.month:02d}_{dia:02d}_GRT_generacion.csv')
        try:
            ree_csv, ree_fecha = descarga(url), f'{dia:02d}-{mes1.month:02d}-{mes1.year}'
            break
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
    if ree_csv:
        break
    mes1 = (mes1 - datetime.timedelta(days=1)).replace(day=1)
if ree_csv:
    open('ree_capacidad.csv', 'wb').write(ree_csv)
    open('ree_capacidad_fecha.txt', 'w', encoding='utf-8').write(ree_fecha)
    print(f'  OK: fichero de {ree_fecha} ({len(ree_csv) // 1024} kB)')
else:
    print('  AVISO: no se encontró fichero de REE en los últimos 6 meses (se conserva el anterior si existe)')

# ---- 5. fecha y regeneración ----
fecha = datetime.datetime.now().strftime('%d-%m-%Y %H:%M')
open('fecha_datos.txt', 'w', encoding='utf-8').write(fecha)
print(f'Fecha de datos: {fecha}')
print('Regenerando la infografía ...')
subprocess.run([sys.executable, '-X', 'utf8', os.path.join(BASE, 'build.py')], check=True)
print('Listo. Abra index.html (en esta misma carpeta).')
