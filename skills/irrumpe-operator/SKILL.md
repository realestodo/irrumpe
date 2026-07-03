---
name: "irrumpe-operator"
description: "Operador de la plataforma Irrumpe vía MCP: contenido, diseños, Brand Center, métricas Pulso, campañas ads, proyectos, tareas, estados y onboarding. Contratos y guardrails."
---

# Irrumpe Operator — operar la plataforma vía MCP

Skill de operación de IrrumpeOS. Su pericia es la interacción con el MCP de Irrumpe
(`https://mcp.realestodo.com/mcp`): qué tool llamar para cada necesidad, la forma exacta de cada
payload, dónde vive cada dato y qué guardrails protegen cada escritura. El criterio creativo y
estratégico queda del lado del usuario; esta skill ejecuta, consulta, verifica y reporta.

## Idioma y voz

Comunicación con el usuario en su idioma; en español, siempre neutro (el voseo rioplatense —
`vos`, `querés`, `tenés`, `mirá` — está prohibido). Nombres de tools, campos y valores JSON van en
inglés: son identificadores, jamás se traducen.

## Arranque de sesión — obligatorio

Antes de cualquier operación:

1. `get_user_account_state` — identidad, `user_type` y locale del actor.
2. `list_user_accessible_brands` — marcas visibles con `membership_role`, `brand_access_role` y los
   flags de capacidad (`can_view`, `can_edit`, `can_manage_settings`, `can_manage_brand_center`,
   `can_manage_billing`, …).
3. Resolver el `brand_id` de trabajo. Con varias marcas visibles y un encargo ambiguo, pregunta al
   usuario en lugar de asumir.

## Mapa de ruteo

Lee la reference del dominio ANTES de operar en él; ahí viven los contratos completos.

| Dominio | Tools principales | Reference |
|---|---|---|
| Contenido, documentos, media, briefs, planificación, hilos | `list_brand_content`, `create_content`, `content_update`, `append_document_blocks`, `replace_block_text`, `content_media_url_import`, `create_domain_item`, `import_brand_planning` | `references/contenido-y-documentos.md` |
| Diseños Konva y assets del Brand Center | `brand_center_item_upsert`, `get_brand_center_item_detail`, `list_brand_center_items`, `search_brand_assets`, `brand_center_file_staged_upload_create/_finalize` | `references/diseno-brand-center.md` |
| Formato del design_document (spec Konva) | — | `references/formato-design-document.md` |
| Campañas Google Ads | `list_brand_ads_*`, escrituras tipadas `ads_*`, `ads_action_approve` | `references/ads.md` |
| Métricas de Pulso | `get_brand_performance_availability`, `get_brand_performance_dashboard`, `list_brand_metric_snapshots`, `list_brand_metric_timeseries` | `references/pulso-metricas.md` |
| Proyectos, tareas, asignaciones, estados, aprobaciones | `list_brand_projects`, `project_update`, `list_brand_tasks`, `task_update`, `task_status_set`, `replace_task_assignees`, `apply_status_transition`, `set_content_status` | `references/proyectos-tareas-estados.md` |
| Onboarding de marca (comando `/onboarding`) | `brand_onboarding_start/save/submit`, `list_brand_onboarding_question_catalog`, `get_brand_onboarding_current` | `references/onboarding-de-marca.md` |
| Notificaciones y equipo | `list_notifications`, `notification_mark_read`, `list_brand_team` | — (contratos simples, usar directo) |

## Guardrails duros

Reglas que ninguna reference relaja:

1. **Permisos por booleanos, jamás por etiquetas.** La autoridad de escritura sale de los flags
   `can_edit` / `can_manage_*` de `list_user_accessible_brands`. Una etiqueta de rol
   (`brand_access_role`, `membership_role`) es informativa; nunca fundamenta una escritura.
2. **Guardrail roto = reporte inmediato.** Una escritura denegada se explica al usuario con el
   permiso faltante, sin reintentos por rutas alternativas. Y una escritura que tuvo éxito cuando
   los flags decían que debía fallar (p. ej. un viewer que logra escribir) se reporta de forma
   explícita como posible falla de permisos de la plataforma.
3. **Diseño: validador siempre.** Cada upsert de diseño pasa antes por
   `python3 tools/validar_design_document.py`; el upsert usa el `upsert_arguments` devuelto tal
   cual. Armar el `typed_payload` a mano está prohibido.
4. **Ads: `dry_run` explícito y confirmación.** Preview con `dry_run: true`; el cambio real requiere
   confirmación del usuario y `dry_run: false`. `pre_revision` es un resultado válido.
5. **Onboarding: `brand_onboarding_personality_set` prohibido.** La personalidad la asigna revisión
   humana interna. `brand_onboarding_submit` requiere confirmación explícita del usuario.
6. **Media sin base64.** Los bytes van por staged upload (create → PUT → finalize) o por
   `content_media_url_import`; nunca por el contexto del modelo.
7. **Datos reales, jamás inventados.** Todo id, token, métrica y enunciado sale de una lectura del
   MCP. Un dato faltante se reporta como faltante.

## Arcos de trabajo

- **Editar contenido:** localizar con `list_brand_content`, metadata con `content_update`, cuerpo
  con `append_document_blocks` / `replace_block_text`, verificación con relectura.
- **Aprobar / rechazar:** resolver el estado y las acciones disponibles
  (`get_content_status_options`, `list_workflow_statuses`), transicionar con
  `apply_status_transition` (`approve` / `request_changes` + `reason`), releer y reportar.
- **Crear o editar un diseño:** leer la spec y los contratos, componer el `design_document`, validar
  con la herramienta, subir media por staged upload, upsert, verificar con
  `get_brand_center_item_detail` y entregar el handoff.
- **Cargar / consultar assets:** `search_brand_assets` y los listados por dimensión para leer;
  staged upload + `brand_center_item_upsert` para cargar.
- **Consultar Pulso:** availability → dashboard (`preset`) → snapshots/timeseries para el detalle.
- **Operar campañas:** lecturas `list_brand_ads_*`, cambio mínimo tipado con `dry_run`, reporte del
  estado devuelto (`applied` / `pre_revision` / `preview` / `blocked`).
- **Enviar briefs / crear items:** `create_domain_item` con la `surface` correcta, cuerpo con
  `append_document_blocks`; planificación con `import_brand_planning`.
- **Proyectos y tareas:** listar → crear (`create_domain_item`) o editar (`project_update`,
  `task_update`, `task_status_set`, `task_schedule_set`, `replace_task_assignees`).
- **Onboarding de marca:** flujo completo en `references/onboarding-de-marca.md`; entrada natural
  por el comando `/onboarding`.

## Manejo de errores

- 401 → guiar re-autenticación OAuth del MCP y reintentar una vez.
- 402 `requires_paid_plan` → mostrar el mensaje y el payload `upsell` tal como llegan; detenerse.
- 403 → reportar el permiso faltante (guardrail 2), sin rodeos ni rutas alternativas.
- Tool ausente en la sesión → registrar el blocker y avisar; nunca improvisar el contrato por otra
  vía.

## Autochequeo — antes de cerrar cualquier escritura

- [ ] El flag de capacidad (`can_edit` / `can_manage_*`) autorizaba la operación.
- [ ] La reference del dominio se leyó y el payload respeta su contrato.
- [ ] Diseño: el validador corrió con 0 errores y el upsert usó su `upsert_arguments`.
- [ ] Ads: `dry_run` fue explícito y el cambio real tuvo confirmación del usuario.
- [ ] El resultado se verificó con una lectura posterior.
- [ ] El usuario recibió identificadores, estado resultante y cualquier anomalía detectada.
