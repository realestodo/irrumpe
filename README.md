# Irrumpe OS

Paquete autónomo de operación para la plataforma [Irrumpe](https://irrumpe.realestodo.com), para
**Claude Code** y **OpenAI Codex**. Incluye dos habilidades y un comando; sus manifiestos declaran el MCP
remoto de Irrumpe (`https://mcp.realestodo.com/mcp`) y usan OAuth con la cuenta de Irrumpe de la
persona:

- **`irrumpe-operator`** — opera la plataforma mediante el MCP: edita contenido y documentos,
  aprueba o rechaza trabajo mediante transiciones de estado, crea y edita diseños Konva, carga y
  consulta recursos de Brand Center, lee métricas de Pulso, opera campañas de Google Ads con
  escrituras tipadas y `dry_run` explícito, envía documentos base, crea proyectos y administra tareas
  y estados de documentos. Mantiene la dirección creativa en la persona usuaria. Traduce documentos
  base, diseños y plantillas aprobados a cargas útiles nativas, respetando los contratos de las
  herramientas y las barreras de escritura.
- **`brand-onboarding`** — onboarding de marca focalizado y neutral al entorno: resuelve el
  contrato vivo del MCP antes de entrevistar, captura respuestas obtenidas del catálogo y la matriz
  emocional de 45 enunciados, permite la revisión y se detiene antes de asignar personalidad o
  ejecutar narrativa. El onboarding sigue siendo una capacidad del producto, pero este paquete lo
  bloquea si el MCP no puede confirmar las herramientas y los contratos vigentes requeridos.
- **`/onboarding`** — adaptador liviano de Claude Code para `brand-onboarding`; no duplica el
  contrato del flujo ni repara la configuración del entorno.

> Este repositorio es un artefacto publicado. La fuente de verdad vive en el repositorio privado de
> Irrumpe; los cambios llegan mediante su proceso de publicación.

## Instalación — Claude Code

```
/plugin marketplace add realestodo/irrumpe
/plugin install irrumpe-os@irrumpe-os
```

El paquete declara el MCP de Irrumpe en `.mcp.json`. Confirma que el entorno instalado expone un
servidor `irrumpe` y autentícate mediante su interfaz MCP con tu cuenta de Irrumpe. Ejecuta
`/onboarding` o solicita operaciones de la plataforma en lenguaje natural solo después de contar
con esa conexión.

## Instalación — Codex

Para instalar desde un marketplace de Codex configurado, usa:

```
codex plugin add <plugin>@<marketplace>
```

Este paquete no registra ni publica un marketplace por sí solo.

Para configurar únicamente el MCP remoto en Codex, ejecuta lo siguiente solo después de que la
persona usuaria haya aprobado el cambio local de configuración y el flujo OAuth:

```
codex mcp add irrumpe --url https://mcp.realestodo.com/mcp
codex mcp login irrumpe
```

El manifiesto de Codex declara `.mcp.json`; una publicación futura en un marketplace debe
verificar cómo el entorno aplica esa declaración. Los comandos slash pertenecen a Claude Code. En
Codex, solicita la operación deseada de la plataforma en lenguaje natural. La habilidad de onboarding
focalizada opera su flujo solo cuando puede confirmar el contrato vivo del MCP.

## Lo que exige el operador

- El acceso de escritura se resuelve mediante indicadores de capacidad (`can_edit`, `can_manage_*`),
  nunca mediante etiquetas de rol. Las escrituras denegadas informan el permiso faltante; una
  escritura que se complete cuando los indicadores señalaban que debía fallar se informa como posible falla de
  permisos de la plataforma.
- El lenguaje dirigido a la persona usuaria sigue su idioma y registro regional; el texto existente
  se conserva salvo que solicite reescribirlo.
- Cuando el entorno expone archivos ejecutables del paquete, los documentos de diseño se validan
  mediante `tools/validar_design_document.py` antes de cada upsert; el upsert usa literalmente los
  argumentos devueltos. Un entorno sin esa capacidad no debe crear el diseño mediante este paquete.
- Los cambios de Ads siguen dependiendo de permisos. Un `dry_run: true` valida sin despachar al
  proveedor, pero puede crear un registro de acción en Irrumpe, por lo que también exige
  confirmación. Una solicitud real usa además `dry_run: false`; el operador informa el estado crudo
  de la acción y sigue las acciones despachadas hasta un resultado terminal antes de consultar las
  vistas sincronizadas con el proveedor.
- Los archivos binarios de diseño y Brand Center usan carga escalonada cuando el entorno puede
  acceder a sus bytes. La importación de URL en el servidor se limita a media http(s) para contenido
  y documentos; ninguna ruta envía bytes a través del modelo.
- El onboarding de marca exige confirmación explícita antes del envío y la asignación de personalidad
  queda en el equipo de revisión humana. La skill focalizada se detiene si no puede confirmar el
  catálogo vivo, una herramienta requerida o su contrato; no reemplaza datos faltantes con supuestos
  locales.

## Requisitos

- Una cuenta de Irrumpe, con autenticación OAuth para el MCP.
- Para upserts de diseño, un entorno que pueda ejecutar el validador incluido desde el paquete
  instalado. Los flujos de consulta no requieren Python ni acceso al sistema de archivos local.

## Revisión, soporte y estado de publicación

Consulta [REVIEW.md](./REVIEW.md) para los cinco casos positivos y los tres negativos de revisión,
y [SUPPORT.md](./SUPPORT.md) para el diagnóstico en ejecución y los bloqueos de publicación externos
al paquete.

## Licencia

MIT — véase [LICENSE](./LICENSE).
