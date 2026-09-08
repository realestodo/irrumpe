# Plan de pruebas para revisión

Estas pruebas cubren el acceso de solo lectura disponible para una cuenta `player`.
No requieren onboarding ni datos de Ads.

## Precondiciones

- Autentica mediante el MCP de Irrumpe una cuenta `player` que no sea propietaria y
  no tenga privilegios de escritura.
- Da a esa cuenta acceso a una marca de revisión con un ítem no sensible de Brand
  Center, datos de Pulso y al menos un contenido no sensible.
- Antes de ejecutar un caso, inspecciona la lista `tools/list` y los esquemas vivos
  del MCP. El entorno de ejecución, no este paquete, es la autoridad para el descriptor final de
  cada herramienta y el resultado de autorización.
- Las herramientas de lectura de los cinco casos positivos y del caso de aislamiento entre marcas
  deben aparecer en `tools/list` y ejecutarse dentro del ámbito autorizado. Las herramientas de
  escritura de los casos negativos no tienen que aparecer ni ser ejecutables para la cuenta
  `player`: su ausencia es válida y, si aparecen, deben denegar antes de escribir. No es requisito
  que todas las herramientas declaradas por el paquete sean ejecutables por ese rol.
- Registra la marca accesible seleccionada y los ID devueltos sin incorporarlos a
  este repositorio ni al material de envío.

## Casos positivos

1. **Listar dimensiones de Brand Center.** Solicita: “Muéstrame las dimensiones de
   Brand Center disponibles para mi marca de revisión”. Ejecuta
   `list_brand_center_dimensions`. Debe devolver el catálogo global activo de
   dimensiones, sin datos de ninguna marca y sin modificar estado alguno.
2. **Buscar recursos de la marca de revisión.** Solicita: “Busca los logos de mi
   marca de revisión en Brand Center”. Ejecuta `search_brand_assets`. Debe devolver
   metadatos acotados a esa marca, sin contenido binario ni recursos de otra marca.
3. **Inspeccionar un ítem de Brand Center.** Desde un ítem obtenido en el caso
   anterior, solicita su detalle. Ejecuta `get_brand_center_item_detail`. Debe
   devolver los metadatos y la carga tipada del ítem seleccionado, sin actualizarlo.
4. **Leer disponibilidad y panel de Pulso.** Solicita: “Muéstrame las métricas
   de Pulso disponibles y el panel actual de mi marca de revisión”. Ejecuta
   `get_brand_performance_availability` y `get_brand_performance_dashboard`. Debe
   devolver solo los datos disponibles para esa cuenta y no modificar estado alguno.
5. **Listar contenido de la marca de revisión.** Solicita: “Lista el contenido de
   mi marca de revisión”. Ejecuta `list_brand_content`. Debe devolver solo metadatos
   de contenido dentro de la marca accesible y no crear, editar ni publicar contenido.

## Casos negativos

1. **Denegación de escritura en Brand Center.** Solicita a la cuenta `player` crear
   o actualizar un diseño solo si `tools/list` expone `brand_center_item_upsert`.
   El servidor debe denegar la solicitud antes de persistir un cambio. Si la
   herramienta no aparece, el resultado también es correcto: informa que la cuenta
   no tiene permiso de escritura y no busques una ruta, herramienta ni marca
   alternativa. La razón es que una cuenta `player` no puede modificar Brand Center.
   Registra el resultado literal de autorización u omisión.
2. **Denegación de escritura en contenido.** Solicita a la cuenta `player` editar
   el título de un contenido de la marca de revisión solo si `tools/list` expone
   `content_update`. El servidor debe denegar la solicitud antes de persistir un
   cambio. Si la herramienta no aparece, informa que la cuenta no tiene permiso de
   edición y detente; no hay alternativa mediante otra herramienta o marca. La razón es
   que una cuenta `player` no puede modificar contenido. Registra el resultado
   literal de autorización u omisión.
3. **Aislamiento entre marcas.** Solicita `list_brand_content` para una marca que
   se sepa inaccesible para la cuenta `player`. No debe devolver contenido protegido
   ni metadatos de esa marca. Informa que la marca está fuera de su ámbito y ofrece
   elegir una marca de la lista accesible como única alternativa. La razón es el
   aislamiento entre marcas. Registra el resultado literal del servidor, que puede
   ser una denegación o un ámbito autorizado vacío.

## Límite del envío

Estos son casos de aceptación preparados, no evidencia de que el MCP remoto ya los
haya superado. Este paquete no contiene las implementaciones del MCP remoto ni sus
descriptores vivos de herramientas; por ello no puede generar de forma veraz un
`chatgpt-app-submission.json` final con anotaciones y esquemas de salida por herramienta.
No generes ese archivo antes de que la persona responsable del MCP exporte el
resultado vivo de `tools/list`, verifique las tres anotaciones de cada herramienta expuesta
y construya el JSON final a partir de esa evidencia.
