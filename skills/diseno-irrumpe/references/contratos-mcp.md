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
referenciarse en `src` / `fillSpec.src`. **Nunca** se incrustan binarios en el JSON ni pasan por el
contexto del modelo. Hoy hay dos rutas:

| Ruta | Acepta | Devuelve | Notas |
|---|---|---|---|
| `brand-center-file-upload` (edge, multipart) | raster (png/jpeg/webp/gif/avif), svg, pdf, fonts. **Rechaza video.** | `public_url` | API-only. Verifica el tipo por magic bytes. Tiene gate de billing. |
| `content-media-upload` (edge, multipart) | `image/*` y `video/*` | `public_url` | Es la ruta para video mientras no exista el staged upload por MCP. |

El binario se envía como `multipart/form-data` con `file` + `brand_id` (+ `dimension_key:"design"`,
`file_role` para brand-center). La respuesta trae `public_url`; esa URL va en la capa.

### Gap conocido — staged upload por MCP

Hoy la subida de bytes es por edge function multipart, no hay tool MCP que suba archivos sin base64.
El objetivo (modelado en el `stagedUploadsCreate` de Shopify) es un par de tools MCP: una crea una
URL PUT prefirmada de R2 (S3-compat) y devuelve el target; el cliente sube los bytes directo a esa
URL; una segunda finaliza (verifica el objeto, registra, dispara el mirror). Hasta que exista, la
subida se hace por las edge functions de arriba.

### Patrón operativo de subida masiva (recreación)

Cuando hay muchos media locales (un export `.pptx`), se sirven por un servidor local con CORS
permisivo; una pestaña autenticada de Irrumpe los lee y los `POST`ea a la edge function con la sesión
del usuario, refrescando el token cuando está por expirar. Los bytes nunca tocan el contexto del
modelo. El resultado es un mapa `{ filename: public_url }` que alimenta el ensamblado.

## 5. Verificación del render

El editor renderiza con `window.Konva`. Para verificar una página sin meter la imagen cruda en el
contexto: localiza el nodo del frame (`#pN-frame`), exporta su rect con `stage.toDataURL`, y manda el
dataURL por trozos a un servidor local que lo guarda en disco; decodifica a JPEG y compáralo con el
original. Espera a `document.fonts.ready` y a que carguen las imágenes de R2 antes de exportar. El
video no se rasteriza en este export (se ve solo en previsualización/exportación del editor).
