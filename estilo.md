# estilo.md — Guía de edición

Salida siempre: **1080x1920, 30 fps**, H.264, AAC 48 kHz.
Las referencias llegan a 576x1032 / 576x1024 (compresión de WhatsApp): el detalle fino (grano, nitidez) no es medible.
Se ignoran en el análisis: la marca de agua de TikTok y el **outro de TikTok** (los últimos ~3 s de ambos vídeos), por indicación del usuario.

Hay **dos formatos distintos**. Antes de editar, elegir uno.

---

## FORMATO A — "Unboxing POV" (referencia-A.mp4, 31,1 s útiles)

### Ritmo de cortes
- 9 planos en 31,1 s → **duración media 3,46 s**, mediana 1,67 s.
- Cortes en: 0,70 · 2,10 · 2,93 · 7,23 · 8,23 · 13,73 · 21,27 · 22,93 s.
- Duraciones: 0,70 / 1,40 / 0,83 / 4,30 / 1,00 / 5,50 / 7,53 / 1,67 / 8,20 s.
- Patrón: **planos cortos (0,7–1,7 s) para saltar pasos del unboxing** + **planos largos (4–8 s) en los momentos clave** (abrir caja interior, sacar reloj, ponérselo).
- Música a **72 BPM** (1 beat = 0,83 s). 3 de 6 cortes caen a ≤0,15 s de un golpe de la música; el resto no. [SUPOSICIÓN] El corte sigue a la acción, no al beat.
- Todos son **cortes secos (jump cuts)** con la misma cámara y el mismo encuadre. Sin transiciones.

### Plano / cámara
- Cámara cenital fija, en POV, a ~40–50 cm de la mesa [SUPOSICIÓN]. Fondo: mesa gris oscuro mate.
- **Sin zoom digital.** El acercamiento lo hace la mano, que lleva el producto a la lente (planos de 13,7 a 21 s: el reloj ocupa el 80–100 % del ancho).
- Desenfoque natural cuando el producto se acerca demasiado; no se corrige.
- Orden narrativo: caja exterior → caja interior → documentación/tarjetas → reloj en el cojín → detalle (cierre, esfera) → reloj puesto en la muñeca (plano final de 8,2 s, estático).

### Subtítulos / textos en pantalla
- **Ninguno.** Ni subtítulos, ni títulos, ni rótulos de producto.

### B-roll
- No hay b-roll: todo es un único setup continuo.

### Color
- Luminancia media (YAVG) **65–97 sobre 255** (≈26–38 %), con clave baja y fondo oscuro.
- Saturación media (SATAVG) **2–20**, casi desaturado. El único color es el **verde de la caja (~#1F3B2E)** [SUPOSICIÓN: hex estimado] más el dorado del logo.
- Tono neutro-frío. Sin LUT evidente; parece luz suave difusa cenital.

### Sonido
- **Solo música, sin voz en off ni SFX.** Canción con voz (balada lenta, 72 BPM).
- Volumen integrado **−20 LUFS**. La música empieza en 0,0 s sin fade-in. [SUPOSICIÓN] No hay ducking porque no hay voz.

---

## FORMATO B — "Cinematic producto" (referencia-B.mp4, 12,27 s útiles)

### Ritmo de cortes
- **4 planos de exactamente 92 frames (3,067 s) cada uno.** Cortes en 3,067 · 6,133 · 9,200 s.
- Rejilla fija, sin relación con la música (es un ambient sin golpes; solo se detectan 2 onsets antes de 12 s).
- **Cortes secos.** Sin transiciones ni fundidos.

### Plano / cámara
Cada plano tiene **un único movimiento lento y continuo** que dura el plano entero:
1. 0–3,07 s: macro de la esfera a 3/4 sobre negro, con **órbita/push-in lento** [SUPOSICIÓN ≈ +5 % de escala en 3 s].
2. 3,07–6,13 s: macro extremo del texto "MONDAY" y la corona, con **deslizamiento lateral + pull-out** hasta mostrar la esfera completa y cambio de foco.
3. 6,13–9,20 s: perfil lateral del reloj sobre degradado gris, con un **push-in frontal lento**.
4. 9,20–12,27 s: plano de estilo de vida (muñeca, traje, puño blanco y fondo de interior desenfocado), con un **foco que pasa de desenfocado a nítido** en ~1 s y la mano ajustando el puño.
- Estructura: detalle → detalle extremo → silueta → producto en uso.
- Si se imita con material real, aplicar un **zoom digital continuo de 100 % → 106 % por plano**, con easing lineal o ease-in-out. [SUPOSICIÓN]

### Subtítulos / textos en pantalla
- **Ninguno.**

### B-roll
- Todo es b-roll de producto (render/estudio y lifestyle). Sin persona hablando.

### Color
- Fondos **negro (#000) → gris grafito degradado (#2A2C30–#5A5D62)** [SUPOSICIÓN: hex estimado].
- YAVG **38–136**: alto contraste, brillos especulares del metal.
- Saturación muy baja (2–10). Único acento de color: el **azul hielo de la esfera (~#A9D8E6)** [SUPOSICIÓN].
- Tono frío. Plano lifestyle: interior cálido-oscuro desenfocado, con la piel neutra.

### Sonido
- **Solo música instrumental, ambient/cinemático, sin percusión marcada.** Sin voz.
- Volumen integrado **−12,9 LUFS** (bastante más fuerte que A).

---

## SUBTÍTULOS — propuesta para vídeos con voz [SUPOSICIÓN completa]
Ninguna referencia tiene subtítulos. Para mi-video.mp4 (con voz) uso esta propuesta, coherente con la estética de las referencias (sobria, oscura, de lujo). Pendiente de que el usuario la valide:
- Fuente: **Montserrat SemiBold 600** (o Inter SemiBold), mayúsculas/minúsculas normales.
- Tamaño: **72 px** en un lienzo de 1080x1920. Color #FFFFFF con sombra 0 4px 16px rgba(0,0,0,.6) y sin caja.
- Posición: centrado horizontal, **línea base al 68 % de la altura (y ≈ 1300 px)**, fuera de la zona de UI de TikTok/Reels.
- Bloques de **1–3 palabras** (máximo 18 caracteres), que cambian en cuanto termina la última palabra del bloque.
- Animación de entrada: **pop de escala 0,9 → 1,0 en 4 frames** con opacidad 0 → 1. Sin animación de salida.
- Palabra destacada (la que suena en cada momento): color de acento del formato (**A: dorado #C9A86A · B: azul hielo #A9D8E6**) y escala 1,05.

## EDICIÓN DE VOZ (para mi-video.mp4)
- Silencios **> 0,3 s se recortan** y se dejan 0,08 s de respiro antes y después de cada palabra.
- Música de fondo bajo la voz a **−18 dB respecto a la voz** [SUPOSICIÓN], y voz final normalizada a −14 LUFS.

---

## Correcciones del usuario (se añaden aquí y mandan sobre lo anterior)
- Ignorar el outro de TikTok de las referencias.
- **Formato por defecto: B ("Cinematic producto").** El usuario va a pasar vídeos detallados de producto del tipo del reloj plata con esfera azul. A queda solo como referencia secundaria.
