---
name: content-creation-guide
description: Skill de referencia para estilo, recursos creativos, restricciones de escritura y formatos de contenido de social media.
---

# Guia de creacion de contenido — Social Media

Referencia de estilo, recursos creativos, restricciones de escritura y formatos de output para contenido de social media.

## Estilo de escritura

- Oraciones activas y directas
- Tono profesional conversacional
- Sin jerga innecesaria
- Ritmo variado de oraciones
- Escritura clara, concreta y con intencion

## Recursos creativos

### Lexico-semanticos
- Metafora
- Simil
- Hiperbole
- Personificacion

### Fonicos
- Aliteracion
- Onomatopeya

### Morfosintacticos
- Hiperbaton
- Anafora

### Figuras del pensamiento
- Alegoria
- Ironia

## Patrones prohibidos

- Estructuras "No solo... sino tambien" y similares
- Tricolon / estructuras de 3 elementos repetitivos
- Multiples conclusiones
- Metaforas extendidas sobre tela/sinfonia/cocina
- Analogias forzadas que sugieren automatizacion
- Cierres tipo chatbot ("en resumen", "en conclusion")
- Parrafos con patron uniforme
- Ritmo monotono

## Patrones obligatorios

- Conectores variados: "ademas", "por otra parte", "en particular"
- Una sola conclusion fuerte
- Variacion de ritmo segun intensidad emocional

## Reglas de volumen por ventana

- 7-14 dias: 4-8 piezas
- 15-31 dias: 8-12 piezas
- Nunca mas de 12 piezas en una ejecucion

## Campos requeridos por pieza

```markdown
## [Titulo del contenido]

- **Objetivo:** ["opcion1", "opcion2"]
- **Etapa Funnel:** [valor valido]
- **Formato:** ["formato1", "formato2"]
- **Plataforma:** ["plataforma1", "plataforma2"]
- **Deadline deseado:** [YYYY-MM-DD dentro de la ventana]
- **Deadline deseado (end):** [YYYY-MM-DD] (opcional; espectro de ejecucion cuando la pieza requiere varios dias de produccion)
- **Contexto:** [por que ahora; senal de estrategia + planificacion]
- **Copy propuesto:**

[copy final]

- **Hashtags (Keywords):** [lista]
- **Acciones:** [CTA + instrucciones de ejecucion]
```

Regla nativa: `Copy propuesto` es caption y `Hashtags (Keywords)` es campo separado. Nunca anexar
hashtags al caption. Si una superficie destino no tiene campo nativo de hashtags, detener con
schema blocker antes de publicar.

## Formato multi-select

`Objetivo`, `Formato` y `Plataforma` siempre como arrays JSON:

- Correcto: `["Leads"]`, `["Leads", "Web Traffic"]`
- Incorrecto: `"Leads"`, `Leads, Web Traffic`, `Leads`

## Checklist de naturalidad (antes de entregar)

- [ ] Suena humano en conversacion real
- [ ] Evita frases cliche
- [ ] Variacion natural de ritmo
- [ ] Usa lenguaje cotidiano preciso
- [ ] Transiciones fluidas
- [ ] Cumple todas las restricciones de patrones prohibidos
- [ ] Todos los deadlines dentro de la ventana
- [ ] Copy/caption sin hashtags anexados
- [ ] Hashtags separados, normalizados y sin duplicados

## Payload JSON — estructura de contenidos

```json
{
  "client": "[Cliente]",
  "window_start": "YYYY-MM-DD",
  "window_end": "YYYY-MM-DD",
  "window_days": 14,
  "item_count": 6,
  "items": [
    {
      "title": "Titulo de la pieza",
      "objetivo": ["Leads"],
      "etapa_funnel": "Consideration",
      "formato": ["Carousel"],
      "plataforma": ["Instagram"],
      "deadline_deseado": "YYYY-MM-DD",
      "deadline_deseado_end": "YYYY-MM-DD",
      "contexto": "Razon de timing",
      "copy": "Texto final",
      "hashtags": ["#tag1", "#tag2"],
      "acciones": "CTA + ejecucion"
    }
  ]
}
```
