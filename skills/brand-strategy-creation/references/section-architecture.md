# Arquitectura de secciones estratégicas

## Principio

Las 19 secciones forman una cadena donde cada una alimenta a las siguientes. La coherencia interna es la métrica principal de calidad: una estrategia donde el diagnóstico dice una cosa y el arco anual hace otra es una estrategia rota.

## Secciones y sus relaciones

### 1. Diagnóstico estratégico

**Propósito**: radiografía del estado actual de la marca en su contexto competitivo.
**Contenido mínimo**: situación de mercado, posición relativa, principales tensiones, oportunidades y amenazas.
**Alimenta a**: Posicionamiento, Segmentos, Riesgos.
**Efecto de STRATEGY_EMPHASIS**: si `growth`, profundiza en oportunidades de expansión; si `positioning`, profundiza en percepción actual vs. deseada; si `profitability`, profundiza en estructura de costos y márgenes.

### 2. Concepto

**Propósito**: ancla conceptual que gobierna toda la estrategia.
**Contenido mínimo**: declaración literal de `GOVERNING_CONCEPT` si existe conceptualización. Si no existe, concepto derivado de narrativa aprobada con declaración explícita de origen.
**Alimenta a**: todas las secciones restantes. Es el filtro de coherencia.
**Regla crítica**: nunca parafrasear el concepto gobernante. Reproducción literal obligatoria.

### 3. Cosmovisión operativa

**Propósito**: cómo la marca entiende su propio funcionamiento en el mundo.
**Contenido mínimo**: modelo mental de la marca sobre su relación con el mercado, su audiencia y su propósito operativo.
**Alimenta a**: Narrativa, Valor, Posicionamiento.

### 4. Segmentos prioritarios

**Propósito**: a quién se dirige la estrategia, en qué orden de prioridad.
**Contenido mínimo**: segmentos definidos con perfil, tamaño estimado, relevancia estratégica y priorización.
**Alimenta a**: Narrativa, Arco anual, KPIs.
**Regla de coherencia**: si `PRIMARY_AGE_RANGE` existe, segmentos fuera de ese rango llevan etiqueta `HIPÓTESIS`.

### 5. Sistema de posicionamiento

**Propósito**: el espacio mental que la marca ocupa (o quiere ocupar) en la mente de sus audiencias.
**Contenido mínimo**: posición actual, posición deseada, diferenciadores clave, marco de referencia competitivo.
**Alimenta a**: Valor, Narrativa, Objetivos.

### 6. Arquitectura de valor

**Propósito**: qué valor entrega la marca, a quién, y cómo se estructura.
**Contenido mínimo**: propuesta de valor por segmento, jerarquía de beneficios (funcionales, emocionales, sociales).
**Alimenta a**: Narrativa, Objetivos, KPIs.

### 7. Foco narrativo y mensajería

**Propósito**: el territorio de comunicación y los mensajes clave.
**Contenido mínimo**: territorio narrativo, mensajes por segmento, tono de voz, pilares de contenido.
**Alimenta a**: Arco anual, Velocidad.

### 8. Objetivos estratégicos

**Propósito**: qué debe lograr la marca en el período de 12 meses.
**Contenido mínimo**: objetivos guiados por `STRATEGY_EMPHASIS` y `STRATEGY_TYPES`, medibles, con horizonte temporal.
**Alimenta a**: Arco anual, KPIs, Kickoff 90 días.
**Efecto de STRATEGY_EMPHASIS**: los objetivos se ponderan según el énfasis. `growth` prioriza adquisición y expansión; `retention` prioriza lealtad y recurrencia; `balanced` distribuye.

### 9. Mapa de ciclo de industria y estacionalidad

**Propósito**: calendario de 12 meses con las dinámicas propias de la industria.
**Contenido mínimo**: meses de alta y valle, eventos del sector, ventanas de oportunidad, fechas comerciales relevantes.
**Alimenta a**: Arco anual, Velocidad.

### 10. Arco estratégico anual (Q1-Q4)

