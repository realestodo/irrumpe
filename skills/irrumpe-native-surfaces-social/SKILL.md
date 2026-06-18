---
name: "irrumpe-native-surfaces-social"
description: "Referencia de superficies nativas Irrumpe MCP para social-media-dept: caption, hashtags, metadata, adjuntos y estado."
---

# Superficies nativas Irrumpe MCP — social-media-dept

Usa esta referencia al generar, publicar o enriquecer piezas de social media en Irrumpe MCP.

## Regla base

Resolver el schema nativo antes de escribir:

| Campo | Regla |
|---|---|
| `surface_type` | `social_content`, `social_planning` o tipo nativo expuesto por MCP. |
| `editor_engine` | `plate` o `legacy_plate` segun declare la superficie. |
| `native_references` | IDs nativos de marca, cliente, estrategia, planificacion, pieza, assets, brief de arte y documentos relacionados. |
| `status_template_key` | Template nativo de la superficie si MCP lo expone. |

Si el schema nativo requerido falta, detener y reportar el blocker.

## Frontera caption y hashtags

`copy` significa caption publicable. `hashtags` vive en un campo separado.

Reglas duras:

- No anexar hashtags al final del caption.
- No guardar hashtags dentro de `copy`, `body`, `contexto` ni `acciones`.
- `hashtags` debe ser array normalizado, con `#`, sin espacios internos, sin duplicados.
- Array vacio es valido cuando la pieza no requiere hashtags.
- Si la superficie destino no tiene campo nativo para hashtags y la pieza trae hashtags, detener con schema blocker.

## Metadata fuera del caption

Estos datos van en campos nativos, no en el caption:

- objetivo;
- etapa del embudo;
- formato;
- plataforma;
- deadline;
- cliente;
- status;
- contexto;
- acciones;
- brief de arte;
- adjuntos y assets.

## Briefs de arte y adjuntos

Un brief de direccion de arte se inserta como bloque nativo o documento relacionado, sin reemplazar el caption original. Los adjuntos se escriben como assets nativos asociados a la pieza.

Si MCP solo expone `legacy_plate`, usarlo mientras exista, manteniendo los IDs nativos como fuente de verdad.

## Verificacion final

Antes de cerrar:

1. Fetch de la pieza publicada.
2. Confirmar que `copy` no contiene hashtags.
3. Confirmar que `hashtags` vive en el campo separado.
4. Confirmar relaciones nativas a cliente, estrategia, planificacion y assets.
5. Confirmar que status y deadlines quedaron en campos nativos.
6. Reportar cualquier fallback legacy usado.
