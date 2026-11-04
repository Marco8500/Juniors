"""Motor de reels SERMAK (derivado del de ObraWeb, misma técnica: gancho en el 1er segundo, todo lo que se dice
se ve, bucles abiertos, subtítulos con palabra clave resaltada). Paleta marino + oro rosa; el reloj es el de las fotos.
Uso: python3 -I reel_semak.py guiones/XXX.json   (antes: voz.sh)"""
import json, math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

D = os.path.dirname(os.path.abspath(__file__))
GUION = os.path.abspath(sys.argv[1])
NAME = os.path.splitext(os.path.basename(GUION))[0]
B = os.path.join(D, "build", NAME)
FOTOS = os.path.join(D, "fotos", "provisionales")  # cambiar a fotos/reales cuando lleguen
W, H, FPS = 1080, 1920, 30
F = lambda w, s: ImageFont.truetype(f"/usr/share/fonts/opentype/inter/Inter-{w}.otf", s)
def SERIF(s, wght=700):
    f = ImageFont.truetype(os.path.join(D, "assets", "fonts", "Cinzel.ttf"), s)
    try: f.set_variation_by_axes([wght])
    except Exception: pass
    return f

# ---- marca SERMAK: azul marino, blanco roto y oro rosa ----
ROSE, WHITE, MUTED = (214, 154, 116), (246, 242, 236), (170, 182, 205)
NAVY0, NAVY1, CARD = (8, 14, 28), (20, 34, 60), (24, 38, 66)
IMPACT = 0.12

rng = np.random.default_rng(5)
ease = lambda x: 1 - (1 - min(max(x, 0.0), 1.0)) ** 3
def back(x):
    x = min(max(x, 0.0), 1.0); c = 1.7
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

# ---------------- guion + voz ----------------
_g = json.load(open(GUION))
scenes = _g["escenas"] if isinstance(_g, dict) else _g
for i, s in enumerate(scenes):
    with wave.open(os.path.join(B, f"v{i}.wav")) as w:
        s["sr"] = w.getframerate()
        s["audio"] = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    s["vd"] = len(s["audio"]) / s["sr"]
    s["pin"] = 0.3 if i == 0 else 0.06
    s["dur"] = s["pin"] + s["vd"] + s.get("tail", 0.1)

# ---------------- utilidades ----------------
def make_bg():
    yy = np.linspace(0, 1, H)[:, None, None]
    g = (np.array(NAVY0) * (1 - yy) + np.array(NAVY1) * yy).repeat(W, 1)
    img = Image.fromarray(g.astype(np.uint8)).convert("RGBA")
    bl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(bl)
    d.ellipse([-200, 500, 1280, 1500], fill=ROSE + (38,)); d.ellipse([200, -300, 1300, 500], fill=(60, 90, 150, 50))
    img.alpha_composite(bl.filter(ImageFilter.GaussianBlur(200)))
    n = (np.random.default_rng(9).normal(0, 4, (H, W, 1))).repeat(3, 2)
    a = np.clip(np.asarray(img, np.float32)[..., :3] + n, 0, 255).astype(np.uint8)
    return Image.fromarray(a).convert("RGBA")
BG = make_bg()

def layer(w, h):
    L = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0)); return L, ImageDraw.Draw(L)
