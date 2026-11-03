# SERMAK 1OF1 — Biblia creativa para vídeo

> "Uno de uno. Y es el tuyo." · *Time to be yourself*

Documento base para que todas las producciones de SERMAK compartan el mismo lenguaje visual. Cada campaña nueva parte de aquí.

---

## 1. Posicionamiento en una frase

**SERMAK no vende relojes caros: vende relojes que solo existen una vez.**
El lujo de SERMAK no es el precio, es la **singularidad**. Por eso la comunicación nunca grita: muestra una pieza, la deja respirar y recuerda que *cuando se vende, no vuelve*.

### Pilares de mensaje
| Pilar | Qué transmite | Cómo se ve |
|---|---|---|
| **1 / 1** | Pieza única, irrepetible | Un único reloj en encuadre, espacio negativo, nunca dos piezas iguales juntas |
| **Ritual** | Estuche, certificado, preparación | Manos, papel, cajas que se cierran, gestos lentos |
| **Identidad** | *Time to be yourself* | La persona no posa: vive. El reloj acompaña, no presume |
| **Escasez honesta** | "Cuando se vende, no vuelve" | Huecos vacíos en el estuche, piezas "entregadas" |

### Lo que SERMAK **no** es
- Ni ostentación (fajos de billetes, champán a chorro, coches en derrape).
- Ni "aspiracional barato" (filtros dorados, destellos, partículas, texto 3D volando).
- Ni comparaciones con otras marcas. **Nunca** mencionar marcas de terceros ni nombres de modelos ajenos en vídeos, copies o prompts (riesgo legal y de credibilidad).

---

## 2. Código visual

**Paleta:** negro profundo, grafito, acero, blanco roto, azul marino (#1B2A41 aprox., el del logo). Acentos solo cuando los da el propio reloj: oro rosa, azul, turquesa, salmón.

**Luz:**
- Clave baja, una fuente lateral principal (45–90°) + reflector negro (*negative fill*) para modelar el acero.
- Reflejos alargados y controlados (softbox de tira), nunca puntos de luz que quemen el cristal.
- Temperatura neutra-fría para acero; cálida (3200 K) solo en noche / interiores.

**Óptica (lenguaje que entienden los modelos de vídeo):**
- Macro: *100mm macro, f/4–f/5.6* (detalle de esfera, bisel, corona).
- Producto: *85mm, f/2.8*.
- Lifestyle: *35mm / 50mm anamorphic, f/2*, grano fino de película.

**Movimiento:** lento, con peso físico. Slider lateral, dolly-in, órbita parcial (≤30°), rack focus. **Prohibido:** giros de 360° del reloj, zooms bruscos, cámara flotante sin motivo, *speed ramps* exagerados.

**Montaje:** planos de 2–4 s. Fundidos a negro, no transiciones de efectos. Último plano siempre respira 1–1,5 s antes del logo.

**Sonido:** piano o cuerdas mínimas, graves cálidos, o *sound design* puro (tic del segundero, clic de corona, cierre magnético del estuche, papel). Silencio como recurso. Sin música épica ni *drops*.

**Tipografía en pantalla:** serif con mayúsculas espaciadas (como el logo). Máximo 5 palabras por pantalla. Blanco sobre negro o marino.

---

## 3. Regla de fidelidad del reloj (lo más importante)

Los modelos de vídeo actuales **reinventan** esferas, textos y números si se les deja. Protocolo obligatorio:

1. **Siempre image-to-video**, nunca text-to-video para el reloj. Partir de una **foto real** de la pieza (las que se hacen antes del envío), no de las imágenes generadas por IA.
   - Ojo: varias imágenes de referencia actuales tienen texto deformado en la esfera (p. ej. el lema bajo el logo del Cronógrafo Glaciar o la escala del bisel). Si se usan como fuente, el vídeo heredará esos errores.
2. **Frame inicial = foto del producto**. Si la herramienta lo permite, frame final también (Kling, Veo, Runway lo admiten).
3. **Plano corto = menos deriva.** 4–5 s por generación. Mejor 6 planos buenos que 1 de 20 s deformado.
4. **Movimiento mínimo del reloj.** Se mueve la cámara o la luz, no el reloj. Las agujas: quietas o con movimiento natural del segundero.
5. **Agujas a 10:10** en todas las fotos de partida para continuidad entre planos.
6. **El logo SERMAK y los textos se añaden en postproducción**, nunca se piden al generador.
7. **Control de calidad plano a plano:** comparar fotograma a fotograma contra la foto real (índices, subesferas, corona, eslabones). Si algo cambia → regenerar o cambiar de encuadre (más cerrado, desenfocado o en sombra).
8. **Muñecas:** usar fotos reales del reloj puesto como frame inicial. Las manos generadas fallan; mantener la mano parcialmente fuera de foco o en reposo.

### Bloque negativo estándar (pegar en todos los prompts)
```
no text distortion, no extra hands, no warped dial, no melting metal, no changing watch design,
no added logos, no extra subdials, no morphing indices, no CGI look, no plastic skin, no oversaturation,
no lens flares, no particles, no glow effects, no 360 spin
```

---

## 4. Talento

- **Creador de la marca** (foto de referencia: hombre de traje marino, gafas de aviador): perfecto para lifestyle y storytelling. Usar su foto como referencia de personaje (Kling *Elements*, Veo *ingredients* / reference image, Runway *References*). Recomendable que no mire a cámara: perfil, manos, reflejo.
- Talento genérico: personas reales de 30–55 años, piel con textura, sin poses de catálogo, ropa sobria (lana, lino, camisa blanca, punto oscuro).

---

## 5. Herramientas recomendadas (noviembre 2026)

| Uso | Herramienta | Por qué |
|---|---|---|
| Producto macro con fidelidad | **Kling** (image-to-video, start/end frame) | Muy estable con objetos metálicos y frames de control |
| Lifestyle con personas y audio | **Veo** | Mejor realismo humano y audio nativo |
| Planos atmosféricos / transiciones | **Runway** | Control de cámara fino |
| Escenas largas narrativas | **Sora** | Coherencia de escena, menos control del producto |
| Montaje y logo | DaVinci Resolve / Premiere / CapCut | Color final, tipografía, sonido |
| Upscale 4K | Topaz Video AI | Escalar 1080p → 2160p sin inventar detalle |

**Prompts en inglés** (todas estas herramientas rinden mejor), estructura fija:
`[Subject] · [Action] · [Camera move] · [Lens] · [Lighting] · [Environment] · [Style] · [Negative]`

---

## 6. Catálogo actual (fuente: sermak.netlify.app)

| Pieza | Estado | Rasgos visuales clave |
|---|---|---|
| Cronógrafo Glaciar | Disponible | Esfera blanca, subesferas negras, bisel taquimétrico negro, brazalete acero |
| Cronógrafo Ónix Rosé | Disponible | Oro rosa, esfera negra, subesferas oro rosa, caucho negro |
| Octogonal Marino | Disponible | Caja octogonal acero, esfera azul texturizada, fecha, brazalete integrado |
| Automático Medianoche | Disponible | Acero, esfera azul, corazón abierto a las 6, piel azul |
| Fase Lunar Aurora | Disponible | Bicolor acero/oro rosa, esfera salmón, calendario y fase lunar, piel marrón |
| Deportivo Laguna | Disponible | Caja cojín oro rosa, esfera turquesa degradada, brazalete integrado |
| Cronógrafo Panda · Deportivo Blanco · Octogonal Azul | **Entregados** | Útiles para piezas de "cuando se vende, no vuelve" |
