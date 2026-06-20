# Operaciones Ads vía Irrumpe MCP

Usa esta referencia cuando el trabajo implique leer, preparar, actualizar o ejecutar cambios sobre
Google Ads desde Irrumpe.

Irrumpe MCP es la superficie operativa primaria. La skill aporta criterio experto; el MCP controla
permisos, auditoría, ejecución real y pre-revisión.

## Principio operativo

1. Resolver marca y campaña en Irrumpe MCP.
2. Leer estado nativo/importado desde vistas Ads.
3. Diagnosticar con datos MCP primero.
4. Pedir export o marcar `blocked` cuando MCP no exponga un segmento crítico.
5. Preparar la acción mínima reversible.
6. Enviar la operación tipada por MCP.
7. Reportar el resultado real devuelto por MCP.

## Lecturas primarias

| Necesidad | Tool MCP |
|---|---|
| Campañas Ads | `list_brand_ads_campaigns` |
| Ad groups | `list_brand_ads_ad_groups` |
| Ads / creatividades | `list_brand_ads_ads` |
| Keywords positivas y negativas | `list_brand_ads_keywords` |
| Audiencias Google Ads provider | `list_brand_ads_audiences` |
| Audiencias fundacionales Irrumpe | `list_brand_audiences` |

Cuando necesites settings, targeting, conversion goals o affordances que no estén en una tool de
lista específica, revisar la fila de campaña/ad group disponible en MCP o las vistas `api.v_brand_ads_*`
expuestas por el contrato nativo. Si la tool no aparece en la sesión, registrar blocker o usar
diagnóstico raw sin escribir.

## Operaciones tipadas

| Operación | Tool MCP |
|---|---|
| Estado de campaña | `ads_campaign_status_set` |
| Presupuesto diario | `ads_campaign_budget_set` |
| Bidding | `ads_campaign_bidding_set` |
| Fechas | `ads_campaign_dates_set` |
| Horarios | `ads_campaign_schedule_set` |
| Redes | `ads_campaign_networks_set` |
| Frequency caps | `ads_campaign_frequency_caps_set` |
| Geos | `ads_targeting_location_add`, `ads_targeting_location_remove` |
| Idiomas | `ads_targeting_language_add`, `ads_targeting_language_remove` |
| Devices | `ads_targeting_device_bid_modifier_set` |
| Conversion goals | `ads_conversion_goal_biddable_set` |
| Actualizar ad group | `ads_ad_group_update` |
| Audiencias en ad group | `ads_audience_attach`, `ads_audience_detach`, `ads_ad_group_audience_mode_set` |
| Keywords | `ads_keyword_add`, `ads_keyword_update`, `ads_keyword_match_type_set`, `ads_keyword_remove` |
| Negativas | `ads_negative_keyword_add` |

Si una operación Ads no tiene tool MCP tipada, registrar `blocked` y explicar qué contrato falta.

## Dry run explícito

No depender de defaults.

- Para preview, enviar `dry_run: true`.
- Para cambio real aprobado, enviar `dry_run: false`.
- Si una tool write no acepta `dry_run`, tratarla como operación real y pedir confirmación.
- Usar `idempotency_key` en operaciones repetibles o sensibles.

## Permisos y pre-revisión

La skill no replica roles ni permisos.

El MCP decide:

- aplicar el cambio en Google Ads;
- dejar la operación en `pre_revision` para revisión humana;
- devolver preview;
- bloquear por falta de contrato, acceso o datos.

Mapear el resultado así:

| Estado | Significado |
|---|---|
| `applied` | El MCP aplicó el cambio o confirmó ejecución provider. |
| `pre_revision` | El MCP registró una solicitud pendiente de revisión humana. |
| `preview` | La operación fue simulada o validada sin escritura real. |
| `blocked` | Falta permiso, dato, contrato o herramienta. |

`pre_revision` es un resultado operativo válido. No reportarlo como error.

## Flujo para cambios

Antes de enviar una write:

1. Confirmar `brand_id`.
2. Confirmar `ad_campaign_id`, `provider_campaign_entity_id`, `provider_ad_group_entity_id` o
   `provider_criterion_entity_id` según corresponda.
3. Confirmar evidencia y falso positivo revisado.
4. Confirmar acción mínima y reversibilidad.
5. Pasar `dry_run` explícito.
6. Leer y reportar el resultado real.

## Segmentos no expuestos

Cuando MCP no exponga un segmento necesario, como search terms crudos o user-location:

- pedir export del usuario;
- trabajar con la lectura disponible y bajar la confianza;
- registrar `blocked` si el dato es indispensable para decidir;
- describir la operación MCP o vista faltante.

## Reporting

Después de operar, reportar:

- entidad afectada;
- cambio solicitado;
- evidencia que lo justifica;
- estado devuelto por MCP;
- `dry_run` usado;
- identificadores relevantes;
- siguiente revisión necesaria.
