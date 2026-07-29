# Continuar el desarrollo (traspaso entre sesiones / máquinas)

Documento de contexto para retomar el proyecto en **otro ordenador y otra sesión de Claude Code**.
Todo lo imprescindible está aquí o en el repositorio; no hace falta ningún fichero externo ni credencial.

Última actualización de este documento: **29-07-2026** (commit de referencia: `35a702f`).

---

## 0. Arranque rápido

```bash
git clone https://github.com/Siliutors/infografia-sistema-electrico.git
cd infografia-sistema-electrico
python -X utf8 build.py     # regenera index.html desde template.html + los .json/.csv del repo
# abrir index.html en el navegador (funciona con file://, no necesita servidor)
```

Requisitos: **Python 3.8+ y solo librería estándar**. Sin dependencias JS: el HTML es autocontenido
(≈1,1 MB, los datos van embebidos como JSON en la propia página).

Para refrescar todos los datos desde las fuentes oficiales y regenerar:

```bash
python actualizar_datos.py
```

**Prompt sugerido para abrir la nueva sesión de Claude:**

> Trabajo en la infografía interactiva del sistema eléctrico español (repo clonado de
> github.com/Siliutors/infografia-sistema-electrico). Lee `CONTINUAR.md` y `README.md` antes de nada:
> contienen el estado, la arquitectura y las reglas del proyecto. Recuerda que `index.html` es
> **generado** — se edita `template.html` o `build.py` y se ejecuta `python -X utf8 build.py`.
> Quiero [describir la tarea].

---

## 1. Qué es

Infografía HTML interactiva de las **unidades de programación (UP)** del sistema eléctrico español
sobre un mapa de España: red de transporte esquemática (400/220 kV + HVDC), nudos con su capacidad de
acceso, zonas de regulación, unidades físicas (UF) de cada UP y una capa de mercados diarios (I90).

- Repo: <https://github.com/Siliutors/infografia-sistema-electrico> (rama `main`, usuario `Siliutors`).
- Publicado: <https://siliutors.github.io/infografia-sistema-electrico/> (GitHub Pages sirve `index.html`
  desde la raíz de `main`; **cada push a `main` republica la web**).
- Idioma de todo el proyecto (interfaz, README, commits, comentarios de código): **español**.

## 2. Estado actual (29-07-2026)

Último commit: `35a702f` — *Exportación a Google My Maps (KML) con UPs y sus unidades físicas*.
Historial (10 commits, del más reciente al más antiguo):

| Commit | Aporte |
|---|---|
| `35a702f` | export KML para Google My Maps (UPs + UFs, carpetas separadas) |
| `f60a0d7` | tabla de nudos anexa al mapa (búsqueda, filtros, orden, selección bidireccional) |
| `eefa475` | capa ⚡ de capacidad de acceso por nudo (CNMC/REE) y asignación UP→nudo vía distribución |
| `f38c172` | I90 solo desde 01-10-2025, disclaimer de IA, salida renombrada a `index.html` |
| `6815317` | adaptación móvil, gestos táctiles, enlaces de autor |
| `005aa54` | barra de mercados visible al inicio, leyenda de sentido, tarjetas al pie |
| `78cc5f8` | capa de mercados: sentido en el borde y corrección de signo |
| `904ec4d` | capa de mercados I90 |
| `824d18a` | etiquetas dinámicas de códigos UP |
| `28df908` | versión inicial |

Cifras que imprime `build.py` con los datos actualmente versionados:

```
OK 881.0 588.0 rows 2930 located 111 dist 26 UF con CCAA 3166 / 6615 kb 1095
nudos CNMC 937 (datos Junio 2026 · REE 01-07-2026) | UP estimadas 1417 (1072 con nudo vía subestación de distribución)
```

- Datos ESIOS/ELECTRA descargados el **16-07-2026** (`fecha_datos.txt`); capacidad CNMC de **junio 2026**;
  fichero REE de **01-07-2026** (`ree_capacidad_fecha.txt`). **Están desactualizados ~2 semanas / 1 mes**:
  lo primero que conviene hacer es `python actualizar_datos.py`.
- El README **todavía no documenta la exportación KML** (`🗺 Google Maps`) añadida en `35a702f`.

## 3. Ficheros

