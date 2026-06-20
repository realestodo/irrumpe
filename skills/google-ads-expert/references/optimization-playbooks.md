# Playbooks de optimizacion

Cada optimizacion parte de un sintoma observable. No optimices por reflejo.

Para auditorias de desperdicio, geos, search terms u oportunidades, cargar tambien
`references/waste-and-opportunity-audit.md`.

## Antes de actuar

Clasifica la señal:

- `confirmed_finding`
- `hypothesis`
- `false_positive_risk`
- `measurement_issue`
- `not_actionable`

Una optimizacion necesita evidencia, explicacion alternativa revisada, confianza y accion minima.

## 1. CTR bajo

Sintoma:

- impresiones suficientes
- CTR por debajo del resto de la cuenta o del cluster comparable

Causas frecuentes:

- keyword demasiado amplia
- anuncio generico
- mal fit con la landing
- mezcla de intenciones en el mismo ad group

Acciones:

- revisar search terms
- separar intentos mezclados
- reescribir RSA con mensaje mas especifico
- eliminar keywords que no representan la oferta real

## 2. CPC alto y conversion aceptable

Sintoma:

- el trafico convierte, pero el costo limita escala

Causas frecuentes:

- auction pressure
- quality signals debiles
- broad sin suficientes negativas
- geo o horario muy caros para el ticket disponible

Acciones:

- revisar `metrics.search_impression_share`, `metrics.search_budget_lost_impression_share`,
  `metrics.search_rank_lost_impression_share`
- mejorar ad relevance y landing fit
- mover terminos caros a estructuras mas controladas
- recortar geo, horario o dispositivo si el valor no sostiene el CPC

## 3. CTR bueno y CVR baja

Sintoma:

- el anuncio atrae clicks, pero no cierra conversion

Causas frecuentes:

- promesa del anuncio no coincide con landing
- keyword informacional en estructura transaccional
- friccion en la page
- conversion tracking erratica

Acciones:

- auditar landing page
- mover la keyword a otro cluster o excluirla
- ajustar el mensaje para filtrar mejor
- validar conversion tracking antes de tocar bidding

## 4. Impresion share perdida por presupuesto

Sintoma:

- `metrics.search_budget_lost_impression_share` alto

Causas frecuentes:

- presupuesto repartido en demasiadas campanas
- campana correcta, pero con presupuesto insuficiente
- consultas de bajo valor consumiendo caja

Acciones:

- reasignar presupuesto a campanas o ad groups de mayor valor
- excluir desperdicio via negativas
- separar brand de non-brand si aun compiten por la misma bolsa

## 5. Impresion share perdida por ranking

Sintoma:

- `metrics.search_rank_lost_impression_share` alto

Causas frecuentes:

- anuncio debil
- landing debil
- puja insuficiente
- cluster mal armado

Acciones:

- reescribir assets RSA
- mejorar fit keyword -> ad -> landing
- revisar bidding strategy
- pausar keywords marginales que bajan la calidad media

## 6. Search terms contaminados

Sintoma:

- terminos irrelevantes generan clicks
- terminos valiosos caen en el ad group incorrecto

Acciones:

- agregar negativas
- promover search terms valiosos a keywords dedicadas
- separar clusters demasiado anchos
- revisar n-grams si el volumen supera revision manual
- validar que el termino no sea asistente, exploratorio o parte de un ciclo largo antes de excluir

## 7. Muchas keywords sin impresiones

Sintoma:

- inventario inflado y sin delivery real

Causas frecuentes:

- sobre-segmentacion
- puja inadecuada
- bajo volumen real
- exceso de exact match en fases tempranas

Acciones:

- consolidar keywords equivalentes
- abrir phrase match donde tenga sentido
- mover a backlog lo que aun no tiene demanda operable

## 8. Conversiones existen pero no escalan

Sintoma:

- hay señales de exito, pero el volumen no crece

Acciones:

- abrir expansion controlada con phrase o broad
- duplicar aprendizajes en clusters vecinos
- separar campanas por presupuesto o bidding cuando el mix actual asfixia escala

## 9. Duplicacion y canibalizacion interna

Sintoma:

- la misma consulta entra por multiples estructuras

Acciones:

- definir ownership de query por campana/ad group
- usar negativas cruzadas cuando haga falta
- simplificar estructura

## 10. Geographic waste

Sintoma:

- geo con gasto relevante y bajo retorno
- clicks desde ubicaciones fuera del mercado objetivo
- CPA muy superior al promedio comparable

Causas frecuentes:

- targeting por interes en vez de presencia
- geos demasiado amplias
- expansion accidental de ubicacion
- conversion offline no importada
- geo estrategica con LTV superior

Acciones:

- revisar configuracion de ubicacion y ubicacion real del usuario cuando este disponible
- excluir o negativizar geos fuera de mercado
- separar campana si la geo necesita presupuesto, puja o mensaje propio
- mantener como hipotesis si la muestra o tracking no alcanzan

## 11. Network leakage

Sintoma:

- gasto en redes que no corresponden a Search puro
- CTR/CVR fuera de patron frente a Google Search

Acciones:

- revisar settings de red en Irrumpe MCP
- apagar superficies no deseadas con `ads_campaign_networks_set` si existe aprobacion
- documentar si el gasto responde a una prueba aprobada

## 12. Device waste

Sintoma:

- device con CPA/CVR fuera de rango y volumen suficiente

Acciones:

- validar tracking especifico de mobile, llamadas, WhatsApp u offline
- aplicar bid modifier solo si la estrategia de puja lo admite
- ajustar landing o mensaje si el device revela friccion

## 13. Smart Bidding sin senales suficientes

Sintoma:

- estrategia automatica con conversiones escasas, erraticas o tracking dudoso

Acciones:

- validar volumen de conversiones y calidad del dato
- bajar confianza de cualquier conclusion si el algoritmo esta en learning
- ajustar bidding por MCP solo con aprobacion y evidencia suficiente

## Orden recomendado de diagnostico

1. tracking y conversion
2. money trail
3. search terms
4. geos
5. redes, devices y horarios
6. estructura
7. anuncio
8. landing page
9. bidding
10. presupuesto

## Regla final

No optimizar solo para bajar costos. Optimizar para mejorar la relacion entre intencion, mensaje,
conversion y escala sostenible.