def ctext(d, y, txt, f, fill, x=W // 2, stroke=0, sfill=(0, 0, 0)):
    tw = d.textlength(txt, font=f)
    d.text((x - tw / 2, y), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
def spaced(d, y, txt, f, fill, x, tr):
    ws = [d.textlength(c, font=f) for c in txt]; tot = sum(ws) + tr * (len(txt) - 1); cx = x - tot / 2
    for c, w in zip(txt, ws): d.text((cx, y), c, font=f, fill=fill); cx += w + tr
def shadowed(L, blur=26, alpha=150):
    a = L.getchannel("A").filter(ImageFilter.GaussianBlur(blur))
    sh = Image.new("RGBA", L.size, (0, 0, 0, 0)); sh.putalpha(a.point(lambda v: v * alpha // 255))
    out = Image.new("RGBA", L.size, (0, 0, 0, 0)); out.alpha_composite(sh, (0, 16)); out.alpha_composite(L); return out
def place(fr, L, cx, cy, scale=1.0, alpha=1.0, rot=0):
    if alpha <= 0.01 or scale <= 0.01: return
    if scale != 1: L = L.resize((max(1, int(L.width * scale)), max(1, int(L.height * scale))), Image.BICUBIC)
    if rot: L = L.rotate(rot, expand=True, resample=Image.BICUBIC)
    if alpha < 1: L = L.copy(); L.putalpha(L.getchannel("A").point(lambda v: int(v * alpha)))
    fr.alpha_composite(L, (int(cx - L.width / 2), int(cy - L.height / 2)))
def headline(fr, t, txt, y=300, size=96, col=WHITE, delay=0.0, serif=True):
    f = SERIF(size) if serif else F("Black", size); L, d = layer(W, int(size * 1.5))
    while d.textlength(txt, font=f) > W - 110: f = SERIF(f.size - 4) if serif else F("Black", f.size - 4)
    ctext(d, 10, txt, f, col, stroke=5, sfill=(4, 8, 18))
    s0 = max(1.0, min(1.35, (W - 40) / (d.textlength(txt, font=f) + 20)))
    place(fr, L, W / 2, y, s0 - (s0 - 1) * back((t - delay) / 0.25), ease((t - delay) / 0.12))
def pill(txt, fill=ROSE, col=WHITE, size=54, pad=44):
    f = F("Black", size); L, d = layer(10, 10); tw = d.textlength(txt, font=f)
    L, d = layer(tw + pad * 2, size * 1.9); d.rounded_rectangle([0, 0, L.width - 1, L.height - 1], L.height // 2, fill=fill)
    ctext(d, size * 0.38, txt, f, col, L.width / 2); return L

# ---- relojes reales (fotos): recorte con borde suave ----
WATCH = dict(onix_rose=(445, 560, 215, 300), glaciar=(428, 528, 190, 265), medianoche=(398, 500, 235, 300),
             aurora=(418, 525, 245, 300), laguna=(332, 720, 290, 330))
_wc = {}
def watch(name, h=900):
    key = (name, h)
    if key in _wc: return _wc[key]
    cx, cy, rx, ry = WATCH[name]
    im = Image.open(os.path.join(FOTOS, name + ".jpg")).convert("RGB").crop((cx - rx, cy - ry, cx + rx, cy + ry))
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).ellipse([8, 8, im.width - 8, im.height - 8], fill=255)
    im.putalpha(m.filter(ImageFilter.GaussianBlur(18)))
    im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))
    _wc[key] = im; return im
def shine(img, p, width=0.12, strength=0.75):
    """Barrido de luz diagonal sobre el reloj (p de 0 a 1)."""
    if p <= 0 or p >= 1: return img
    w, h = img.size; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dd = (xx / w * 0.8 + yy / h * 0.45) - (-0.3 + 1.9 * p)
    band = np.exp(-(dd / width) ** 2)
    a = np.asarray(img, np.float32); lum = a[..., :3].mean(2) / 255
    add = (band * (0.15 + lum ** 1.3) * strength * 255)[..., None] * np.array([1.0, 0.93, 0.86])
    a[..., :3] = np.clip(a[..., :3] + add, 0, 255)
    return Image.fromarray(a.astype(np.uint8), "RGBA")
def glow(fr, cx, cy, r, col=ROSE, a=70):
    gl, d = layer(W, H); d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (a,))
    fr.alpha_composite(gl.filter(ImageFilter.GaussianBlur(r * 0.45)))

def logo_alpha(width, tagline=True):
    lg = np.asarray(Image.open(os.path.join(FOTOS, "logo.png")).convert("RGB"), np.float32).mean(2)
    bgv = np.median(lg); a = np.clip((lg - bgv - 25) / (235 - bgv - 25), 0, 1)
    im = Image.fromarray((a * 255).astype(np.uint8)); bb = im.point(lambda v: 255 if v > 90 else 0).getbbox()
    if not tagline: bb = (bb[0], bb[1], bb[2], int(bb[1] + (bb[3] - bb[1]) * 0.78))
    im = im.crop((bb[0] - 6, bb[1] - 6, bb[2] + 6, bb[3] + 6)); im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    L = Image.new("RGBA", im.size, WHITE + (0,)); L.putalpha(im); return L

# ---- iconos dibujados ----
def generic_watch(s=1.0, col=(150, 160, 180)):
    L, d = layer(120 * s, 200 * s)
    d.rounded_rectangle([38 * s, 0, 82 * s, 200 * s], int(10 * s), fill=tuple(int(c * 0.6) for c in col))
    d.ellipse([10 * s, 50 * s, 110 * s, 150 * s], fill=col); d.ellipse([20 * s, 60 * s, 100 * s, 140 * s], fill=(40, 46, 60))
    d.line([60 * s, 100 * s, 60 * s, 72 * s], fill=col, width=max(1, int(5 * s))); d.line([60 * s, 100 * s, 80 * s, 100 * s], fill=col, width=max(1, int(5 * s)))
    return L
def silhouette(kind, s=1.0):
    L, d = layer(300 * s, 380 * s); c = (70, 82, 108); dark = (32, 40, 58)
    d.rounded_rectangle([105 * s, 0, 195 * s, 380 * s], int(20 * s), fill=dark)
    if kind == "oct":
        r = 120 * s; pts = [(150 * s + r * math.cos(math.radians(22.5 + k * 45)), 190 * s + r * math.sin(math.radians(22.5 + k * 45))) for k in range(8)]
        d.polygon(pts, fill=c)
    elif kind == "cushion": d.rounded_rectangle([35 * s, 75 * s, 265 * s, 305 * s], int(70 * s), fill=c)
    else: d.ellipse([30 * s, 70 * s, 270 * s, 310 * s], fill=c)
    d.ellipse([60 * s, 100 * s, 240 * s, 280 * s], fill=(230, 232, 238) if kind == "panda" else (52, 62, 84))
    if kind == "panda":
        for (x, y) in [(110, 175), (190, 175), (150, 235)]: d.ellipse([(x - 22) * s, (y - 22) * s, (x + 22) * s, (y + 22) * s], fill=(25, 25, 30))
    return L
def gift_box(s=1.0, lid_off=0.0, lid_rot=0.0):
    L, d = layer(520 * s, 560 * s)
    d.rectangle([40 * s, 200 * s, 480 * s, 540 * s], fill=CARD); d.rectangle([235 * s, 200 * s, 285 * s, 540 * s], fill=ROSE)
    d.rectangle([40 * s, 200 * s, 480 * s, 210 * s], fill=(10, 16, 30))
    Lid, dl = layer(500 * s, 110 * s); dl.rectangle([0, 0, 500 * s, 110 * s], fill=(34, 52, 88)); dl.rectangle([225 * s, 0, 275 * s, 110 * s], fill=ROSE)
    lo = logo_alpha(int(150 * s), False); L.alpha_composite(lo, (int(185 * s), int(300 * s)))
    Lid = Lid.rotate(lid_rot, expand=True, resample=Image.BICUBIC)
    L.alpha_composite(Lid, (int(260 * s - Lid.width / 2 - lid_off * 160 * s), max(0, int(150 * s - Lid.height / 2 - lid_off * 140 * s))))
    return L

# ---------------- gancho: cristal ahumado que estalla y revela el reloj ----------------
def smoked_glass(text):
    L, d = layer(900, 1150)
    d.rounded_rectangle([0, 0, 899, 1149], 40, fill=(30, 36, 50, 245), outline=(120, 130, 150, 255), width=6)
    for k in range(7): d.line([80 + k * 120, 40, -200 + k * 120, 1110], fill=(255, 255, 255, 14), width=30)
    for i, ln in enumerate(text):
        f = SERIF(120 if i == 0 else 86); ctext(d, 420 + i * 150 - (len(text) - 1) * 70, ln, f, (200, 205, 215))
    return L
def make_shards(img, ix, iy, n_ang=16):
    angs = np.sort(rng.uniform(0, 2 * np.pi, n_ang)); rings = [0, 120, 280, 480, 2000]; pieces = []
    for a0, a1 in zip(angs, np.roll(angs, -1)):
        if a1 < a0: a1 += 2 * np.pi
        for r0, r1 in zip(rings[:-1], rings[1:]):
            jit = lambda r: r * rng.uniform(0.85, 1.15)
            poly = [(ix + jit(r0) * math.cos(a0), iy + jit(r0) * math.sin(a0)), (ix + jit(r1) * math.cos(a0), iy + jit(r1) * math.sin(a0)),
                    (ix + jit(r1) * math.cos(a1), iy + jit(r1) * math.sin(a1)), (ix + jit(r0) * math.cos(a1), iy + jit(r0) * math.sin(a1))]
            m = Image.new("L", img.size, 0); ImageDraw.Draw(m).polygon(poly, fill=255); bb = m.getbbox()
            if not bb: continue
            pc = img.crop(bb); pc.putalpha(Image.composite(pc.getchannel("A"), Image.new("L", pc.size, 0), m.crop(bb)))
            ImageDraw.Draw(pc).polygon([(x - bb[0], y - bb[1]) for x, y in poly], outline=(220, 225, 235, 200))
            if not pc.getbbox(): continue
            cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2; dx, dy = cx - ix, cy - iy; dist = math.hypot(dx, dy) + 1
            sp = rng.uniform(900, 2200) * (1.3 - min(dist, 500) / 900)
            pieces.append(dict(img=pc, x=cx, y=cy, vx=dx / dist * sp + rng.normal(0, 150), vy=dy / dist * sp - rng.uniform(200, 700), vr=rng.uniform(-540, 540)))
    return pieces
GCX, GCY = W // 2, 860
GLASS = smoked_glass(scenes[0].get("glass", ["?"]))
SHARDS = make_shards(GLASS, GLASS.width // 2, GLASS.height // 2 - 40)
SPARKS = [dict(a=rng.uniform(0, 2 * np.pi), v=rng.uniform(500, 1900), r=rng.uniform(4, 11), c=ROSE if rng.random() < 0.6 else WHITE) for _ in range(90)]

def sc_reveal(fr, t, dur, s):
    dt = t - IMPACT; wname = s.get("watch", "onix_rose")
    if dt >= 0:
        glow(fr, GCX, GCY, 520, ROSE, 70)
        sc = 1.18 - 0.18 * ease(dt / 0.6) + 0.03 * (t / dur)
        place(fr, shadowed(shine(watch(wname, 1000), (dt - 0.5) / 1.2)), GCX, GCY, sc, min(1, dt / 0.05))
    if dt < 0:
        place(fr, GLASS, GCX, GCY); return 0
    for p in SHARDS:
        k = max(0.0, dt - 0.03)
        x = GCX - GLASS.width / 2 + p["x"] + p["vx"] * k; y = GCY - GLASS.height / 2 + p["y"] + p["vy"] * k + 1500 * k * k
        place(fr, p["img"], x, y, 1, max(0, 1 - max(0, dt - 0.45) / 0.35), p["vr"] * k)
    L, d = layer(W, H); ix, iy = GCX, GCY - 40; r = 1400 * ease(dt / 0.5)
    d.ellipse([ix - r, iy - r, ix + r, iy + r], outline=(255, 255, 255, int(200 * max(0, 1 - dt / 0.5))), width=16)
    for sp in SPARKS:
        x = ix + math.cos(sp["a"]) * sp["v"] * dt; y = iy + math.sin(sp["a"]) * sp["v"] * dt + 1400 * dt * dt; al = max(0, 1 - dt / 0.8)
        if al > 0: d.ellipse([x - sp["r"], y - sp["r"], x + sp["r"], y + sp["r"]], fill=sp["c"] + (int(255 * al),))
    fr.alpha_composite(L)
    if dt < 0.18: fr.alpha_composite(Image.new("RGBA", (W, H), (255, 245, 235, int(235 * (1 - dt / 0.18)))))
    h1, h2 = s.get("h", ["SOLO EXISTE", "UNO"])
    headline(fr, t, h1, 250, 92, WHITE, IMPACT + 0.3)
    headline(fr, t, h2, 1400, 150, ROSE, IMPACT + 0.45)
    return 30 * max(0, 1 - dt / 0.45)

# ---------------- resto de planos ----------------
def sc_giftpromise(fr, t, dur, s):
    sh = 8 * math.sin(t * 30); glow(fr, W / 2, 880, 380, ROSE, 50)
    place(fr, shadowed(gift_box(1.0)), W / 2 + sh, 880, back(t / 0.3), 1)
    T = pill("AL FINAL", CARD, ROSE, 60); place(fr, T, W / 2, 470, back((t - 0.2) / 0.3), 1, -4)
    headline(fr, t, s.get("h", "TE DARÉ UN REGALO"), 1300, 96, WHITE, 0.15)
    return 0

def sc_mass(fr, t, dur, s):
    """Relojes iguales que se multiplican: fabricados por miles."""
    n = min(8, 1 + int(t / (dur / 9)) * 1) ; cols = [1, 2, 3, 4, 5, 6, 7, 8][n - 1]
    size = 1.6 / cols * 3.2; cell = W / cols
    rows = max(1, int(1050 / (200 * size * 1.25)))
    for r in range(rows):
        for c in range(cols):
            place(fr, generic_watch(size), cell * (c + 0.5), 430 + r * 200 * size * 1.25 + 100 * size, 1, 0.9)
    L = pill("TODOS IGUALES", (60, 70, 92), WHITE, 58); place(fr, shadowed(L), W / 2, 1450, back((t - dur * 0.55) / 0.25), 1, -3)
    headline(fr, t, s.get("h", "POR MILES"), 270, 120, WHITE, 0.0)
    return 4 if t > dur * 0.55 and t < dur * 0.55 + 0.15 else 0

def sc_one(fr, t, dur, s):
    """Los iguales desaparecen y queda uno: el reloj real con un 1 gigante."""
    k = ease(t / 0.35)
    if k < 1:
        for r in range(6):
            for c in range(8):
                a = (1 - k) * 0.9
                place(fr, generic_watch(0.62), W / 8 * (c + 0.5), 480 + r * 205, 1, a)
    glow(fr, W / 2, 900, 470, ROSE, int(70 * k))
    place(fr, shadowed(shine(watch(s.get("watch", "onix_rose"), 860), (t - 0.5) / 1.4)), W / 2, 920, 0.6 + 0.4 * back(t / 0.4), k)
    L, d = layer(500, 420); ctext(d, 0, "1", SERIF(380), ROSE, 250, stroke=6, sfill=(4, 8, 18))
    st = s["pin"] + s["vd"] * s.get("mark", 0.55)
    place(fr, L, 830, 520, 1.6 - 0.6 * back((t - st) / 0.25), ease((t - st) / 0.1), -6)
    headline(fr, t, s.get("h", "SOLO UNO"), 270, 110, WHITE, 0.1)
    return 22 * max(0, 1 - (t - st) / 0.3) if t >= st else 0

def sc_sold(fr, t, dur, s):
    """Tarjetas de piezas vendidas; el sello VENDIDO cae en cada una."""
    items = s.get("items", [["Cronógrafo", "Panda", "panda"], ["Deportivo", "Blanco", "cushion"], ["Octogonal", "Azul", "oct"]])
    marks = s.get("marks", [0.35, 0.55, 0.75]); shake = 0
    for k, (n1, n2, kind) in enumerate(items):
        y = 560 + k * 360; a = back((t - k * 0.12) / 0.3)
        C, d = layer(900, 320); d.rounded_rectangle([0, 0, 899, 319], 36, fill=CARD, outline=(60, 76, 108), width=4)
        C.alpha_composite(silhouette(kind, 0.78), (40, 12)); d.text((300, 60), n1, font=SERIF(54), fill=WHITE); d.text((300, 125), n2, font=SERIF(54), fill=MUTED)
        place(fr, shadowed(C), W / 2 + 900 * (1 - min(1, a)), y, 1, 1)
        st = s["pin"] + s["vd"] * marks[k]
        if t >= st:
            S, d = layer(430, 130); d.rounded_rectangle([5, 5, 424, 124], 18, outline=(214, 60, 60), width=10)
            ctext(d, 22, "VENDIDO", F("Black", 76), (214, 60, 60), 215)
            place(fr, S, W / 2 + 300, y + 70, (2.0 - 1.2 * ease((t - st) / 0.12)) * 0.8, min(1, (t - st) / 0.06), -10)
            if t - st < 0.15: shake = 18
    headline(fr, t, s.get("h", "NO VUELVEN"), 270, 120, ROSE, 0.0)
    return shake

def sc_boxshake(fr, t, dur, s):
    """Bucle: la caja SERMAK tiembla, ¿qué hay dentro?"""
    sh = 14 * math.sin(t * 38) * (0.6 + 0.4 * math.sin(t * 5)); glow(fr, W / 2, 900, 420, ROSE, 55)
    place(fr, shadowed(gift_box(1.15)), W / 2 + sh, 930, back(t / 0.3), 1, sh * 0.15)
    L, d = layer(240, 260); ctext(d, 0, "?", SERIF(240), ROSE, 120)
    place(fr, L, W / 2 + 330, 560, back((t - 0.3) / 0.3), 1, 12)
    headline(fr, t, s.get("h", "LO QUE LLEGA A TU CASA"), 300, 84, WHITE, 0.05)
    return 0

def sc_boxopen(fr, t, dur, s):
    """Foto real del reloj en su estuche SERMAK, con zoom lento."""
    im = Image.open(os.path.join(FOTOS, "marino_estuche.jpg")).convert("RGB")
    z = 1.0 + 0.10 * (t / dur); cw, ch = im.width / z, im.height / z; x0 = (im.width - cw) * 0.6; y0 = (im.height - ch) * 0.5
    c = im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((1000, int(1000 * ch / cw)), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", c.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, c.width - 1, c.height - 1], 40, fill=255); c.putalpha(m)
    c = shine(c, (t - 0.3) / 1.6, 0.1, 0.5)
    place(fr, shadowed(c), W / 2, 900, 0.85 + 0.15 * back(t / 0.35), 1)
    place(fr, pill(s.get("tag", "ESTUCHE SERMAK"), ROSE, WHITE, 56), W / 2, 1290, back((t - 0.35) / 0.3), 1, -3)
    headline(fr, t, s.get("h", "TU RELOJ"), 300, 120, WHITE, 0.0)
    return 0

def sc_cert(fr, t, dur, s):
    """Certificado 1 / 1 con el modelo y el propietario que se escribe."""
    C, d = layer(860, 1000); d.rounded_rectangle([0, 0, 859, 999], 24, fill=(246, 240, 230)); d.rounded_rectangle([24, 24, 835, 975], 14, outline=ROSE, width=4)
    lo = logo_alpha(380, False); navy = Image.new("RGBA", lo.size, (20, 32, 58, 255)); navy.putalpha(lo.getchannel("A")); C.alpha_composite(navy, (240, 80))
    spaced(d, 330, "CERTIFICADO", SERIF(48), (20, 32, 58), 430, 10)
    d.line([120, 420, 740, 420], fill=ROSE, width=3)
    d.text((120, 470), "MODELO", font=F("Bold", 30), fill=(120, 110, 100)); d.text((120, 510), s.get("modelo", "Cronógrafo Ónix Rosé"), font=SERIF(46), fill=(20, 32, 58))
    d.text((120, 620), "PROPIETARIO", font=F("Bold", 30), fill=(120, 110, 100))
    name = s.get("owner", "Tu nombre"); typed = name[: int(max(0, t - 0.5) * 14)]
    d.text((120, 660), typed + ("|" if int(t * 4) % 2 and len(typed) < len(name) else ""), font=SERIF(46), fill=(20, 32, 58))
    place(fr, shadowed(C), W / 2, 900, back(t / 0.35), 1, -2)
    st = s["pin"] + s["vd"] * s.get("mark", 0.45)
    if t >= st:
        S, d = layer(360, 360); d.ellipse([10, 10, 349, 349], outline=ROSE, width=12); ctext(d, 110, "1 / 1", SERIF(100), ROSE, 180)
        place(fr, S, W / 2 + 230, 1240, 2.0 - 1.0 * ease((t - st) / 0.12), min(1, (t - st) / 0.06), -14)
    headline(fr, t, s.get("h", "UNO DE UNO"), 270, 120, ROSE, 0.0)
    return 16 if st <= t < st + 0.14 else 0

def phone(w, h, content, t):
    L, d = layer(w, h); d.rounded_rectangle([0, 0, w - 1, h - 1], 70, fill=(12, 14, 20)); d.rounded_rectangle([14, 14, w - 15, h - 15], 58, fill=(240, 242, 246))
    d.rounded_rectangle([w // 2 - 80, 30, w // 2 + 80, 62], 16, fill=(12, 14, 20))
    content(L, d, w, h, t); return L
def chat_header(L, d, w):
    d.rectangle([14, 80, w - 15, 190], fill=(20, 32, 58)); d.ellipse([40, 105, 110, 175], fill=ROSE)
    lo = logo_alpha(48, False); L.alpha_composite(lo, (51, 118)); d.text((130, 118), "SERMAK", font=SERIF(40), fill=WHITE)
def photo_bubble(L, x, y, wname, size):
    im = watch(wname, size).copy(); bg = Image.new("RGBA", im.size, (225, 228, 235, 255)); bg.alpha_composite(im)
    m = Image.new("L", bg.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, bg.width - 1, bg.height - 1], 24, fill=255); bg.putalpha(m)
    L.alpha_composite(bg, (int(x), int(y)))
def sc_realphotos(fr, t, dur, s):
    """Chat: antes de enviarlo te llegan fotos reales de tu reloj."""
    wname = s.get("watch", "onix_rose")
    def c(L, d, w, h, tt):
        chat_header(L, d, w)
        if tt > 0.3:
            d.rounded_rectangle([40, 220, w - 120, 320], 26, fill=(255, 255, 255)); d.text((64, 248), "Tu reloj, antes de enviarlo", font=F("Bold", 32), fill=(20, 24, 36))
        if tt > 0.8: photo_bubble(L, 60, 350, wname, 330)
        if tt > 1.3: photo_bubble(L, 330, 560, wname, 330)
    place(fr, shadowed(phone(620, 1060, c, t)), W / 2, 960, back(t / 0.3), 1)
    place(fr, pill(s.get("tag", "FOTOS REALES"), ROSE, WHITE, 58), W / 2 + 200, 1440, back((t - dur * 0.5) / 0.25), 1, -5)
    headline(fr, t, s.get("h", "ANTES DE ENVIARLO"), 270, 92, WHITE, 0.0)
    return 0

def sc_steps(fr, t, dur, s):
    steps = s.get("steps", [["SÍGUEME", "follow"], ["COMENTA «MÍO»", "comment"]]); word = s.get("word", "MÍO")
    headline(fr, t, s.get("h", "TU REGALO"), 330, 110, ROSE, 0.0)
    marks = s.get("marks", [0.3, 0.6])
    for k, (lab, icon) in enumerate(steps):
        st = s["pin"] + marks[k] * s["vd"] - 0.15
        if t < st: continue
        a = back((t - st) / 0.25); y = 760 + k * 420
        L, d = layer(940, 340); d.rounded_rectangle([0, 0, 939, 339], 50, fill=CARD, outline=ROSE, width=5)
        d.ellipse([40, 110, 160, 230], fill=ROSE); ctext(d, 112, str(k + 1), SERIF(96), WHITE, 100)
        d.text((200, 70), lab, font=F("Black", 64), fill=WHITE)
        if icon == "follow":
            on = t > st + 0.6
            d.rounded_rectangle([200, 180, 520, 270], 26, fill=(60, 70, 95) if on else (0, 149, 246)); ctext(d, 196, "Siguiendo" if on else "Seguir", F("Black", 44), WHITE, 360)
        else:
            d.rounded_rectangle([200, 180, 760, 270], 45, fill=(40, 54, 86)); typed = word[: int(max(0, t - st - 0.2) * 8)]
            d.text((236, 194), typed, font=F("Black", 48), fill=WHITE); d.rounded_rectangle([620, 190, 750, 260], 35, fill=ROSE)
            ctext(d, 202, "Enviar", F("Bold", 30), WHITE, 685)
        place(fr, shadowed(L), W / 2 - 280 * (1 - min(1, a)), y, 1, min(1, a))
    return 0

def sc_delivery(fr, t, dur, s):
    """Te llega por mensaje la propuesta de tu reloj por encargo."""
    def c(L, d, w, h, tt):
        chat_header(L, d, w)
        if tt > 0.25:
            d.rounded_rectangle([40, 220, w - 90, 320], 26, fill=(255, 255, 255)); d.text((64, 248), s.get("msg", "Tu diseño, solo para ti"), font=F("Bold", 32), fill=(20, 24, 36))
        if tt > 0.6:
            d.rounded_rectangle([40, 345, w - 60, 880], 26, fill=(20, 32, 58))
            for j, (lab, val) in enumerate([("CAJA", "a tu gusto"), ("ESFERA", "a tu gusto"), ("CORREA", "a tu gusto")]):
                if tt > 0.8 + j * 0.25:
                    d.text((80, 390 + j * 150), lab, font=F("Bold", 28), fill=ROSE); d.text((80, 425 + j * 150), val, font=SERIF(44), fill=WHITE)
    place(fr, shadowed(phone(620, 1000, c, t)), W / 2, 900, back(t / 0.3), 1)
    for k, lab in enumerate(s.get("tags", ["GRATIS", "SIN COMPROMISO"])):
        st = dur * (0.45 + 0.2 * k)
        if t < st: continue
        T = pill(lab, ROSE if k == 0 else WHITE, WHITE if k == 0 else ROSE, 56)
        place(fr, T, W / 2 + (-200 if k == 0 else 170), 1380 + k * 140, back((t - st) / 0.25), 1, (-5, 4)[k])
    headline(fr, t, s.get("h", "POR MENSAJE"), 270, 110, WHITE, 0.0)
    return 0

def sc_logo(fr, t, dur, s):
    glow(fr, W / 2, 820, 420, ROSE, 45)
    place(fr, logo_alpha(820, True), W / 2, 760, 0.9 + 0.1 * ease(t / 0.6), ease(t / 0.4))
    L, d = layer(W, 120); spaced(d, 10, s.get("tag", "UNO DE UNO"), SERIF(64), ROSE, W / 2, 16)
    place(fr, L, W / 2, 1050, 1, ease((t - 0.4) / 0.4))
    on = t > dur * 0.5
    Bt, d = layer(520, 140); d.rounded_rectangle([0, 0, 519, 139], 40, fill=(60, 70, 95) if on else (0, 149, 246))
    ctext(d, 34, "Siguiendo" if on else "Seguir", F("Black", 62), WHITE, 260)
    place(fr, shadowed(Bt), W / 2, 1280, back((t - 0.2) / 0.3) * (0.92 if dur * 0.5 < t < dur * 0.5 + 0.12 else 1), 1)
    return 0

DRAW = dict(reveal=sc_reveal, giftpromise=sc_giftpromise, mass=sc_mass, one=sc_one, sold=sc_sold, boxshake=sc_boxshake,
            boxopen=sc_boxopen, cert=sc_cert, realphotos=sc_realphotos, steps=sc_steps, delivery=sc_delivery, logo=sc_logo)

# ---------------- subtítulos (palabra clave en oro rosa) ----------------
FS = F("Black", 70); MAXW = W - 140; d0 = ImageDraw.Draw(Image.new("RGB", (10, 10)))
def _tw(ws, f): return d0.textlength(" ".join(ws), font=f) + 18
def sub_layer(words, hi):
    f, lines = FS, [words]
    if _tw(words, f) > MAXW and len(words) > 1:
        k = min(range(1, len(words)), key=lambda k: max(_tw(words[:k], f), _tw(words[k:], f))); lines = [words[:k], words[k:]]
    while max(_tw(l, f) for l in lines) > MAXW and f.size > 40: f = F("Black", f.size - 4)
    lh = int(f.size * 1.18); L, d = layer(W, lh * len(lines) + 40); k = 0
    for li, line in enumerate(lines):
        x = (W - d.textlength(" ".join(line), font=f)) / 2
        for wd in line:
            d.text((x, 20 + li * lh), wd, font=f, fill=ROSE if k == hi else WHITE, stroke_width=9, stroke_fill=(4, 8, 18))
            x += d.textlength(wd + " ", font=f); k += 1
    return L

# ---------------- portada ----------------
def make_cover(lines):
    fr = BG.copy(); glow(fr, W / 2, 1000, 520, ROSE, 70)
    place(fr, shadowed(watch(scenes[0].get("watch", "onix_rose"), 1000)), W / 2, 1060, 1, 1)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
    for y in range(700): ds.line([0, y, W, y], fill=(4, 8, 18, int(220 * (1 - y / 700))))
    fr.alpha_composite(sh); d = ImageDraw.Draw(fr); y = 150
    for ln in lines:
        big = ln.startswith("*"); txt = ln.lstrip("*"); f = SERIF(190 if big else 96)
        while d.textlength(txt, font=f) > W - 110: f = SERIF(f.size - 6)
        ctext(d, y, txt, f, ROSE if big else WHITE, stroke=5, sfill=(4, 8, 18)); y += int(f.size * 1.15)
    place(fr, logo_alpha(420, False), W / 2, 1700)
    fr.convert("RGB").save(os.path.join(D, "videos", NAME + "_portada.jpg"), quality=92)
make_cover(scenes[0].get("cover", ["SOLO EXISTE", "*UNO"]))

# ---------------- render ----------------
PREVIEW = os.environ.get("PREVIEW")  # "1.0,3.5,..." segundos globales -> PNG y salir
out_v = os.path.join(B, "video.mp4")
if not PREVIEW:
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", out_v], stdin=subprocess.PIPE)
want = sorted(float(x) for x in PREVIEW.split(",")) if PREVIEW else []
gt = 0.0
for si, s in enumerate(scenes):
    words = s.get("sub", s["text"]).upper().split()
    groups = [words[i:i + 3] for i in range(0, len(words), 3)]
    wt = np.array([len(w) + 2 for w in words], float)
    wb = np.concatenate([[0], np.cumsum(wt) / wt.sum()]) * s["vd"] + s["pin"]
    nfr = int(round(s["dur"] * FPS))
    for fi in range(nfr):
        t = fi / FPS; g = gt + t
        if PREVIEW and not any(abs(g - x) < 0.5 / FPS for x in want): continue
        fr = BG.copy()
        shake = abs(DRAW[s["kind"]](fr, t, s["dur"], s) or 0)
        if t >= s["pin"] * 0.5 and not s.get("nosub"):
            wi = int(min(max(np.searchsorted(wb, t, side="right") - 1, 0), len(words) - 1)); acc = 0
            for gg in groups:
                if wi < acc + len(gg): break
                acc += len(gg)
            pop = ease((t - wb[acc]) / 0.1) if t >= wb[acc] else 1
            place(fr, sub_layer(gg, wi - acc), W / 2, 1660, 0.86 + 0.14 * pop)
        if shake:
            ox, oy = rng.uniform(-shake, shake), rng.uniform(-shake, shake)
            fr = fr.transform(fr.size, Image.AFFINE, (1, 0, ox, 0, 1, oy), resample=Image.BILINEAR, fillcolor=NAVY0 + (255,))
        if s.get("cut") and t < 0.08:
            fr.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(120 * (1 - t / 0.08)))))
        if PREVIEW: fr.convert("RGB").save(os.path.join(B, f"prev_{g:05.2f}.jpg"), quality=85)
        else: ff.stdin.write(fr.convert("RGB").tobytes())
    gt += nfr / FPS
    print("plano", si, s["kind"], "ok", flush=True)
if PREVIEW: sys.exit(0)
ff.stdin.close(); ff.wait()

# ---------------- audio: voz + música (pulso con tic de reloj) + efectos ----------------
SR = 24000
voice, starts = [], []; pos = 0
for s in scenes:
    a = s["audio"] if s["sr"] == SR else np.interp(np.linspace(0, len(s["audio"]) - 1, int(len(s["audio"]) * SR / s["sr"])), np.arange(len(s["audio"])), s["audio"])
    n = int(round(s["dur"] * FPS)) * SR // FPS
    seg = np.zeros(n, np.float32); st = int(s["pin"] * SR); seg[st:st + len(a)] = a[: n - st]
    voice.append(seg); starts.append(pos); pos += n
voice = np.concatenate(voice); n = len(voice); tt = np.arange(n) / SR
fx = np.zeros(n, np.float32)
# impacto: golpe grave + cristal rompiéndose
i0 = int(IMPACT * SR); L = int(1.2 * SR); k = np.arange(L) / SR
boom = np.sin(2 * np.pi * (55 * k - 22 * k * k)) * np.exp(-k * 4)
noise = np.random.default_rng(1).standard_normal(L) * np.exp(-k * 10) * 0.45
glass = np.zeros(L); gr = np.random.default_rng(2)
for _ in range(60):
    o = int(gr.uniform(0, 0.6) * SR); f = gr.uniform(2800, 8000); m = L - o
    glass[o:] += np.sin(2 * np.pi * f * k[:m]) * np.exp(-k[:m] * gr.uniform(18, 40)) * 0.11
fx[i0:i0 + L] += (boom + noise + glass)[: n - i0]
for s, st in zip(scenes, starts):
    if s.get("cut"):
        Lw = int(0.3 * SR); nz = np.random.default_rng(st).standard_normal(Lw)
        nz = np.convolve(nz, np.ones(10) / 10, "same") * np.sin(np.linspace(0, np.pi, Lw)) ** 2 * 0.3
        a0 = max(0, st - Lw // 2); fx[a0:a0 + Lw] += nz[: n - a0]
    for mk in s.get("hits", []):  # golpes de sello
        p = st + int((s["pin"] + s["vd"] * mk) * SR); kk = np.arange(int(0.3 * SR)) / SR
        hit = np.sin(2 * np.pi * 70 * kk) * np.exp(-kk * 16) * 0.6 + np.random.default_rng(p).standard_normal(len(kk)) * np.exp(-kk * 40) * 0.25
        fx[p:p + len(hit)] += hit[: max(0, n - p)]
# música: pulso oscuro a 100 bpm, el hi-hat es un tic de reloj, acordes menores suaves
bpm = 100; beat = 60 / bpm; music = np.zeros(n, np.float32); roots = [55.0, 43.65, 49.0, 41.2]
b = 0
while True:
    a0 = int((IMPACT + 0.5 + b * beat) * SR)
    if a0 >= n: break
    kk = np.arange(min(int(beat * SR), n - a0)) / SR
    if b % 2 == 0: music[a0:a0 + len(kk)] += np.sin(2 * np.pi * 50 * np.exp(-kk * 14) * kk * 6) * np.exp(-kk * 7) * 0.6
    for half in (0, 1):  # tic tac
        h0 = int(half * beat / 2 * SR); m = len(kk) - h0
        if m > 0:
            tk = np.random.default_rng(b * 2 + half).standard_normal(m) * np.exp(-kk[:m] * 220) * (0.10 if half == 0 else 0.07)
            tk += np.sin(2 * np.pi * (3600 if half == 0 else 3000) * kk[:m]) * np.exp(-kk[:m] * 300) * 0.08
            music[a0 + h0:a0 + len(kk)] += tk
    r = roots[(b // 4) % 4]
    music[a0:a0 + len(kk)] += np.sin(2 * np.pi * r * kk) * np.minimum(1, kk * 20) * np.exp(-kk * 2) * 0.16
    for mm in (2, 2.38, 3): music[a0:a0 + len(kk)] += np.sin(2 * np.pi * r * mm * kk) * np.minimum(1, kk * 6) * 0.025
    b += 1
music *= np.minimum(1, (tt[-1] - tt) / 0.8)
env = np.convolve(np.abs(voice), np.ones(2400) / 2400, "same"); duck = 1 - 0.5 * np.clip(env / 0.04, 0, 1)
mix = voice * 1.15 + music * 0.55 * duck + fx * 0.7
mix /= np.abs(mix).max() / 0.95
with wave.open(os.path.join(B, "audio.wav"), "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
final = os.path.join(D, "videos", NAME + ".mp4")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", out_v, "-i", os.path.join(B, "audio.wav"), "-c:v", "copy", "-c:a", "aac",
                "-b:a", "192k", "-shortest", "-movflags", "+faststart", final], check=True)
print("listo", final, round(n / SR, 1), "s")