| Fichero | Papel |
|---|---|
| `template.html` (1.207 líneas) | **fuente** de la interfaz: CSS, HTML y todo el JS. Se edita aquí. |
| `build.py` (563 líneas) | generador: gacetero, red esquemática, proyección, emparejado UF↔ELECTRA, nudos, KML-ready coords |
| `index.html` (generado, ~1,1 MB) | **salida — nunca editar a mano**; se versiona porque es lo que sirve Pages |
| `actualizar_datos.py` (155 líneas) | descarga *todas* las fuentes y ejecuta `build.py` |
| `spain.topo.json` | contorno de España (es-atlas/IGN) |
| `up.json` / `uf.json` / `sm.json` | ESIOS archivos 82 / 81 / 83 |
| `ElectraExp.csv` | registro ELECTRA (RAIPRE) del MITECO (4 MB) |
| `nudos_transporte.json` | 937 nudos CNMC con capacidad |
| `nudos_distribucion.json` | 6.167 subestaciones de distribución con `NUDO_AFECCION_RDT` |
| `ree_capacidad.csv` | fichero mensual de capacidad por nudo de REE |
| `fecha_datos.txt`, `ree_capacidad_fecha.txt` | sellos de fecha inyectados en el HTML |

## 4. Arquitectura

**Pipeline:** `actualizar_datos.py` → (descarga fuentes) → `build.py` → sustituye marcadores
`__W__ __H__ __REGIONS__ __CANARIAS__ __GRID__ __CNX__ __NODES__ __NLBL__ __FECHA__ __DATA__`
en `template.html` → escribe `index.html` (y copia a `../infografia_sistema_electrico_espana.html` si existe).

**Secciones de `build.py`** (en orden, con su cabecera de comentario):

1. Carga de `up.json`/`uf.json`/`sm.json`; `mw()` normaliza potencias.
2. `TECH_GROUPS`: 8 grupos tecnológicos → variables CSS `--s0..--s7` (paleta dataviz validada).
3. **Gacetero curado** `G` (`g(codes, lat, lon, site, nudo, multi)`): ~111 UP con emplazamiento real y
   nudo de conexión conocido. Es la parte “a mano” del proyecto; ampliarlo es la mejora de calidad más directa.
4. **Red esquemática**: `NODES` (nombre → lat, lon, kV), tramos 400/220 kV, `LDC`/`LSUB` (HVDC e
   interconexiones). Trazado **esquemático**, no geometría real.
5. **Proyección** equirectangular `XY(lat, lon)` → coordenadas del viewBox 881×588. Canarias se traslada
   al inset con un desplazamiento **+7,9 lat / +4,6 lon** aplicado en dos sitios: el TopoJSON y `_mapll()`.
6. **Emparejado UF → comunidad autónoma** contra ELECTRA por nombre normalizado (`_norm`, `_core`, lista
   de *stopwords* `_STOP`, prefijos y tokens). Acierta 3.166/6.615 UF (≈48 %); el resto son códigos internos.
7. **Nudos oficiales y capacidad** (CNMC/REE): normalización de nombres `_nkey`/`_RE_NUDO`
   (`"LASTRAS 400"`, `"CARTUJA220"`), motivos de reserva `RES_KINDS` y **malla espacial** `_cell`/`_nearest`
   (celda 30 uds ≈ 0,5°) para vecinos más próximos. Si faltan los ficheros de nudos, hay *fallback* al
   comportamiento antiguo (nudo 400 kV más próximo).
8. **Filas de UP** (`rows`): ver esquema abajo; offsets radiales deterministas para UPs que comparten nudo.
9. **Ubicación estimada** de UPs agregadas: centroide de sus UF ponderado por potencia sobre los centroides
   de comunidad `CA_POS`, + *jitter* determinista por `md5(código)` para no apilar puntos. Se dibujan las
   ≥10 MW con ≥25 % de potencia identificada. Nudo estimado = subestación de distribución más cercana →
   su `NUDO_AFECCION_RDT`, o el nudo de transporte más próximo si está aún más cerca.
10. Ensamblado de SVG estático y volcado de `DATA`.

**Esquema de una fila de UP** (`DATA.rows[i]`, claves cortas por tamaño del HTML):

```
c código · d descripción · t índice de grupo tecnológico · tp tipo de producción · mw potencia
sm/smn sujeto de mercado (código/nombre) · zr zona de regulación · tu tipo de UP · uf nº de UF
ufs [[nombre, MW, índice CCAA, grupo tecnológico], ...]
situadas:  x, y (viewBox) · site · nudo · multi · shared[] · lat, lon (reales, para el KML)
estimadas: ex, ey · ep (% potencia identificada) · est=1 · en (nudo) · enx, eny · evia
           elat, elon (reales, para el KML)
```

