# Auditoría de desperdicio y oportunidades

Usa esta referencia cuando el usuario pida diagnosticar Google Ads, detectar geografías de bajo
valor, encontrar filtraciones de presupuesto, revisar search terms o descubrir oportunidades de
escala.

La auditoría parte del gasto y termina en una decisión operable. Una anomalía requiere evidencia,
falsación y contexto antes de convertirse en hallazgo.

## Cadena de investigación

1. Money trail
2. Geografía
3. Search terms
4. Filtraciones estructurales
5. Oportunidades de escala
6. Decisión de arquitectura
7. Operación por Irrumpe MCP o pre-revisión

Mantén esta secuencia. Evita saltar directo a keywords o geos cuando el patrón de gasto todavía no
está claro.

## Taxonomía de señales

Clasifica cada señal antes de recomendar:

| Clasificación | Uso |
|---|---|
| `confirmed_finding` | Hay volumen suficiente, patrón estable y causa probable. |
| `hypothesis` | Hay señal, pero falta evidencia para actuar. |
| `false_positive_risk` | Parece un problema, pero puede explicarse por contexto legítimo. |
| `measurement_issue` | El dato puede estar incompleto, roto o mal atribuido. |
| `not_actionable` | Falta impacto, muestra, permiso o herramienta para ejecutar. |

Cada recomendación debe incluir:

- evidencia observada;
- explicación alternativa revisada;
- confianza (`low`, `medium`, `high`);
- acción propuesta;
- estado operativo esperado (`preview`, `pre_revision`, `applied`, `blocked`).

## Guardrails contra falsos positivos

Antes de marcar desperdicio, revisa:

### Muestra suficiente

- No excluir por pocos clicks y cero conversiones.
- Revisar costo, clicks, conversiones y días activos.
- Para decisiones duras, preferir 30-90 días según volumen y estacionalidad.

### Comparación justa

- Separar brand y non-brand.
- Separar campañas nuevas, maduras y en learning.
- Comparar geos, devices y ad groups contra clusters equivalentes.
- Diferenciar campañas exploratorias de campañas de eficiencia.

### Tracking sano

- CPA alto puede venir de conversion tracking incompleto.
- Mobile bajo puede ocultar llamadas, WhatsApp o conversiones offline.
- Geo aparentemente mala puede tener ventas offline o LTV mayor.
- Search terms sin conversión pueden estar asistiendo si el ciclo de venta es largo.

### Intención estratégica

- Una campaña puede comprar aprendizaje, cobertura, defensa de marca o inventario futuro.
- Broad match puede estar descubriendo demanda útil si tiene negativas y puja coherente.
- Una geo cara puede justificar inversión si el valor de cliente es superior.

### Explicaciones alternativas

Revisar:

- estacionalidad;
- cambios recientes de presupuesto;
- landing nueva;
- bidding strategy en learning;
- presupuesto limitado;
- promociones o cambios comerciales;
- importación tardía de conversiones;
- poca muestra.

## 1. Money trail

Objetivo: identificar dónde se gasta la plata antes de decidir qué optimizar.

Pasos:

1. Tomar 60-90 días cuando el volumen lo permita.
2. Ordenar campañas, ad groups, keywords y search terms por costo.
3. Calcular CPA/CVR usando conversiones confiables y, si existe, valor real de negocio.
4. Separar el presupuesto que consume mucho y aporta poco.
5. Identificar el bottom de gasto con bajo resultado y el top de resultado con capacidad de escala.

Preguntas:

- ¿Qué 20% de entidades concentra gasto con bajo retorno?
- ¿Qué entidades concentran conversiones o valor con bajo impression share?
- ¿El CPA observado se sostiene con datos de CRM, revenue o calidad de lead?
- ¿El gasto viene de intención, geografía, dispositivo, red, horario o estructura?

Salida:

- `waste_pool`: entidades con gasto alto y bajo retorno;
- `opportunity_pool`: entidades con buen retorno y limitación de escala;
- `measurement_gaps`: tracking o atribución que impide decidir.

## 2. Geo audit

Objetivo: separar mercados valiosos, mercados con desperdicio y errores de configuración.

Revisar:

- configuración de ubicación (`presence` vs. interés);
- geos objetivo;
- ubicación real o user-location cuando esté disponible;
- geos con gasto significativo y cero conversiones;
- geos con CPA bajo y bajo impression share;
- geos fuera del mercado objetivo.

