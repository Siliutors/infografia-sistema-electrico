# -*- coding: utf-8 -*-
"""Genera la infografía de UPs del sistema eléctrico español (fuentes: ESIOS/REE, MITECO)."""
import json, math, re, sys, os, csv, unicodedata, collections, bisect, datetime
sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

D = lambda f, k: json.load(open(f, encoding='utf-8'))[k]
UP = D('up.json', 'UnidadesProgramacion')
UF = D('uf.json', 'UnidadesFisicas')
SM = D('sm.json', 'SujetosMercado')

# fecha de los datos: fecha_datos.txt (escrita por actualizar_datos.py) o mtime de up.json
try:
    FECHA = open('fecha_datos.txt', encoding='utf-8').read().strip()
except OSError:
    FECHA = datetime.datetime.fromtimestamp(os.path.getmtime('up.json')).strftime('%d-%m-%Y')

def mw(s):
    try: return float(s.replace('.', '').replace(',', '.'))
    except: return 0.0

SM_NAME = {r['Código de sujeto'].strip(): r['Nombre'].strip() for r in SM}

# ---------- agrupación tecnológica (8 grupos, paleta validada) ----------
TECH_GROUPS = [
    ('Hidráulica y bombeo', '#2a78d6', '#3987e5'),
    ('Eólica',              '#1baf7a', '#199e70'),
    ('Solar fotovoltaica',  '#eda100', '#c98500'),
    ('Biomasa y otras renov.', '#008300', '#008300'),
    ('Nuclear',             '#4a3aa7', '#9085e9'),
    ('Solar térmica',       '#e34948', '#e66767'),
    ('Cogeneración y térmica', '#e87ba4', '#d55181'),
    ('Ciclo combinado',     '#eb6834', '#d95926'),
]
def tech_idx(t):
    t = (t or '').lower()
    if t == 'nuclear': return 4
    if any(k in t for k in ('hidráulica', 'bombeo', 'almacenamiento', 'fluyente', 'embalse', 'batería')): return 0
    if t.startswith('eólica'): return 1
    if t == 'solar fotovoltaica': return 2
    if t == 'solar térmica': return 5
    if t.startswith('ciclo combinado') or t == 'gas natural': return 7
    if any(k in t for k in ('cogeneración', 'derivados del petróleo', 'fuel', 'residual', 'hulla',
                            'minería', 'residuos', 'vapor')): return 6
    return 3  # biogás, biomasa, océano/geotérmica, híbridas, resto

GEN_TYPES = ('Generación', 'Unidades hibridas', 'Unidades de almacenamiento', 'Consumo bombeo')

# ---------- gacetero curado: código UP -> (lat, lon, emplazamiento, nudo, multi) ----------
# multi=True -> agrupación de varias UF: posición = zona aproximada (centroide ponderado por potencia)
G = {}
def g(codes, lat, lon, site, nudo, multi=False):
    for c in codes.split(): G[c] = (lat, lon, site, nudo, multi)

