# Diseño y Brand Center — contratos MCP

Cómo se crean, editan y archivan los diseños del editor Konva, cómo se consultan los assets del
Brand Center y cómo entran los archivos a R2. Prosa en español; tools, campos y valores en inglés.

---

## 1. Modelo

Un **diseño** es un item de Brand Center con `dimension_key: "design"` (o `"template"`), cuyo
`typed_payload` es la envoltura `{ kind: "design_document", schema_version: 1, editor_key: "konva",
design_name, design_document }`. El `design_document` es un `EditorDocument` JSON plano
(`{ version: 1, pages[] }`); la especificación completa del formato está en
`formato-design-document.md`. El Brand Center también guarda las demás dimensiones de la marca
(logos, paletas, tipografías, productos, banco de imágenes); consulta el listado vigente con
`list_brand_center_dimensions`.

## 2. Consultar assets

| Necesidad | Tool |
|---|---|
| Dimensiones activas del Brand Center | `list_brand_center_dimensions` |
| Items por dimensión | `list_brand_center_items` (`brand_id`, `dimension_key`) |
| Detalle de un item, incluido `typed_payload` | `get_brand_center_item_detail` (`brand_center_item_id`) |
| Búsqueda por texto y recencia | `search_brand_assets` (`brand_id`, `query`, `dimension_key`, `limit` ≤50) |
| Archivos (metadata, sin binarios) | `list_brand_center_files` (`brand_id`, `brand_center_item_id`, `mime_type`) |
| Carpetas y su contenido | `list_brand_center_folders`, `list_brand_center_folder_items` |
| Contexto semántico de assets | `resolve_brand_asset_context`, `get_brand_asset` |

Las búsquedas devuelven resúmenes de metadata; los binarios nunca viajan por el MCP.

## 3. Crear y editar diseños — `brand_center_item_upsert`

El backend valida solo que `typed_payload` sea un objeto JSON; la validación real de la estructura
Konva la hace el editor al cargar. Un documento malformado se guarda sin error de API y el editor lo
bloquea al abrirlo. Por eso la verificación previa con `tools/validar_design_document.py` es
obligatoria en cada upsert de diseño.

**Flujo:** valida el `design_document` con la herramienta; ella devuelve `upsert_arguments`; pasa ese
objeto **tal cual** como argumentos de `brand_center_item_upsert`. Armar la envoltura a mano está
prohibido.

Los argumentos del tool son **planos** (sin objeto `payload` envolvente):

```jsonc
brand_center_item_upsert({
  brand_id,
  dimension_key: "design",              // o "template"
  title,
  item_key: "design-<slug>-pNN",        // crear: item_key nuevo, sin brand_center_item_id
  brand_center_item_id: "<uuid>",       // editar: fuerza la actualización del item existente
  typed_payload: { /* lo arma la herramienta */ }
})
```

Reglas:
- La respuesta NO devuelve el `typed_payload`; confírmalo con `get_brand_center_item_detail`.
- **Crear:** `item_key` nuevo, sin `brand_center_item_id`.
- **Editar:** lee el documento actual con `get_brand_center_item_detail`, modifica y re-sube **con el
  `brand_center_item_id` explícito**. Sin ese id, un `item_key` existente puede preservar el diseño
  guardado en lugar de reemplazarlo.
- **Documento inválido = no se sube.** Si la herramienta reporta errores, corrige el documento antes
  de intentar el upsert. Revisa también las advertencias (`media://` sin resolver, datos de chart no
  positivos, fuentes sin stack de fallback).
- **Lint de layout (`LAYOUT_*`).** La herramienta también audita la geometría del documento y
  advierte: elementos que sobresalen de su frame (`LAYOUT_OUT_OF_FRAME`), capas raíz fuera de todo
  artboard, bordes casi alineados a 1–6 px de la línea que comparten sus hermanos
  (`LAYOUT_NEAR_ALIGNED`), ritmos verticales casi parejos (`LAYOUT_IRREGULAR_SPACING`), textos que
  se pisan (`LAYOUT_TEXT_OVERLAP`, con alturas estimadas) y texto de bajo contraste contra el fondo
  sólido que tiene debajo (`LAYOUT_LOW_CONTRAST`). Son advertencias: corrige cada una o justifícala
  ante el usuario como decisión de diseño (badges rotados y fondos full-bleed ya están exentos).
  `--no-layout-lint` las silencia cuando el encargo las acepta de forma explícita.