Otras claves de `DATA`: `located`, `dist`, `groups`, `tot`, `zr`, `szr`, `enl` (enlace Rómulo), `nodes`,
`canames`, `capos`, `fecha`, `ufmatch`, `nest`, `cnodes` (los 937 nudos), `capfecha`, `reefecha`, `resk`.

**Frontend (`template.html`)** — funciones principales: `setTheme`, `renderEst`, `renderCap`/`capTip`,
`selectNode`/`napply` (tabla de nudos), `applyZoom`/`zoomBy`/`clampZ` (zoom con contra-escalado de
marcadores), `renderLabels` (etiquetas anticolisión), `apply` (buscador y filtros), `selectUP`/`renderUFmarks`
(panel de detalle), `mktSelect`/`renderMkt`/`mktStep`/`parseSheet` (capa I90), export PNG/PDF/KML.
Breakpoints: 1100 px (una columna) y 720 px (móvil), más `@media (pointer:coarse)` para gestos táctiles.

## 5. Reglas del proyecto (respetarlas al modificar)

1. **`index.html` es generado.** Editar `template.html` (interfaz) o `build.py` (datos/geometría) y ejecutar
   `python -X utf8 build.py`. Commitear siempre `template.html` + `index.html` juntos; si divergen, la web
   publicada deja de corresponder al código.
2. **La build es reproducible**: `build.py` sobre los mismos datos no produce diff. Si aparece diff
   inesperado en `index.html`, es que alguien tocó la salida a mano o cambiaron los `.json`.
3. **Nada de credenciales en el repo.** `ESIOS_TOKEN` solo por variable de entorno (y de hecho no hace
   falta: los archivos 81/82/83 y el 34 son públicos). El `.gitignore` bloquea `*token*`, `*.key`, `.env`.
4. **I90 y el signo**: los CSV con columna *Sentido* traen las bajadas **ya en negativo**. Se fuerza
   `−|v|` / `+|v|` según el sentido; **no** multiplicar por el signo (duplicaría la corrección).
5. **I90 solo desde 01-10-2025**: ese día REE cambió a periodos cuartohorarios; el parser no entiende el
   formato anterior. La descarga es del navegador (`api.esios.ree.es/archives/34/download`, CORS `*`) y el
   ZIP se descomprime en JS con `DecompressionStream('deflate-raw')`.
6. **Coherencia del inset de Canarias**: cualquier punto nuevo en el mapa debe pasar por la misma
   traslación (+7,9 / +4,6). Los puntos del inset se **excluyen** del KML (sus coordenadas de pantalla no
   son geográficas; para el KML se usan `lat/lon` y `elat/elon` reales).
7. **Google My Maps** admite 2.000 elementos por capa: el KML reparte en carpetas de ≤1.800.
8. **Nombres de subestación inconsistentes** en las fuentes CNMC (mayúsculas, espacios sobrantes,
   `"Guadiana "`): siempre normalizar antes de cruzar con `NODES`.
9. **Honestidad de los datos**: las limitaciones (asignación UP→nudo no pública, UF solo a nivel de
   comunidad, red esquemática, advertencia CNMC de que las capacidades no son sumables, aviso de que la
   herramienta está generada con IA) están escritas tanto en el README como **dentro del propio HTML**.
   No eliminarlas ni suavizarlas al refactorizar.
10. **Commits en español**, mensaje descriptivo de una línea + cuerpo explicando el porqué, y línea final
    `Co-Authored-By: Claude <...>`. Identidad git: `Siliutors` / `sixtoo@hotmail.es`.

## 6. Fuentes de datos (endpoints exactos)

- **ESIOS (REE)**, JSON públicos sin token:
  `https://api.esios.ree.es/archives/{81|82|83}/download?locale=es` → UF / UP / sujetos de mercado.
  Archivo **34** = I90 diario (ZIP con 13 cuadernos; se publica con ~90 días de retraso).
- **MITECO — ELECTRA (RAIPRE)**: `https://energia.serviciosmin.gob.es/Electra/BuscarDatos.aspx`,
  POST ASP.NET reenviando `__VIEWSTATE` / `__VIEWSTATEGENERATOR` / `__EVENTVALIDATION` +
  `ctl00$ContentPlaceHolder1$mButDescargaCSV=CSV`; devuelve un ZIP con el CSV. La exportación pública
  **no** trae código RAIPRE, municipio ni coordenadas: solo nombre y comunidad autónoma.
