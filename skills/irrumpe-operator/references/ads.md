# Campañas Ads — contratos MCP

Cómo se leen y modifican campañas de Google Ads desde Irrumpe. El MCP controla permisos, auditoría,
ejecución real y pre-revisión; el operador prepara operaciones mínimas, tipadas y reversibles.
Prosa en español; tools, campos y valores en inglés.

---

## 1. Principio operativo

1. Resolver marca y campaña en el MCP.
2. Leer el estado desde las vistas Ads.
3. Preparar la acción mínima reversible.
4. Enviar la operación tipada con `dry_run` explícito.
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
| Frequency caps | `ads_campaign_frequency_caps_set` |
| Geos | `ads_targeting_location_add` / `ads_targeting_location_remove` |
| Idiomas | `ads_targeting_language_add` / `ads_targeting_language_remove` |
| Devices | `ads_targeting_device_bid_modifier_set` |
| Content labels | `ads_targeting_content_label_add` / `_remove` |
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
- Preview → `dry_run: true`.
- Cambio real aprobado → `dry_run: false`.
- Si una write no acepta `dry_run`, trátala como operación real y pide confirmación previa.
- Usa `idempotency_key` en operaciones repetibles o sensibles.

## 5. Permisos y pre-revisión

El operador nunca replica roles. El backend resuelve la autoridad de edición Ads por marca y usuario
(`execute` | `propose` | `none`) y decide el destino de cada write:

| Estado devuelto | Significado |
|---|---|
| `applied` | El cambio se aplicó o el provider confirmó la ejecución. |
| `pre_revision` | Quedó una solicitud pendiente de revisión humana. |
| `preview` | Operación simulada o validada sin escritura real. |
| `blocked` | Falta permiso, dato, contrato o herramienta. |

`pre_revision` es un resultado operativo válido; nunca lo reportes como error.

### Aprobar tras revisión humana

- `ads_action_approve({ action_id })` — aprueba una acción de Google Ads existente. El backend
  re-verifica autoridad de ejecución, entitlement del plan y la cuenta verificada.
- `integration_action_approve({ action_id })` — aprueba acciones de providers distintos de Google
  Ads. Las acciones pendientes se listan con `list_brand_integration_actions`.

La aprobación ocurre únicamente cuando el usuario la pide de forma explícita sobre una acción
identificada.

## 6. Checklist previo a cada write

1. `brand_id` confirmado.
2. Identificadores confirmados: `ad_campaign_id`, `provider_campaign_entity_id`,
   `provider_ad_group_entity_id` o `provider_criterion_entity_id` según corresponda.
3. Evidencia revisada (lecturas recientes, falso positivo descartado).
4. Acción mínima y reversible definida.
5. `dry_run` explícito.
6. Resultado real leído y reportado.

## 7. Métricas y segmentos no expuestos

El desempeño agregado vive en Pulso (`pulso-metricas.md`). Cuando el MCP no exponga un segmento
necesario (search terms crudos, user-location), pide un export al usuario, trabaja con la lectura
disponible bajando la confianza, o registra `blocked` si el dato es indispensable.

## 8. Reporte posterior

Después de operar reporta: entidad afectada, cambio solicitado, evidencia, estado devuelto por el
MCP, `dry_run` usado, identificadores relevantes y la siguiente revisión necesaria.
