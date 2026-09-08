# Contenido y documentos — contratos MCP

Cómo se crea, edita, consulta y estructura el contenido nativo de Irrumpe: items de calendario,
documentos ricos, media y briefs. Prosa en español; nombres de tools, campos y valores en inglés.

---

## Índice

1. [Modelo](#1-modelo)
2. [Descubrimiento y lectura](#2-descubrimiento-y-lectura)
3. [Crear y editar contenido](#3-crear-y-editar-contenido)
4. [Media de contenido y documentos](#4-media-de-contenido-y-documentos)
5. [Escribir el cuerpo](#5-escribir-el-cuerpo--append_document_blocks)
6. [Versiones de documento](#6-versiones-de-documento)
7. [Briefs e items de dominio](#7-briefs-e-items-de-dominio--create_domain_item)
8. [Hilos sociales](#8-hilos-sociales)
9. [Verificación posterior a escritura](#9-verificación-posterior-a-escritura)

## 1. Modelo

Un **contenido** es un item del calendario de la marca con metadata operativa (título, caption,
plataformas, formatos, agenda, estado) y un **documento nativo editable** (`body_document_id`) cuyo
cuerpo son bloques Plate/Yjs. La metadata se edita con tools estructuradas; el cuerpo se edita con
las tools de bloques. Mezclar ambos planos produce documentos rotos.

## 2. Descubrimiento y lectura

| Necesidad | Tool |
|---|---|
| Buscar/filtrar contenidos de la marca | `list_brand_content` (`brand_id`, `query`, `status_code`, `status_phase`, `content_type`, `date_from/date_to`, `content_id`, `body_document_id`) |
| Calendario agendado | `list_content_calendar` (`brand_id`, `start_date`, `end_date`) |
| Metadata + bloques proyectados + versiones recientes de un documento | `get_document_detail` (`document_id`) |
| Árbol de bloques paginado | `get_document_blocks` (`body_document_id`, `parent_block_id`, `limit`, `offset`) |
| Media activa de un documento | `list_document_media_assets` |
| Contenidos eliminados (papelera) | `list_deleted_brand_content` |

## 3. Crear y editar contenido

### `create_content`

Crea el item de calendario junto con su documento nativo. Campos: `brand_id`, `title` (≤240,
obligatorio), `caption` (≤5000), `platforms[]`, `formats[]`, `deadline` (date), agenda
(`schedule_start_date/time`, `schedule_end_date/time`, `schedule_timezone`, default
`America/Santiago`), `media[]` con `{ media_asset_id }`.

### `content_update`

PATCH de metadata: `brand_id` + `content_id` obligatorios; acepta `title`, `caption`, `contexto`
(≤10000), `hashtags_keywords`, `objetivo[]`, `platforms[]`, `formats[]`, `deadline` /
`clear_deadline`, agenda / `clear_schedule`. El backend valida acceso a la marca, rol del actor,
campos editables y semántica del rango de agenda.

### Frontera caption / hashtags

- `caption` es el texto publicable. Los hashtags viven en `hashtags_keywords`, fuera del caption.
- Nunca anexes hashtags al final del caption ni los guardes en `contexto`.
- Metadata (objetivo, plataforma, formato, deadline, estado) va en sus campos nativos, nunca dentro
  del cuerpo del documento.

### Otras operaciones

`content_duplicate`, `content_delete` (papelera; restaurar con `brand_trash_restore`),
`content_media_add` / `content_media_remove` / `content_media_reorder` (adjuntos por
`media_asset_id`).

## 4. Media de contenido y documentos

`content_media_url_import` descarga una URL http(s) del lado del servidor, guarda los bytes en R2 y
devuelve `media_asset_id` + un nodo de bloque listo para Plate. Campos: `brand_id`, `source_url`
obligatorios; `content_id` o `document_id` para asociarla; `usage_context`
(`block` | `content_media` | `draft_content_media`); `client_import_id` para idempotencia. El media
inline o base64 se rechaza: los bytes nunca pasan por el contexto del modelo.

## 5. Escribir el cuerpo — `append_document_blocks`

La tool de autoría del cuerpo nativo. `body_document_id` + `blocks[]` (1–200). `mode: "append"`
(default) agrega al final y colapsa el párrafo semilla de un documento recién creado;
`mode: "replace"` reescribe el cuerpo completo y exige `expected_content_revision`.

Bloques hoja: `p`, `h1`–`h6`, `blockquote`, `code_block` (opcional `language`), `ul` / `ol`
(`items[]`), `to_do` (`text`, `checked`), `hr`, `page_break`, `toc`, `equation` (`expression`),
`table` (`rows[][]`, `header: true` para encabezado), `image` / `video` (por `media_asset_id` de un
asset activo del documento), `audio` / `file` / `bookmark` (URL https externa), `embed`
(YouTube/Vimeo/Loom/Spotify), `mention_card` (`ref_kind` + `ref_id` uuid + `ref_title`, enlaza otra
entidad nativa).

Bloques de layout: `callout` (icono emoji opcional + `children`), `toggle` (`title` + `children`),
`column_group` (2–6 `column`, cada una con bloques hoja y callouts).

Formato inline dentro de textos, items de lista, celdas y captions: subset markdown que el server
convierte a marcas nativas — `**bold**`, `*italic*`, `__underline__`, `~~strikethrough~~`,
`` `code` `` y `[label](https://url)`. La estructura de bloques nunca se expresa con markdown: sin
`#` inicial, sin `-`, sin `>` ni tablas pipe. En la superficie publicada no deben quedar marcadores
markdown visibles.

### Corrección puntual — `replace_block_text`

Reemplazo de texto de UN bloque existente, guardado por revisión: `body_document_id`, `block_id`,
`expected_content_revision`, `expected_current_text`, `replacement_text`. Para campos de dominio usa
primero las tools estructuradas (`content_update`, `task_update`, `project_update`,
`planning_update`, `update_changelog_report`).

## 6. Versiones de documento

- `list_document_versions` (`document_id`) — historial visible al usuario.
- `document_version_restore` (`version_id`) — restaura una versión.
- `document_version_milestone` — marca un hito. No existe eliminación de versiones en la superficie
  pública del MCP; si alguien la pide, explicar que esa operación no está disponible por esta vía.

## 7. Briefs e items de dominio — `create_domain_item`

Crea items nativos que llevan documento: `brand_id`, `surface`
(`irrumpe`, `conceptualization`, `strategy`, `planning_item`, `website`, `design_system`, `project`,
`task`, `change_log`, `ad_campaign`, `ad_group`, `ad_segment`, `audience`, `context`, `tagline`,
`homepage`), `title`, `status_code` (default `briefing`), `fields{}`, `relations{}`,
`body_markdown` (≤50000) o autoría posterior con `append_document_blocks`, `idempotency_key`.
El backend valida rol del actor, acceso a la marca, superficie permitida y estado inicial.
Para reportes finales de Changelog usa `create_changelog_report` en su lugar.

### Planificación — `import_brand_planning`

Importa filas de planificación completas: `brand_id`, `items[]` (1–50, cada fila exige
`macrociclo`, `periodo`, `descripcion` y las doce columnas de mes), `status_code` (default
`pre_revision`), `dry_run`, `idempotency_prefix`. Normaliza alias en español y rechaza campos
desconocidos. Lee el estado previo con `list_brand_planning`; edita filas con `planning_update`.

## 8. Hilos sociales

`create_social_thread` / `create_social_message` crean conversación asociada a la marca;
`list_social_threads` / `list_social_messages` la leen; `mark_social_thread_read` marca lectura.

## 9. Verificación posterior a escritura

1. Vuelve a leer lo escrito (`list_brand_content` con `content_id`, o `get_document_blocks`).
2. Confirma que el caption quedó sin hashtags y la metadata en sus campos.
3. Confirma que el cuerpo renderiza bloques nativos sin marcadores markdown visibles.
4. Reporta al usuario el identificador del recurso y su estado.
