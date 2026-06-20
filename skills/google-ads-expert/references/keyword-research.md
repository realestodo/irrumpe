# Keyword research para Google Ads Search

Esta referencia convierte keywords semilla en expansion util para campañas reales.

Usala cuando necesites:

- expandir 3-5 seeds en clusters accionables;
- convertir demanda en estructura de Search campaigns;
- limpiar listas demasiado genericas o alejadas del lenguaje real del mercado;
- priorizar keywords para SEM y SEO sin perder realismo comercial.

Si la vertical cambia de forma importante el lenguaje de compra, carga tambien
`references/vertical-expansion-patterns.md`.

## Inputs minimos

- oferta exacta
- conversion principal o tipo de accion esperada
- geo
- idioma
- landing pages disponibles
- restricciones de marca, legales o de mercado
- seeds iniciales cuando existan

## Secuencia operativa

### 1. Fijar el scope antes de expandir

Bloquear primero:

- producto, servicio, especie o solucion exacta;
- geo explicita;
- idioma;
- tipo de intencion dominante;
- exclusiones obvias.

Si el usuario fijo un cultivo, especie, tecnologia o vertical, no abrir el scope hacia familias
mas amplias ni verticales vecinas. `Cerezo` no habilita `frutales` por defecto. `Antiheladas`
no habilita cualquier termino climatico.

### 2. Descomponer cada seed

Separar cada keyword en:

- nucleo tematico;
- calificador;
- intencion implicita.

Ejemplo:

- `control de heladas en cerezos`
  - nucleo: `heladas`
  - calificador: `control` + `cerezos`
  - intencion implicita: proteger, prevenir, resolver

Esta descomposicion evita listas planas y permite recombinaciones con criterio.

### 3. Elegir fuentes de investigacion

Usar fuentes segun madurez:

- sitio y categorias propias para seeds;
- Search Console para lenguaje organico ya probado;
- competidores para demanda y anuncios observables;
- Keyword Planner para magnitud relativa, CPC e ideas;
- Search Terms Report para expansion continua;
- n-grams cuando el volumen vuelve inmanejable la revision manual.

Advertencia:

- Semrush, SpyFu y herramientas similares muestran queries o estimaciones, no necesariamente las
  keywords exactas que el competidor targetea.
- Keyword Planner sirve para ordenar magnitud, no para prometer volumen exacto.
- Search Terms Report es la fuente mas accionable para negativas y nuevas keywords cuando la cuenta
  ya esta corriendo.

### 4. Expandir en cuatro capas

#### Capa A: variaciones morfologicas

Explorar:

- singular y plural;
- variantes naturales de forma;
- orden sintactico frecuente;
- sinonimos cercanos que no cambien la categoria de demanda.

Reglas:

- incluir singular y plural cuando ambos suenen naturales en el mercado;
- no forzar conjugaciones raras ni errores ortograficos como rutina;
- no generar ruido solo porque broad match podria capturarlo despues.

#### Capa B: matriz de modificadores

Cruzar el nucleo con modificadores de alto valor:

- audiencia: empresa, productor, pyme, pareja, familia, industrial;
- atributo: precio, premium, profesional, automatico, eficiente, urgente;
- ubicacion: pais, region, ciudad, zona;
- intencion: cotizar, comprar, contratar, reservar, comparar;
- etapa: nuevo, reparar, renovar, mantener, migrar.

Reglas:

- combinar 1-2 modificadores por vez como default;
- usar 3 modificadores solo si la frase sigue sonando natural;
- evitar strings largos y poco creibles sin evidencia de volumen.

#### Capa C: lenguaje del sector

Cruzar tres vocabularios:

- como lo nombra el cliente final;
- como lo nombra el experto tecnico;
- como lo nombra el comprador o decisor.

Esto destapa keywords mas cercanas a la realidad de compra y evita depender solo del termino
canonico del negocio.

#### Capa D: pain, feature y use case

Expandir desde:

- problema: el dolor que activa la busqueda;
- solucion: la categoria que lo resuelve;
- feature: el atributo tecnico que diferencia;
- caso de uso: el escenario donde se aplica.

Para paid search, esta capa suele ordenar mejor los futuros ad groups.

## Clasificacion de intencion

Etiquetar cada keyword en una de estas categorias:

- `Informational`
- `Navigational`
- `Commercial`
- `Transactional`

Para Google Ads Search, priorizar `Commercial` y `Transactional` como base del lanzamiento.
Mantener `Informational` solo cuando exista una razon clara de captura temprana o soporte SEO.

## Priorizacion operativa

Ordenar con esta lectura simple:

- `P1`: alta intencion + buen ajuste con la landing + propuesta clara
- `P2`: buena intencion, pero requiere test de mensaje, oferta o angulo
- `P3`: expansion controlada o exploratoria
- `P4`: investigar despues, no lanzar todavia

## Filtro de viabilidad

Antes de entregar, pasar cada keyword por este filtro:

1. Tiene probabilidad razonable de convertir para este negocio?
2. Existe o puede existir una landing page coherente para esa query?
3. Suena como algo que una persona real buscaria?
4. Mantiene una intencion clara y no mezcla objetivos incompatibles?

Descartar o degradar cuando ocurra cualquiera de estas condiciones:

- 5 o mas modificadores encadenados sin evidencia;
- mezcla de intencion informacional y transaccional en la misma frase;
- sinonimos redundantes sin cambio real de intencion;
- expansion a verticales, especies o mercados no pedidos;
- terminos tan especificos que parecen briefing interno y no busqueda real.

## Negativos sugeridos para SEM

Cuando el contexto sea de Google Ads Search, proponer negativos basales junto con la expansion.

Categorias base:

- empleo: `trabajo`, `empleo`, `vacante`, `sueldo`, `salario`
- educacion gratuita: `gratis`, `pdf`, `descargar`
- informacion pura: `que es`, `definicion`, `historia de`
- geos fuera del mercado objetivo
- competidores si no existe estrategia de conquista aprobada

Agregar negativos tacticos cuando veas:

- otras especies o categorias adyacentes;
- queries academicas o regulatorias sin valor comercial;
- terminos que disparan otra intencion distinta al cluster.

## Match types

- `EXACT`: control alto para brand, compra clara, terminos sensibles en costo y queries ya probadas
- `PHRASE`: default recomendado para descubrir variantes calificadas con control sano
- `BROAD`: solo con negativas limpias, conversion confiable y estrategia de puja coherente

No usar los tres match types por reflejo.

## Estructura recomendada de salida

### En quick mode

Entregar:

- 4-6 clusters maximo;
- keywords principales;
- keywords secundarias o long tails cuando agreguen valor;
- negativos sugeridos si el pedido es claramente de SEM o campañas.

### En research estructurado

Entregar:

- cluster;
- intencion dominante;
- prioridad;
- match type sugerido;
- lista de keywords;
- negativos del cluster;
- observaciones de riesgo si aplica.

## Principios anti-estrategia sinsentido

Rechazar activamente estos patrones:

1. keywords demasiado largas sin evidencia de demanda;
2. keywords que parecen titulo de documento interno y no query real;
3. listas infladas con sinonimos casi identicos sin diferencia util;
4. campañas de performance cargadas de TOFU sin justificacion;
5. expansion automatica a categorias cercanas por asociacion semantica debil.

## Entregables recomendados

- lista priorizada de keywords por cluster;
- negativas iniciales cuando el caso sea paid search;
- recomendacion de match type por cluster cuando el usuario la pida;
- backlog de expansion posterior, separado del lanzamiento inicial.
