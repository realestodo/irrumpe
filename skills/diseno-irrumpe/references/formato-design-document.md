# Formato del documento de diseño de Irrumpe (Designer / Konva)

Referencia canónica de **cómo se guardan** las fuentes, los estilos, las propiedades y la
geometría en el formato nativo del Designer de Irrumpe. Esta es la verdad de fondo que la
skill usa para producir un diseño que el editor renderiza sin pérdidas.

Prosa en español; los nombres de campos, tipos y ejemplos JSON van en inglés (son
identificadores del formato, no se traducen).

Fuente de verdad en el código (Irrumpe Front):
- `app/lib/editor/editor-model.ts` — estructura del documento, tipos de capa, validador `parseEditorDocument`.
- `app/lib/editor/editor-style.ts` — vocabulario de estilo opcional y capacidades por tipo de capa.
- `app/lib/editor/editor-brand-library.ts` — envoltura de persistencia `DesignTypedPayload`.
- `app/lib/editor/editor-font-library.ts` — resolución de fuentes (system/google/url/adobe).

---

## 1. Cómo se guarda un diseño (envoltura de persistencia)

Un diseño es un **item de Brand Center** con `dimension_key: "design"`, cuyo `typed_payload` es JSON
plano (sin CRDT ni estado Yjs): el autoguardado reemplaza el `typed_payload` completo.

```jsonc
// typed_payload (DesignTypedPayload)
{
  "kind": "design_document",
  "schema_version": 1,
  "editor_key": "konva",
  "design_name": "Plantillas de ejemplo.",
  "design_document": { /* EditorDocument, ver §2 */ },
  "source_template_item_id": null   // opcional: id del template de origen
}
```

Tabla física: `app.brand_center_designs.design_document` (jsonb). El backend valida solo que sea
un objeto JSON (`runtime.is_json_object`); la validación real de la estructura la hace el Front
con `parseEditorDocument` al cargar. Un `design_document` malformado degrada a documento vacío
o de error, no rompe la carga.

### Contrato de carga por MCP

```jsonc
brand_center_item_upsert({ payload: {
  brand_id, dimension_key: "design", item_key: "design-<uuid>",
  title, typed_payload: { /* DesignTypedPayload */ }
}})
```

- La respuesta del upsert NO devuelve el `typed_payload`; verificar con `get_brand_center_item_detail`.
- El `design_document` se fija en la **creación**. Un upsert sobre un item existente con el mismo
  `item_key` preserva el diseño guardado (protege la edición del usuario en el Designer). Para una
  nueva versión migrada, usar un `item_key` nuevo.
- Handoff: `https://irrumpe.realestodo.com/brand/<brandId>/designer?item=<itemId>`.

---

## 2. EditorDocument

```ts
EditorDocument = {
  version: 1,            // literal 1 (obligatorio)
  pages: Page[]          // una entrada por página/artboard
}

Page = {
  id: string,            // string único (puede ser propio, no requiere uuid)
  name: string,          // p. ej. "Página 1"
  layers: Layer[],       // z-order = orden del array (último = arriba)
  durationSeconds?: number  // duración de la página para preview/export de video (default 5)
}
```

Cada página es un artboard independiente con su propia línea de tiempo. El lienzo del editor es
**infinito** (no hay rectángulo de fondo fijo); para acotar la página a 1080×1920 se usa una capa
`frame` (ver §4). Historias de Instagram = 1080×1920.

---

## 3. Propiedades comunes a toda capa (LayerBase)

```ts
LayerBase = {
  id: string,            // único en el documento
  name: string,          // etiqueta en el panel de capas
  x: number,             // coordenada ABSOLUTA de lienzo (px)
  y: number,             // coordenada ABSOLUTA de lienzo (px)
  rotation: number,      // grados
  opacity: number,       // 0..1
  visible: boolean,
  locked: boolean,
  parentId: string | null,  // ver "frames"; null = capa raíz
  animation?: LayerAnimation // ausente = capa estática
}
```