# Nuclear
g('COF1', 39.216, -1.050, 'C.N. Cofrentes (Valencia)', 'Cofrentes')
g('ALZ1 ALZ2', 39.807, -5.697, 'C.N. Almaraz (Cáceres)', 'Almaraz')
g('TRL1', 40.701, -2.622, 'C.N. Trillo (Guadalajara)', 'Trillo')
g('ASC1 ASC2', 41.200, 0.571, 'C.N. Ascó (Tarragona)', 'Ascó')
g('VAN2', 40.951, 0.866, 'C.N. Vandellòs II (Tarragona)', 'Vandellós')
# UGH hidráulicas (zona aproximada por centroide ponderado de sus UF)
g('DUER', 41.22, -6.60, 'Cuenca del Duero · Aldeadávila–Villarino (Salamanca/Zamora)', 'Aldeadávila', True)
g('DUEB', 41.26, -6.48, 'Villarino–Aldeadávila, bombeo (Salamanca)', 'Villarino', True)
g('TAJO', 39.75, -6.30, 'Cuenca del Tajo · Alcántara–Valdecañas (Cáceres)', 'J.M. Oriol', True)
g('TAJB', 39.72, -6.42, 'Cuenca del Tajo, bombeo (Cáceres)', 'J.M. Oriol', True)
g('SIL', 42.40, -7.45, 'Cuenca del Sil (Ourense/León)', 'Trives', True)
g('SILB', 42.43, -7.38, 'Cuenca del Sil, bombeo', 'Trives', True)
g('EBRFEN', 41.85, 0.62, 'Ebro–Pirineos · Mequinenza/Ribarroja/Pallars', 'Ribarroja', True)
g('EBRACC1', 42.20, 0.50, 'Pirineo aragonés-catalán (aprox.)', 'Sallente', True)
g('JUCA', 39.24, -0.95, 'Cuenca del Júcar · Cortes de Pallás (Valencia)', 'Cofrentes', True)
g('GDLQ', 37.95, -4.90, 'Cuenca del Guadalquivir (aprox.)', 'Guillena', True)
g('GDNA', 38.80, -6.00, 'Cuenca del Guadiana (aprox.)', 'San Serván', True)
g('SBEU', 42.30, -7.10, 'Sil–Bibey–Eume (Ourense/A Coruña)', 'Trives', True)
g('HCHI', 43.20, -6.75, 'Occidente asturiano · Salime–Navia', 'Soto de Ribera', True)
g('UFMI', 42.65, -7.71, 'Miño · Belesar (Lugo)', 'Belesar', True)
g('UFTA', 40.30, -2.90, 'Alto Tajo · Bolarque–Entrepeñas (Guadalajara)', 'Bolarque', True)
g('UFGC', 42.90, -8.40, 'Galicia Costa (aprox.)', 'Mesón do Vento', True)
g('VIES', 43.15, -4.40, 'Nansa–Cantábrico (aprox.)', 'Penagos', True)
# Bombeo puro y baterías grandes
g('MUEL MUEB', 39.240, -0.900, 'C.H. Cortes–La Muela (Valencia)', 'Cofrentes')
g('SLTG SLTB', 42.510, 0.990, 'Sallente–Estany Gento (Lleida)', 'Sallente')
g('TJEG TJEB', 36.930, -4.770, 'Tajo de la Encantada (Málaga)', 'Tajo de la Encantada')
g('AGUG AGUB', 43.130, -3.990, 'C.H. Aguayo (Cantabria)', 'Aguayo')
g('MLTG MLTB', 42.550, 0.750, 'Moralets–Baserca (Huesca/Lleida)', 'Pont de Suert')
g('UFBG UFBB', 40.360, -2.830, 'C.H. Bolarque (Guadalajara)', 'Bolarque')
g('GUIG GUIB', 37.610, -6.050, 'C.H. Guillena (Sevilla)', 'Guillena')
# Ciclos combinados y térmicas
g('BES3 BES4 BES5', 41.423, 2.230, 'Besòs · Sant Adrià (Barcelona)', 'Besòs')
g('PBCN1 PBCN2', 41.335, 2.155, 'Port de Barcelona', 'Port de Barcelona')
g('CTN3 CTN4', 39.965, 0.020, 'C.T. Castellón (Grao)', 'La Plana')
g('SAGU1 SAGU2 SAGU3', 39.640, -0.232, 'C.C. Sagunto (Valencia)', 'Morvedre')
g('ARCOS1 ARCOS2 ARCOS3', 36.720, -5.810, 'Arcos de la Frontera (Cádiz)', 'Arcos')
g('ALG3', 36.190, -5.395, 'Bahía de Algeciras · San Roque (Cádiz)', 'Pinar del Rey')
g('SROQ1 SROQ2', 36.235, -5.385, 'C.T. San Roque (Cádiz)', 'Pinar del Rey')
g('CAMGI10 CAMGI20', 36.180, -5.440, 'Campo de Gibraltar · Los Barrios (Cádiz)', 'Pinar del Rey')
g('BRR1', 36.175, -5.470, 'C.T. Los Barrios (Cádiz)', 'Pinar del Rey')
g('PALOS1 PALOS2 PALOS3', 37.175, -6.905, 'C.C. Palos de la Frontera (Huelva)', 'Palos')
g('COL4', 37.220, -6.945, 'C.T. Cristóbal Colón (Huelva)', 'Palos')
g('ESC6', 37.567, -0.945, 'C.T.C.C. Escombreras (Cartagena)', 'El Fangal')
g('ESCCC1 ESCCC2 ESCCC3', 37.590, -0.960, 'CCGT Cartagena Energía · Escombreras', 'El Fangal')
g('CTGN1 CTGN2 CTGN3', 37.600, -0.975, 'C.C. Cartagena (Murcia)', 'El Fangal')
g('MALA1', 36.715, -4.470, 'C.C.C. Málaga', 'Málaga')
g('PVENT1 PVENT2', 40.955, 0.845, 'Plana del Vent · Vandellòs (Tarragona)', 'Vandellós')
g('TAPOWER', 41.105, 1.195, 'Tarragona Power (polígono petroquímico)', 'Tarragona')
g('ECT2 ECT3', 41.290, -0.320, 'C.C. Escatrón (Zaragoza)', 'Aragón')
g('CTNU', 41.225, -0.400, 'C.C. Castelnou (Teruel)', 'Aragón')
g('CTJON1 CTJON2 CTJON3', 42.170, -1.690, 'C.C. Castejón (Navarra)', 'Castejón')
g('ARRU1 ARRU2', 42.435, -2.240, 'C.C. Arrúbal (La Rioja)', 'Arrúbal')
g('AMBIETA', 43.245, -2.720, 'C.C. Amorebieta–Boroa (Bizkaia)', 'Boroa')
g('BAHIAB', 43.355, -3.080, 'Bahía de Bizkaia · Zierbena', 'Santurtzi')
g('STC4', 43.330, -3.030, 'C.T. Santurce 4 (Bizkaia)', 'Santurtzi')
g('SRI3 SRI4 SRI5', 43.310, -5.880, 'Soto de Ribera (Asturias)', 'Soto de Ribera')
g('PGR5', 43.440, -7.860, 'C.C. As Pontes (A Coruña)', 'As Pontes')
g('SBO3', 43.335, -8.510, 'C.C. Sabón · Arteixo (A Coruña)', 'Sabón')
g('ABO1 ABO2G', 43.555, -5.720, 'C.T. Aboño · Gijón (Asturias)', 'Aboño')
g('ACE3 ACE4', 39.940, -3.830, 'C.C. Aceca · Villaseca de la Sagra (Toledo)', 'Aceca')
g('REPPLL', 38.650, -4.050, 'Refinería Repsol Puertollano (C. Real)', 'Manzanares (aprox.)')
g('EPU50', 38.680, -4.100, 'ENCE Biomasa Puertollano (C. Real)', 'Manzanares (aprox.)')
# Fotovoltaicas y termosolares con emplazamiento conocido
g('FIBGEPI', 39.570, -5.750, 'FV Francisco Pizarro · Torrecillas de la Tiesa (Cáceres)', 'Almaraz')
g('FIBGENB', 38.350, -6.170, 'FV Núñez de Balboa · Usagre (Badajoz)', 'Bienvenida')
g('SIGMU', 38.050, -1.400, 'FV Mula (Murcia)', 'El Palmar')
g('FTASOL', 39.710, -6.280, 'FV Talasol · Talaván (Cáceres)', 'J.M. Oriol')
g('FIBGECR', 40.600, -6.530, 'FV Ciudad Rodrigo (Salamanca)', 'Aldeadávila (aprox.)')
g('FIBGEOR', 39.720, -6.850, 'FV Oriol · Alcántara (Cáceres)', 'J.M. Oriol')
g('GALPS65 GEXTRII GEXTIII', 38.620, -6.600, 'Extresol · Torre de Miguel Sesmero (Badajoz)', 'San Serván (aprox.)')
g('SMASOL1', 39.240, -3.250, 'Manchasol · Alcázar de San Juan (C. Real)', 'Manzanares (aprox.)')
g('STSOLB1 STSOLB2 STSOLB3 STSOLB6', 39.350, -5.450, 'Solaben · Logrosán (Cáceres)', 'Almaraz (aprox.)')
g('STSOLA1 STSOLA2', 37.950, -4.500, 'Solacor · El Carpio (Córdoba)', 'Guillena (aprox.)')
g('UPEBRO', 41.500, -0.800, 'Molinos del Ebro (Zaragoza, aprox.)', 'Magallón (aprox.)', True)

