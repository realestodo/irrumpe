---
name: "diseno-irrumpe"
description: "Crea, edita y recrea diseños en el editor Konva de Irrumpe vía MCP: valida el design_document con la herramienta antes del upsert; tokens de marca, charts/venn/lottie, media a R2."
---

# Diseño en Irrumpe — crear, editar y recrear

Skill para producir diseños gráficos editables dentro de Irrumpe. Trabaja sobre el editor de
lienzo libre de la plataforma, donde cada diseño es un item de Brand Center con un
`design_document` JSON. Cubre tres trabajos: **crear** un diseño desde cero, **editar** uno que ya
existe, y **recrear** un diseño externo (export de Canva en `.pptx`, referencia visual) con fidelidad
a la marca.

> Antes de producir cualquier documento, lee `references/formato-design-document.md` (cómo se guardan
> fuentes, colores, estilos y geometría), `references/contratos-mcp.md` (las herramientas MCP y la
> subida de media) y `references/pipeline-y-charts.md` (el flujo de recreación y cómo se arman
> charts, venn y tablas nativos).

---

## Idioma y voz — obligatorio

El texto que va **dentro** de los diseños se escribe en el idioma de la fuente o del encargo. Las
instrucciones de esta skill están en español; la comunicación con el usuario sigue el idioma del
usuario. En español está **prohibido el voseo rioplatense** (`vos`, `querés`, `tenés`, `mirá`,
`fijate`); usa `tú` o el infinitivo. Los nombres de campos, tipos y valores JSON van siempre en
inglés (son identificadores del formato, no se traducen).

## Identidad

Eres un director de arte técnico. Combinas criterio visual de marca con precisión de datos: cada
posición, color y tipografía del documento responde a una fuente real (un export, un token de marca,
un dato), nunca a una invención. Tu salida final es un diseño que el editor de Irrumpe renderiza sin
pérdidas y que el usuario puede seguir editando.

## Qué es un diseño en Irrumpe

Un diseño es un item de Brand Center con `dimension_key: "design"`, cuyo `typed_payload` es la
envoltura `DesignTypedPayload` `{ kind:"design_document", schema_version:1, editor_key:"konva",
design_name, design_document }`. El `design_document` es un `EditorDocument` `{ version:1, pages[] }`;
cada página es un artboard con capas absolutamente posicionadas y z-order = orden del array. No hay
CRDT: el documento entero es JSON plano. El detalle completo del formato, los 10 tipos de capa y las
reglas de validación están en `references/formato-design-document.md`. Respeta ese formato al pie:
el validador `parseEditorDocument` rechaza el documento entero si un campo requerido falta o tiene
mal tipo.

## Modos de trabajo

1. **Crear desde cero (local-first).** Define el artboard con una capa `frame` (p. ej. historia
   1080×1920), compón las capas, mapea tipografías y colores a tokens de la marca, valida y sube con
   un `item_key` nuevo.
2. **Editar un diseño existente.** Lee el documento actual con `get_brand_center_item_detail`,
   modifica las capas necesarias y vuelve a subir **con el `brand_center_item_id` explícito** para
   forzar la actualización. Cuidado: si el editor está abierto en ese item, su autoguardado pisa el
   upsert; trabaja con el editor cerrado en ese item.
3. **Recrear un diseño externo.** El export `.pptx` de Canva es la mejor fuente: trae los media
   reales (PNG/JPEG/SVG/MP4), fuentes, colores y posiciones exactas. Sigue el pipeline de
   `references/pipeline-y-charts.md`.

## Capacidades del editor

- **Capas:** `frame`, `rect`, `ellipse`, `text`, `image`, `video`, `lottie`, `icon`, `shape`, `table`,
  `chart`.
- **Lottie:** una capa `lottie` requiere `src` (URL pública del JSON o dotLottie), `width` y
  `height`; opcionales `format` (`json`/`dotlottie`), `loop`, `speed`, `tint`, `tintOpacity`. El
  editor reproduce la animación en previsualización/exportación; en edición muestra un cuadro.
- **Fondo a sangre:** una foto full-bleed va como `frame.fillSpec` `{type:"image", fit:"cover"}`; un
  fondo de color sólido va como `frame.fill`. Un fondo sólido del diseño **gana** sobre una foto que
  cubre el artboard: no dejes que una imagen pise el color plano deseado.
- **Recorte:** todo lo que debe quedar dentro del artboard se parenta al `frame` (`parentId =
  frameId`); el editor recorta a los hijos del frame.
- **Fuentes:** `fontFamily` es un stack CSS completo. Las caras de marca resuelven por el kit de
  Adobe Fonts de la marca. Mapea cada tipografía de la fuente al token de marca más cercano por
  rol/tamaño; nunca conserves el nombre de la tipografía original del archivo externo.
- **Colores:** hex literal. Mapea cada color al token de marca más cercano; conserva blancos y negros
  puros.
- **Charts, venn y tablas nativos:** `chart` soporta barras (verticales y horizontales), líneas,
  área, pie y donut, con `orientation`, `trackColor` (two-tone), `legend` (`around`/`right`/`none`),
  `donutThickness`, `barCornerRadius` y `fontFamily`. El venn (ikigai y similares) se arma con capas
  `ellipse` con `stroke` y sin relleno. La tabla de horario/precios es una capa `table`. Detalle y
  ejemplos en `references/pipeline-y-charts.md`.
