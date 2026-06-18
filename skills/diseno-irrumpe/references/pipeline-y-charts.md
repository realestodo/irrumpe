# Pipeline de recreación, charts, venn y tablas

Cómo se recrea un diseño externo con fidelidad a la marca, y cómo se arman los elementos nativos.
Incluye los aprendizajes que evitan los errores ya cometidos. Prosa en español; campos y valores en
inglés.

---

## 1. Flujo de recreación desde un `.pptx`

Canva exporta un diseño como `.pptx`. Es la mejor fuente: media reales en disco, fuentes con su
nombre real, colores en hex y posiciones exactas en EMU. Canva preserva el artboard 9:16
(`sldSz cx=10287000 cy=18288000` EMU = 1080×1920), así que el EMU mapea a píxeles de lienzo con una
escala uniforme; `font_px = sizePt × 1.3333`.

1. **Parse → `extraction.json`.** Una entrada por slide con `background`, y elementos ordenados
   (imagen / texto / forma) con su `box` en píxeles. Extrae explícitamente:
   - **Fondo de slide** (`p:cSld/p:bg`): color sólido o imagen. Si no lo lees, las páginas de fondo
     sólido salen en blanco con el texto invisible.
   - **Ancla vertical** del texto (`bodyPr@anchor`: `t`/`ctr`/`b`).
   - **Autofit** (`bodyPr/normAutofit@fontScale`, per-cent-mille): Canva encoge el texto para que
     entre en su caja. Sin esto el texto se desborda y reparte una palabra por línea.
   - **Interlineado** (`pPr/lnSpc/spcPct`) y **orientación vertical** (`bodyPr@vert`): una marca de
     agua lateral usa `vert`/`vert270` y debe rotarse.
   - **Geometría de forma** (`prstGeom@prst` o `custGeom`) y `fill`/`stroke`.
2. **Mapear a la marca.** Cada tipografía del export se mapea a una cara de marca por rol/tamaño
   (nunca se conserva el nombre original). Cada color se ajusta (snap) al token de paleta más
   cercano; blancos y negros puros se conservan. El `font_px` se multiplica por el `fontScale` del
   autofit.
3. **Ensamblar** un `EditorDocument` por página y parentar cada capa al `frame`.
4. **Subir media** a R2 y rellenar los `src` (ver `contratos-mcp.md`).
5. **Upsert** y **verificar** página por página contra el original.

## 2. Aprendizajes que evitan errores (no repetir)

- **Fondo a sangre por área, no por umbrales de borde.** Una imagen cuenta como fondo cuando su
  intersección con el artboard cubre ≥ 97% del área; los umbrales de borde rígidos rechazan fotos
  genuinamente full-bleed que sobresalen un poco.
- **Fondo sólido manda.** Si el slide define `p:cSld/p:bg` sólido, ese color es el `frame.fill` y
  ninguna imagen cubridora lo reemplaza. Una foto que pisa un color plano deseado es un error.
- **Píldora vs forma.** Una `custGeom` sin relleno y solo con `stroke` NO es siempre una píldora;
  puede ser un círculo (venn) o una línea. No la conviertas en `rect` redondeado por defecto: mira la
  geometría real (un cuadrado con `stroke` y sin relleno es un círculo → `ellipse`).
- **Fuente de marca, siempre.** Mapea toda tipografía a las dos caras reales de la marca; nunca
  conserves el nombre del archivo externo. Una tipografía serif "del archivo" en el resultado es un
  defecto.
- **Verifica antes de declarar listo.** Renderiza y compara con el original. Un documento que valida
  puede verse mal (texto desbordado, fondo equivocado, forma incorrecta).
- **Versiones de fuente distintas.** Un export viejo puede diferir de la versión actual del diseño
  (otro color de fondo, otro layout). Cuando el export y la referencia visual no coincidan, pídele al
  usuario cuál es la verdad; no asumas.

## 3. Charts nativos