Reglas de geometría:
- **Todas las coordenadas son absolutas**, incluidos los hijos de un `frame` (también guardan x/y
  absolutos). `parentId` solo controla recorte (clipping), agrupación y "arrastrar el frame mueve a
  los hijos". No es un offset de coordenadas.
- **z-order = orden del array** `layers`. El primero es el de más abajo; el último, el de más arriba.
- Unidades: **píxeles puros**. Konva no tiene unidades físicas; presets de impresión vienen
  pre-convertidos a px @300dpi.

`LayerAnimation` (opcional, para video): `{ entrance, exit, delay, duration, exitDuration,
timeOnScreen, easing }`. Un spec de animación inválido se descarta silenciosamente (la capa queda
estática). `easing ∈ {linear, ease-in, ease-out, ease-in-out, back-out}`.

---

## 4. Tipos de capa y sus campos

Hay 10 tipos. Cada uno extiende `LayerBase` y agrega lo siguiente:

### frame — artboard / contenedor que recorta
```ts
{ type: "frame", width, height, fill: string }
```
Es el rectángulo del artboard. Recorta a sus hijos (`parentId === frameId`), los arrastra con él, y
es el área de exportación cuando se selecciona un único frame. Para una historia: `width:1080,
height:1920`. Puede llevar `fillSpec` de imagen (§6) para un fondo a sangre con `fit:"cover"`.

### rect — rectángulo
```ts
{ type: "rect", width, height, fill: string }
```
Una **píldora/botón** se hace con `rect` + `cornerRadius` alto (≈ height/2) + `stroke`, y `fill`
transparente (`"#00000000"`). Ver §6.

### ellipse — elipse
```ts
{ type: "ellipse", radiusX, radiusY, fill: string }
```

### text — texto
```ts
{
  type: "text",
  text: string,            // contenido literal (incluye \n para saltos de línea)
  fontSize: number,        // px de lienzo
  fill: string,            // color del texto (hex)
  width: number,           // ancho de caja; el texto se alinea/ajusta dentro
  fontFamily: string,      // STACK CSS completo, p. ej. "\"brandon-grotesque\", sans-serif"
  fontStyle: "normal" | "bold" | "italic" | "italic bold",
  letterSpacing: number,   // tracking extra en px de lienzo (Konva letterSpacing)
  lineHeight: number,      // multiplicador del font-size (Konva lineHeight), p. ej. 1.4
  align: "left" | "center" | "right" | "justify"
}
```
**Cómo se guardan las fuentes** (clave para esta skill): la fuente es un **string de stack CSS** en
`fontFamily`. No hay id de fuente; el editor resuelve la familia contra sus proveedores
(`editor-font-library.ts`):
- `system` — fuentes del sistema.
- `google` — Google Fonts vía CDN.
- `url` — caras self-hosted (CDN del proyecto).
- `adobe` — kit de Adobe Fonts de la marca, cargado vía `use.typekit.net`; **rankea primero** en el
  selector del Designer.

Para que resuelva una cara de marca, `fontFamily` debe contener su nombre CSS de Adobe. Una marca de
ejemplo usa **Brandon Grotesque** (`"brandon-grotesque", sans-serif`, títulos) y **New Science**
(`"new-science", sans-serif`, cuerpo/cita). Konva no tiene `text-transform`: las mayúsculas se
aplican al **literal** de `text`. El estilo itálico va en `fontStyle`.

### image — imagen rasterizada
```ts
{ type: "image", src: string, width, height }
```
`src` es **cualquier string de URL**: http(s) (debe servirse con CORS para que el export no se
contamine; el editor pone `crossOrigin="anonymous"` en remotas), o un `data:` URI. El placeholder
por defecto del editor es un `data:image/svg+xml`. Por eso un **vector arbitrario de Canva se puede
incrustar como SVG en un data-URI** dentro de un `image` (vector nítido, sin subir nada). Las fotos
de marca van en R2 y se referencian por `https://pipelines.realestodo.com/...` (CORS *).

