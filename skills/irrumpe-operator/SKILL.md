---
name: "irrumpe-operator"
description: "Usar para operar Irrumpe vía MCP: contenido, diseños desde briefs aprobados, Brand Center, Pulso, Ads, proyectos, tareas, estados y onboarding seguro."
---

# Irrumpe Operator — operar la plataforma vía MCP

Skill de operación de Irrumpe. Su pericia es la interacción con el MCP remoto
(`https://mcp.realestodo.com/mcp`): qué tool llamar para cada necesidad, la forma exacta de cada
payload, dónde vive cada dato y qué guardrails protegen cada escritura. El criterio creativo y
estratégico queda del lado del usuario; esta skill ejecuta, consulta, verifica y reporta.

## Idioma y voz

Responder en el idioma y registro regional del usuario. Usar su redacción y el `locale` de una
lectura de cuenta confirmada como señales; si no existe una señal regional, usar español internacional
claro. Cuando ambas señales indiquen una variante concreta, mantener también su gramática de
segunda persona (tuteo, voseo u otra) sin agregar jerga ni caricaturizarla. Preservar literalmente
el texto aportado por el usuario y el contenido existente: no normalizar dialecto, tono ni
ortografía sin que lo pida. Al redactar texto nuevo, priorizar la forma de segunda persona que el
usuario haya usado explícitamente; al mostrar un mensaje devuelto por el servidor, citarlo sin
reescribir su variante. Mantener en inglés los nombres de tools, campos y valores JSON porque son
identificadores del contrato.

## Arranque de sesión — obligatorio

Al comenzar una sesión o después de reautenticar:

1. Descubrir las lecturas de cuenta y acceso a marcas efectivamente soportadas por el MCP y resolver
   identidad, `locale`, `brand_id` y flags de capacidad sólo con sus resultados. Si una lectura
   anunciada devuelve error, reportar su nombre y mensaje literal y detener la operación dependiente.
2. Para una operación con marca, usar la lectura vigente de marcas accesibles y sus flags de
   capacidad (`can_view`, `can_edit`, `can_manage_settings`, `can_manage_brand_center`,
   `can_manage_billing`, …). Con varias marcas y un encargo ambiguo, preguntar en lugar de asumir.
3. Para una operación de cuenta o notificaciones sin marca, omitir la resolución de `brand_id`.
4. El onboarding carga `brand-onboarding`; esa skill confirma su propio contrato antes de iniciar,
   guardar o enviar una ficha.

## Mapa de ruteo

Lee la reference del dominio ANTES de operar en él; ahí viven los contratos completos.

| Dominio | Tools principales | Reference |
|---|---|---|
| Contenido, documentos, media, briefs, planificación, hilos | `list_brand_content`, `create_content`, `content_update`, `append_document_blocks`, `replace_block_text`, `content_media_url_import`, `create_domain_item`, `import_brand_planning` | `references/contenido-y-documentos.md` |
| Diseños Konva y assets del Brand Center | `brand_center_item_upsert`, `get_brand_center_item_detail`, `list_brand_center_items`, `search_brand_assets`, `brand_center_file_staged_upload_create/_finalize` | `references/diseno-brand-center.md` |
| Formato del design_document (spec Konva) | — | `references/formato-design-document.md` |
| Campañas Google Ads | `list_brand_ads_*`, escrituras tipadas `ads_*`, `ads_campaign_keyword_match_type_set`, `ads_action_approve` | `references/ads.md` |
| Métricas de Pulso | `get_brand_performance_availability`, `get_brand_performance_dashboard`, `list_brand_metric_snapshots`, `list_brand_metric_timeseries` | `references/pulso-metricas.md` |
| Proyectos, tareas, asignaciones, estados, aprobaciones | `list_brand_projects`, `project_update`, `list_brand_tasks`, `task_update`, `task_status_set`, `replace_task_assignees`, `apply_status_transition`, `set_content_status` | `references/proyectos-tareas-estados.md` |
| Onboarding de marca | — | Cargar la skill `brand-onboarding`; ella es dueña del contrato, los guardrails y la referencia del flujo. |
| Equipo de la marca | `list_brand_team` | — (contrato simple, usar directo). Las notificaciones no forman parte de la superficie pública del MCP. |

## Guardrails duros

Reglas que ninguna reference relaja:

1. **Permisos por booleanos, jamás por etiquetas.** La autoridad de escritura sale de los flags
   `can_edit` / `can_manage_*` de `list_user_accessible_brands`. Una etiqueta de rol
   (`brand_access_role`, `membership_role`) es informativa; nunca fundamenta una escritura.
2. **Guardrail roto = reporte inmediato.** Una escritura denegada se explica al usuario con el
   permiso faltante, sin reintentos por rutas alternativas. Y una escritura que tuvo éxito cuando
   los flags decían que debía fallar (p. ej. un viewer que logra escribir) se reporta de forma
   explícita como posible falla de permisos de la plataforma.
3. **Diseño sin dirección creativa autónoma.** Componer un `design_document` solo desde un brief
   explícito aprobado por el usuario, un diseño existente o un template. Cuando falten concepto,
   jerarquía, contenido o formato, pedirlos antes de componer; no inventar una campaña ni un sistema
   visual.