**Propósito**: la estrategia traducida a cuatro trimestres con foco progresivo.
**Contenido mínimo**: foco de cada trimestre, prioridades, conexión con objetivos y ciclo de industria.
**Alimenta a**: Velocidad, KPIs, Kickoff 90 días.
**Efecto de STRATEGY_EMPHASIS**: la distribución de intensidad por trimestre cambia según el énfasis. `launch` concentra en Q1; `growth` escala progresivamente; `positioning` mantiene constancia.

### 11. Modelo de velocidad

**Propósito**: control multi-ritmo para la ejecución estratégica.
**Contenido mínimo**: ritmos diferenciados por tipo de acción (always-on, campañas, experimentos), cadencia de revisión.
**Alimenta a**: KPIs.

### 12. Árbol de KPI

**Propósito**: métricas que miden el progreso de la estrategia.
**Contenido mínimo**: KPIs primarios vinculados a objetivos, KPIs secundarios por tipo de estrategia, frecuencia de medición.
**Alimenta a**: Riesgos (umbrales de alerta).
**Regla de coherencia**: cada KPI debe conectar con al menos un objetivo estratégico.

### 13. Registro de riesgos y supuestos

**Propósito**: transparencia sobre incertidumbres y dependencias.
**Contenido mínimo**: riesgos identificados con probabilidad e impacto, supuestos explícitos con plan de validación, conflictos entre fuentes.

### 14. Kickoff de 90 días

**Propósito**: las acciones prioritarias para los primeros 3 meses.
**Contenido mínimo**: top 5-7 acciones concretas, responsables sugeridos, métricas de éxito a 90 días.
**Regla**: subordinada a la estrategia de 12 meses. No es un plan independiente.

### 15. Cobertura de señales estratégicas

**Propósito**: demostrar que todas las señales relevantes encontradas en fuentes se integraron.
**Contenido mínimo**: tabla con señal, fuente, sección donde se integró, estado.

### 16. Cobertura por tipo de estrategia

**Propósito**: verificar que cada tipo de estrategia declarado tiene representación en el documento.
**Contenido mínimo**: tabla tipo → secciones que lo cubren → estado de cobertura.

### 17. Puentes desde conceptualización

**Propósito**: hacer explícita la conexión entre conceptualización y estrategia.
**Contenido mínimo**: elementos de conceptualización retomados, cómo se tradujeron a secciones estratégicas.

### 18. Plan de cierre de faltantes

**Propósito**: plan de acción para cada `[MISSING]` declarado.
**Contenido mínimo**: faltante, owner propuesto, deadline sugerido, método de obtención.
**Regla**: solo se incluye si hay al menos un `[MISSING]` en el documento.

### 19. Capas opcionales explícitas

**Propósito**: integración de capas adicionales solicitadas o detectadas.
**Contenido mínimo**: depende de la capa. Para `personal-branding-socios`: diagnóstico de marca personal, puntos de integración con estrategia corporativa, alcance estratégico (sin táctico).
**Regla**: solo se incluye si `OPTIONAL_STRATEGY_LAYERS` ≠ `none`.

## Cadena de coherencia

La validación de coherencia sigue esta cadena:

```
Diagnóstico → Posicionamiento → Segmentos → Objetivos → Arco anual (Q1-Q4) → KPIs
```

Cada eslabón debe derivarse lógicamente del anterior. Si un objetivo no tiene raíz en el diagnóstico, o un KPI no conecta con un objetivo, la cadena está rota.

## Efecto de STRATEGY_EMPHASIS sobre el documento completo

| Énfasis | Secciones con mayor peso | Secciones subordinadas |
| --- | --- | --- |
| `growth` | Segmentos, Arco anual, Velocidad | Posicionamiento (soporte) |
| `positioning` | Posicionamiento, Narrativa, Concepto | Velocidad (soporte) |
| `profitability` | Valor, KPIs, Diagnóstico (costos) | Narrativa (soporte) |
| `retention` | Segmentos, Valor, Velocidad | Posicionamiento (soporte) |
| `reputation` | Narrativa, Posicionamiento, Riesgos | Velocidad (soporte) |
| `launch` | Arco anual (Q1 intenso), Kickoff 90d, Velocidad | Riesgos (elevado) |
| `efficiency` | Velocidad, KPIs, Diagnóstico (recursos) | Narrativa (soporte) |
| `balanced` | Distribución uniforme | Ninguna subordinada |
