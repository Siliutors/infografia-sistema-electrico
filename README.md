# Infografía del sistema eléctrico español

Infografía interactiva (HTML autocontenido, sin dependencias) de las **unidades de programación (UP)** del
sistema eléctrico español sobre un mapa de España, con la **red de transporte esquemática** (400/220 kV y
enlaces HVDC), los **nudos** de conexión, las **zonas de regulación** y las **unidades físicas (UF)** de cada UP.

**➡ Versión en línea: https://siliutors.github.io/infografia-sistema-electrico/** — o abrir `index.html` en cualquier navegador.

## Funcionalidades

- Mapa con **zoom y paneo** (rueda/arrastre o botones), tema claro/oscuro/auto.
- **111 UP geolocalizadas** (curadas) y **~1.400 UP con ubicación estimada** por el centroide ponderado de sus
  UF identificadas por comunidad autónoma (conmutables con «◌ estimadas»).
- Conectores **UP → nudo** que muestran qué plantas comparten nudo.
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

Descarga los ficheros públicos de ESIOS (unidades físicas, unidades de programación y sujetos de mercado),
la exportación CSV del registro ELECTRA (RAIPRE) del Ministerio, y regenera el HTML con la fecha de datos.
Solo requiere Python 3.8+ (librería estándar).

| Fichero | Papel |
|---|---|
| `actualizar_datos.py` | descarga de datos y regeneración |
| `build.py` | generador (gacetero de emplazamientos, red esquemática, emparejado UF↔RAIPRE) |
| `template.html` | plantilla de la infografía (estilos e interacción) |
| `spain.topo.json` | contorno de España (es-atlas / IGN) |
| `up.json`, `uf.json`, `sm.json` | datos ESIOS (REE) |
| `ElectraExp.csv` | registro ELECTRA/RAIPRE (MITECO) |

## Fuentes y limitaciones

- **ESIOS (Red Eléctrica de España)**: unidades de programación, unidades físicas, sujetos de mercado y zonas
  de regulación (`api.esios.ree.es/archives` 81–83).
- **MITECO — registro ELECTRA (RAIPRE)**: la exportación pública solo incluye nombre de instalación y comunidad
  autónoma (sin código RAIPRE, municipio ni coordenadas), por lo que las UF se sitúan **a nivel de comunidad**
  cruzando nombres normalizados (~48 % identificadas; el resto son códigos internos).
- La **asignación UP→nudo no es un dato público**: los nudos indicados son los de conexión conocidos o los más
  próximos (aproximados), y el trazado de la red es **esquemático**, no la geometría real de las líneas.
- Los emplazamientos puntuales de las grandes centrales proceden de información pública de cada planta; las UP
  multi-instalación se sitúan en su zona aproximada (centroide ponderado por potencia).

Proyecto de visualización con fines informativos; no es material oficial de REE ni del MITECO.

> ⚠ **Herramienta generada con IA** (Claude — modelos Fable 5 y Opus 4.8, de Anthropic): puede contener
> errores en algunos datos, ubicaciones o agregados. Contraste la información relevante con las fuentes oficiales.
