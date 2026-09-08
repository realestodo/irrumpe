---
description: "Onboarding conversacional de marca en Irrumpe: cuestionario de 6 etapas con ayudas, matriz de emociones y envío a Pre-revisión humana vía MCP."
---

# /onboarding — adaptador de onboarding de marca

Entrada del usuario (nombre de marca, opcional): $ARGUMENTS

Activa la skill `brand-onboarding`. Conserva el nombre aportado como contexto
de resolución, pero no asumas una marca ni repliques la lógica de entrevista,
validación, reanudación o envío: la skill y su referencia son la única fuente
del contrato. Si el MCP no expone las lecturas necesarias o devuelve un error,
informa el bloqueo literal y detente.