### video
```ts
{ type: "video", src: string, width, height, loop: boolean, muted: boolean }
```

### icon — ícono de registro
```ts
{ type: "icon", iconId: string, fill: string, width, height }
```
`iconId` se resuelve contra `editor-icon-library.ts`. No acepta path arbitrario.

### shape — forma de registro o vector libre
```ts
{ type: "shape", shapeId: string, fill: string, width, height,
  pathData?: string,        // path SVG; sobrescribe shapeId en el render
  viewBox?: [number, number, number, number] }  // [minX, minY, w>0, h>0]
```
`shapeId` se resuelve contra un **registro de paths** (`editor-shape-library.ts`). `pathData` permite
un vector libre y **sobrescribe** `shapeId` al dibujar, pero `shapeId` (string) **sigue siendo
obligatorio para validar** (`isValidLayer` lo exige siempre). Para una forma libre, usa un `shapeId`
del registro como base y agrega tu `pathData`.

### lottie — animación
```ts
{ type: "lottie", src: string, width, height,
  format?: "json" | "dotlottie",   // ausente → "json"
  loop?: boolean, speed?: number, tint?: string | null, tintOpacity?: number }
```
`src` es la URL pública (R2) del JSON o dotLottie. El editor reproduce la animación en
previsualización/exportación; en edición muestra un cuadro estático.

### table — tabla nativa
```ts
{
  type: "table", width, height,
  cells: string[][],        // matriz fila-mayor; toda fila comparte el conteo de columnas de la 1ª
  headerRow: boolean,       // la 1ª fila usa estilo de encabezado
  bandedRows: boolean,      // filas alternas con relleno de banda
  fontSize: number,
  textFill, headerTextFill, borderFill, headerFill, cellFill, bandFill: string  // todos hex
}
```
La tabla de horario de la plantilla (página 11) es una capa `table` nativa.

### chart — gráfico nativo
```ts
{
  type: "chart", chartKind: string, width, height,
  data: { label: string, value: number }[],   // ≥ 1 punto
  palette: string[],         // colores de serie; los puntos ciclan la paleta
  showLabels, showValues, showGrid: boolean,
  textFill: string, fontSize: number
}
```
`chartKind` se resuelve contra `editor-chart-library.ts` (id desconocido → barras). Barras
(página 7) y dona (página 14) son capas `chart` nativas con los valores reales.

---

## 5. Cómo se guardan los colores

- Strings hex: `#rrggbb` o `#rrggbbaa` (los 2 últimos dígitos = alpha). También admite `#rgb`.
- **Transparente** = `"#00000000"` (alpha 00).
- No hay tokens de marca en el documento: el color se guarda como hex literal. La skill **mapea**
  cada color de Canva al token de la marca más cercano (ver el archivo de tokens de la marca) y escribe su hex; el
  blanco/negro puros se conservan.

---

## 6. Vocabulario de estilo opcional (LayerStyle)

Campos opcionales que cualquier capa puede llevar **además** de su `fill` sólido. Ausentes =
documento idéntico byte a byte (compatibilidad). Un campo de estilo inválido se **descarta**
silenciosamente al parsear (la capa sobrevive).

