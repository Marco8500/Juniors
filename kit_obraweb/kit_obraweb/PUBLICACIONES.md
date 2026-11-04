# Cómo trabajamos las publicaciones

## ESTRATEGIA DE RETENCIÓN (prioridad absoluta)
Orden de prioridades: **RETENCIÓN → VISUALIZACIONES → SEGUIDORES → POTENCIALES CLIENTES.**
Nada de vídeos corporativos ni anuncios. Cada vídeo planta una pregunta en la cabeza del espectador y **retrasa la respuesta**.

### Cadena de curiosidad
Cada frase abre una puerta nueva **antes** de cerrar la anterior:
gancho → primera revelación ("no es por X") → nuevo interrogante → desarrollo corto → nuevo estímulo ("pero hay algo más…") → revelación → recompensa.
Nunca se revela todo al principio. Ninguna escena es de relleno: o aporta información o despierta curiosidad.

### Recompensa final (real)
Se anuncia **justo después del gancho** («Al final de este vídeo te daré un regalo», plano `giftpromise`) y se entrega en el cierre con **pasos numerados** (plano `steps`: 1 sígueme · 2 comenta DEMO) y cómo llega (plano `delivery`: por mensaje, gratis y sin compromiso). CTA base:
**«Si has llegado hasta aquí, sígueme y comenta DEMO. Te preparo gratis una demo de cómo quedaría la web de tu negocio, sin compromiso.»**
Otras recompensas válidas: ideas para mejorar su presencia digital, ejemplos de cómo quedaría su negocio, consejos de automatización.
⚠️ La recompensa se cumple SIEMPRE: cada «DEMO» en comentarios recibe su demo. No prometer nada que no se vaya a entregar.

### Formatos que se alternan (no repetir el mismo dos veces seguidas)
1. Storytelling con revelación final · 2. Errores que hacen perder clientes · 3. Antes y después (con / sin web)
4. Situaciones hipotéticas de dueños de negocio · 5. Listas con la última recomendación más potente
6. Secretos que los empresarios desconocen · 7. Problema cotidiano → solución digital · 8. Afirmación polémica o inesperada

### Edición y narración
Primer segundo que atrapa (explosión) · sin saludos ni presentaciones · frases cortas · estímulo visual nuevo cada 2-3 s ·
preguntas, revelaciones y giros · subtítulos dinámicos con la palabra clave resaltada · sin silencios · duración natural.

### Público y servicios
Dueños de negocios, autónomos y emprendedores (no frikis de la IA). Servicios de OBRAWEB: diseño web, chatbots con IA,
automatizaciones, sistemas de captación de clientes y reservas. La IA se cuenta por lo que resuelve ("te contestan aunque estés cerrado"), no por la tecnología.

### Entregable de cada reel (lo genera `crear.sh` desde el guion)
`videos/XXX.mp4` + `_portada.jpg` + `.txt` (Instagram/TikTok) + `_ficha.md` con: 1 título/concepto · 2 gancho · 3 guion por escenas ·
4 voz exacta · 5 texto en pantalla · 6 qué se ve · 7 técnicas de retención · 8 CTA · 9 descripción · 10 hashtags.
Guion en formato `{"meta": {...}, "escenas": [{"kind", "text", "sub", "screen", "visual", "tecnica", ...}]}` (ver `guiones/011_*.json`).

## Orden diaria
El usuario dice **"crea publicación nueva"** (y de qué marca: ObraWeb o Entra).
Yo decido el formato y digo cuál toca hoy: **reel** (la mayoría), **carrusel** o **imagen**. Varío los temas y los formatos para no repetir.

## Reels (formato principal)

### 3 REGLAS OBLIGATORIAS en todos los reels
1. **Gancho visual brutal en el primer segundo**: algo se rompe o explota (pantalla que se hace añicos, explosión con destello, sacudida y sonido de golpe) dentro del primer segundo. El fotograma 0 ya muestra el objeto que va a romperse.
2. **Todo lo que se dice se ve, de forma LITERAL y con detalle**: cada frase lleva su imagen y cada palabra importante aparece justo cuando se dice.
   Ejemplo de referencia: «una peluquería siempre llena» = local iluminado, cartel ABIERTO y clientes comprando con bolsas; «la otra, vacía» = local a oscuras, el dueño solo detrás del mostrador, telarañas y polvo. «Mismas tijeras» = se ven unas tijeras. Nada de iconos genéricos cuando la frase describe algo concreto.
   Antes: Si la voz dice "3 segundos", sale un cronómetro; si dice "móvil", sale un móvil; si dice "se van", se ven clientes yéndose. Cada frase es su propio plano, sincronizado con la voz.
3. **Bucles abiertos para la retención**: en cuanto se cierra una idea se abre la siguiente ("pero el segundo es peor…", "y el tercero es el que más dinero te cuesta"). Nunca hay un momento en que el espectador sienta que ya lo ha visto todo, hasta el final.

### Además
- **Gancho en el primer segundo**: la primera frase tiene que parar el dedo. El contenido ya se ve en el fotograma 0, con un texto grande que repite el gancho.
- **Voz oficial**: piper es_ES-davefx-medium (voz 1), natural y fluida, length_scale 0.85, pausas mínimas (`voz.sh`).
- Duración de 15 a 30 s. Frases cortas, ritmo alto, un cambio visual cada 2 o 3 s para retener.
- Termina con una llamada a la acción clara.
- Entrega: video MP4 + `_portada.jpg` + `.txt` con el texto para Instagram y para TikTok.

## Carrusel
- 5 a 8 diapositivas **cuadradas 1:1 (1080x1080), sin puntitos de progreso**. La 1ª es el gancho, la última la llamada a la acción ("Guárdalo", "Escríbenos").
- Entrega: las imágenes numeradas + `.txt` con el texto.

## Imagen
- Una imagen **1:1 (1080x1080)** para el feed o 1080x1920 para historia. Entrega: la imagen + `.txt`.

## Ganchos tipo (ejemplos)
- Entra: "Así saqué un 14 en la EBAU…" → **solo si es un testimonio real y autorizado**. Si no, lo planteo como posibilidad o POV:
  "POV: estudias con tus propios apuntes y la IA te pone el examen", "Cómo sacar un 14 en la EBAU estudiando menos horas", "Si tienes la EBAU en junio, mira esto".
- ObraWeb: "Tu competencia te está robando clientes ahora mismo", "Esto es lo que ve un cliente cuando te busca y no tienes web".

## Reglas fijas
- No inventar precios, notas, cifras de resultados ni testimonios. No decir "la más barata" ni "la mejor".
- ObraWeb: paleta azul marino, blanco y naranja (ver MARCA.md).
- **ObraWeb: NUNCA decir ni mostrar el precio** (ni en voz, ni en pantalla, ni en portada, ni en el texto). La llamada a la acción es **seguir y comentar DEMO** (antes era «WEB» por mensaje).
