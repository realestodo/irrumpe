# Onboarding de marca — contrato completo

El contrato que ejecuta el comando `/onboarding`: cuestionario Mapa Irrumpe de 6 etapas, matriz de
emociones y envío a revisión humana. Prosa en español; tools, campos y valores en inglés.

---

## 1. Qué produce

Una **ficha de onboarding** (`brand_onboardings`) con las respuestas narrativas de la marca y su
matriz de resonancia emocional. Al enviarla, la ficha se congela y la marca pasa a **Pre-revisión**
con `status = needs_personality_review`: una persona del equipo interno revisa la data y asigna la
personalidad. El envío jamás dispara generación automática.

## 2. Fase 0 — Verificación del MCP

Antes de todo, confirma que el MCP de Irrumpe responde con una lectura barata
(`get_user_account_state`). Si el server está ausente y el entorno tiene filesystem (Claude Code,
Cowork, Codex):

- **Claude Code:** el plugin ya trae `.mcp.json`; si el server sigue sin aparecer, registra el
  remoto con `claude mcp add --transport http irrumpe https://mcp.realestodo.com/mcp` y pide al
  usuario autenticarse vía `/mcp` (OAuth con su cuenta de Irrumpe).
- **Codex:** el plugin trae `.codex-mcp.json`; en instalaciones manuales agrega el server a la
  config de Codex (`mcp_servers.irrumpe.url = "https://mcp.realestodo.com/mcp"`) y pide
  `codex mcp login irrumpe`.
- **Sin filesystem:** entrega la instrucción manual y detente hasta que el usuario confirme la
  conexión.

Si la lectura falla por autenticación (401), guía la re-autenticación OAuth y reintenta. Nunca
inventes un estado de cuenta.

## 3. Fase 1 — Pre-flight de permisos

1. `get_user_account_state` — identidad y `user_type` del actor.
2. `list_user_accessible_brands` — marcas visibles, roles y flags de capacidad.

Reglas de detención:
- **Marca ya vinculada con onboarding:** si el usuario apunta a una marca existente, lee
  `get_brand_onboarding_current` (`brand_id`). Una ficha activa en curso se **reanuda** (el save es
  PATCH); una ficha ya enviada o congelada se informa y el flujo se detiene: repetir el onboarding
  de una marca ya onboardeada queda fuera del alcance del player.
- **Cupo de marcas:** las tools de billing están deshabilitadas por MCP, así que el cupo se
  verifica en el server al llamar `brand_onboarding_start`. Un HTTP 402 `requires_paid_plan`
  significa que el usuario ya consume su cupo de marca gratuita; muestra el mensaje y el payload de
  `upsell` tal como llegan y detén el flujo. Continuar requiere un plan pagado.
- **Idempotencia por nombre:** `start` con un `brand_name` ya usado por el actor reutiliza la ficha
  activa existente en lugar de duplicar la marca. Informa al usuario cuando esto ocurra.

## 4. Fase 2 — `brand_onboarding_start`

`brand_onboarding_start({ brand_name })` para una marca nueva, o
`brand_onboarding_start({ brand_id })` para una existente. Devuelve (o reutiliza) la ficha con su
`onboarding_id`. Guarda ese id: todas las escrituras siguientes lo requieren.

## 5. Fase 3 — Catálogo en vivo

`list_brand_onboarding_question_catalog` (filtros: `stage_number` 1–6, `question_key`,
`question_type`; pagina con `limit`/`offset` hasta agotar el catálogo). Cada fila trae:

- `stage_key`, `stage_number`, `stage_order`, `stage_label`, `stage_intro` — las 6 etapas.
- `question_key`, `question_order`, `question_type`, `title`, `required`.
- `subquestions` — las subpreguntas de ayuda que profundizan la respuesta.
- `ai_guidance` — guía de conducción para formular y evaluar la respuesta.
- `definition` — JSON con la configuración específica (escala y fuente de enunciados de la matriz,
  opciones de selección, etc.).

El catálogo es la única fuente de verdad de las preguntas: nunca las inventes, reordenes ni
traduzcas por tu cuenta. Las 12 preguntas narrativas mapean 1:1 a columnas de la ficha (`por_que`,
`historia`, `producto`, `experiencia`, `publico_objetivo`, `cultura`, `estilo_trabajo`,
`valor_agregado`, `posicionamiento`, `posicionamiento_deseado`, `contexto`, `claims_industria`).
`personalidad` jamás es una pregunta del cuestionario.