Lectura:

- Geo con gasto alto y cero conversiones: hipótesis de desperdicio.
- Geo con CPA bajo y bajo impression share: hipótesis de escala.
- Geo fuera de target: revisar settings antes de excluir por rendimiento.
- Geo con CPA alto: validar muestra, LTV, offline conversions y objetivo estratégico.

Acciones posibles:

- excluir geo;
- agregar geo negativa;
- ajustar bid modifier si la estrategia lo permite;
- separar campaña por geo cuando necesita presupuesto, puja o mensaje propio;
- mantener observación si la muestra es baja.

## 3. Search terms audit

Objetivo: convertir consultas reales en negativas, keywords nuevas o decisiones de estructura.

Proceso:

1. Revisar 30-60 días por costo descendente.
2. Marcar términos irrelevantes, informacionales o fuera de oferta.
3. Promover términos con conversión o intención clara a keywords explícitas.
4. Detectar consultas que entran por el ad group incorrecto.
5. Separar clusters cuando una familia de consultas necesita anuncio o landing propia.

Señales:

- Search term caro sin conversión y sin fit: candidato a negativa.
- Search term con conversión y mensaje no dedicado: candidato a keyword/ad group.
- Muchos términos informacionales entrando por broad: contaminación de intención.
- La misma query entrando por varias estructuras: canibalización interna.

## 4. N-gram analysis

Usa n-grams cuando el volumen de search terms supera la revisión manual.

El objetivo es agrupar patrones de 1-3 palabras y sumar costo, clicks, conversiones y CPA.

Usos:

- encontrar palabras que queman presupuesto;
- encontrar modificadores con conversión;
- detectar oportunidades de ad group;
- descubrir demanda de producto u oferta no cubierta.

Regla de implementación:

- Si existe tool determinista de n-grams, usarla.
- Si no existe, pedir export o usar una hoja/BI validada.
- No improvisar agregación manual en prompts largos para cuentas grandes.

## 5. Filtraciones estructurales

Revisar en este orden:

1. Search terms contaminados.
2. Geos fuera de mercado o con mala economía.
3. Redes activadas sin intención (`content`, partners u otras superficies no deseadas).
4. Devices con CPA/CVR fuera de rango.
5. Smart Bidding con poca data o tracking inestable.
6. Broad match sin negativas, landing fit ni estructura semántica.
7. Horarios con gasto consistente y bajo retorno.

Cada filtración requiere:

- impacto estimado;
- confianza;
- cambio mínimo reversible;
- riesgo de falso positivo;
- forma de monitorear después.

## 6. Oportunidades de escala

Buscar:

- geos con CPA bajo y bajo impression share;
- ad groups con CVR sano y limitación de presupuesto;
- search terms convertidores sin cobertura explícita;
- keywords con buen valor y anuncios genéricos;
- clusters vecinos con intención comercial;
- audiencias observadas que justifican segmentación o ajuste.

Escalar con cuidado:

- aumentar presupuesto donde ya existe fit;
- separar campaña cuando el mercado necesita control propio;
- abrir phrase o broad solo con negativas limpias y tracking confiable;
- crear ad group dedicado cuando el mensaje o landing cambia.

## 7. Arquitectura resultante

Usar STAGs: ad groups por tema/intención dominante.

Principios:

- agrupar keywords que comparten intención, promesa y landing;
- evitar SKAGs mecánicos;
- consolidar cuando la estructura fragmenta aprendizaje;
- separar cuando cambian presupuesto, geo, objetivo, puja, mensaje o landing;
- usar broad con contexto semántico, negativas y señales de conversión.

## Cadencia recomendada

- Semanal: CPA, CVR, gasto, search terms de alto costo y fatiga de anuncios.
- Mensual: geos, devices, horarios, search terms y oportunidades de escala.
- Trimestral: auditoría completa de estructura, bidding, medición, geos, keywords y landings.

## Formato de salida

Usa este formato para hallazgos:

```text
Señal:
Evidencia:
Chequeos de falso positivo:
Clasificación:
Confianza:
Acción recomendada:
Vía operativa:
Estado esperado:
```

`Vía operativa` debe ser Irrumpe MCP. Si el segmento necesario no está expuesto por MCP, pedir un
export del usuario o marcar el hallazgo como `blocked`.