```ts
LayerStyle = {
  fillSpec?: FillSpec,        // si está, gana sobre el `fill` sólido
  stroke?: StrokeSpec,
  shadows?: ShadowSpec[],     // máx 6
  cornerRadius?: number | [tl, tr, br, bl],
  cornerShape?: "round" | "cut",   // default round; "cut" achaflana
  blendMode?: BlendMode       // ausente = compositing normal
}

FillSpec =
  | { type: "solid", color }
  | { type: "linear-gradient", angle, stops: { offset:0..1, color }[] }   // angle CSS: 0=arriba, 90=derecha
  | { type: "radial-gradient", stops: {...}[] }
  | { type: "image", src, fit: "cover" | "contain" | "tile" }

StrokeSpec = { color, width, align: "inside" | "center" | "outside" }
ShadowSpec = { color, blur, offsetX, offsetY, opacity: 0..1 }
BlendMode  = "multiply" | "screen" | "overlay" | "darken" | "lighten"
           | "color-dodge" | "color-burn" | "hard-light" | "soft-light"
           | "difference" | "exclusion" | "hue" | "saturation" | "color" | "luminosity"
```

### Qué controles soporta cada tipo de capa (STYLE_CAPABILITIES)

| Tipo   | fill sólido | gradiente | image fill | stroke | stroke align in/out | corners | corner cut | máx sombras | blend |
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

Un campo fuera de capacidad es inerte (no rompe), pero no se renderiza. Ejemplo: una píldora =
`rect` con `cornerRadius` ≈ height/2, `stroke` blanco y `fill: "#00000000"`.

---

## 7. Validación (parseEditorDocument) — qué exige el editor al cargar

Rechaza el documento entero (→ vacío/error) si falla cualquiera de:
- `version !== 1` o `pages` no es array.
- Alguna página sin `id`/`name` string, o `durationSeconds` no finito, o `layers` no array.
- `LayerBase` inválido: `id`/`name` string; `x`/`y`/`rotation`/`opacity` finitos; `visible`/`locked`
  booleanos; `parentId` null o string.
- Campos requeridos por tipo (mínimos que TODA capa migrada debe cumplir):
  - frame/rect: `width`, `height` finitos, `fill` string.
  - ellipse: `radiusX`, `radiusY` finitos, `fill` string.
  - text: `text` string, `fontSize` finito, `fill` string, `width` finito.
  - image/video: `src` string, `width`/`height` finitos.
  - lottie: `src` string, `width`/`height` finitos, `format` ausente o string.
  - icon/shape: `iconId`/`shapeId` string, `fill` string, `width`/`height` finitos. `shape` exige
    `shapeId` aunque definas `pathData`.
  - table: `width`/`height` finitos, `cells` matriz rectangular no vacía, flags booleanos, `fontSize`
    finito y los 6 colores string.
  - chart: `chartKind` string, `width`/`height` finitos, `data` no vacío con `{label:string,
    value:number}`, `palette` array de strings, flags booleanos, `textFill` string, `fontSize` finito.

Tolerancias (no rechazan, se rellenan/limpian):
- Campos de estilo de texto faltantes (fontFamily, fontStyle, letterSpacing, lineHeight, align) se
  rellenan con defaults.
- `video.loop`/`video.muted` faltantes → `true`.
- `animation` inválida → se descarta (capa estática).
- Campos `LayerStyle` inválidos → se descartan uno a uno.

La skill DEBE validar el `design_document` con `tools/validar_design_document.py` antes de subir; la
herramienta espeja exactamente estas reglas y, además, advierte (sin rechazar) cuando un chart tiene
todos sus valores ≤ 0 (se ve como estado vacío), un `src` usa `media://` o no es `https://`/`data:`,
o una `fontFamily` no trae stack con fallback. El upsert usa el `upsert_arguments` que devuelve.

---

## 8. Específicos de la marca (ejemplo de migración)

- `brandId`: `<brandId>` (id real de la marca destino).
- Fuentes (Adobe kit de la marca): títulos `"brandon-grotesque", sans-serif`; cuerpo/cita
  `"new-science", sans-serif`.
- Paleta principal: Primario `#667759`, Texto `#444444`, Acento `#FCDECE`, Fondo
  `#FDFBE5`; más grupos "Símbolos" y "Extendida" (ver el archivo de tokens de la marca).
- Imágenes: se migran al espacio de la marca en R2 y se referencian por `pipelines.realestodo.com`.
