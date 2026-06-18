---
name: strategy-types
description: Canonical catalog of strategy types, their tag mappings, base requirements, and additional permitted types for the creative department strategy workflow.
---

# Strategy types catalog — creative-dept

## Base types (always included)

| Strategy type | Tag (`Tipo de Estrategia`) |
|---|---|
| Estrategia de Contenidos | Contenidos |
| Estrategias de Crecimiento | Crecimiento |

## Additional permitted types

| Strategy type | Tag (`Tipo de Estrategia`) |
|---|---|
| Estrategia de Venta | Venta |
| Estrategia de Comunicación y Reputación | Comunicación y Reputación |
| Estrategia de Performance | Performance / Medios |
| Estrategia de Personal Branding | Personal Branding |
| Estrategia de Diseño | Diseño |
| Estrategia de Pricing | Pricing |
| Estrategia de Producto | Producto |
| Funnel versus Estrategia de Contenidos | Contenidos |
| Estrategia de Experiencia User Centered | Experiencia de Cliente (CX) |

## Rules

- `STRATEGY_TYPES` must always include the two base types.
- `STRATEGY_TYPE_TAGS` must always include `Contenidos` and `Crecimiento`.
- Derive `STRATEGY_TYPE_TAGS` from `STRATEGY_TYPES` using the mapping tables above.
- Deduplicate tags after derivation.
- Never invent types outside the permitted list.

## Strategy emphasis values

Valid values for `STRATEGY_EMPHASIS`:

- `growth`
- `positioning`
- `profitability`
- `retention`
- `reputation`
- `launch`
- `efficiency`
- `balanced`

## Optional strategy layers

Valid values for `OPTIONAL_STRATEGY_LAYERS`:

- `personal-branding-socios`
- `none` (default)

Activation rules:
- If `OPTIONAL_STRATEGY_LAYERS` is `none` or absent, do not force additional layers.
- If `personal-branding-socios` is present, integrate with strategic scope (avoid tactical detail).
- The layer can also activate when client evidence indicates direct need (founder spokespersonship, personal brand dependency, or commercial reliance on partner figures).
