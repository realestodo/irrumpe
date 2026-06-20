# Arquitectura de Search campaigns

Esta referencia define como convertir keywords y objetivos en una estructura operable.

## Principios

- La estructura debe seguir el negocio, no una obsesion por granularidad.
- Usar STAGs: ad groups por tema e intencion dominante.
- Evitar SKAGs mecanicos salvo casos sensibles donde el control exacto tenga justificacion.
- Cada capa debe responder a una pregunta distinta:
  - campana = control de presupuesto, geo, idioma, puja, riesgo
  - ad group = intencion y mensaje
  - keyword = cobertura puntual
- La landing page manda. Si no existe una page adecuada, no fuerces estructura.

## Separaciones recomendadas

Separar campanas cuando cambie una de estas variables:

- brand vs non-brand
- geo
- idioma
- objetivo de negocio
- presupuesto aislado
- estrategia de bidding

Separar ad groups cuando cambie:

- el angulo del mensaje
- la promesa principal
- la familia semantica
- la landing page

## Estructura minima sana

Para una cuenta nueva o desordenada, empezar con:

- 1 campana brand
- 1-3 campanas non-brand segun linea de negocio
- ad groups por cluster de intencion
- keywords exact/phrase como base
- broad solo cuando ya exista control de negativas y medicion estable

## Consolidacion moderna

Consolidar cuando:

- la cuenta reparte pocas conversiones en demasiadas campanas;
- los ad groups tienen diferencias artificiales;
- Smart Bidding no acumula senales suficientes;
- el reporting exige demasiado trabajo para explicar lo basico.

Separar cuando:

- cambia presupuesto, geo, idioma, objetivo o estrategia de bidding;
- cambia la promesa dominante;
- cambia la landing;
- existe un mercado ganador que necesita impression share propio;
- una familia de search terms demuestra valor y merece mensaje dedicado.

Broad match puede funcionar dentro de STAGs cuando:

- la frase entrega suficiente contexto semantico;
- hay negativas limpias;
- existe conversion tracking confiable;
- la landing refuerza el mismo tema;
- el presupuesto tolera aprendizaje.

## Nombres

Usar nombres que permitan leer la estructura sin abrir la UI.

Patron recomendado:

- Campana: `[network] | [brand/nonbrand] | [geo] | [objetivo] | [oferta]`
- Ad group: `[tema] | [mensaje] | [landing]`

## Anuncios RSA

Crear RSA que reflejen la intencion del ad group, no slogans generales.

Para construir los assets de texto, consulta `references/ad-messaging.md`. Si la vertical cambia
mucho el lenguaje de compra, suma `references/ad-messaging-by-vertical.md`.

Reglas:

- cargar multiples headlines y descriptions distintas, no variaciones cosmeticas del mismo claim
- cubrir al menos: problema, solucion, prueba, CTA, marca cuando aplique
- pinnear solo cuando exista una razon dura de compliance o de mensaje critico
- alinear headline principal con el cluster y con la landing page

Google sirve tres headlines y dos descriptions por impresion. La combinacion ganadora emerge del pool de assets, asi que conviene diversidad real.

## Landing page fit

Antes de lanzar una keyword, confirmar:

- la promesa existe en la page
- la oferta es visible sin friccion excesiva
- la conversion principal esta clara
- el query no promete algo que la page no entrega

El desajuste query -> anuncio -> landing destruye CTR, CVR y quality signals.

## Bidding

Usar la estrategia de puja segun madurez de datos:

- `Maximize Clicks`: discovery controlado o cuentas sin suficiente data de conversion
- `Maximize Conversions`: cuando la conversion tracking ya es confiable y el objetivo es volumen
- `Target CPA`: cuando el negocio tiene un CPA objetivo real
- `Target ROAS`: cuando existe valor de conversion confiable y suficiente volumen

No recomendar Smart Bidding si:

- la conversion tracking esta rota
- el volumen de conversion es demasiado bajo para aprender
- el usuario no acepta el rango de exploracion necesario

## Presupuesto

El presupuesto inicial debe comprar aprendizaje y presencia rentable.

Señales de mala asignacion:

- demasiadas campanas con presupuesto simbolico
- brand absorbiendo volumen que deberia medirse separado
- non-brand compartiendo presupuesto con clusters de valor muy distinto

## Checklist pre-lanzamiento

- conversion principal validada
- naming consistente
- brand separado de non-brand
- mensajes por ad group alineados a landing page
- negativas iniciales cargadas
- ubicaciones e idiomas correctos
- Search Network confirmado segun estrategia
- anuncios y keywords en estado esperado

## Cuando simplificar

Simplificar estructura cuando veas:

- multiples campanas peleando por el mismo inventario
- ad groups con diferencias artificiales
- bajo volumen repartido en demasiadas cajas
- reporting imposible de leer

La mejor arquitectura es la que mantiene control sin romper aprendizaje.
