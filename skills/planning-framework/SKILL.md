---
name: planning-framework
description: Skill de referencia para estructura de planificación social media, filas, capas, payloads y validación.
---

# Framework de planificacion — Social Media

Estructura del Brand Strategy Planner: orden de filas, bloques, capas de poblamiento, densidad temporal, schemas de payload y validacion.

## Capas de poblamiento

La grilla se puebla en orden estricto, nunca toda de una vez:

### Capa 1 — Contexto (fila 01)
Senales por mes del contexto de industria. Cada celda: 1-2 oraciones sobre que pasa en la industria ese mes.

### Capa 2 — Objetivos (filas 02, 03, 04)
- **Anuales (02):** Objetivos estrategicos del investigador. Mismo texto en las 12 columnas.
- **Trimestrales (03):** Division de los anuales en 4 focos. Mismo texto en 3 columnas.
- **Mensuales (04):** Objetivo especifico del mes, conectado al trimestral correspondiente.

### Capa 3 — Narrativa (filas 05, 06)
- **Mensaje Principal (05):** Eje de comunicacion del mes, cruce entre objetivo mensual + contexto.
- **Noticia/Hito (06):** Hitos del cliente + eventos de industria. Si un mes no tiene hito: `—`.

### Capa 4 — Contenido Objetivos (fila 07)
2-3 objetivos de contenido por mes de la lista de 14, alineados con el objetivo mensual.

### Capa 5 — Ejecucion Tactica (filas restantes)
La capa mas granular. Aplican reglas de densidad temporal.

## Densidad temporal

- **Meses 1-3** (mas cercanos): maximo detalle en todas las filas
- **Meses 4-6**: detalle medio — formatos y keywords si, produccion y paid media estimados
- **Meses 7-12**: directrices generales — `—` en filas sin informacion suficiente

## Paid Media tags

- **[ALWAYS ON]**: campanas que corren todo el ano (remarketing, brand awareness)
- **[TEMPORAL]**: campanas de temporada o evento especifico

## Metadata por fila

Cada fila de la grilla es una pagina nativa en Irrumpe MCP:

| Campo | Tipo | Que poner |
|-------|------|-----------|
| Macrociclo | title | Nombre exacto de fila canonica (nunca prefijo de cliente/marca) |
| Bloque | payload tag | Estrategia / Comunicacion / Tactico / Contenidos / Publicidad / Optimizacion |
| Descripcion | text | Descripcion general de la fila |
| Status | status | Default: `Pre-revision` |
| row_index | integer (payload) | Posicion canonica 1..N |
| Periodo | date (start + end) | Fecha inicio a fecha fin del ciclo |
| Ene-Dic | text | Contenido de cada mes |

## Temporalidad anual

La planificacion se ancla a un ano de planificacion (`PLAN_YEAR`):
- `period_start = PLAN_YEAR-01-01`
- `period_end = PLAN_YEAR-12-31`
- `months` = exactamente `Ene..Dic` de `PLAN_YEAR`

Si el usuario pide un periodo acotado (ej: "solo Q2"), poblar solo esos meses pero mantener las 12 columnas con `—` en los no planificados.

## Validacion estructural (14 puntos)

Antes de entregar, validar:

1. Cantidad de filas = `CANONICAL_ROW_COUNT` (derivado del Brand Strategy Planner)
2. Orden de filas coincide exactamente con `CANONICAL_ROWS`
3. Cada fila declara un `Bloque` valido
4. Existen exactamente 12 columnas de mes
5. Existe `Fecha inicio` y `Fecha fin`
6. Tabla consolidada y JSON contienen exactamente las mismas filas y valores
7. `extension_rows` solo para capas explicitas en estrategia + `ALLOWED_OPTIONAL_LAYERS`

## Payload JSON — estructura canonica

```json
{
  "client": "[Cliente]",
  "period_start": "YYYY-MM-DD",
  "period_end": "YYYY-MM-DD",
  "months": ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
  "canonical_source": "Brand Strategy Planner + Planificaciones (resolved at runtime via Irrumpe MCP)",
  "row_count": 0,
  "rows": [
    {
      "row_index": 1,
      "row_name": "[Nombre exacto fila canonica]",
      "block": "[Bloque valido]",
      "description": "[Descripcion de la fila]",
      "values": {
        "Ene": "...", "Feb": "...", "Mar": "...", "Abr": "...",
        "May": "...", "Jun": "...", "Jul": "...", "Ago": "...",
        "Sep": "...", "Oct": "...", "Nov": "...", "Dic": "..."
      }
    }
  ],
  "extension_rows_count": 0,
  "extension_rows": []
}
```

## Extension rows

Maximo 3 por planificacion anual. Cada una:

```json
{
  "row_name": "Nombre capa extension",
  "block": "Comunicacion",
  "description": "Descripcion breve",
  "rationale": "Por que esta capa no esta cubierta por las filas canonicas",
  "parent_row_name": "Fila canonica o extension existente",
  "depends_on_row_names": ["Fila A", "Fila B"],
  "values": { "Ene": "...", "Feb": "...", "...": "..." }
}
```

Requisitos:
- Explicitamente respaldada por estrategia y por `ALLOWED_OPTIONAL_LAYERS`
- `parent_row_name` obligatorio y debe resolver a fila existente
- Nombre no puede colisionar con filas canonicas ni llevar prefijo de cliente/marca
- Grafo de dependencias debe ser aciclico
