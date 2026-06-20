# Contratos MCP y subida de media

Cómo se crean, leen, actualizan y archivan los diseños, y cómo entran los archivos a R2. Prosa en
español; nombres de herramientas, campos y valores en inglés.

---

## 1. Autoría del documento — `brand_center_item_upsert`

Crea o actualiza un item de Brand Center con su `design_document`. El backend valida solo que
`typed_payload` sea un objeto JSON; la validación real de la estructura Konva la hace el editor al
cargar. Por eso un documento mal formado se guarda sin error de API y luego el editor lo bloquea al
abrirlo. La herramienta `tools/validar_design_document.py` es la verificación previa obligatoria.

**Flujo:** validas el `design_document` con la herramienta; ella devuelve el objeto
`upsert_arguments`; ese objeto se pasa **tal cual** como argumentos de `brand_center_item_upsert`. No
armes la envoltura a mano.

Los argumentos del tool MCP son **planos** (no envueltos en un objeto `payload`):

```jsonc
brand_center_item_upsert({
  brand_id,
  dimension_key: "design",              // o "template"
  title,
  item_key: "design-<slug>-pNN",        // crear: item_key nuevo, sin brand_center_item_id
  brand_center_item_id: "<uuid>",       // editar: fuerza la actualización del item existente
  typed_payload: {                       // lo arma la herramienta
    kind: "design_document", schema_version: 1, editor_key: "konva",
    design_name, design_document: { version: 1, pages: [ /* ... */ ] }
  }
})
```

Reglas:
- La respuesta NO devuelve el `typed_payload`; confírmalo con `get_brand_center_item_detail`.
- **Crear:** envía un `item_key` nuevo, sin `brand_center_item_id`. El `design_document` queda fijado.
- **Editar/recrear:** envía el `brand_center_item_id` del item existente para forzar la
  actualización. Sin ese id, un `item_key` ya existente puede preservar el diseño guardado en lugar
  de reemplazarlo.
- **Documento inválido = no se sube.** Si la herramienta reporta errores, corrige el documento; no
  intentes el upsert. Un documento que no parsea abre como bloqueado en el editor (no se edita ni se
  sobrescribe el contenido previo), así que subirlo no destruye datos pero deja el item inusable.
- **Gotcha de autoguardado:** si el editor está abierto en ese item, su autoguardado pisa el upsert.
  Re-sube con el editor cerrado en ese item (por ejemplo, navegando antes a otra vista).
- Handoff: `https://irrumpe.realestodo.com/brand/<brandId>/designer?item=<itemId>`.

## 2. Lectura y listado

- `get_brand_center_item_detail({ brand_center_item_id })` — recupera el item, incluido el
  `typed_payload` con el `design_document` actual. Úsalo para editar sobre lo existente y para
  verificar que un upsert persistió.
- `list_brand_center_items({ brand_id, dimension_key: "design" })` — lista los diseños de la marca
  (item_key, brand_center_item_id, title, status). Útil para mapear páginas a sus ids antes de
  editar o renderizar. La salida puede ser grande; filtra por `item_key`.

## 3. Archivado — `brand_center_item_archive`

`brand_center_item_archive({ brand_id, brand_center_item_id })` archiva (soft-delete, reversible) un
item. Úsalo para retirar versiones obsoletas de una migración sin borrar nada de forma permanente.

## 4. Subida de media a R2 — sin base64

Las imágenes y videos deben vivir en una URL pública de R2 (`pipelines.realestodo.com`, CORS `*`) y
referenciarse en `src` / `fillSpec.src`. Los binarios nunca se incrustan en el JSON ni pasan por el
contexto del modelo.

La ruta principal es el **staged upload por MCP**, modelado en el `stagedUploadsCreate` de Shopify: el
MCP prefirma y registra; el host sube los bytes directo a R2 con un PUT prefirmado. Acepta imágenes y
video.