# ---------- red de transporte esquemática ----------
NODES = {  # nombre: (lat, lon, kv)
 'Argia (FR)': (43.32, -1.30, 400), 'Hernani': (43.26, -1.98, 400), 'Vitoria': (42.85, -2.67, 400),
 'Penagos': (43.33, -3.80, 400), 'Aguayo': (43.13, -3.99, 400), 'Soto de Ribera': (43.31, -5.88, 400),
 'As Pontes': (43.44, -7.86, 400), 'Mesón do Vento': (43.20, -8.25, 400), 'Sabón': (43.335, -8.51, 220),
 'Aboño': (43.555, -5.72, 220), 'Cartelle': (42.25, -8.02, 400), 'Lindoso (PT)': (41.87, -8.20, 400),
 'Trives': (42.35, -7.30, 400), 'Belesar': (42.65, -7.71, 220), 'Montearenas': (42.56, -6.55, 400),
 'La Mudarra': (41.78, -4.95, 400), 'Tordesillas': (41.50, -5.00, 400), 'Aldeadávila': (41.21, -6.62, 400),
 'Villarino': (41.27, -6.47, 400), 'Lagoaça (PT)': (41.12, -6.93, 400), 'Segovia': (40.90, -4.20, 400),
 'S.S. Reyes': (40.55, -3.62, 400), 'Loeches': (40.38, -3.42, 400), 'Morata': (40.23, -3.44, 400),
 'Aceca': (39.94, -3.83, 400), 'Trillo': (40.701, -2.622, 400), 'Bolarque': (40.36, -2.83, 220),
 'Castejón': (42.17, -1.69, 400), 'Arrúbal': (42.435, -2.24, 220), 'Magallón': (41.83, -1.45, 400),
 'Aragón': (41.29, -0.32, 400), 'Ascó': (41.20, 0.571, 400), 'Vandellós': (40.951, 0.866, 400),
 'Ribarroja': (41.30, 0.45, 220), 'Sallente': (42.51, 0.99, 400), 'Pont de Suert': (42.55, 0.75, 220),
 'Pierola': (41.53, 1.77, 400), 'Sentmenat': (41.62, 2.13, 400), 'Vic': (41.95, 2.28, 400),
 'Sta. Llogaia': (42.23, 2.93, 400), 'Baixas (FR)': (42.60, 2.80, 400), 'Besòs': (41.423, 2.23, 220),
 'Port de Barcelona': (41.335, 2.155, 220), 'Tarragona': (41.105, 1.195, 220),
 'Almaraz': (39.807, -5.697, 400), 'J.M. Oriol': (39.72, -6.88, 400), 'Cedillo': (39.65, -7.50, 400),
 'Falagueira (PT)': (39.60, -7.95, 400), 'San Serván': (38.86, -6.40, 400), 'Bienvenida': (38.30, -6.20, 400),
 'Brovales': (38.35, -6.65, 400), 'Alqueva (PT)': (38.30, -7.35, 400), 'Guillena': (37.61, -6.05, 400),
 'Palos': (37.18, -6.90, 400), 'P. Guzmán': (37.55, -7.25, 400), 'Tavira (PT)': (37.40, -7.75, 400),
 'Arcos': (36.72, -5.81, 400), 'Pinar del Rey': (36.28, -5.38, 400), 'Tarifa': (36.05, -5.65, 400),
 'Fardioua (MA)': (35.72, -5.55, 400), 'Tajo de la Encantada': (36.93, -4.77, 400),
 'Caparacena': (37.28, -3.68, 400), 'Málaga': (36.715, -4.47, 220), 'El Palmar': (37.93, -1.20, 400),
 'El Fangal': (37.59, -0.96, 400), 'Escombreras': (37.567, -0.945, 220), 'Rocamora': (38.15, -0.85, 400),
 'Cofrentes': (39.216, -1.050, 400), 'La Eliana': (39.57, -0.53, 400), 'Morvedre': (39.64, -0.232, 400),
 'La Plana': (39.97, 0.02, 400), 'Sta. Ponsa (Mallorca)': (39.51, 2.47, 250),
 'Boroa': (43.245, -2.72, 400), 'Santurtzi': (43.33, -3.03, 220), 'Manzanares': (38.95, -3.55, 400),
 # densificación de la malla
 'Boimente': (43.55, -7.55, 400), 'Lada': (43.28, -5.68, 400), 'Velilla': (42.83, -4.85, 400),
 'Vilecha': (42.56, -5.57, 400), 'La Robla': (42.80, -5.63, 220), 'Güeñes': (43.21, -3.09, 400),
 'Gatika': (43.36, -2.89, 400), 'Ichaso': (43.06, -2.10, 400), 'Muruarte': (42.62, -1.63, 400),
 'Peñalba': (41.49, 0.04, 400), 'Fuendetodos': (41.34, -0.96, 400), 'Mezquita': (40.77, -0.86, 400),
 'Morella': (40.62, -0.10, 400), 'Olmedilla': (39.60, -2.10, 400), 'Minglanilla': (39.53, -1.60, 400),
 'Romica': (39.05, -1.75, 400), 'Brazatortas': (38.65, -4.35, 400), 'Valdecaballeros': (39.24, -5.18, 400),
 'Baza': (37.55, -2.77, 400), 'Litoral': (36.97, -1.90, 400), 'Don Rodrigo': (37.20, -5.92, 400),
 'La Secuita': (41.22, 1.28, 400), 'Rubí': (41.49, 2.03, 400), 'Galapagar': (40.62, -4.03, 400),
 'Puertollano': (38.68, -4.10, 220),
}
L400 = [('Argia (FR)','Hernani'),('Hernani','Vitoria'),('Vitoria','Penagos'),('Penagos','Soto de Ribera'),
 ('Soto de Ribera','As Pontes'),('As Pontes','Mesón do Vento'),('Mesón do Vento','Cartelle'),
 ('Cartelle','Lindoso (PT)'),('Cartelle','Trives'),('Trives','Montearenas'),('Montearenas','La Mudarra'),
 ('La Mudarra','Tordesillas'),('Tordesillas','Aldeadávila'),('Aldeadávila','Lagoaça (PT)'),
 ('Aldeadávila','Villarino'),('Tordesillas','Segovia'),('Segovia','S.S. Reyes'),('S.S. Reyes','Loeches'),
 ('Loeches','Morata'),('Morata','Aceca'),('S.S. Reyes','Trillo'),('Vitoria','Castejón'),
 ('Penagos','Aguayo'),('Castejón','Magallón'),('Magallón','Aragón'),('Aragón','Ascó'),
 ('Ascó','Vandellós'),('Aceca','Almaraz'),('Almaraz','J.M. Oriol'),('J.M. Oriol','Cedillo'),
 ('Cedillo','Falagueira (PT)'),('Almaraz','San Serván'),('San Serván','Brovales'),
 ('Brovales','Alqueva (PT)'),('San Serván','Bienvenida'),('Bienvenida','Guillena'),('Guillena','Palos'),
 ('Guillena','P. Guzmán'),('P. Guzmán','Tavira (PT)'),('Guillena','Don Rodrigo'),('Don Rodrigo','Arcos'),
 ('Arcos','Pinar del Rey'),
 ('Pinar del Rey','Tarifa'),('Arcos','Tajo de la Encantada'),('Tajo de la Encantada','Caparacena'),
 ('Caparacena','El Palmar'),('El Palmar','El Fangal'),('El Palmar','Rocamora'),('Rocamora','Cofrentes'),
 ('Cofrentes','La Eliana'),('La Eliana','Morvedre'),('Morvedre','La Plana'),('La Plana','Vandellós'),
 ('Vandellós','La Secuita'),('La Secuita','Pierola'),('Pierola','Rubí'),('Rubí','Sentmenat'),
 ('Sentmenat','Vic'),('Vic','Baixas (FR)'),
 ('Vic','Sta. Llogaia'),('Sallente','Sentmenat'),('Boroa','Vitoria'),('Trillo','Magallón'),
 ('Caparacena','Guillena'),('Manzanares','Aceca'),('Manzanares','Caparacena'),
 # cornisa cantábrica y noroeste
 ('As Pontes','Boimente'),('Boimente','Soto de Ribera'),('Soto de Ribera','Lada'),('Lada','Velilla'),
 ('Velilla','Vilecha'),('Vilecha','Montearenas'),('Velilla','La Mudarra'),
 ('Penagos','Güeñes'),('Güeñes','Gatika'),('Gatika','Hernani'),('Güeñes','Vitoria'),('Boroa','Gatika'),
 ('Hernani','Ichaso'),('Ichaso','Vitoria'),('Ichaso','Muruarte'),('Muruarte','Castejón'),
 # eje Mudéjar Aragón–Levante y Ebro
 ('Magallón','Fuendetodos'),('Fuendetodos','Mezquita'),('Mezquita','Morella'),('Morella','La Plana'),
 ('Aragón','Peñalba'),('Peñalba','Ascó'),
 # La Mancha–Levante
 ('Olmedilla','Minglanilla'),('Minglanilla','Cofrentes'),('Romica','Minglanilla'),('Trillo','Olmedilla'),
 # CLM–Extremadura–Andalucía
 ('Manzanares','Brazatortas'),('Brazatortas','Guillena'),('Almaraz','Valdecaballeros'),
 ('Valdecaballeros','Brazatortas'),
 # Andalucía oriental–Murcia
 ('Caparacena','Baza'),('Baza','Litoral'),('Litoral','El Palmar'),
 # Madrid oeste
 ('Segovia','Galapagar'),('Galapagar','S.S. Reyes')]