La capa `chart` cubre barras (verticales/horizontales), líneas, área, pie y donut. Campos relevantes:
`chartKind`, `data:[{label,value}]`, `palette[]`, `orientation`, `trackColor`, `barCornerRadius`,
`legend` (`around`/`right`/`none`), `donutThickness`, `donutCornerRadius`, `fontFamily`, `showLabels`,
`showValues`, `textFill`, `fontSize`.

### Barras horizontales two-tone (ej. "ALCANCE DE MARCA")

La barra de color representa el valor; el `trackColor` rellena el resto. Para clavar labels y valores
exactos (con `%`, en el idioma correcto, en su posición), deja el chart **solo con las barras**
(`showLabels:false`, `showValues:false`) y pon los labels y valores como capas `text` encima, con sus
colores (label oscuro sobre la barra clara; valor claro sobre el track). El chart va detrás de los
textos en z-order.

```jsonc
{ "type":"chart", "chartKind":"bar", "orientation":"horizontal",
  "x":120, "y":612, "width":840, "height":740,
  "data":[{"label":"SKINCARE","value":80},{"label":"BIENESTAR","value":60},
          {"label":"HOGAR","value":50},{"label":"BEAUTY","value":70}],
  "palette":["#FDFBE5"], "trackColor":"#CBAB6B", "barCornerRadius":18,
  "showLabels":false, "showValues":false, "showGrid":false,
  "textFill":"#FDFBE5", "fontSize":24, "fontFamily":"\"new-science\", sans-serif" }
```

### Donut con leyenda alrededor (ej. "REVENUE DE MARCA")

`legend:"around"` ubica cada label + valor alrededor del anillo, en el color de su segmento. Los
`data.value` se reparten como porcentaje del total; ponlos como porcentajes reales (suman ~100).

```jsonc
{ "type":"chart", "chartKind":"donut", "legend":"around", "donutThickness":0.46,
  "x":40, "y":300, "width":1000, "height":1040,
  "data":[{"label":"Shopping","value":11.8},{"label":"Food","value":11.8},
          {"label":"Bills","value":17.6},{"label":"Medicine","value":23.5},{"label":"Others","value":35.3}],
  "palette":["#2A313A","#3E4751","#EFD6E2","#97A05C","#6E7A45"],
  "showLabels":true, "showValues":true, "textFill":"#444444",
  "fontSize":26, "fontFamily":"\"new-science\", sans-serif" }
```

Detalle: el chart muestra el valor numérico (`11.8`) sin el símbolo `%`. Si la fidelidad exige `%`,
apaga `showValues`/`legend` y pon los labels alrededor como capas `text` (`"Shopping 11.8%"`).

## 4. Venn / diagramas (ikigai)

No hay primitiva de diagrama. Un venn se arma con capas `ellipse`: un círculo es una `ellipse` con
`radiusX=radiusY`, `stroke` (borde) y `fill:"#00000000"` (transparente). Centro = esquina + radio.
Las regiones del ikigai (`PASIÓN`, `AMOR`, `TU`, …) son capas `text` encima de los círculos. Para un
vector más complejo que no sea un círculo, usa `shape` con `pathData` (recuerda incluir igual un
`shapeId` del registro: la validación lo exige aunque `pathData` lo sobrescriba al dibujar).

```jsonc
{ "type":"ellipse", "x":391, "y":1034, "radiusX":297, "radiusY":297,
  "fill":"#00000000", "stroke":{"color":"#FCDECE","width":3,"align":"center"} }
```

## 5. Tablas

La tabla de horario/precios es una capa `table` nativa: `cells` (matriz fila-mayor), `headerRow`,
`bandedRows`, `fontSize` y los colores (`textFill`, `headerTextFill`, `borderFill`, `headerFill`,
`cellFill`, `bandFill`). Para que no se vea apretada, respeta el interlineado de la fuente y dimensiona
la caja al alto real del contenido.

## 6. Video de fondo

Un fondo de video es una capa `video` con su URL pública de R2. El editor lo reproduce solo en
previsualización/exportación; en modo edición se ve el fondo del frame, no el cuadro de video. Eso es
correcto: no lo confundas con un video roto. Verifica la URL aparte (debe responder `200` con
`content-type: video/*`).