4. **Diseño: validador obligatorio cuando el host lo puede ejecutar.** Resolver
   `tools/validar_design_document.py` sólo desde una raíz instalada que el host exponga. En Claude
   Code, la raíz instalada es `${CLAUDE_PLUGIN_ROOT}` y la herramienta vive en
   `${CLAUDE_PLUGIN_ROOT}/tools/validar_design_document.py`. Si el host no expone esa variable pero
   da una ruta de la skill y acceso local, verificar que `../../tools/validar_design_document.py`
   exista desde `SKILL.md`, convertirla a ruta absoluta y ejecutarla; nunca buscar `tools/` desde el
   workspace del usuario. Si el host no expone ejecución local o la ruta no existe, no afirmar una
   validación ni hacer un upsert de diseño: explicar que hace falta el validador empaquetado o una
   validación equivalente confirmada por el MCP. El upsert usa el `upsert_arguments` devuelto tal
   cual. Armar el `typed_payload` a mano está prohibido.
5. **Ads: `dry_run` explícito, confirmación y estado real.** `dry_run: true` no despacha al provider,
   pero puede crear una acción en Irrumpe; obtener confirmación antes de usarlo. Una solicitud real
   requiere además `dry_run: false`. Reportar el `status` crudo de `runtime.integration_actions`; no
   sustituirlo por etiquetas inventadas. Las acciones `approved` o `running` todavía pueden estar en
   cola o ejecución.
6. **Media externa sin base64 y por la ruta de su dominio.** En diseños y Brand Center, todo archivo
   aportado por el usuario o descargado de otra fuente va obligatoriamente por staged upload
   (create → PUT → finalize). `content_media_url_import` se usa solo para media de contenido o
   documentos cuya fuente sea una URL http(s); no es una ruta de carga para diseños ni Brand Center.
   Los bytes nunca pasan por el contexto del modelo. El soporte `data:` del formato se limita a SVG
   textual creado por el modelo cuando una forma nativa no alcanza.
7. **Configuración local con consentimiento.** Antes de ejecutar `claude mcp add`, `codex mcp add`,
   editar archivos de configuración o instalar dependencias, explicar el cambio y obtener
   confirmación explícita. Guiar manualmente cuando la superficie no permita modificar archivos.
8. **Datos reales, jamás inventados.** Todo id, token, métrica y enunciado sale de una lectura del
   MCP. Un dato faltante se reporta como faltante.

## Arcos de trabajo

- **Editar contenido:** localizar con `list_brand_content`, metadata con `content_update`, cuerpo
  con `append_document_blocks` / `replace_block_text`, verificación con relectura.
- **Aprobar / rechazar:** resolver el estado y las acciones disponibles
  (`get_content_status_options`, `list_workflow_statuses`), transicionar con
  `apply_status_transition` (`approve` / `request_changes` + `reason`), releer y reportar.
- **Crear o editar un diseño:** confirmar el brief/template de entrada, leer la spec y los
  contratos, componer el `design_document`, resolver y ejecutar el validador, subir media por staged
  upload, hacer upsert, verificar con `get_brand_center_item_detail` y entregar el handoff. Declarar
  la validación visual pendiente hasta contar con un render real o la inspección del usuario.
- **Cargar / consultar assets:** `search_brand_assets` y los listados por dimensión para leer;
  staged upload + `brand_center_item_upsert` para cargar.
- **Consultar Pulso:** availability → dashboard (`preset`) → snapshots/timeseries para el detalle.
- **Operar campañas:** lecturas `list_brand_ads_*`, cambio mínimo tipado con `dry_run`, reporte de la
  acción creada y polling con `list_brand_integration_actions` cuando exista despacho. Tras
  `succeeded`, esperar la resincronización indicada por el tool antes de validar en las vistas Ads.
- **Enviar briefs / crear items:** `create_domain_item` con la `surface` correcta, cuerpo con
  `append_document_blocks`; planificación con `import_brand_planning`.
- **Proyectos y tareas:** listar → crear (`create_domain_item`) o editar (`project_update`,
  `task_update`, `task_status_set`, `task_schedule_set`, `replace_task_assignees`).

## Manejo de errores

- 401 → guiar re-autenticación OAuth del MCP y releer el estado. Nunca repetir una escritura cuyo
  resultado quedó desconocido.
- 402 `plan_required` → informar que la operación no está disponible en el plan actual y
  detenerse. El contrato público no expone ofertas, precios ni metadata comercial.
- 409 `content_revision_changed` → releer el documento y reintentar sólo con
  `expected_content_revision` actualizado; no reutilizar una revisión vencida.
- 422 `onboarding_incomplete` → mostrar únicamente los campos tipados de `detail.failing` y
  volver al campo indicado; no inferir detalles internos desde el mensaje.
- 403 → reportar el permiso faltante (guardrail 2), sin rodeos ni rutas alternativas.
- Tool ausente en la sesión → registrar el blocker y avisar; nunca improvisar el contrato por otra
  vía.

## Autochequeo — antes de cerrar cualquier escritura

- [ ] El flag de capacidad (`can_edit` / `can_manage_*`) autorizaba la operación.
- [ ] La reference del dominio se leyó y el payload respeta su contrato.
- [ ] Diseño: existía brief/template, el validador se resolvió desde el plugin, corrió con 0 errores
      y el upsert usó su `upsert_arguments`; no se afirmó calidad visual sin inspección.
- [ ] Ads: `dry_run` fue explícito y tuvo confirmación; el cambio real tuvo confirmación adicional y
      se reportó el estado crudo; una acción despachada se siguió hasta estado terminal.
- [ ] El resultado se verificó con una lectura posterior.
- [ ] El usuario recibió identificadores, estado resultante y cualquier anomalía detectada.
