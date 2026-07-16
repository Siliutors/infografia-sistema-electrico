# -*- coding: utf-8 -*-
"""
Actualiza los datos de la infografía del sistema eléctrico español y la regenera.

Descarga:
  1. ESIOS (REE): UnidadesFisicas (81), UnidadesProgramacion (82), SujetosMercado (83)
  2. Ministerio (MITECO): exportación CSV del registro ELECTRA (RAIPRE)
y después ejecuta build.py, que reescribe index.html.

Uso:  python actualizar_datos.py
Requisitos: Python 3.8+ (solo librería estándar).
"""
import datetime, io, json, os, re, subprocess, sys, urllib.parse, urllib.request, zipfile

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
    with urllib.request.urlopen(req, timeout=timeout) as r:
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

# ---- 3. fecha y regeneración ----
fecha = datetime.datetime.now().strftime('%d-%m-%Y %H:%M')
open('fecha_datos.txt', 'w', encoding='utf-8').write(fecha)
print(f'Fecha de datos: {fecha}')
print('Regenerando la infografía ...')
subprocess.run([sys.executable, '-X', 'utf8', os.path.join(BASE, 'build.py')], check=True)
print('Listo. Abra index.html (en esta misma carpeta).')