L220 = [('Sabón','Mesón do Vento'),('Belesar','Trives'),('Aboño','Soto de Ribera'),
 ('Santurtzi','Penagos'),('Santurtzi','Boroa'),('Bolarque','Loeches'),('Bolarque','Trillo'),
 ('Escombreras','El Fangal'),('Tarragona','Vandellós'),('Port de Barcelona','Besòs'),
 ('Besòs','Sentmenat'),('Arrúbal','Castejón'),('Ribarroja','Ascó'),('Pont de Suert','Sallente'),
 ('Málaga','Tajo de la Encantada'),('La Robla','Vilecha'),('La Robla','Velilla'),
 ('Puertollano','Brazatortas'),('Puertollano','Manzanares'),('Aboño','Lada'),
 ('Santurtzi','Güeñes'),('Tarragona','La Secuita'),('Belesar','Montearenas'),('Málaga','Caparacena')]
LDC = [('Sta. Llogaia','Baixas (FR)','HVDC ±320 kV · int. Francia'),
       ('Morvedre','Sta. Ponsa (Mallorca)','HVDC ±250 kV · enlace Rómulo (Baleares)')]
LSUB = [('Tarifa','Fardioua (MA)','400 kV submarino · int. Marruecos')]

# ---------- proyección ----------
LON0, LAT1, K, CY = -14.2, 44.35, 60.0, math.cos(math.radians(40))
def XY(lat, lon): return (round((lon - LON0) * K * CY, 1), round((LAT1 - lat) * K, 1))
W, H = XY(35.0, 4.75)[0] + 10, XY(34.55, 0)[1]

