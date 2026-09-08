# Formato del design_document (editor Konva)

Especificación factual de cómo se guardan fuentes, estilos, propiedades y geometría en el formato
nativo del Designer de Irrumpe. Prosa en español; campos, tipos y ejemplos JSON en inglés (son
identificadores del formato, no se traducen). El contrato de carga y la subida de media están en
`diseno-brand-center.md`.

---

## Índice

1. [Envoltura de persistencia](#1-envoltura-de-persistencia)
2. [EditorDocument](#2-editordocument)
3. [Propiedades comunes](#3-propiedades-comunes-layerbase)
4. [Tipos de capa](#4-tipos-de-capa)
5. [Colores](#5-colores)
6. [Vocabulario de estilo](#6-vocabulario-de-estilo-opcional-layerstyle)
7. [Validación](#7-validación--qué-exige-el-editor-al-cargar)
8. [Recetas de elementos nativos](#8-recetas-de-elementos-nativos)

## 1. Envoltura de persistencia

```jsonc
// typed_payload (DesignTypedPayload)
{
  "kind": "design_document",
  "schema_version": 1,
  "editor_key": "konva",
  "design_name": "Nombre del diseño",
  "design_document": { /* EditorDocument, ver §2 */ },
  "source_template_item_id": null   // opcional: id del template de origen
}
```

JSON plano, sin CRDT: el autoguardado del editor reemplaza el `typed_payload` completo. El backend
valida solo que sea un objeto JSON; la estructura Konva la valida el editor al cargar
(`parseEditorDocument`). `tools/validar_design_document.py` espeja exactamente esas reglas y arma
los `upsert_arguments`.

## 2. EditorDocument

```ts
EditorDocument = {
  version: 1,            // literal 1 (obligatorio)
  pages: Page[]
}

Page = {
  id: string,            // string único (no requiere uuid)
  name: string,
  layers: Layer[],       // z-order = orden del array (último = arriba)
  durationSeconds?: number  // duración para preview/export de video (default 5)
}
```

Cada página es un artboard independiente. El lienzo es infinito; el artboard se acota con una capa
`frame` (§4). Historias de Instagram = 1080×1920.

## 3. Propiedades comunes (LayerBase)

```ts
LayerBase = {
  id: string,            // único en el documento
  name: string,
  x: number,             // coordenada ABSOLUTA de lienzo (px)
  y: number,
  rotation: number,      // grados
  opacity: number,       // 0..1
  visible: boolean,
  locked: boolean,
  parentId: string | null,  // null = capa raíz
  animation?: LayerAnimation
}
```

Reglas de geometría:
- **Todas las coordenadas son absolutas**, incluidos los hijos de un `frame`. `parentId` controla
  recorte, agrupación y arrastre conjunto; nunca es un offset de coordenadas.
- **z-order = orden del array** `layers`.
- Unidades: píxeles puros (presets de impresión pre-convertidos a px @300dpi).

`LayerAnimation` (opcional): `{ entrance, exit, delay, duration, exitDuration, timeOnScreen,
easing }` con `easing ∈ {linear, ease-in, ease-out, ease-in-out, back-out}`. Un spec inválido se
descarta en silencio (capa estática).

## 4. Tipos de capa

Once tipos; cada uno extiende `LayerBase`.

### frame — artboard / contenedor que recorta
```ts
{ type: "frame", width, height, fill: string }
```
Recorta a sus hijos (`parentId === frameId`) y es el área de exportación. Puede llevar `fillSpec`
de imagen (§6) para fondo a sangre con `fit:"cover"`. Cuando el diseño define un color de fondo
plano, ese `fill` manda por sobre cualquier foto cubridora.

### rect
```ts
{ type: "rect", width, height, fill: string }
```
Una píldora/botón = `rect` + `cornerRadius` alto (≈ height/2) + `stroke` + `fill` transparente
(`"#00000000"`).

### ellipse
```ts
{ type: "ellipse", radiusX, radiusY, fill: string }
```
Un círculo de venn = `ellipse` con `radiusX = radiusY`, `stroke` y `fill` transparente. Centro =
esquina + radio.

### text
```ts
{
  type: "text",
  text: string,            // literal, con \n para saltos de línea
  fontSize: number,        // px de lienzo
  fill: string,
  width: number,           // ancho de caja
  fontFamily: string,      // STACK CSS completo, p. ej. "\"mi-fuente\", sans-serif"
  fontStyle: "normal" | "bold" | "italic" | "italic bold",
  letterSpacing: number,   // px de lienzo
  lineHeight: number,      // multiplicador del font-size
  align: "left" | "center" | "right" | "justify"
}
```
La fuente se guarda como stack CSS en `fontFamily`; el editor la resuelve contra sus proveedores
(system, Google Fonts, self-hosted, kit de Adobe Fonts de la marca — este último rankea primero).
Konva carece de `text-transform`: las mayúsculas se aplican al literal de `text`.

### image
```ts
{ type: "image", src: string, width, height }
```
`src` acepta URL http(s) (con CORS; el editor usa `crossOrigin="anonymous"`) o `data:` URI. Este
soporte del parser no reemplaza el upload: todo archivo aportado por el usuario o descargado de una
fuente externa va a R2. Reservar `data:image/svg+xml,...` para SVG textual compuesto por el modelo
cuando `shape` o `icon` no expresen el vector; no convertir archivos binarios a base64 dentro del
contexto. Las fotos de marca van en R2 (`https://pipelines.realestodo.com/...`).

### video
```ts
{ type: "video", src: string, width, height, loop: boolean, muted: boolean }
```
El editor reproduce el video solo en previsualización/exportación; en modo edición muestra el fondo
del frame. Eso es comportamiento correcto. Verifica la URL aparte (`200`, `content-type: video/*`).

### icon
```ts
{ type: "icon", iconId: string, fill: string, width, height }
```
`iconId` se resuelve contra el registro de íconos del editor; sin paths arbitrarios.

### shape
```ts
{ type: "shape", shapeId: string, fill: string, width, height,
  pathData?: string,        // path SVG; sobrescribe shapeId al dibujar
  viewBox?: [minX, minY, w, h] }
```
`shapeId` se resuelve contra el registro de formas y **sigue siendo obligatorio para validar**
aunque definas `pathData`. Para un vector libre usa un `shapeId` del registro como base.

### lottie
```ts
{ type: "lottie", src: string, width, height,
  format?: "json" | "dotlottie", loop?: boolean, speed?: number,
  tint?: string | null, tintOpacity?: number }
```
`src` es la URL pública del JSON o dotLottie. Anima en previsualización/exportación; en edición se
ve un cuadro estático.

### table
```ts
{
  type: "table", width, height,
  cells: string[][],        // matriz fila-mayor, rectangular
  headerRow: boolean, bandedRows: boolean, fontSize: number,
  textFill, headerTextFill, borderFill, headerFill, cellFill, bandFill: string
}
```

### chart
```ts
{
  type: "chart", chartKind: string, width, height,
  data: { label: string, value: number }[],   // ≥ 1 punto
  palette: string[],
  showLabels, showValues, showGrid: boolean,
  textFill: string, fontSize: number
}
```
`chartKind` cubre barras (verticales/horizontales), líneas, área, pie y donut; un id desconocido
degrada a barras. Campos adicionales: `orientation`, `trackColor` (two-tone), `legend`
(`around`/`right`/`none`), `donutThickness`, `donutCornerRadius`, `barCornerRadius`, `fontFamily`.

## 5. Colores

Strings hex: `#rrggbb` o `#rrggbbaa` (últimos 2 dígitos = alpha); admite `#rgb`. Transparente =
`"#00000000"`. El documento guarda hex literales; el operador mapea cada color a un token de la
paleta de la marca (Brand Center) y conserva blancos y negros puros.

## 6. Vocabulario de estilo opcional (LayerStyle)

Campos opcionales sobre cualquier capa, además de su `fill` sólido. Un campo de estilo inválido se
descarta en silencio (la capa sobrevive).

```ts
LayerStyle = {
  fillSpec?: FillSpec,        // si está, gana sobre el fill sólido
  stroke?: StrokeSpec,
  shadows?: ShadowSpec[],     // máx 6
  cornerRadius?: number | [tl, tr, br, bl],
  cornerShape?: "round" | "cut",
  blendMode?: BlendMode
}

FillSpec =
  | { type: "solid", color }
  | { type: "linear-gradient", angle, stops: { offset: 0..1, color }[] }  // angle CSS: 0=arriba
  | { type: "radial-gradient", stops: [...] }
  | { type: "image", src, fit: "cover" | "contain" | "tile" }

StrokeSpec = { color, width, align: "inside" | "center" | "outside" }
ShadowSpec = { color, blur, offsetX, offsetY, opacity: 0..1 }
BlendMode  = "multiply" | "screen" | "overlay" | "darken" | "lighten" | "color-dodge"
           | "color-burn" | "hard-light" | "soft-light" | "difference" | "exclusion"
           | "hue" | "saturation" | "color" | "luminosity"
```

### Capacidades por tipo de capa

| Tipo   | fill sólido | gradiente | image fill | stroke | stroke align | corners | corner cut | máx sombras | blend |
|--------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| frame  | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 6 | ✓ |
| rect   | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 6 | ✓ |
| ellipse| ✓ | ✓ | ✓ | ✓ | ✓ | — | — | 6 | ✓ |
| shape  | ✓ | ✓ | ✓ | ✓ | — | — | — | 6 | ✓ |
| text   | ✓ | ✓ | — | ✓ | — | — | — | 1 | ✓ |
| image  | — | — | — | ✓ | — | ✓ | — | 1 | ✓ |
| video  | — | — | — | ✓ | — | ✓ | — | 1 | ✓ |
| icon   | ✓ | — | — | — | — | — | — | 1 | ✓ |
| table  | — | — | — | — | — | — | — | 0 | ✓ |
| chart  | — | — | — | — | — | — | — | 0 | ✓ |

Un campo fuera de capacidad es inerte (el documento valida y el campo se ignora al renderizar).

## 7. Validación — qué exige el editor al cargar

Rechaza el documento entero si falla cualquiera de:
- `version !== 1` o `pages` fuera de tipo array.
- Página sin `id`/`name` string, `durationSeconds` no finito, o `layers` fuera de tipo array.
- `LayerBase` inválido: `id`/`name` string; `x`/`y`/`rotation`/`opacity` finitos; `visible`/`locked`
  booleanos; `parentId` null o string.
- Campos requeridos por tipo:
  - frame/rect: `width`, `height` finitos, `fill` string.
  - ellipse: `radiusX`, `radiusY` finitos, `fill` string.
  - text: `text` string, `fontSize` finito, `fill` string, `width` finito.
  - image/video: `src` string, `width`/`height` finitos.
  - lottie: `src` string, `width`/`height` finitos, `format` ausente o string.
  - icon/shape: `iconId`/`shapeId` string, `fill` string, `width`/`height` finitos.
  - table: `width`/`height` finitos, `cells` matriz rectangular no vacía, flags booleanos,
    `fontSize` finito y los 6 colores string.
  - chart: `chartKind` string, `width`/`height` finitos, `data` no vacío con
    `{label: string, value: number}`, `palette` array de strings, flags booleanos, `textFill`
    string, `fontSize` finito.

Tolerancias (se rellenan o limpian sin rechazar): estilo de texto faltante (fontFamily, fontStyle,
letterSpacing, lineHeight, align) → defaults; `video.loop`/`muted` faltantes → `true`; `animation`
inválida → descartada; campos `LayerStyle` inválidos → descartados uno a uno.

La herramienta `tools/validar_design_document.py` espeja estas reglas y además **advierte** (sin
rechazar) cuando un chart tiene todos sus valores ≤ 0, un `src` usa `media://` o un esquema distinto
de `https://`/`data:`, o una `fontFamily` no trae stack con fallback.

## 8. Recetas de elementos nativos

### Barras horizontales two-tone

La barra de color representa el valor; `trackColor` rellena el resto. Para controlar labels y
valores exactos (símbolo `%`, idioma, posición), deja el chart solo con las barras
(`showLabels: false`, `showValues: false`) y pon los textos como capas `text` encima, con el chart
detrás en z-order.

```jsonc
{ "type": "chart", "chartKind": "bar", "orientation": "horizontal",
  "x": 120, "y": 612, "width": 840, "height": 740,
  "data": [{"label": "A", "value": 80}, {"label": "B", "value": 60}],
  "palette": ["#FDFBE5"], "trackColor": "#CBAB6B", "barCornerRadius": 18,
  "showLabels": false, "showValues": false, "showGrid": false,
  "textFill": "#FDFBE5", "fontSize": 24 }
```

### Donut con leyenda alrededor

`legend: "around"` ubica cada label + valor alrededor del anillo en el color de su segmento. Los
`data.value` se reparten como porcentaje del total (procura que sumen ~100). El chart muestra el
valor numérico sin `%`; si la fidelidad exige el símbolo, apaga `showValues`/`legend` y pon los
labels como capas `text`.

### Venn / diagramas

Sin primitiva de diagrama: círculos = capas `ellipse` con `stroke` y `fill: "#00000000"`, textos de
región como capas `text` encima. Para vectores complejos, `shape` con `pathData` (con un `shapeId`
del registro como base).

### Tablas

Horarios y precios = capa `table` nativa. Dimensiona la caja al alto real del contenido para que no
se vea apretada.