- **Gotcha de autoguardado:** si el editor está abierto en ese item, su autoguardado pisa el upsert.
  Re-sube con el editor cerrado en ese item.
- Handoff al usuario: `https://irrumpe.realestodo.com/brand/<brandId>/designer?item=<itemId>`.
- Tokens reales: toda tipografía y color del diseño salen del Brand Center de la marca (paletas,
  fuentes vía `list_brand_fonts`). Si falta un token, repórtalo; nunca lo inventes.

## 4. Archivar — `brand_center_item_archive`

`brand_center_item_archive({ brand_id, brand_center_item_id })` es un soft-delete reversible.
`brand_trash_restore` recupera desde la papelera; `list_brand_trash_items` la lista.

## 5. Cargar archivos a R2 — staged upload, sin base64

Imágenes, video, fuentes y documentos viven en una URL pública de R2
(`pipelines.realestodo.com`, CORS `*`). Los binarios nunca se incrustan en JSON ni pasan por el
contexto del modelo. Tres pasos; el del medio corre en el host (shell):

1. **`brand_center_file_staged_upload_create`** — `brand_id`, `dimension_key` (`"design"` para media
   de un diseño, `"image_bank"` para imágenes de marca, …) y `files[]` con
   `{ filename, mime_type, byte_size, sha256? }`. Devuelve `staged_targets[]` con `upload_url` (PUT
   prefirmado), `upload_headers`, `r2_object_key`, `resource_url` y `expires_at` (10 min). Hasta 50
   archivos por llamada. Acepta raster (png/jpeg/webp/gif/avif), svg, pdf y fuentes hasta 100 MB;
   video mp4/webm/mov hasta 500 MB.
2. **PUT directo a R2** — el host sube los bytes:
   `curl -X PUT --data-binary @archivo "<upload_url>" -H "Content-Type: <mime>"`. La URL ya va
   firmada. `byte_size` y `sha256` se calculan en el host (`stat`, `shasum -a 256`). Manda
   exactamente el `Content-Type` que devolvió `create`.
3. **`brand_center_file_staged_upload_finalize`** — `brand_id` y `staged[]` con
   `{ r2_object_key, item_id?, file_role?, metadata? }`. El backend recomputa hash y tamaño,
   re-verifica magic bytes y registra el archivo. Devuelve `files[]` con `{ file, public_url }` y
   `rejected[]` por archivo. Esa `public_url` es la que se referencia en las capas (`src`,
   `fillSpec.src`).

Para colgar el archivo de un item, primero haz el `brand_center_item_upsert` y pasa su
`brand_center_item_id` como `item_id` en `finalize`. Sin `item_id` el archivo queda suelto en su
dimensión, referenciable solo por URL.

Subida masiva: calcula `byte_size` + `sha256` de todos los archivos en el host, llama a `create` con
el `files[]` completo, sube cada uno con `curl` y llama a `finalize` con todos los `r2_object_key`.
Revisa `rejected[]` y reintenta solo esos.

Reglas de seguridad:
- Nunca leas sesión, cookies ni `localStorage` del usuario para forzar una subida. `create` y
  `finalize` corren con el actor del MCP; el PUT usa la URL prefirmada.
- Los bytes van únicamente por el PUT directo a R2. Base64 y multipart a través del modelo están
  prohibidos.

## 6. Guardar outputs generados

`brand_center_output_save` persiste outputs de generación asociados al Brand Center;
`upsert_brand_asset` / `archive_brand_asset` administran assets sueltos;
`upsert_brand_visual_system` actualiza el sistema visual.

## 7. Verificación posterior

1. `get_brand_center_item_detail` confirma que el `typed_payload` persistió.
2. Para diseños: renderiza o pide al usuario abrir el handoff antes de declarar el trabajo listo. Un
   documento que valida puede verse mal (texto desbordado, fondo equivocado).
3. Para archivos: la `public_url` debe responder `200` con el `content-type` esperado.