# ---------- geometría España (TopoJSON -> paths) ----------
topo = json.load(open('spain.topo.json', encoding='utf-8'))
tr = topo['transform']; arcs_raw = topo['arcs']
def dec_arc(a):
    x = y = 0; out = []
    for dx, dy in a:
        x += dx; y += dy
        out.append((x * tr['scale'][0] + tr['translate'][0], y * tr['scale'][1] + tr['translate'][1]))
    return out
ARCS = [dec_arc(a) for a in arcs_raw]
def ring_coords(ring):
    pts = []
    for ai in ring:
        a = ARCS[ai] if ai >= 0 else list(reversed(ARCS[~ai]))
        pts.extend(a if not pts else a[1:])
    return pts
def geom_paths(geom, shift=(0, 0)):
    polys = geom['arcs'] if geom['type'] == 'MultiPolygon' else [geom['arcs']]
    d = []
    for poly in polys:
        for ring in poly:
            pts = ring_coords(ring)
            if len(pts) < 4: continue
            seg = 'M' + 'L'.join(f"{XY(la + shift[0], lo + shift[1])[0]},{XY(la + shift[0], lo + shift[1])[1]}" for lo, la in pts) + 'Z'
            d.append(seg)
    return ''.join(d)
paths_pen, path_can = [], ''
for gm in topo['objects']['autonomous_regions']['geometries']:
    nm = gm['properties']['name']
    if nm == 'Canarias':
        path_can = geom_paths(gm, shift=(7.9, 4.6))   # inset: trasladada al suroeste
    elif 'Gibraltar' not in nm:
        paths_pen.append((nm, geom_paths(gm)))