- **CNMC — mapas de capacidad** (ArcGIS público, actualización mensual), host
  `https://services9.arcgis.com/F9FmuOlj5xjEjPRZ/arcgis/rest/services`:
  - `Generacion_en_Transporte/FeatureServer/0` → 937 nudos (geometría Web Mercator EPSG:3857).
  - `Generacion_en_Distribucion/FeatureServer/4` → 6.167 subestaciones (**layer 4, no 0**) con
    `NUDO_AFECCION_RDT`.
  - `Capacidad_Periodo/FeatureServer/10` → mes de referencia.
  - Query: `/query?where=1=1&outFields=*&f=json`, paginando con `resultOffset` (~1.000-2.000 por petición).
  - Los endpoints salieron de la config de las apps Experience:
    `www.arcgis.com/sharing/rest/content/items/<appId>/data?f=json`, appId generación
    `0dac803d644f41519fdd11da11ef10ae`, **demanda `c7dc433cb2e44d53a908a8a467523f5a`** (sin explotar aún).
- **REE — capacidad mensual por nudo**:
  `https://www.ree.es/sites/default/files/12_CLIENTES/Documentos/aaaa_mm_dd_GRT_generacion.csv`
  (publicado en los ~5 primeros días de cada mes; `actualizar_datos.py` prueba días 1-5 y retrocede
  hasta 6 meses). Cabecera multinivel de 3 filas separada por `;`. Existe también `_GRT_demanda`.
- **No existe públicamente**: la asignación planta/UP/UF → nudo (es confidencial). Pistas parciales:
  resoluciones de concursos de capacidad (MITECO/BOE por nudo) y resoluciones AAP/DIA del BOE para
  instalaciones >50 MW, que citan la infraestructura de evacuación — scrapeables vía la API de datos
  abiertos del BOE.

## 7. Cómo verificar un cambio

- Lo normal: `python -X utf8 build.py` y abrir `index.html` en el navegador.
- Comprobación automatizable sin abrir ventana (útil para Claude): Chrome headless
  `chrome --headless=new --virtual-time-budget=8000 --screenshot=<ruta> --window-size=1600,1200 <file://...>`,
  inyectando antes de `</script>` un pequeño script que haga clic en el botón a probar. Recortar la
  captura con PIL para inspeccionar la zona de interés.
- Revisar siempre `git diff --stat`: si `index.html` cambia mucho más de lo esperado, revisar por qué.

## 8. Ideas pendientes (backlog **propuesto**, no comprometido con el usuario)

Ordenadas por relación valor/esfuerzo, para proponer — no ejecutar sin confirmar:

1. **Actualizar datos** (`actualizar_datos.py`) y revisar que el HTML sigue correcto: los datos son de
   mediados de julio de 2026.
2. **Documentar el export KML en el README** (funcionalidad ya en producción, sin documentar).
3. **Actualización automática con GitHub Actions**: un workflow mensual que ejecute `actualizar_datos.py`
   y haga commit si hay cambios; la web se republicaría sola. Ojo: el POST a ELECTRA y las capas ArcGIS
   deben funcionar desde los *runners*.
4. **Enlaces profundos** (`#up=XXXX`, `#nudo=...`, `#fecha=...`) para compartir una vista concreta.
5. **Ampliar el gacetero curado** más allá de las 111 UP situadas y **mejorar el emparejado UF↔ELECTRA**
   (hoy 48 %): ambos elevan directamente la calidad del mapa.
6. **Capa de demanda por nudo** con la app CNMC de demanda (appId ya identificado arriba).
7. **Histórico mensual de capacidad** para ver la evolución de los nudos (requiere guardar instantáneas).
8. **Peso de la página**: 1,1 MB de HTML; separar `DATA` a un `.json` con `fetch` rompería el uso con
   `file://`, así que si se hace, mantener una variante autocontenida.
9. **I90 anterior a 01-10-2025** (formato horario antiguo), si interesa el histórico largo.

## 9. Entorno y publicación

- **GitHub Pages** ya está activado sobre `main` / raíz. Publicar = `git push`.
- El proyecto **no tiene tests ni CI**; la verificación es visual.
- Peculiaridades del **portátil de trabajo** donde nació el proyecto (probablemente **no** aplican en un
  ordenador personal, pero explican decisiones del código): proxy corporativo con TLS interceptado —de ahí
  el *fallback* a contexto SSL sin verificar en `descarga()` de `actualizar_datos.py` para `arcgis.com`—,
  `pip` incapaz de instalar paquetes nuevos (403 en `files.pythonhosted.org`) —de ahí la regla de **solo
  librería estándar**—, `gh auth login` con 2FA inservible y autenticación vía Git Credential Manager.
  En una máquina personal con red normal todo eso debería sobrar; el *fallback* TLS es inocuo.
- Consola Windows: usar `python -X utf8` para evitar mojibake con los acentos.
