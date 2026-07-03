---
description: "Onboarding conversacional de marca en Irrumpe: cuestionario de 6 etapas con ayudas, matriz de emociones y envío a Pre-revisión humana vía MCP."
---

# /onboarding — onboarding de marca

Entrada del usuario (nombre de marca, opcional): $ARGUMENTS

## Contrato de ejecución

Carga la skill `irrumpe-operator` y su reference `references/onboarding-de-marca.md`. Toda la
lógica del flujo (contratos, validaciones, manejo de errores, reanudación) vive en esa reference;
este comando solo fija la secuencia y sus puntos de detención.

## Secuencia

1. **Fase 0 — MCP.** Verifica que el MCP de Irrumpe responde. Si falta y el entorno tiene
   filesystem, repara el cableado según la reference y guía la autenticación OAuth; sin filesystem,
   entrega la instrucción manual y espera confirmación.
2. **Fase 1 — Permisos.** Pre-flight con `get_user_account_state` y `list_user_accessible_brands`.
   Detente con mensaje claro cuando la marca ya tenga un onboarding enviado, y ante un 402 muestra
   el upsell tal como llega.
3. **Fase 2 — Inicio.** `brand_onboarding_start` (reanuda la ficha activa si existe).
4. **Fase 3 — Catálogo.** Carga el catálogo completo de preguntas en vivo
   (`list_brand_onboarding_question_catalog`).
5. **Fase 4 — Cuestionario.** Etapa por etapa: preguntas con sus subpreguntas de ayuda, opciones
   cerradas con la herramienta nativa de preguntas bloqueantes, respuestas abiertas por chat,
   gate local de obligatorias y mínimo de caracteres, y `brand_onboarding_save` al cierre de cada
   etapa.
6. **Fase 5 — Matriz de emociones.** Los 45 enunciados desde el mapping de la ficha, escala 0–3.
7. **Fase 6 — Resumen.** Muestra el resumen completo por etapa y ofrece correcciones.
8. **Fase 7 — Envío.** `brand_onboarding_submit` únicamente con confirmación explícita del usuario;
   informa que la revisión y la asignación de personalidad quedan en manos del equipo humano.

## Prohibiciones

- Nunca llames `brand_onboarding_personality_set` ni corridas de narrativa.
- Nunca envíes la ficha sin confirmación explícita.
- Nunca respondas preguntas en nombre del usuario ni infles respuestas para pasar el mínimo de
  caracteres.