## 6. Fase 4 — Cuestionario etapa por etapa

Conduce etapa por etapa, en el orden del catálogo:

1. Presenta la etapa con su `stage_intro`.
2. Para cada pregunta: formula el `title`, ofrece las `subquestions` como ayuda cuando la respuesta
   llegue corta o vaga, y usa el `ai_guidance` para evaluar si la respuesta es contundente.
3. Preguntas con opciones cerradas (según `question_type`/`definition`) van con la herramienta
   nativa de preguntas bloqueantes (`AskUserQuestion` en Claude Code, `request_user_input` en
   Codex); las abiertas van por chat.
4. **Gate local de calidad (el server no lo valida):** toda pregunta `required` necesita respuesta;
   las respuestas de texto requeridas necesitan un mínimo de **140 caracteres** de contenido
   sustantivo. Re-pregunta con las subpreguntas de ayuda hasta alcanzarlo. Rellenar o parafrasear
   para inflar el conteo está prohibido: el contenido lo aporta el usuario.
5. Al cerrar cada etapa persiste con `brand_onboarding_save`:

```jsonc
brand_onboarding_save({
  onboarding_id,
  current_step,               // 0–6, la etapa vigente
  current_question_key,       // debe existir en el catálogo y pertenecer a current_step
  patch: { por_que: "...", historia: "..." }   // PATCH: solo las columnas respondidas
})
```

El save es PATCH: guarda temprano y seguido; una sesión interrumpida se reanuda leyendo
`get_brand_onboarding_current` y continuando desde `current_question_key`.

## 7. Fase 5 — Matriz de emociones

La etapa de resonancia emocional captura la personalidad de la organización:

- Los **enunciados** llegan con la ficha (`enneagram_mapping` en `get_brand_onboarding_current`).
  Si el mapping llega vacío, detente y reporta el problema; nunca inventes enunciados.
- La respuesta es `enneagram_matrix`: **exactamente 45 enteros de 0 a 3**, uno por enunciado, en el
  orden del mapping. Escala: `0 = Nada`, `1 = Algo`, `2 = Mucho`, `3 = Clave`.
- Conduce los enunciados en grupos pequeños con la herramienta de preguntas bloqueantes, registrando
  el valor de cada uno. La mecánica interna (9 tipos × 5 enunciados) queda invisible para el
  usuario: presenta los enunciados como afirmaciones emocionales sobre la organización.
- Persiste con `brand_onboarding_save` (`patch: { enneagram_matrix: [/* 45 ints */] }`). El backend
  calcula los puntajes; el operador nunca calcula ni sugiere el tipo resultante.

## 8. Fase 6 — Resumen de revisión

Antes de enviar, muestra al usuario un resumen por etapa: cada pregunta con su respuesta (o su
ausencia), y la matriz completada. Ofrece corregir cualquier punto (los saves son PATCH). Verifica
el gate local completo: todas las `required` respondidas, mínimos cumplidos, matriz con 45 valores.

## 9. Fase 7 — `brand_onboarding_submit`

Solo con confirmación explícita del usuario:

```jsonc
brand_onboarding_submit({ onboarding_id })
```

Congela la ficha, mueve la marca a **Pre-revisión** y deja `status = needs_personality_review` con
notificación interna de revisión. Informa al usuario que una persona del equipo revisará la data y
asignará la personalidad; ese paso queda fuera del alcance de este flujo.

## 10. Prohibiciones y errores

- **`brand_onboarding_personality_set` está prohibido.** Requiere supervisión interna; para un
  player devuelve 403. Lo mismo aplica a la corrida de narrativa.
- 402 `requires_paid_plan` → muestra el upsell y detente (ver §3).
- 403 en cualquier tool → reporta el permiso faltante sin reintentar por rutas alternativas.
- Error de red o token vencido a mitad del cuestionario → guía la re-autenticación, relee
  `get_brand_onboarding_current` y reanuda desde donde quedó.
- Nunca envíes (`submit`) sin confirmación explícita; nunca respondas preguntas en nombre del
  usuario; nunca infles respuestas para pasar el gate de caracteres.
