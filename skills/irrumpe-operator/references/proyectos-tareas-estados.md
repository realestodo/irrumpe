# Proyectos, tareas y estados — contratos MCP

Cómo se consultan y modifican proyectos, tareas, asignaciones y transiciones de estado (incluida la
aprobación y el rechazo de documentos). Prosa en español; tools, campos y valores en inglés.

---

## Índice

1. [Proyectos](#1-proyectos)
2. [Tareas](#2-tareas)
3. [Vocabulario de estados](#3-vocabulario-de-estados)
4. [Aprobar o rechazar](#4-aprobar--rechazar--apply_status_transition)
5. [Versiones de documento](#5-versiones-de-documento)

## 1. Proyectos

### Lecturas

- `list_brand_projects` (`brand_id`, `query`, `status_code`, `status_phase`, `date_from/date_to`,
  `project_id`, `include_archived`) — proyectos con agenda y estado canónico de workflow.
- `list_brand_project_hierarchy` (`brand_id`, `project_id`, `parent_project_id`, `root_project_id`)
  — contexto padre/raíz; consúltala antes de crear o editar work items dentro de un proyecto.
- `list_brand_project_edges` — aristas entre proyectos y work items; `list_brand_work_items` — vista
  agregada.

### Crear

Un proyecto nuevo se crea con `create_domain_item` (`surface: "project"`, ver
`contenido-y-documentos.md` §7).

### Editar — `project_update`

PATCH de metadata y agenda: `brand_id` + `project_id` obligatorios; acepta `title` (≤240),
`deadline` / `clear_deadline`, agenda (`schedule_start_date/time`, `schedule_end_date/time`,
`schedule_timezone`) / `clear_schedule`, y `fields{}` para campos de dominio. Los cambios de estado
de workflow van por `apply_status_transition` (§4); `project_update` nunca cambia estados.

## 2. Tareas

### Lecturas

- `list_brand_tasks` (`brand_id`, `query`, `status_code`, `status_id`,
  `date_from/date_to`, `include_archived`) — tareas con estado canónico, agenda y asignaciones
  nativas.
- `list_brand_task_assignees`, `list_brand_task_links`, `list_task_status_options` — asignados,
  links y ciclo de vida operacional.

### Escrituras

Las tools de tarea usan parámetros con prefijo `p_`:

- `task_update` — PATCH: `p_task_id` + `p_patch` con claves permitidas `title`, `descripcion` y
  `prioridad`. Cualquier otra clave es rechazada como campo no soportado.
- `task_status_set` — `p_task_id` + `p_status_code ∈ {briefing, en_desarrollo, terminado,
  postergado, cancelado}` + `p_reason` opcional (≤1000). Las tareas usan este ciclo operacional y no
  aceptan acciones de revisión de documentos.
- `task_schedule_set` — `p_task_id` + `p_due_date` / `p_clear_due_date`, rango
  (`p_schedule_start_date/time`, `p_schedule_end_date/time`, `p_schedule_timezone`) /
  `p_clear_schedule`.
- `task_archive` — `p_task_id` + `p_reason` opcional. Archivado reversible.
- `task_links_replace` — `p_task_id` + `p_links[]`: reemplaza el set completo de links activos;
  envía siempre el conjunto entero, incluidos los que se conservan.

### Asignaciones

1. `search_task_assignee_candidates` (`brand_id`, `query`, `task_id`) — el set acotado de candidatos
   (miembros activos de la marca + admins internos).
2. `replace_task_assignees` (`task_id`, `assignee_user_ids[]` ≤20, ids validados del set de
   candidatos) — reemplaza los responsables activos; array vacío los limpia.

Nunca asignes un user id que no salió del set de candidatos.

### Crear

Una tarea nueva se crea con `create_domain_item` (`surface: "task"`).

## 3. Vocabulario de estados

`list_workflow_statuses` (`brand_id`, `surface`, `phase`, `code`, `review_owner`, `is_terminal`) —
el vocabulario canónico de estados y su semántica de rol/dueño de revisión para contenidos, tareas,
proyectos y demás work items. Consúltalo antes de razonar sobre un estado desconocido.

Para contenido:
- `get_content_status_options` (`brand_id`, `content_id` o `body_document_id`) — estado actual y
  opciones visibles para el usuario autenticado.
- `set_content_status` (`brand_id`, `target_status_code ∈ {briefing, en_desarrollo, para_revision,
  aprobado_publicar, publicado}`, `reason` opcional) — aplica un estado visible de contenido.

## 4. Aprobar / rechazar — `apply_status_transition`

Toda mutación de estado de workflow de documentos y work items pasa por este contrato:

```jsonc
apply_status_transition({
  action: "submit_for_internal_review" | "approve" | "request_changes" | "postpone" | "cancel",
  brand_id,
  document_id,
  logical_name: "tasks" | "projects" | "contents" | "ad_campaigns" | "planning_items"
              | "websites" | "irrumpes" | "conceptualizations" | "strategies"
              | "change_logs" | "reports" | "design_systems",
  reason                  // ≤1000; obligatorio en la práctica para request_changes
})
```

- **Aprobar** = `action: "approve"`. **Rechazar / pedir cambios** = `action: "request_changes"` con
  `reason` que explique qué corregir.
- El backend valida qué acciones permite el estado actual y el rol del actor; una acción no
  disponible devuelve error, y eso es información para el usuario, jamás algo que ocultar.
- Después de transicionar, relee el recurso y reporta el estado resultante.

## 5. Versiones de documento

`list_document_versions`, `document_version_restore`, `document_version_milestone` — detalladas en
`contenido-y-documentos.md` §6; aplican a cualquier documento nativo, incluidos los cuerpos de
tareas y proyectos.