# ---------- emparejado UF -> comunidad autónoma vía registro ELECTRA (RAIPRE) ----------
def _norm(s):
    s = unicodedata.normalize('NFD', s.upper())
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return ' '.join(''.join(ch if ch.isalnum() else ' ' for ch in s).split())
_STOP = {'P','E','PE','PF','UF','UP','FV','PSF','PSFV','CH','C','H','B','CE','SR','SL','SA','SAU','U','I','II','III','IV','V',
 'COMPRA','VENTA','PARQUE','EOLICO','EOLICA','SOLAR','FOTOVOLTAICA','FOTOVOLTAICO','PLANTA','CENTRAL','FASE','GRUPO',
 'HIDROELECTRICA','HIDRAULICA','TERMICA','TERMOSOLAR','INSTALACION','DE','DEL','LA','EL','LOS','LAS','Y','T','G','CT','CTCC','CC','S',
 '1','2','3','4','5','6','7','8','9','10'}
def _core(s): return ' '.join(t for t in _norm(s).split() if t not in _STOP)
_sq = lambda s: s.replace(' ', '')
CA_POS = {  # centroides aproximados (Canarias trasladada al inset)
 'Galicia': (42.75,-8.10), 'Principado de Asturias': (43.25,-5.95), 'Cantabria': (43.15,-4.05),
 'Pais Vasco': (43.00,-2.65), 'Navarra': (42.65,-1.65), 'La Rioja': (42.30,-2.52),
 'Aragon': (41.55,-0.90), 'Cataluna': (41.75,1.55), 'Castilla y Leon': (41.70,-4.75),
 'Comunidad de Madrid': (40.45,-3.70), 'Castilla-La Mancha': (39.40,-3.05),
 'Comunidad Valenciana': (39.35,-0.85), 'Region de Murcia': (38.00,-1.50),
 'Extremadura': (39.10,-6.15), 'Andalucia': (37.40,-4.70), 'Baleares': (39.60,2.95),
 'Canarias': (36.40,-11.20), 'Ceuta': (35.89,-5.31), 'Melilla': (35.35,-2.95)}
CA_LIST = list(CA_POS)
def build_registry():
    def addk(d, a, k, ca):
        if len(k) < 5: return
        if k in d and d[k] != ca: a.add(k)
        else: d[k] = ca
    reg, amb, regc, ambc, regs, ambs = {}, set(), {}, set(), {}, set()
    tok, tokdf = collections.defaultdict(set), collections.Counter()
    with open('ElectraExp.csv', encoding='cp1252', errors='replace') as f:
        rd = csv.reader(f, delimiter=';'); next(rd)
        for row in rd:
            if len(row) < 5: continue
            ca = row[4].strip()
            if ca not in CA_POS: continue
            n1, c1 = _norm(row[3]), _core(row[3])
            addk(reg, amb, n1, ca); addk(regc, ambc, c1, ca)
            addk(regs, ambs, _sq(n1), ca); addk(regs, ambs, _sq(c1), ca)
            for t in set(c1.split()):
                if len(t) >= 5: tok[t].add(ca); tokdf[t] += 1
    for d, a in ((reg, amb), (regc, ambc), (regs, ambs)):
        for k in a: d.pop(k, None)
    return reg, regc, regs, tok, tokdf
REG, REGC, REGS, TOK, TOKDF = build_registry()
_KEYS = sorted(REG)
def _pref(q):
    if len(q) < 7: return None
    i = bisect.bisect_left(_KEYS, q); cas = set(); n = 0
    while i < len(_KEYS) and _KEYS[i].startswith(q):
        cas.add(REG[_KEYS[i]]); i += 1; n += 1
        if n > 40: return None
    return cas.pop() if len(cas) == 1 else None
def _bytoken(c):
    ts = sorted((t for t in _core(c).split() if len(t) >= 5 and t in TOK), key=lambda t: TOKDF[t])
    for t in ts[:2]:
        if TOKDF[t] <= 150 and len(TOK[t]) == 1: return next(iter(TOK[t]))
    return None
def uf_ca(rec):
    cands = [rec['Descripción larga'], rec['Descripción corta'], rec['Código de UF']]
    for c in cands:
        if _norm(c) in REG: return REG[_norm(c)]
    for c in cands:
        if _core(c) in REGC: return REGC[_core(c)]
    for c in cands:
        for k in (_sq(_norm(c)), _sq(_core(c))):
            if k in REGS: return REGS[k]
    for c in cands:
        p = _pref(_norm(c)) or _pref(_core(c))
        if p: return p
    for c in cands:
        p = _bytoken(c)
        if p: return p
    return None

# ---------- datos de UPs ----------
ufs_by_up, n_ca_match = {}, 0
for r in UF:
    ca = uf_ca(r)
    if ca: n_ca_match += 1
    ufs_by_up.setdefault(r['Vinculación con UP'], []).append(
        (r['Descripción larga'], mw(r['Potencia máxima MW']),
         CA_LIST.index(ca) if ca else -1, tech_idx(r['Tipo de producción'])))

