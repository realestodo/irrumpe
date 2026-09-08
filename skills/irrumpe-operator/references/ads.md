# Campañas Ads — contratos MCP

Cómo se leen y modifican campañas de Google Ads desde Irrumpe. El MCP controla permisos, auditoría,
ejecución real y pre-revisión; el operador prepara operaciones mínimas, tipadas y reversibles.
Prosa en español; tools, campos y valores en inglés.

---

## Índice

1. [Principio operativo](#1-principio-operativo)
2. [Lecturas](#2-lecturas)
3. [Escrituras tipadas](#3-escrituras-tipadas)
4. [Dry run explícito](#4-dry-run-explícito)
5. [Permisos y pre-revisión](#5-permisos-y-pre-revisión)
6. [Checklist previo a cada write](#6-checklist-previo-a-cada-write)
7. [Métricas y segmentos no expuestos](#7-métricas-y-segmentos-no-expuestos)
8. [Reporte posterior](#8-reporte-posterior)

## 1. Principio operativo

1. Resolver marca y campaña en el MCP.
2. Leer el estado desde las vistas Ads.
3. Preparar la acción mínima reversible.
4. Obtener confirmación antes de cualquier operación tipada, incluido un `dry_run`, y enviarla con
   `dry_run` explícito.
5. Reportar el resultado real devuelto por el MCP.

## 2. Lecturas

| Necesidad | Tool |
|---|---|
| Campañas | `list_brand_ads_campaigns` |
| Ad groups | `list_brand_ads_ad_groups` |
| Ads / creatividades | `list_brand_ads_ads` |
| Keywords positivas y negativas | `list_brand_ads_keywords` |
| Audiencias del provider | `list_brand_ads_audiences` |
| Audiencias fundacionales de Irrumpe | `list_brand_audiences` |

Cuando una lectura necesaria carezca de tool en la sesión, registra el blocker y opera solo con lo
disponible; nunca escribas a ciegas.

## 3. Escrituras tipadas

| Operación | Tool |
|---|---|
| Estado de campaña | `ads_campaign_status_set` |
| Presupuesto diario | `ads_campaign_budget_set` |
| Bidding | `ads_campaign_bidding_set` |
| Fechas | `ads_campaign_dates_set` |
| Horarios | `ads_campaign_schedule_set` |
| Redes | `ads_campaign_networks_set` |
| Modo de match de keywords de campaña | `ads_campaign_keyword_match_type_set` (`BROAD` activa broad-only; `UNSPECIFIED` lo desactiva) |
| Frequency caps | `ads_campaign_frequency_caps_set` |
| Geos | `ads_targeting_location_add` / `ads_targeting_location_remove` |
| Idiomas | `ads_targeting_language_add` / `ads_targeting_language_remove` |
| Devices | `ads_targeting_device_bid_modifier_set` |
| Content labels | `ads_targeting_content_label_add` / `ads_targeting_content_label_remove` |
| Conversion goals | `ads_conversion_goal_biddable_set` |
| Ad group (nombre, estado, cpc) | `ads_ad_group_update`, `ads_ad_group_status_set` |
| Rotación de ads | `ads_ad_group_ad_rotation_set` |
| Audiencias en ad group | `ads_audience_attach` / `ads_audience_detach` / `ads_ad_group_audience_mode_set` |
| RSA (títulos/descripciones) | `ads_ad_rsa_update` |
| Keywords | `ads_keyword_add` / `ads_keyword_update` / `ads_keyword_match_type_set` / `ads_keyword_remove` |
| Negativas | `ads_negative_keyword_add` |

Si una operación carece de tool tipada, registra `blocked` y describe el contrato faltante; nunca la
improvises por otra vía.

## 4. Dry run explícito

Sin depender de defaults:
- Validación sin despacho → `dry_run: true`. Puede crear una fila de acción en Irrumpe y quedar
  `validated`, pero jamás se envía al provider; no la trates como lectura y reporta siempre
  `dry_run` junto al estado.
- Solicitud de cambio real confirmada → `dry_run: false`. El backend decide si queda pendiente de
  aprobación o si entra a la cola del dispatcher.
- Si una write no acepta `dry_run`, tratarla como operación real y pedir confirmación previa.
- Usar `idempotency_key` en operaciones repetibles o sensibles.

## 5. Permisos y pre-revisión

No replicar roles en el cliente. El backend resuelve la autoridad de edición Ads por marca y usuario
(`execute` | `propose` | `none`) y devuelve una fila real de `runtime.integration_actions`.
Conservar y reportar el `status` crudo:

| Estado devuelto | Significado |
|---|---|
| `drafted` | Acción creada, todavía sin validación/aprobación suficiente. |
| `validated` | Acción validada y pendiente. Con `dry_run: true` es solo preview; con `dry_run: false` es una propuesta real pendiente de aprobación. |
| `approved` | Acción aprobada y elegible para despacho; todavía no confirma un cambio en Google Ads. |
| `running` | El dispatcher está ejecutando la acción contra el provider. |
| `succeeded` | El provider confirmó la ejecución; la lectura importada aún puede esperar resincronización. |
| `failed` | La ejecución terminó con error; reportar `response_payload` y `latest_event_payload` cuando estén disponibles. |
| `canceled` | La acción fue cancelada y no debe despacharse. |

`Pre-revisión` puede ser una explicación de producto para una acción real `validated` que espera
aprobación. No presentarla como si fuera el valor literal retornado por el MCP.

### Aprobar tras revisión humana

- `ads_action_approve({ action_id })` — aprueba una acción de Google Ads existente. El backend
  re-verifica autoridad de ejecución, entitlement del plan y la cuenta verificada.
- `integration_action_approve({ action_id })` — aprueba acciones de providers distintos de Google
  Ads. Las acciones pendientes se listan con `list_brand_integration_actions`.

La aprobación ocurre únicamente cuando el usuario la pide de forma explícita sobre una acción
identificada. Aprobar pone la acción en cola: el dispatcher corre cada minuto y procesa hasta cinco
acciones por tick. Después de aprobar, consultar
`list_brand_integration_actions({ action_id })` hasta `succeeded`, `failed` o `canceled`; no tratar
`approved` como éxito del provider.

## 6. Checklist previo a cada write

1. `brand_id` confirmado.
2. Identificadores confirmados: `ad_campaign_id`, `provider_campaign_entity_id`,
   `provider_ad_group_entity_id` o `provider_criterion_entity_id` según corresponda.
3. Evidencia revisada (lecturas recientes, falso positivo descartado).
4. Acción mínima y reversible definida.
5. `dry_run` explícito.
6. Fila de acción leída y reportada con `action_id`, `status`, `dry_run` y `approval_required`.
7. Si hubo despacho, seguimiento hasta estado terminal y resincronización posterior.

## 7. Métricas y segmentos no expuestos

El desempeño agregado vive en Pulso (`pulso-metricas.md`). Cuando el MCP no exponga un segmento
necesario (search terms crudos, user-location), pide un export al usuario, trabaja con la lectura
disponible bajando la confianza, o registra `blocked` si el dato es indispensable.

## 8. Reporte posterior

Después de operar reporta: entidad afectada, cambio solicitado, evidencia, estado devuelto por el
MCP, `dry_run` usado, `action_id`, identificadores relevantes y la siguiente revisión necesaria.
Tras `succeeded`, las vistas de keywords pueden tardar 1–3 minutos en reflejar el cambio; confirmar
con `provider_last_seen_at` y una nueva lectura en vez de declarar fallo por ausencia inmediata.
