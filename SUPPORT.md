# Soporte y estado de publicación

## Soporte

Los metadatos autónomos del catálogo declaran `hola@realestodo.com` como
contacto propietario del paquete. No hay una URL pública de soporte, política de
privacidad ni términos de servicio declarada en este paquete. Esas URL son bloqueos
externos: deben proveerse y verificarse fuera de este paquete antes de usarlas en
un catálogo o en un envío de Apps. No las inventes.

Los recursos gráficos locales de logotipo e icono de compositor se declaran en el manifiesto de
Codex. No sustituyen las URL externas de soporte, privacidad o términos.

## Diagnóstico

- **No está el servidor MCP `irrumpe`.** Confirma que el entorno instaló la
  declaración MCP del paquete. Para una configuración directa de Codex, obtén la
  aprobación de la persona usuaria antes de ejecutar
  `codex mcp add irrumpe --url https://mcp.realestodo.com/mcp`; después ejecuta
  `codex mcp login irrumpe` para completar OAuth.
- **Falla OAuth o una respuesta 401.** Vuelve a autenticar el MCP y repite la
  lectura requerida antes de reintentar una operación. No reutilices la identidad,
  marca ni datos de permisos de una sesión anterior.
- **Falta una herramienta requerida o su esquema está desactualizado.** Informa el
  nombre literal de la herramienta y el error del servidor. No sustituyas la acción
  ni infieras su carga útil. La superficie pública del MCP retiró el 31-08-2026 las
  lecturas de cuenta, notificaciones y eliminación de versiones; las lecturas de
  cuenta y acceso vigentes son `get_user_brand_creation_state` y
  `list_user_accessible_brands`. Un descriptor que anuncie otra cosa es obsoleto y
  el flujo dependiente debe detenerse.
- **Ocurre una respuesta 403.** Informa el permiso denegado y no reintentes mediante
  una herramienta o una marca alternativas.
- **Un diseño necesita un upsert pero el entorno no puede ejecutar el validador
  incluido.** No crees el diseño. Usa una superficie nativa de Irrumpe o una ruta de
  validación MCP viva solo cuando el entorno de ejecución demuestre que es equivalente.
- **Se solicita un cambio de Ads.** Trata tanto `dry_run: true` como `dry_run: false`
  como escrituras en Irrumpe y obtén confirmación primero. El primero no debe
  despachar al proveedor, pero puede crear un registro de acción.

## Estado de publicación

Versión del paquete: `1.2.3`.

Validación local en Claude Code: `claude plugin validate --strict <ruta-del-paquete>`.
Cuando el paquete se valida desde su propio directorio, ese comando valida primero
el catálogo `.claude-plugin/marketplace.json`; el manifiesto del plugin se valida al
instalar el paquete o al validar una copia sin ese catálogo.

Ruta de distribución en el ecosistema de Claude: el catálogo `claude-plugins-official`
es curado por Anthropic sin proceso de solicitud; los envíos de terceros van al
marketplace comunitario `claude-community` a través del formulario de Console o
de claude.ai, tras pasar `claude plugin validate` y el análisis automático de
seguridad. Mientras no exista esa aprobación, la instalación se hace desde el
catálogo propio del paquete, como indica el README.

El paquete está listo para revisión estática de manifiesto, instrucciones y
validador local. No demuestra una publicación externa ni un envío de ChatGPT Apps
completado. Los bloqueos externos vigentes son la verificación en vivo de los
descriptores y autorizaciones del MCP con la cuenta `player`, las anotaciones y los
esquemas de salida finales por herramienta, y las URL públicas de soporte, privacidad y
términos cuando la superficie de distribución las exija. No se debe generar
`chatgpt-app-submission.json` hasta contar con una exportación viva de `tools/list`
que sustente esos campos.