gen = [r for r in UP if r['Tipo de UP'] in GEN_TYPES]
rows, located, distributed = [], [], []
for r in sorted(gen, key=lambda r: -mw(r['Potencia máxima MW'])):
    c = r['Código de UP'].strip(); p = mw(r['Potencia máxima MW'])
    zr = (r['Zona de Regulación'] or '').strip(); smc = (r['Sujeto del Mercado'] or '').strip()
    n_uf = len(ufs_by_up.get(c, []))
    all_uf = sorted(ufs_by_up.get(c, []), key=lambda u: -u[1])
    row = dict(c=c, d=r['Descripción larga'].strip(), t=tech_idx(r['Tipo de producción']),
               tp=r['Tipo de producción'], mw=round(p, 1), sm=smc, smn=SM_NAME.get(smc, ''),
               zr=zr, uf=n_uf, tu=r['Tipo de UP'],
               ufs=[[n, round(m, 1), ca, t] for n, m, ca, t in all_uf])
    if c in G:
        lat, lon, site, nudo, multi = G[c]
        x, y = XY(lat, lon)
        row.update(x=x, y=y, site=site, nudo=nudo, multi=(1 if (multi or n_uf > 3) else 0))
        located.append(row)
    elif p >= 200 and n_uf > 3:
        distributed.append(row)
    rows.append(row)

# enlace Baleares (4 UPs sobre el enlace Rómulo)
enl = [dict(c=r['Código de UP'].strip(), d=r['Descripción larga'].strip(), mw=mw(r['Potencia máxima MW']),
            sm=(r['Sujeto del Mercado'] or '').strip(), zr=(r['Zona de Regulación'] or '').strip())
       for r in UP if r['Tipo de UP'] == 'Enlace península baleares']

# agregados
tot = {}
for r in rows:
    a = tot.setdefault(r['t'], [0, 0.0]); a[0] += 1; a[1] += r['mw'] if r['tu'] != 'Consumo bombeo' else 0
zr_agg = {}
for r in rows:
    z = r['zr'] or '—'
    a = zr_agg.setdefault(z, [0, 0.0, {}]); a[0] += 1; a[1] += r['mw']; a[2][r['sm']] = a[2].get(r['sm'], 0) + 1
zr_list = sorted(([z, n, round(m), max(sm, key=sm.get)] for z, (n, m, sm) in zr_agg.items() if z != 'SZR'),
                 key=lambda x: -x[2])
szr = zr_agg.get('SZR', [0, 0, {}])

# nudos compartidos: offsets radiales deterministas para UPs en el mismo nudo
from collections import defaultdict
by_node = defaultdict(list)
for r in located: by_node[r['nudo']].append(r)
for node, lst in by_node.items():
    if len(lst) > 1:
        lst.sort(key=lambda r: -r['mw'])
        for i, r in enumerate(lst):
            ang = i * 2 * math.pi / len(lst) - math.pi / 2
            rad = 7 + 3 * (len(lst) > 4)
            r['x'] = round(r['x'] + rad * math.cos(ang), 1); r['y'] = round(r['y'] + rad * math.sin(ang), 1)
    for r in lst: r['shared'] = [q['c'] for q in lst if q is not r]

# ---------- ubicación estimada de UPs agregadas (centroide ponderado de UFs por comunidad) ----------
import hashlib
N400 = {n: XY(la, lo) for n, (la, lo, kv) in NODES.items() if kv == 400 and '(' not in n}
n_est = 0
for row in rows:
    if 'x' in row: continue
    locuf = [u for u in row['ufs'] if u[2] >= 0]
    if not locuf: continue
    wtot = sum(max(u[1], 0.1) for u in locuf)
    lat = sum(CA_POS[CA_LIST[u[2]]][0] * max(u[1], 0.1) for u in locuf) / wtot
    lon = sum(CA_POS[CA_LIST[u[2]]][1] * max(u[1], 0.1) for u in locuf) / wtot
    h = int(hashlib.md5(row['c'].encode()).hexdigest()[:8], 16)
    lat += ((h & 0xFFF) / 4095 - 0.5) * 0.85          # jitter determinista para no apilar
    lon += (((h >> 12) & 0xFFF) / 4095 - 0.5) * 1.1
    ex, ey = XY(lat, lon)
    en = min(N400, key=lambda n: (N400[n][0] - ex) ** 2 + (N400[n][1] - ey) ** 2)
    pct = round(100 * sum(u[1] for u in locuf) / row['mw']) if row['mw'] else 100
    row.update(ex=ex, ey=ey, en=en, ep=min(pct, 100), est=1)
    n_est += 1

# conectores UP situada -> nudo (muestra qué plantas comparten nudo)
svg_cnx = ''
for r in located:
    nd = NODES.get(r['nudo'].replace(' (aprox.)', ''))
    if nd:
        nx, ny = XY(nd[0], nd[1])
        svg_cnx += f'<line class="cnx" x1="{r["x"]}" y1="{r["y"]}" x2="{nx}" y2="{ny}"/>'

DATA = dict(rows=rows, located=[r['c'] for r in located], dist=[r['c'] for r in distributed],
            groups=[[t[0], t[1], t[2]] for t in TECH_GROUPS],
            tot={str(k): [v[0], round(v[1])] for k, v in tot.items()},
            zr=zr_list, szr=[szr[0], round(szr[1])], enl=enl,
            nodes={n: list(XY(la, lo)) + [kv] for n, (la, lo, kv) in NODES.items()},
            canames=CA_LIST, capos=[list(XY(la, lo)) for la, lo in CA_POS.values()],
            fecha=FECHA, ufmatch=[n_ca_match, len(UF)], nest=n_est)