| Ruta | Acepta | Notas |
|---|---|---|
| **staged upload por MCP** (`brand_center_file_staged_upload_create` + `_finalize`) | raster (png/jpeg/webp/gif/avif), svg, pdf, fonts hasta 100 MB; video mp4/webm/mov hasta 500 MB | Ruta principal. Los bytes van por un PUT prefirmado directo a R2; el MCP solo prefirma y registra. |
| `brand-center-file-upload` (edge, multipart) | raster, svg, pdf, fonts. Rechaza video. | Ruta de la UI del Brand Center. API-only, multipart, tope de 50 MB en memoria, gate de billing. |
| `content-media-upload` (edge, multipart) | `image/*`, `video/*` | Ruta de media de documentos nativos. |

### Staged upload por MCP — create → PUT → finalize

Tres pasos. El paso del medio corre en el host (shell); el MCP solo prefirma y registra.

1. **`brand_center_file_staged_upload_create`** — entrega `brand_id`, `dimension_key` (`"design"` para
   media de un diseño, `"image_bank"` para imágenes de marca, …) y `files[]` con
   `{ filename, mime_type, byte_size, sha256? }`. Devuelve `staged_targets[]` con `upload_url` (PUT
   prefirmado), `upload_headers`, `r2_object_key`, `resource_url` (la URL pública final) y `expires_at`
   (10 min). Hasta 50 archivos por llamada.
2. **PUT directo a R2** — el host sube los bytes:
   `curl -X PUT --data-binary @archivo "<upload_url>" -H "Content-Type: <mime>"`. Sin token: la URL ya
   va firmada (SigV4). El `byte_size` y el `sha256` se sacan en el host (`stat -f%z`, `shasum -a 256`).
3. **`brand_center_file_staged_upload_finalize`** — entrega `brand_id` y `staged[]` con
   `{ r2_object_key, item_id?, file_role?, metadata? }`. El backend lee el objeto por streaming,
   recomputa sha256 + tamaño, re-verifica los magic bytes, registra el archivo y dispara el mirror de
   svg/pdf. Devuelve `files[]` con `{ file, public_url }` y `rejected[]` por archivo (un mismatch de
   contenido borra el objeto huérfano). Esa `public_url` va en la capa.

Para colgar el archivo de un item, primero `brand_center_item_upsert` y pasa su `brand_center_item_id`
como `item_id` en `finalize`. Sin `item_id`, el archivo queda suelto en su dimensión y se referencia
solo por URL (suficiente para el `src` de una capa).

Reglas de seguridad:
- Nunca leas la sesión del usuario, cookies ni `localStorage` para forzar la subida. El `create` y el
  `finalize` corren con tu actor del MCP; el PUT usa la URL prefirmada.
- Los bytes van únicamente por el PUT directo a R2. Prohibido base64 o multipart a través del modelo.
- En el PUT manda exactamente el `Content-Type` que devolvió `create`.

### Subida masiva (recreación)

Para muchos media locales (un export `.pptx`): saca `byte_size` + `sha256` de cada archivo en el host,
llama a `create` con el `files[]` completo (batch hasta 50), sube cada uno con `curl` a su `upload_url`,
y llama a `finalize` con todos los `r2_object_key`. Revisa `rejected[]` y reintenta solo esos. El
resultado es un mapa `{ filename: public_url }` que alimenta el ensamblado. No hace falta servidor
local con CORS ni pestaña autenticada del Front.

## 5. Verificación del render

El editor renderiza con `window.Konva`. Para verificar una página sin meter la imagen cruda en el
contexto: localiza el nodo del frame (`#pN-frame`), exporta su rect con `stage.toDataURL`, y manda el
dataURL por trozos a un servidor local que lo guarda en disco; decodifica a JPEG y compáralo con el
original. Espera a `document.fonts.ready` y a que carguen las imágenes de R2 antes de exportar. El
video no se rasteriza en este export (se ve solo en previsualización/exportación del editor).
