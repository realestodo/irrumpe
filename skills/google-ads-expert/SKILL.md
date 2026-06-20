---
name: "google-ads-expert"
description: "Experto público de Google Ads Search vía Irrumpe MCP: auditoría de gasto, geos, search terms, oportunidades, negativas, RSA y pre-revisión."
---

# Google Ads Expert

Skill pública para trabajo experto de Google Ads Search dentro de Irrumpe.

Irrumpe MCP es la única superficie operativa: lectura, permisos, preview, pre-revisión y aplicación
de cambios pasan por MCP. La skill aporta criterio: investiga, valida hipótesis, recomienda acciones
y reporta el estado real que devuelve la plataforma.

## Alcance

- Google Ads Search.
- Auditoría de desperdicio, geos de bajo valor, search terms y oportunidades.
- Investigación de keywords para paid search.
- Arquitectura de campañas, ad groups, keywords y negativas.
- Assets RSA: headlines, descriptions, callouts y sitelinks.
- Operaciones tipadas por Irrumpe MCP cuando el usuario aprueba.

Quedan fuera del core:

- PMax
- Display
- YouTube
- Shopping
- Meta Ads

## Antes de actuar

Si la tarea es expansión simple de keywords:

- cargar `references/keyword-research.md`;
- mantener el scope literal de oferta, geo, idioma y vertical;
- cargar `references/vertical-expansion-patterns.md` solo cuando la vertical cambia el lenguaje de compra;
- entregar una lista compacta y útil.

Si la tarea pide anuncios o planning:

- entregar el artefacto pedido;
- cargar `references/ad-messaging.md`;
- sumar `references/ad-messaging-by-vertical.md` cuando la vertical lo requiera;
- dejar riesgos y recomendaciones fuera del artefacto si el usuario pidió un output cerrado.

Si la tarea pide auditoría, geos, leaks, desperdicio u oportunidades:

- cargar `references/waste-and-opportunity-audit.md`;
- partir por money trail;
- tratar anomalías como hipótesis hasta falsarlas;
- exigir evidencia, explicación alternativa y confianza antes de recomendar.

Si la tarea implica leer o cambiar una cuenta:

- cargar `references/native-mcp-ads-operations.md`;
- resolver marca, cuenta, campaña y entidades por MCP;
- usar `dry_run: true` explícito para preview cuando la tool lo acepte;
- usar `dry_run: false` solo con aprobación explícita del usuario;
- reportar `applied`, `pre_revision`, `preview` o `blocked` según respuesta MCP.

## Referencias

| Situación | Referencia |
|---|---|
| Discovery, expansión o limpieza de keywords | `references/keyword-research.md` |
| Vertical con lenguaje sectorial específico | `references/vertical-expansion-patterns.md` |
| Auditoría de gasto, geos, search terms, leaks u oportunidades | `references/waste-and-opportunity-audit.md` |
| Crear o rediseñar estructura Search | `references/search-campaign-architecture.md` |
| Optimizar una campaña activa | `references/optimization-playbooks.md` |
| Proponer RSA, callouts o sitelinks | `references/ad-messaging.md` |
| Calibrar mensaje por vertical | `references/ad-messaging-by-vertical.md` |
| Leer, previsualizar o ejecutar cambios vía MCP | `references/native-mcp-ads-operations.md` |

## Workflow base

1. Clasificar el trabajo:
   - `research`
   - `waste-audit`
   - `architecture`
   - `ad-messaging`
   - `mcp-operation`
   - `optimization`
2. Confirmar objetivo:
   - leads
   - ventas
   - tráfico calificado
   - defensa de marca
3. Confirmar restricciones:
   - geo
   - idioma
   - presupuesto
   - conversión principal
   - landing pages disponibles
4. Resolver datos por Irrumpe MCP.
5. Separar dato observado, inferencia y recomendación.
6. Revisar falsos positivos.
7. Proponer acción mínima.
8. Ejecutar por MCP solo con aprobación.

## Evidencia mínima

Preferir evidencia de:

- campañas Ads disponibles en MCP;
- ad groups;
- ads;
- keywords positivas y negativas;
- audiencias;
- budget, bidding, targeting y conversion goals cuando estén expuestos;
- search terms o user-location cuando MCP los exponga o el usuario aporte export.

Si un segmento crítico no está disponible por MCP, marcar `blocked` o pedir export. No inventar el
dato faltante.

## Reglas de criterio

- Separar brand y non-brand salvo instrucción contraria.
- Agrupar ad groups por tema e intención dominante.
- Usar broad match con negativas, señales de conversión y landing fit.
- Evitar listas infladas con keywords poco naturales.
- Revisar tracking antes de culpar bidding, geos o devices.
- Revisar muestra y estacionalidad antes de excluir.
- Tratar `pre_revision` como resultado operativo válido.
- Dejar permisos y publicación real bajo autoridad del MCP.

## Formato de recomendación

Usa este formato para hallazgos de auditoría:

```text
Señal:
Evidencia:
Chequeos de falso positivo:
Clasificación:
Confianza:
Acción recomendada:
Vía operativa:
Estado esperado:
```

## Autochequeo

Antes de entregar:

- [ ] La respuesta distingue dato, inferencia y recomendación.
- [ ] Cada anomalía relevante fue falsada antes de convertirse en hallazgo.
- [ ] La vía operativa es Irrumpe MCP.
- [ ] La acción propuesta es mínima y reversible cuando toca cuenta real.
- [ ] `dry_run` queda explícito cuando hay preview.
- [ ] El estado final refleja la respuesta real de MCP.