# ---------- SVG estático ----------
def line_svg(pairs, cls):
    out = []
    for a, b, *lbl in pairs:
        (x1, y1), (x2, y2) = DATA['nodes'][a][:2], DATA['nodes'][b][:2]
        t = (lbl[0] if lbl else ('Línea 400 kV' if cls == 'l400' else 'Línea 220 kV')) + f' · {a} – {b}'
        out.append(f'<line class="{cls}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" data-tip="{t}"/>')
    return ''.join(out)
svg_regions = ''.join(f'<path class="reg" d="{d}"><title>{n}</title></path>' for n, d in paths_pen)
svg_lines = (line_svg(L220, 'l220') + line_svg(L400, 'l400')
             + line_svg(LDC, 'ldc') + line_svg(LSUB, 'lsub'))
svg_nodes = ''.join(
    f'<g class="nd{" nd2" if kv == 220 else ""}" transform="translate({x},{y})" data-tip="Nudo {n} · {kv} kV (esquemático)">'
    f'<rect x="-2.6" y="-2.6" width="5.2" height="5.2"/></g>'
    for n, (x, y, kv) in DATA['nodes'].items())
# contexto geográfico + inset Canarias
def T(lat, lon): return XY(lat, lon)
ctx = []
for txt, lat, lon in [('PORTUGAL', 39.6, -8.35), ('FRANCIA', 43.75, -0.7), ('MARRUECOS', 35.35, -4.6)]:
    x, y = T(lat, lon); ctx.append(f'<text class="ctx" x="{x}" y="{y}" text-anchor="middle">{txt}</text>')
cx1, cy1 = XY(37.7, -13.75); cx2, cy2 = XY(35.35, -8.6)
ctx.append(f'<rect class="inset" x="{cx1}" y="{cy1}" width="{round(cx2-cx1,1)}" height="{round(cy2-cy1,1)}" rx="6"/>')
ctx.append(f'<text class="ctx" x="{cx1+6}" y="{cy1+12}" style="letter-spacing:.08em">CANARIAS</text>')
bx, by = XY(40.05, 2.9)
ctx.append(f'<text class="ctx" x="{bx}" y="{by}" style="letter-spacing:.08em">ILLES BALEARS</text>')
sx, sy = DATA['nodes']['Sta. Ponsa (Mallorca)'][:2]
ctx.append(f'<text class="nlbl" x="{sx+4}" y="{sy+8}">Sta. Ponsa</text>')
svg_ctx = ''.join(ctx)
NODE_LBL = ['Almaraz', 'J.M. Oriol', 'Guillena', 'Pinar del Rey', 'El Palmar', 'Cofrentes', 'Morvedre',
            'Ascó', 'Vandellós', 'Sentmenat', 'Sta. Llogaia', 'Castejón', 'Vitoria', 'Penagos',
            'Soto de Ribera', 'As Pontes', 'Cartelle', 'Trives', 'Aldeadávila', 'La Mudarra',
            'S.S. Reyes', 'Trillo', 'Aceca', 'San Serván', 'Palos', 'Arcos', 'El Fangal', 'Aragón',
            'Tarifa', 'Sallente', 'Hernani', 'Boroa', 'Velilla', 'Vilecha', 'Olmedilla', 'Minglanilla',
            'Romica', 'Brazatortas', 'Valdecaballeros', 'Baza', 'Litoral', 'Peñalba', 'Mezquita',
            'Morella', 'Ichaso', 'Muruarte', 'Galapagar', 'Don Rodrigo', 'La Secuita', 'Caparacena']
svg_nlbl = ''.join(f'<text class="nlbl" x="{DATA["nodes"][n][0] + 4}" y="{DATA["nodes"][n][1] - 3}">{n}</text>'
                   for n in NODE_LBL)

html = open('template.html', encoding='utf-8').read()
html = (html.replace('__W__', str(int(W))).replace('__H__', str(int(H)))
            .replace('__REGIONS__', svg_regions).replace('__CANARIAS__', path_can)
            .replace('__GRID__', svg_lines).replace('__NODES__', svg_nodes).replace('__CNX__', svg_cnx)
            .replace('__NLBL__', svg_nlbl + svg_ctx).replace('__FECHA__', FECHA)
            .replace('__DATA__', json.dumps(DATA, ensure_ascii=False, separators=(',', ':'))))
OUT = os.path.join(BASE, 'infografia_sistema_electrico_espana.html')
open(OUT, 'w', encoding='utf-8').write(html)
# sincroniza la copia de la carpeta padre si existe (ruta habitual de consulta)
_parent = os.path.join(os.path.dirname(BASE), 'infografia_sistema_electrico_espana.html')
if os.path.isfile(_parent):
    import shutil; shutil.copyfile(OUT, _parent); print('->', _parent)
print('OK', W, H, 'rows', len(rows), 'located', len(located), 'dist', len(distributed),
      'UF con CCAA', n_ca_match, '/', len(UF), 'kb', len(html) // 1024)
print('->', OUT)
