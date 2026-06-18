---
name: "irrumpe-native-surfaces-creative"
description: "Referencia de superficies nativas Irrumpe MCP para creative-dept: bloques ricos, templates de estado, metadata y enlaces internos."
---

# Superficies nativas Irrumpe MCP — creative-dept

Usa esta referencia cuando un flujo creativo lea, cree o actualice contenido en Irrumpe MCP.
El destino primario es la superficie nativa del MCP.

## Regla base

Antes de escribir, resolver:

| Campo | Regla |
|---|---|
| `surface_type` | `brand_narrative`, `conceptualization`, `strategy`, `visual_system`, `blog_article` o el tipo nativo expuesto por MCP. |
| `editor_engine` | `plate` para documentos ricos actuales; `legacy_plate` solo cuando la superficie aun lo declare. |
| `status_template_key` | `Irrumpe`, `Conceptualización` o `Estrategia` para los flujos de esta pasada. |
| `document_template_key` | Template nativo asociado al tipo de documento cuando MCP lo exponga. |
| `native_references` | IDs nativos de marca, cliente, narrativa, concepto, estrategia, documento fuente y documentos relacionados. |

Si una operacion requerida no existe en MCP, detener y reportar el blocker. No degradar a Markdown visible de forma silenciosa.

## Cuerpo nativo

El body que llega al editor debe ser una lista de bloques nativos:

- `heading_1`, `heading_2`, `heading_3`
- `paragraph`
- `bulleted_list_item` o lista nativa equivalente
- `numbered_list_item` o lista nativa equivalente
- `blockquote`
- `callout`
- `table`
- `divider`
- `link` o referencia interna nativa cuando corresponda

Markdown puede existir como formato local de trabajo, pero la escritura final debe convertirlo a bloques. En la superficie publicada no deben quedar marcadores visibles como `#`, `##`, `**`, `_`, YAML frontmatter, wrappers crudos o tablas pipe.

## Metadata fuera del body

Nunca meter en el cuerpo:

- subheadline como etiqueta literal;
- caption;
- hashtags sociales;
- cliente, fecha, estado o template;
- IDs, URLs internas o datos de sincronizacion;
- listas de metadata del agente.

Estos datos se escriben en campos nativos si existen. Si el campo nativo falta y el dato es obligatorio, detener y reportar schema blocker.

## Blog y articulos

Para `blog_article`:

- `title` va en el campo titulo.
- `subheadline` va en metadata nativa cuando exista.
- `body_blocks` contiene solo el contenido editorial.
- `keywords` o tags SEO van en metadata, nunca como hashtags visibles.
- No escribir captions ni hashtags sociales salvo que la superficie nativa tenga campos dedicados y el usuario los haya pedido.

La verificacion final debe confirmar que el body no contiene `##`, `**`, YAML, caption ni hashtags sociales visibles.

## Callouts, tablas y enlaces internos

Preservar callouts como bloque `callout`, con icono y color si MCP lo soporta.
Preservar tablas como bloque `table` o estructura nativa equivalente.
Preservar enlaces a documentos, contextos, marcas, clientes, estrategias, transcripciones y superficies Irrumpe como `native_references` o links internos nativos.

Si el input trae un link a un documento existente en contexto, buscar su ID nativo antes de escribir. Si el ID no puede resolverse, conservar la URL como link externo y reportar advertencia.

## Verificacion final

Antes de cerrar una publicacion:

1. Fetch del documento o item escrito.
2. Confirmar `surface_type`, `editor_engine`, `status_template_key` y `native_references`.
3. Confirmar que el body renderiza bloques nativos.
4. Confirmar que no quedaron marcadores Markdown visibles.
5. Confirmar que metadata, hashtags, captions e IDs no quedaron dentro del body.
