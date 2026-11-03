# Instagram Reel — "BRASAS" · Cronógrafo Ónix Rosé

**Formato:** Reel 9:16 · 1080×1920 (upscale a 4K) · 24 fps · **15 s**
**Herramienta principal:** Kling (image-to-video, start/end frame) · Montaje: CapCut / Premiere / DaVinci
**Estado:** prompts y guion listos. **Ningún vídeo generado todavía.**

---

## Concepto

El oro rosa nace del fuego. Rodamos el Ónix Rosé en un mundo de **madera carbonizada con vetas de cobre, piedras negras y brasas apagándose**, la misma estética de tu imagen de referencia, pero en movimiento.

- **Gancho (primer segundo):** un brillo naranja late sobre una superficie curva en la oscuridad. No se sabe qué es. Al abrirse el plano descubrimos que es el reflejo de una brasa sobre la caja de oro rosa.
- **Cierre:** las brasas se apagan, queda solo el reloj, y aparece **1 / 1**. Una pieza, un fuego, una vez.

**Por qué funciona en Instagram:** misterio en el primer segundo (retiene), contraste negro y naranja que destaca en el feed, nada de texto hasta el final y un loop natural (empieza y termina en oscuridad con brasa).

---

## Preparación: frames iniciales reales (clave para la fidelidad)

Monta un bodegón real de 1 m² en casa. Sale barato y es lo que hace que el reloj salga perfecto:

- Base: tablero negro mate o pizarra.
- **Carbón vegetal en trozos grandes** (madera carbonizada real) y **piedras negras de río** (tienda de jardinería).
- 2–3 ramitas de helecho/hojas pintadas con spray **oro rosa / cobre**.
- Luz: una lámpara con bombilla cálida 2700–3200 K a un lado, muy baja + una cartulina negra al otro lado.
- Reloj con **agujas a 10:10** y el segundero parado en las 12 (para la foto).
- Cámara del móvil en modo PRO/RAW, 4K, ISO bajo, sobre trípode.

**Fotos a hacer (serán los FRAME INICIAL / FINAL):**
| Foto | Encuadre |
|---|---|
| F1 | Macro extremo del flanco de la caja entre corona y pulsadores, casi a oscuras |
| F2 | 3/4 del reloj completo apoyado en el carbón (corona hacia cámara) |
| F3 | Macro frontal de la esfera (las tres subesferas en cuadro) |
| F4 | Lateral bajo, reloj sobre carbón con piedras delante desenfocadas |
| F5 | Igual que F2 pero con la luz atenuada al 30 % |

> Si no puedes hacer el bodegón: fotografía el reloj sobre fondo negro con la misma luz cálida lateral y pide el entorno en el prompt. Es menos fiable; revisa cada plano con lupa.

---

## Guion plano a plano

| # | Tiempo | Plano | Movimiento | Sonido | Texto |
|---|---|---|---|---|---|
| 1 | 0:00–0:02 | **HOOK.** Oscuridad total; un reflejo naranja late sobre una curva metálica | Estático, push-in casi imperceptible | Crepitar de brasa, muy cerca | — |
| 2 | 0:02–0:05 | Se abre: corona y pulsadores de oro rosa, brasas desenfocadas detrás | Dolly-out lento | Entra un drone grave de violonchelo | — |
| 3 | 0:05–0:08 | Macro de la esfera negra, subesferas oro rosa; una franja de luz cálida las barre | Estático | Tic del segundero en primer plano | — |
| 4 | 0:08–0:11 | Lateral bajo: el reloj sobre madera carbonizada con vetas cobre, chispas flotando muy lejos | Slider lateral lento izquierda → derecha | Crepitar + chelo | — |
| 5 | 0:11–0:13 | Las brasas se apagan; solo queda el contorno del reloj iluminado | Estático, la luz baja | El chelo se corta, silencio | — |
| 6 | 0:13–0:15 | Negro | — | Una nota grave de piano | **1 / 1** → *ÓNIX ROSÉ* → logo SERMAK |

**Música:** violonchelo grave en sostenido + crepitar de fuego + tic del segundero. Sin percusión. Busca en la biblioteca de Instagram/CapCut "dark cello ambient" o "cinematic drone"; la nota final de piano la añades tú.

**Etalonaje:** negros profundos (sin lavar), naranjas de brasa contenidos, el oro rosa se mantiene rosado y nunca amarillo. Grano de película fino al 10 %.

---

## Prompts (Kling, en inglés)

`[NEG]` = bloque negativo de `BIBLIA_CREATIVA.md` §3 + `no flames touching the watch, no fire on the watch, no smoke covering the dial`

**Plano 1 — Hook** · FRAME INICIAL: F1
```
Extreme macro in near-total darkness: the curved polished side of a rose-gold watch case between the crown and pushers.
A warm orange ember glow slowly pulses and reflects across the curved metal, breathing like a dying fire.
Camera: locked-off with an almost imperceptible push-in. Lens: 100mm macro, f/4.
Lighting: only the flickering orange ember light from below-left, everything else pure black.
Style: high-end watch commercial, photographic realism, real metal reflections, fine film grain. [NEG]
```

