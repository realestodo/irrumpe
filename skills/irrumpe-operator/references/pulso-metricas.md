# Pulso — métricas de performance

Cómo se consulta el desempeño de la marca (Pulso) por MCP. Todas las tools de esta referencia son de
solo lectura. Prosa en español; tools, campos y valores en inglés.

---

## 1. Orden de consulta

1. **`get_brand_performance_availability`** (`brand_id`) — qué proveedores y secciones tienen datos
   disponibles. Consúltala primero: evita presentar un dashboard vacío como si fuera un desempeño en
   cero.
2. **`get_brand_performance_dashboard`** (`brand_id`, `preset`) — el payload listo para dashboard
   que arma el backend. `preset ∈ {yesterday, 7d, 30d, 90d}` (default `7d`). Esta es la fuente
   primaria para "cómo va la marca": usa este payload en lugar de componer métricas crudas a mano.
3. **`list_brand_metric_snapshots`** (`brand_id`, `provider_key`, `source_kind`, `date_from`,
   `date_to`) — hechos y métricas normalizadas por snapshot, para profundizar en un proveedor o
   periodo puntual.
4. **`list_brand_metric_timeseries`** (`brand_id`, `metric_key`, `provider_key`, `source_kind`,
   `date_from`, `date_to`) — serie temporal normalizada de una métrica, para tendencias y
   comparaciones entre periodos.

## 2. Reglas de interpretación

- El dashboard es la verdad presentable; snapshots y timeseries son el detalle. Cuando ambos
  difieran, reporta el dashboard y marca la discrepancia.
- Un proveedor ausente en `availability` significa sin conexión o sin datos; nunca lo reportes como
  desempeño cero.
- Fechas en formato `YYYY-MM-DD`. Los rangos de snapshots/timeseries son inclusivos.
- Paginación estándar: `limit` (≤100) + `offset`. Con más filas que el `limit`, itera antes de
  concluir.
- El desempeño de campañas Ads a nivel entidad (campaña, ad group, keyword) se lee con las tools de
  `ads.md`; Pulso agrega la vista de marca.

## 3. Presentación al usuario

- Indica siempre el periodo (`preset` o rango) junto a cada cifra.
- Distingue métrica observada y variación contra el periodo previo cuando el payload la incluya.
- Cifras con formato local del usuario; claves de métrica (`metric_key`) en su forma original.
- Cuando el usuario pida una métrica que el payload no trae, dilo de forma explícita y ofrece el
  detalle disponible más cercano (snapshot o timeseries).
