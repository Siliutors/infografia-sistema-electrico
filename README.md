# Infografía del sistema eléctrico español

Infografía interactiva (HTML autocontenido, sin dependencias) de las **unidades de programación (UP)** del
sistema eléctrico español sobre un mapa de España, con la **red de transporte esquemática** (400/220 kV y
enlaces HVDC), los **nudos** de conexión, las **zonas de regulación** y las **unidades físicas (UF)** de cada UP.

**➡ Versión en línea: https://siliutors.github.io/infografia-sistema-electrico/** — o abrir `index.html` en cualquier navegador.

## Funcionalidades

- Mapa con **zoom y paneo** (rueda/arrastre o botones), tema claro/oscuro/auto.
- **111 UP geolocalizadas** (curadas) y **~1.400 UP con ubicación estimada** por el centroide ponderado de sus
  UF identificadas por comunidad autónoma (conmutables con «◌ estimadas»).
- **Capa de capacidad de acceso (⚡)**: los **937 nudos de la red de transporte** con su posición oficial y su
  capacidad ocupada / disponible (generación y almacenamiento, MPE y MGES) / en tramitación y posiciones libres,
  según los **mapas de capacidad de la CNMC** (actualización mensual), más el **motivo de reserva** (concursos y
  nudos de transición justa) del fichero mensual de capacidad por nudo de REE. Verde = con capacidad para nueva
  generación, rojo = sin capacidad, anillo ámbar = nudo reservado, Ø ∝ capacidad ocupada.
- **Tabla de nudos anexa al mapa**: los 937 nudos con búsqueda (nudo/municipio/provincia), filtros (tensión,
  con/sin capacidad disponible, con capacidad para almacenamiento, reservados) y **ordenación por columna**
  (ocupada, disponible MPE/MGES, almacenamiento, en tramitación, posiciones libres, UPs). Clic en una fila:
  resalta y centra el nudo en el mapa y filtra el buscador de UPs por las unidades asociadas a ese nudo
  (asignación estimada); clic en un nudo del mapa selecciona su fila.
- Conectores **UP → nudo** que muestran qué plantas comparten nudo. Para las UP estimadas, el nudo se estima
  con la **subestación de distribución más cercana y su nudo de afección en transporte** (dato CNMC) o el nudo
  de transporte más próximo.
- Clic en una UP: panel con todas sus **unidades físicas** y su despliegue en el mapa (◆ por comunidad).
- **Buscador** de las 2.932 UP de generación por código, nombre, sujeto de mercado, nudo **o unidad física**;
  filtros por tecnología y zona de regulación.
- Exportación de la vista actual a **PNG** y a **PDF** (impresión).
- **Capa de mercados (I90)**: el botón «📊 mercados» descarga desde el navegador el I90 diario de ESIOS
  (archivo 34) para la fecha elegida y anima sobre el mapa la actuación de cada UP por mercado
  (PDBF, PDVP, PHF-1/2/3, PHFC, P48, restricciones técnicas, terciaria mFRR, balance RR, bilaterales,
  indisponibilidades) y periodo cuartohorario: azul = sube/positivo, rojo = baja/negativo,
  Ø ∝ |MWh|, con avance por pasos o reproducción automática («play») y etiquetas de cantidades.
  El I90 se publica con ~90 días de retraso. Solo admite fechas **desde el 01-10-2025**: ese día
  Red Eléctrica cambió el formato del fichero (periodos cuartohorarios) y la herramienta no
  interpreta el formato anterior.
- Paneles de zonas de regulación, carteras distribuidas y enlace Península–Baleares (Rómulo).

## Actualizar los datos

```bash
python actualizar_datos.py
```

**Un único script** descarga todas las fuentes y regenera el HTML: los ficheros públicos de ESIOS (unidades
físicas, unidades de programación y sujetos de mercado), la exportación CSV del registro ELECTRA (RAIPRE) del
Ministerio, las capas de nudos de transporte y subestaciones de distribución de los mapas de capacidad de la
CNMC (servicios ArcGIS públicos) y el fichero mensual de capacidad de acceso por nudo de REE (busca el más
reciente de los últimos 6 meses). Solo requiere Python 3.8+ (librería estándar).

| Fichero | Papel |
|---|---|
| `actualizar_datos.py` | descarga de **todas** las fuentes y regeneración |
| `build.py` | generador (gacetero de emplazamientos, red esquemática, emparejado UF↔RAIPRE, asignación de nudo) |
| `template.html` | plantilla de la infografía (estilos e interacción) |
| `spain.topo.json` | contorno de España (es-atlas / IGN) |
| `up.json`, `uf.json`, `sm.json` | datos ESIOS (REE) |
| `ElectraExp.csv` | registro ELECTRA/RAIPRE (MITECO) |
| `nudos_transporte.json` | nudos de la red de transporte con capacidad de acceso (CNMC) |
| `nudos_distribucion.json` | subestaciones de distribución >1 kV con su nudo de afección en transporte (CNMC) |
| `ree_capacidad.csv` | fichero mensual de capacidad de acceso por nudo (REE) |

## Fuentes y limitaciones

- **ESIOS (Red Eléctrica de España)**: unidades de programación, unidades físicas, sujetos de mercado y zonas
  de regulación (`api.esios.ree.es/archives` 81–83).
- **MITECO — registro ELECTRA (RAIPRE)**: la exportación pública solo incluye nombre de instalación y comunidad
  autónoma (sin código RAIPRE, municipio ni coordenadas), por lo que las UF se sitúan **a nivel de comunidad**
  cruzando nombres normalizados (~48 % identificadas; el resto son códigos internos).
- **CNMC — mapas de capacidad de acceso** (Circular informativa 6/2025): capas ArcGIS públicas
  (`services9.arcgis.com/F9FmuOlj5xjEjPRZ`) con los nudos de transporte (posición, tensión, capacidad ocupada,
  disponible y en tramitación, posiciones) y las subestaciones de distribución >1 kV con su **nudo de afección**
  en la red de transporte. Actualización mensual. **Advertencia CNMC**: los valores de capacidad son informativos
  y **no directamente sumables** entre nudos.
- **REE — fichero mensual de capacidad por nudo** (`aaaa_mm_dd_GRT_generacion.csv`, obligación de la Resolución
  CNMC de 01-12-2025): capacidad otorgada por criterios y **motivo de reserva** de cada nudo (concursos, nudos
  de transición justa).
- La **asignación UP→nudo no es un dato público** (la gestión de los permisos de acceso y conexión es
  confidencial): los nudos indicados son los de conexión conocidos públicamente o **estimaciones por
  proximidad** — para las UP estimadas, la subestación de distribución más cercana a su posición estimada y su
  nudo de afección (CNMC), o el nudo de transporte más próximo. **Ningún nudo mostrado debe interpretarse como
  el punto de conexión real de una instalación.** El trazado de la red es **esquemático**, no la geometría real
  de las líneas.
- Los emplazamientos puntuales de las grandes centrales proceden de información pública de cada planta; las UP
  multi-instalación se sitúan en su zona aproximada (centroide ponderado por potencia).

Proyecto de visualización con fines informativos; no es material oficial de REE ni del MITECO.

> ⚠ **Herramienta generada con IA** (Claude — modelos Fable 5 y Opus 4.8, de Anthropic): puede contener
> errores en algunos datos, ubicaciones o agregados. Contraste la información relevante con las fuentes oficiales.