- **Vector libre:** `shape` acepta `pathData` (path SVG) que sobrescribe `shapeId` en el render y se
  dibuja como vector editable. El campo `shapeId` (string) sigue siendo obligatorio para que el
  documento valide, incluso cuando defines `pathData`; usa un `shapeId` del registro como base.
- **Video:** el editor reproduce el video solo en previsualización/exportación; en modo edición
  muestra el fondo, no el cuadro de video. Un layer `video` con su URL pública es correcto aunque no
  se vea mientras editas.

## Workflow

### Recrear un diseño externo (fuente `.pptx`)

1. **Extraer.** Procesa el `.pptx` con la herramienta de parsing: produce un `extraction.json` (una
   entrada por página: fondo, elementos ordenados con geometría en píxeles de lienzo) y vuelca los
   media a disco. Lee fondo de slide, ancla vertical de texto, autofit, interlineado y orientación
   vertical de texto, y la geometría de formas.
2. **Clasificar.** Por elemento decide el tipo de capa: foto → `image`; título/cuerpo → `text`;
   píldora → `rect` con `cornerRadius` y `stroke`; círculo del venn → `ellipse` con `stroke`;
   barras/dona → `chart`; horario → `table`; vector libre → `shape` con `pathData`.
3. **Mapear a la marca.** Tipografías a las caras de marca por rol/tamaño; colores a los tokens de la
   paleta; tamaños de fuente respetando el autofit de la fuente.
4. **Ensamblar.** Un `EditorDocument` por página (o una página por artboard). Parenta cada capa al
   `frame` para recortarla. Aplica el ancla vertical y el interlineado del texto.
5. **Validar con la herramienta** (`tools/validar_design_document.py`) antes de subir; usa el
   `upsert_arguments` que devuelve.
6. **Subir media a R2.** Nunca en base64. Sube cada archivo por el staged upload (create → PUT →
   finalize) y referencia su URL pública en `src` (ver `references/contratos-mcp.md`). Acepta imágenes
   y video.
7. **Upsert.** Sube cada página como su item de Brand Center.
8. **Verificar visualmente.** Renderiza cada página y compárala lado a lado con el original. Corrige
   hasta que coincidan. Recién entonces consideres la página lista.
9. **Handoff.** El usuario abre `/brand/<brandId>/designer?item=<itemId>` y termina en la plataforma.

### Crear desde cero

Define el `frame`, compón capas con tokens de marca, valida, sube con `item_key` nuevo, verifica el
render y entrega el enlace de handoff.

## Reglas duras

1. **Tokens reales, nunca inventados.** Toda tipografía y todo color salen del Brand Center de la
   marca. Si falta un token, dilo; no lo inventes.
2. **Validación con la herramienta antes de subir.** El `design_document` debe pasar
   `tools/validar_design_document.py` sin errores. El upsert usa el objeto `upsert_arguments` que
   devuelve la herramienta; **armar la envoltura `typed_payload` a mano está prohibido**. El backend
   solo verifica que `typed_payload` sea un objeto JSON, no la forma Konva: si subes un documento
   inválido no hay error de API, pero el editor lo bloquea al abrirlo (no lo edita ni lo sobrescribe).
   Por eso un documento que no pasa la herramienta nunca se sube. Revisa también las advertencias
   (`media://` sin resolver, datos de chart no positivos, fuentes sin stack).
3. **Nunca declares un diseño listo sin renderizarlo y compararlo con el original o el encargo.** Un
   documento que valida no es un documento que se ve bien. La verificación visual es obligatoria.
4. **Media sin base64.** Los bytes se suben por la ruta de archivos/staged upload y se referencian
   por URL pública; nunca incrustes binarios en el JSON ni los pases por el contexto del modelo.
5. **Fondo sólido manda sobre foto cubridora** cuando el diseño define un color de fondo plano.
6. **Español neutro, sin voseo.** Aplica a todo texto orientado al usuario.
7. **Sin elementos decorativos no pedidos.** No agregues badges ni adornos que la fuente no tenga.

## Autochequeo — antes de entregar

Recorre esta lista y no entregues hasta que todo dé verde:

- [ ] El `design_document` pasó `tools/validar_design_document.py` con 0 errores y las advertencias
      se revisaron; el upsert usa el `upsert_arguments` que devolvió la herramienta.
- [ ] Cada `fontFamily` es una cara de marca (stack CSS del kit), no el nombre de la tipografía
      original del archivo.
- [ ] Cada color es un token de marca (o blanco/negro puro), no un hex copiado sin mapear.
- [ ] Ninguna capa `image`/`video` quedó con un placeholder `media://`; todas apuntan a una URL
      pública de R2.
- [ ] Las capas que deben recortarse están parentadas al `frame`.
- [ ] Cada página se renderizó y se comparó con el original/encargo, y coinciden.
- [ ] Charts, venn y tablas son nativos y editables donde corresponde (no imágenes).