**Plano 2 — Revelación** · FRAME INICIAL: F1 · FRAME FINAL: F2
```
Slow pull-back revealing a rose-gold chronograph watch with black dial, rose-gold subdials, black ceramic bezel and black rubber strap, resting on charred wood with copper-veined cracks.
Out-of-focus glowing embers in the background. Warm ember light reflects along the polished case, crown and pushers.
Camera: slow smooth dolly-out. Lens: 85mm, f/2.8, shallow depth of field.
Lighting: warm low-key side light 3000K, black negative fill on the opposite side.
The watch stays perfectly still and identical to the reference images. [NEG]
```

**Plano 3 — Esfera** · FRAME INICIAL: F3
```
Macro of the black dial of a rose-gold chronograph watch with three rose-gold subdials and rose-gold applied indices.
A narrow strip of warm light slowly sweeps from left to right across the sapphire crystal, revealing the sunray texture of the subdials. The central seconds hand ticks naturally.
Camera: static. Lens: 100mm macro, f/5.6.
Lighting: strip softbox, warm 3200K, deep shadows.
All dial details, text and indices remain exactly as in the reference image. [NEG]
```

**Plano 4 — Mundo** · FRAME INICIAL: F4
```
Low side angle of a rose-gold chronograph watch with black rubber strap lying on a dark charred log with glowing copper veins, smooth black river stones in the foreground out of focus, small rose-gold leaves nearby.
Tiny sparks float slowly far in the background.
Camera: slow lateral slider move from left to right, parallax between foreground stones and the watch. Lens: 50mm, f/2.
Lighting: warm ember light from behind, soft side key light, deep black shadows.
Style: cinematic luxury watch campaign, photographic realism. [NEG]
```

**Plano 5 — Se apaga** · FRAME INICIAL: F2 · FRAME FINAL: F5
```
The background embers slowly fade out and the scene darkens until only the polished rim of the rose-gold watch case and its subdials catch a last thin line of warm light.
Camera: static. Lens: 85mm, f/2.8.
Lighting: gradually dimming warm light, ending in near-black.
The watch does not move or change. [NEG]
```

**Plano 6:** no se genera. Negro puro en el editor + textos.

**Consejos de generación**
- Genera **3–4 variantes** de cada plano y quédate con la más fiel; descarta cualquiera en la que cambien los números del bisel, las subesferas o el logo.
- Usa la duración mínima (5 s) y recorta en montaje.
- Si el plano 3 deforma la esfera: usa la foto F3 con un "Ken Burns" (zoom 3 % en el editor) + una capa de luz animada en post. Nadie notará la diferencia.

---

## Textos en pantalla (montaje)

- Tipografía: serif en mayúsculas espaciadas (Cormorant Garamond, Cinzel o Trajan), blanco roto `#F2EEE9`.
- 0:13 → **1 / 1** (centro, grande, fade-in de 8 frames)
- 0:14 → **ÓNIX ROSÉ** (pequeño, debajo)
- 0:14,5 → logo SERMAK con la corona (archivo vectorial del logo, nunca generado)
- Deja libre el **20 % inferior y el 15 % superior** (zona de interfaz de Instagram).

## Portada del Reel

Fotograma del plano 3 (esfera con la luz cálida), texto centrado: **ÓNIX ROSÉ** / *1 OF 1*. Recorte 4:5 centrado en el reloj para que se vea bien en la cuadrícula.

---

## Copy de Instagram

**Opción 1 (recomendada)**
> Hay fuegos que solo se encienden una vez.
>
> Cronógrafo Ónix Rosé. Esfera negra, oro rosa, una sola pieza.
> Cuando se vende, no vuelve.
>
> Estuche Sermak + certificado 1 of 1.
> Escríbenos por WhatsApp · enlace en la bio.
>
> *Time to be yourself.*

**Opción 2 (más corta)**
> Ónix Rosé. 1 de 1.
> Cuando tenga dueño, no habrá otro.
> 🔗 Bio

**Hashtags** (pocos y propios, sin marcas ajenas):
`#Sermak #Sermak1of1 #TimeToBeYourself #RelojUnico #OroRosa #Cronografo #RelojesHombre #PiezaUnica #WatchOfTheDay #Relojeria`

**Publicación:** martes a jueves, entre 20:00 y 21:30 (hora de España). En las primeras 2 horas, responde a todos los comentarios y comparte el Reel en Historias con la encuesta "¿Lo llevarías? 🔥 / 🖤".

---

## Checklist
- [ ] Bodegón montado y fotos F1–F5 hechas (agujas 10:10)
- [ ] 3–4 variantes por plano generadas
- [ ] Revisión contra foto real: bisel, subesferas, logo, corona, pulsadores, correa
- [ ] Logo y textos en post
- [ ] Etalonaje: negros profundos, oro rosa sin amarillear
- [ ] Export 1080×1920, 24 fps, H.264 alta calidad (o 4K tras upscale)
- [ ] Portada 4:5 + copy + hashtags
