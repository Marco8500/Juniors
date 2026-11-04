"""Motor de reels SEMAK (copia del de ObraWeb; se adapta a relojes tras confirmar la marca).
Uso: python3 -I reel_semak.py guiones/XXX.json"""
import json, math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

D = os.path.dirname(os.path.abspath(__file__))
GUION = os.path.abspath(sys.argv[1])
NAME = os.path.splitext(os.path.basename(GUION))[0]
B = os.path.join(D, "build", NAME)
W, H, FPS = 1080, 1920, 30
F = lambda w, s: ImageFont.truetype(f"/usr/share/fonts/opentype/inter/Inter-{w}.otf", s)

# Marca ObraWeb: azul marino, blanco y naranja
ORANGE, WHITE, MUTED = (255, 122, 26), (255, 255, 255), (176, 190, 220)
NAVY_CARD, BLUE, GREY = (18, 36, 78), (40, 90, 200), (120, 130, 155)
IMPACT = 0.12  # segundo en que explota el gancho

rng = np.random.default_rng(3)
ease = lambda x: 1 - (1 - min(max(x, 0.0), 1.0)) ** 3
def back(x):
    x = min(max(x, 0.0), 1.0); c = 1.7
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

# ---------------- guion + voz ----------------
_g = json.load(open(GUION))
scenes = _g["escenas"] if isinstance(_g, dict) else _g  # formato nuevo {meta, escenas} o lista antigua
for i, s in enumerate(scenes):
    with wave.open(os.path.join(B, f"v{i}.wav")) as w:
        s["sr"] = w.getframerate()
        s["audio"] = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    s["vd"] = len(s["audio"]) / s["sr"]
    s["pin"] = 0.3 if i == 0 else 0.06
    s["dur"] = s["pin"] + s["vd"] + 0.1

# ---------------- utilidades de dibujo ----------------
def make_bg():
    yy = np.linspace(0, 1, H)[:, None, None]
    g = (np.array([6, 16, 40]) * (1 - yy) + np.array([12, 30, 72]) * yy).repeat(W, 1)
    img = Image.fromarray(g.astype(np.uint8)).convert("RGBA")
    bl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(bl)
    d.ellipse([-300, 200, 600, 1100], fill=BLUE + (110,)); d.ellipse([500, 1100, 1400, 2000], fill=ORANGE + (40,))
    img.alpha_composite(bl.filter(ImageFilter.GaussianBlur(160)))
    gr = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(gr)
    for x in range(0, W, 90): d.line([x, 0, x, H], fill=(255, 255, 255, 9))
    for y in range(0, H, 90): d.line([0, y, W, y], fill=(255, 255, 255, 9))
    img.alpha_composite(gr)
    return img
BG = make_bg()

def layer(w, h):
    L = Image.new("RGBA", (w, h), (0, 0, 0, 0)); return L, ImageDraw.Draw(L)
def ctext(d, y, txt, f, fill, x=W // 2, stroke=0):
    tw = d.textlength(txt, font=f)
    d.text((x - tw / 2, y), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
def shadowed(L, blur=26, alpha=130):
    a = L.getchannel("A").filter(ImageFilter.GaussianBlur(blur))
    sh = Image.new("RGBA", L.size, (0, 0, 0, 0)); sh.putalpha(a.point(lambda v: v * alpha // 255))
    out = Image.new("RGBA", L.size, (0, 0, 0, 0)); out.alpha_composite(sh, (0, 16)); out.alpha_composite(L); return out
def place(fr, L, cx, cy, scale=1.0, alpha=1.0, rot=0):
    if alpha <= 0.01 or scale <= 0.01: return
    if scale != 1: L = L.resize((max(1, int(L.width * scale)), max(1, int(L.height * scale))), Image.BILINEAR)
    if rot: L = L.rotate(rot, expand=True, resample=Image.BILINEAR)
    if alpha < 1: L = L.copy(); L.putalpha(L.getchannel("A").point(lambda v: int(v * alpha)))
    fr.alpha_composite(L, (int(cx - L.width / 2), int(cy - L.height / 2)))
def headline(fr, t, txt, y=300, size=96, col=WHITE, delay=0.0):
    f = F("Black", size); L, d = layer(W, int(size * 1.4))
    while d.textlength(txt, font=f) > W - 100: f = F("Black", f.size - 4)
    ctext(d, 10, txt, f, col, stroke=6)
    place(fr, L, W / 2, y, 1.5 - 0.5 * back((t - delay) / 0.25), ease((t - delay) / 0.12))
def badge(fr, t, txt, y=200):
    f = F("Black", 54); L, d = layer(W, 120); tw = d.textlength(txt, font=f)
    d.rounded_rectangle([(W - tw) / 2 - 40, 10, (W + tw) / 2 + 40, 100], 45, fill=ORANGE)
    ctext(d, 22, txt, f, WHITE)
    place(fr, L, W / 2, y, back(t / 0.25), 1)
def person(col=WHITE, s=1.0):
    L, d = layer(int(120 * s), int(220 * s))
    d.ellipse([30 * s, 0, 90 * s, 60 * s], fill=col); d.rounded_rectangle([10 * s, 70 * s, 110 * s, 220 * s], int(40 * s), fill=col)
    return L
def browser(w=820, h=700, url="tunegocio.com", content=None, t=0):
    L, d = layer(w, h)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 32, fill=(245, 246, 252))
    d.rounded_rectangle([0, 0, w - 1, 72], 32, fill=(222, 226, 238)); d.rectangle([0, 44, w - 1, 72], fill=(222, 226, 238))
    for i, c in enumerate([(255, 95, 87), (255, 189, 46), (40, 200, 64)]): d.ellipse([24 + i * 38, 24, 50 + i * 38, 50], fill=c)
    d.rounded_rectangle([160, 16, w - 30, 58], 21, fill=WHITE); d.text((182, 22), url, font=F("Medium", 26), fill=(90, 95, 120))
    if content: content(L, d, w, h, t)
    return L
def phone(w=520, h=1000, content=None, t=0):
    L, d = layer(w, h)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 66, fill=(10, 14, 30), outline=(70, 90, 140), width=6)
    d.rounded_rectangle([w // 2 - 70, 20, w // 2 + 70, 48], 14, fill=(0, 0, 0))
    if content: content(L, d, w, h, t)
    return L
def lock(s=1.0, shake=0):
    L, d = layer(int(200 * s), int(240 * s))
    d.arc([40 * s, 0, 160 * s, 130 * s], 180, 360, fill=WHITE, width=int(22 * s))
    d.line([51 * s, 65 * s, 51 * s, 110 * s], fill=WHITE, width=int(22 * s)); d.line([149 * s, 65 * s, 149 * s, 110 * s], fill=WHITE, width=int(22 * s))
    d.rounded_rectangle([10 * s, 100 * s, 190 * s, 240 * s], int(26 * s), fill=ORANGE)
    ctext(d, 118 * s, "?", F("Black", int(90 * s)), WHITE, int(100 * s))
    return L
def coin(s=1.0):
    L, d = layer(int(110 * s), int(110 * s))
    d.ellipse([0, 0, 109 * s, 109 * s], fill=ORANGE, outline=(255, 190, 120), width=int(6 * s))
    ctext(d, 18 * s, "€", F("Black", int(64 * s)), WHITE, int(55 * s)); return L
def cursor(s=1.0):
    L, d = layer(int(70 * s), int(100 * s))
    d.polygon([(4, 4), (4, 84 * s), (24 * s, 64 * s), (40 * s, 96 * s), (54 * s, 88 * s), (38 * s, 58 * s), (64 * s, 58 * s)], fill=WHITE, outline=(0, 0, 0))
    return L

# ---------------- ESCENA 0: la web vieja EXPLOTA ----------------
def old_web():
    def content(L, d, w, h, t):
        d.rectangle([30, 100, w - 30, 190], fill=(200, 200, 205)); d.text((50, 120), "MI NEGOCIO", font=F("Black", 44), fill=(110, 110, 120))
        for k in range(0, w, 60): d.polygon([(k, 230), (k + 30, 230), (k + 60, 290), (k + 30, 290)], fill=(240, 200, 40))
        ctext(d, 320, "EN CONSTRUCCIÓN", F("Black", 52), (120, 120, 130), w // 2)
        for r in range(6): d.rectangle([60, 420 + r * 42, 60 + (r * 97) % 500 + 200, 440 + r * 42], fill=(205, 207, 214))
        d.rectangle([60, 700, 300, 860], fill=(215, 215, 220)); d.line([60, 700, 300, 860], fill=(180, 180, 190), width=4); d.line([300, 700, 60, 860], fill=(180, 180, 190), width=4)
    return browser(760, 920, "minegocio-1998.com", content)
def insta_profile():
    L, d = layer(760, 920)
    d.rounded_rectangle([0, 0, 759, 919], 40, fill=(250, 250, 252))
    d.ellipse([50, 60, 230, 240], fill=ORANGE); d.ellipse([62, 72, 218, 228], fill=(250, 250, 252)); d.ellipse([74, 84, 206, 216], fill=(255, 190, 140))
    ctext(d, 118, "TN", F("Black", 60), WHITE, 140)
    for k, (n, lab) in enumerate([("128", "posts"), ("2.340", "seguidores"), ("310", "seguidos")]):
        ctext(d, 100, n, F("Black", 46), (20, 20, 40), 330 + k * 150); ctext(d, 160, lab, F("Medium", 24), (110, 110, 130), 330 + k * 150)
    d.text((50, 270), "@tunegocio", font=F("Black", 40), fill=(20, 20, 40))
    d.text((50, 325), "Pide cita por mensaje directo", font=F("Medium", 30), fill=(90, 90, 110))
    d.rounded_rectangle([50, 380, 710, 440], 16, fill=(225, 228, 238)); ctext(d, 392, "Seguir", F("Bold", 32), (20, 20, 40), 380)
    cols = [(255, 160, 90), (90, 130, 220), (255, 200, 150), (60, 90, 170), (255, 122, 26), (150, 175, 230)]
    for k in range(6):
        x, y = 4 + (k % 3) * 251, 470 + (k // 3) * 222
        d.rectangle([x, y, x + 247, y + 218], fill=cols[k])
    return L
def closed_sign():
    L, d = layer(760, 900)
    d.line([380, 0, 180, 300], fill=(150, 150, 160), width=10); d.line([380, 0, 580, 300], fill=(150, 150, 160), width=10)
    d.ellipse([360, 0, 400, 40], fill=(200, 200, 210))
    d.rounded_rectangle([20, 280, 739, 860], 50, fill=(200, 30, 40), outline=WHITE, width=16)
    ctext(d, 410, "CERRADO", F("Black", 128), WHITE, 380)
    ctext(d, 620, "Abrimos mañana", F("Bold", 54), (255, 220, 220), 380); ctext(d, 700, "a las 9:00", F("Bold", 54), (255, 220, 220), 380)
    return L
def biz_card():
    L, d = layer(820, 500)
    d.rounded_rectangle([0, 0, 819, 499], 36, fill=(250, 248, 242))
    d.rectangle([0, 0, 40, 499], fill=(150, 150, 160))
    d.text((90, 70), "MI NEGOCIO", font=F("Black", 66), fill=(30, 30, 50))
    d.text((90, 160), "Reformas y más", font=F("Medium", 40), fill=(110, 110, 130))
    d.line([90, 240, 730, 240], fill=(210, 210, 215), width=4)
    d.text((90, 280), "Tel. 600 000 000", font=F("Bold", 42), fill=(60, 60, 80))
    d.text((90, 350), "C/ Mayor, 1", font=F("Medium", 38), fill=(110, 110, 130))
    return L.rotate(-6, expand=True, resample=Image.BICUBIC)
def stopwatch():
    L, d = layer(700, 820)
    d.rounded_rectangle([300, 0, 400, 70], 16, fill=(200, 205, 220)); d.rectangle([330, 60, 370, 120], fill=(200, 205, 220))
    d.rounded_rectangle([520, 90, 600, 150], 16, fill=(200, 205, 220))
    d.ellipse([20, 110, 680, 770], fill=(245, 246, 252), outline=(200, 205, 220), width=26)
    for k in range(12):
        a = k * math.pi / 6; d.line([350 + math.sin(a) * 270, 440 - math.cos(a) * 270, 350 + math.sin(a) * 300, 440 - math.cos(a) * 300], fill=(150, 155, 175), width=8)
    d.pieslice([90, 180, 610, 700], -90, -90 + 18, fill=ORANGE)
    ctext(d, 520, "0:03", F("Black", 120), (20, 20, 40), 350)
    d.line([350, 440, 350 + math.sin(0.31) * 230, 440 - math.cos(0.31) * 230], fill=ORANGE, width=14)
    d.ellipse([326, 416, 374, 464], fill=(20, 20, 40))
    return L
def error404():
    def content(L, d, w, h, t):
        ctext(d, 170, "404", F("Black", 260), (200, 30, 40), w // 2)
        ctext(d, 480, "Página no encontrada", F("Bold", 50), (90, 95, 120), w // 2)
        d.ellipse([w // 2 - 70, 600, w // 2 + 70, 740], outline=(150, 155, 175), width=10)
        d.ellipse([w // 2 - 35, 640, w // 2 - 15, 660], fill=(150, 155, 175)); d.ellipse([w // 2 + 15, 640, w // 2 + 35, 660], fill=(150, 155, 175))
        d.arc([w // 2 - 40, 690, w // 2 + 40, 750], 200, 340, fill=(150, 155, 175), width=8)
    return browser(760, 860, "tunegocio.com/servicios", content)
def piggy():
    L, d = layer(760, 620)
    d.ellipse([60, 120, 700, 560], fill=ORANGE); d.ellipse([600, 270, 740, 400], fill=(255, 150, 70))
    d.ellipse([650, 310, 672, 332], fill=(120, 50, 10)); d.ellipse([690, 310, 712, 332], fill=(120, 50, 10))
    d.polygon([(200, 160), (250, 60), (300, 170)], fill=(255, 150, 70)); d.ellipse([540, 230, 570, 260], fill=(40, 20, 10))
    for x in (160, 260, 470, 570): d.rounded_rectangle([x, 500, x + 60, 610], 18, fill=(230, 100, 15))
    d.rounded_rectangle([300, 140, 460, 170], 14, fill=(120, 50, 10)); ctext(d, 270, "€", F("Black", 180), (255, 220, 190), 360)
    return L
def search_phone():
    def c(L, d, w, h, t):
        d.rounded_rectangle([18, 70, w - 18, h - 18], 50, fill=(245, 246, 252))
        d.rounded_rectangle([40, 110, w - 40, 190], 40, fill=(228, 231, 242)); d.text((80, 128), "peluquería cerca de mí", font=F("Medium", 34), fill=(40, 40, 60))
        for k, (n, lit) in enumerate([("Peluquería A", True), ("Peluquería B", False)]):
            y = 230 + k * 260; d.rounded_rectangle([40, y, w - 40, y + 230], 26, fill=(232, 235, 245))
            d.ellipse([64, y + 40, 154, y + 130], fill=ORANGE if lit else GREY); d.text((180, y + 50), n, font=F("Black", 40), fill=(20, 20, 40))
            d.text((180, y + 110), "Web · Reservar" if lit else "Solo teléfono", font=F("Bold", 30), fill=ORANGE if lit else (120, 120, 140))
    return phone(560, 900, c)
def notif_phone():
    def c(L, d, w, h, t):
        d.rounded_rectangle([18, 70, w - 18, h - 18], 50, fill=(20, 26, 48))
        ctext(d, 120, "14:32", F("Black", 90), WHITE, w // 2)
        for k, m in enumerate(["¿Hacéis presupuestos?", "¿Podéis venir hoy?", "¿Qué horario tenéis?", "¿Hola? ¿Estáis?"]):
            y = 280 + k * 130; d.rounded_rectangle([36, y, w - 36, y + 110], 26, fill=(245, 246, 252))
            d.ellipse([56, y + 25, 116, y + 85], fill=(40, 200, 110)); d.text((136, y + 34), m, font=F("Bold", 30), fill=(20, 20, 40))
    L = phone(560, 900, c)
    d = ImageDraw.Draw(L); d.ellipse([440, 0, 560, 120], fill=(230, 40, 50)); ctext(d, 22, "27", F("Black", 64), WHITE, 500)
    return L
def paper_planner():
    L, d = layer(760, 860)
    d.rounded_rectangle([0, 0, 759, 859], 30, fill=(140, 40, 40))  # tapas
    d.rounded_rectangle([30, 20, 739, 839], 16, fill=(250, 246, 232))
    for k in range(9): d.ellipse([10, 60 + k * 88, 54, 104 + k * 88], fill=(200, 200, 205))  # anillas
    d.text((90, 50), "AGENDA", font=F("Black", 64), fill=(140, 40, 40))
    notes = ["9:00  Sra. López ??", "10:30 llamar fontanería", "12:00 ¿presupuesto?", "13:00 no vino", "16:00 reclamar factura", "17:30 devolver llamada"]
    for k, n in enumerate(notes):
        y = 170 + k * 105; d.line([90, y + 70, 700, y + 70], fill=(210, 205, 190), width=3)
        d.text((100, y + 10), n, font=F("Medium", 40), fill=(60, 60, 90))
    d.line([100, 545, 520, 515], fill=(200, 30, 40), width=8)  # tachón
    return L
def nameplate():
    L, d = layer(860, 520)
    d.line([200, 0, 200, 120], fill=(150, 150, 160), width=12); d.line([660, 0, 660, 120], fill=(150, 150, 160), width=12)
    d.rounded_rectangle([0, 110, 859, 519], 36, fill=(30, 50, 100), outline=(200, 205, 220), width=14)
    ctext(d, 170, "ELECTRICIDAD", F("Black", 100), WHITE, 430); ctext(d, 290, "PÉREZ", F("Black", 140), ORANGE, 430)
    d.polygon([(400, 450), (460, 450), (430, 500)], fill=(255, 214, 64)); d.polygon([(440, 420), (470, 470), (430, 470)], fill=(255, 214, 64))
    return L
def sparkle(d, x, y, r, col=(255, 214, 64)):
    d.polygon([(x, y - r), (x + r * 0.25, y - r * 0.25), (x + r, y), (x + r * 0.25, y + r * 0.25), (x, y + r), (x - r * 0.25, y + r * 0.25), (x - r, y), (x - r * 0.25, y - r * 0.25)], fill=col)
def pretty_web(clients=True):
    """Web muy bonita (degradados, destellos, corazones) pero sin forma de conseguir clientes."""
    def c(L, d, w, h, t):
        for y in range(70, h - 1):
            k = (y - 70) / (h - 70); d.line([1, y, w - 2, y], fill=(int(255 - 60 * k), int(170 + 40 * k), int(200 + 40 * k)))
        ctext(d, 120, "Bienvenidos", F("Black", 80), WHITE, w // 2); ctext(d, 220, "a nuestro mundo", F("Bold", 46), WHITE, w // 2)
        for (x, y, r) in [(120, 360, 34), (620, 330, 26), (380, 460, 40), (200, 560, 22), (560, 590, 30)]: sparkle(d, x, y, r)
        for (x, y) in [(300, 380), (480, 520)]:
            d.ellipse([x - 26, y - 20, x, y + 6], fill=(255, 90, 140)); d.ellipse([x - 4, y - 20, x + 22, y + 6], fill=(255, 90, 140)); d.polygon([(x - 26, y - 4), (x + 22, y - 4), (x - 2, y + 34)], fill=(255, 90, 140))
        if clients:
            d.rounded_rectangle([w // 2 - 190, h - 130, w // 2 + 190, h - 50], 40, fill=(255, 255, 255, 200)); ctext(d, h - 118, "0 clientes", F("Black", 46), (200, 30, 40), w // 2)
    return browser(760, 820, "tunegocio.com", c)
OBJECTS = dict(oldweb=old_web, insta=insta_profile, closed=closed_sign, card=biz_card, stopwatch=stopwatch, e404=error404, piggy=piggy, searchphone=search_phone, notifphone=notif_phone, planner=paper_planner, nameplate=nameplate, prettyweb=pretty_web)
OLD = shadowed(OBJECTS[scenes[0].get("obj", "oldweb")](), 30)
OCX, OCY = W // 2, 860
def make_shards(img, ix, iy, n_ang=16):
    angs = np.sort(rng.uniform(0, 2 * np.pi, n_ang)); rings = [0, 110, 260, 460, 2000]
    pieces = []
    for a0, a1 in zip(angs, np.roll(angs, -1)):
        if a1 < a0: a1 += 2 * np.pi
        for r0, r1 in zip(rings[:-1], rings[1:]):
            jit = lambda r: r * rng.uniform(0.85, 1.15)
            poly = [(ix + jit(r0) * math.cos(a0), iy + jit(r0) * math.sin(a0)), (ix + jit(r1) * math.cos(a0), iy + jit(r1) * math.sin(a0)),
                    (ix + jit(r1) * math.cos(a1), iy + jit(r1) * math.sin(a1)), (ix + jit(r0) * math.cos(a1), iy + jit(r0) * math.sin(a1))]
            m = Image.new("L", img.size, 0); ImageDraw.Draw(m).polygon(poly, fill=255)
            bb = m.getbbox()
            if not bb: continue
            pc = img.crop(bb); al = Image.composite(pc.getchannel("A"), Image.new("L", pc.size, 0), m.crop(bb)); pc.putalpha(al)
            if not pc.getbbox(): continue
            cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
            dx, dy = cx - ix, cy - iy; dist = math.hypot(dx, dy) + 1
            sp = rng.uniform(900, 2200) * (1.3 - min(dist, 500) / 900)
            pieces.append(dict(img=pc, x=cx, y=cy, vx=dx / dist * sp + rng.normal(0, 150), vy=dy / dist * sp - rng.uniform(200, 700),
                               rot=0, vr=rng.uniform(-540, 540)))
    return pieces
SHARDS = make_shards(OLD, OLD.width // 2 + 40, OLD.height // 2 - 60)
SPARKS = [dict(a=rng.uniform(0, 2 * np.pi), v=rng.uniform(500, 1900), r=rng.uniform(5, 14), c=ORANGE if rng.random() < 0.6 else WHITE) for _ in range(90)]

def gear(size, col, rot=0.0, hole=True):
    L, d = layer(size, size); c = size / 2; R = size * 0.42; r = size * 0.32
    for k in range(10):
        a = math.radians(rot + k * 36)
        pts = [(c + R * math.cos(a + o) + size * 0.06 * math.cos(a) * (1 if abs(o) < 0.1 else 0), c + R * math.sin(a + o)) for o in (-0.16, 0.16)]
        x, y = c + (R + size * 0.06) * math.cos(a), c + (R + size * 0.06) * math.sin(a)
        d.ellipse([x - size * 0.07, y - size * 0.07, x + size * 0.07, y + size * 0.07], fill=col)
    d.ellipse([c - R, c - R, c + R, c + R], fill=col)
    if hole:
        hm = Image.new("L", L.size, 255); ImageDraw.Draw(hm).ellipse([c - r * 0.55, c - r * 0.55, c + r * 0.55, c + r * 0.55], fill=0)
        L.putalpha(Image.composite(L.getchannel("A"), Image.new("L", L.size, 0), hm))
    return L
def sc_boom(fr, t, dur, s):
    dt = t - IMPACT
    if dt < 0:
        place(fr, OLD, OCX, OCY)
        return 0
    # grietas un instante antes de saltar
    for p in SHARDS:
        k = max(0.0, dt - 0.03)
        x = OCX - OLD.width / 2 + p["x"] + p["vx"] * k
        y = OCY - OLD.height / 2 + p["y"] + p["vy"] * k + 0.5 * 3000 * k * k
        place(fr, p["img"], x, y, 1, max(0, 1 - max(0, dt - 0.5) / 0.4), p["vr"] * k)
    L, d = layer(W, H)
    ix, iy = OCX + 40, OCY - 60
    r = 1400 * ease(dt / 0.5)  # onda expansiva
    d.ellipse([ix - r, iy - r, ix + r, iy + r], outline=(255, 255, 255, int(200 * max(0, 1 - dt / 0.5))), width=18)
    for sp in SPARKS:
        k = dt; x = ix + math.cos(sp["a"]) * sp["v"] * k; y = iy + math.sin(sp["a"]) * sp["v"] * k + 1400 * k * k
        al = max(0, 1 - dt / 0.8)
        if al > 0: d.ellipse([x - sp["r"], y - sp["r"], x + sp["r"], y + sp["r"]], fill=sp["c"] + (int(255 * al),))
    fr.alpha_composite(L)
    if dt < 0.18:  # destello
        fl = Image.new("RGBA", (W, H), (255, 240, 220, int(235 * (1 - dt / 0.18)))); fr.alpha_composite(fl)
    # después: titular y clientes huyendo
    h1, h2 = s.get("h", ["TU WEB ESPANTA", "A TUS CLIENTES"])
    headline(fr, t, h1, 560, 110, WHITE, IMPACT + 0.3)
    headline(fr, t, h2, 700, 110, ORANGE, IMPACT + 0.45)
    if s.get("after") == "search0":
        st = IMPACT + 0.6
        if t > st:
            place(fr, shadowed(search_bar(s.get("query0", "Electricidad Pérez"), cursor_on=False)), W / 2, 1060, back((t - st) / 0.3), 1)
            n = max(0, int(9 - (t - st) * 12)); L, d = layer(W, 160)
            ctext(d, 10, f"{n} BÚSQUEDAS", F("Black", 110), (230, 40, 50) if n == 0 else WHITE, stroke=5)
            place(fr, L, W / 2, 1290, back((t - st - 0.1) / 0.3), 1)
        return 30 * max(0, 1 - dt / 0.45)
    if s.get("after") == "gears":
        for k in range(3):
            st = IMPACT + 0.6 + k * 0.25
            if t > st:
                G = gear(200, ORANGE if k == 2 else WHITE, (t - st) * (90 if k % 2 == 0 else -90), hole=False)
                place(fr, G, 260 + k * 280, 1150 + (k % 2) * 40, back((t - st) / 0.3), 1)
                L, d = layer(120, 120); ctext(d, 10, str(k + 1), F("Black", 90), (6, 16, 40), 60)
                place(fr, L, 260 + k * 280, 1150 + (k % 2) * 40, back((t - st) / 0.3), 1)
        return 30 * max(0, 1 - dt / 0.45)
    if s.get("after") == "shops":
        st = s["pin"] + s["vd"] * s.get("marks", [0.45, 0.75])[0]; st2 = s["pin"] + s["vd"] * s.get("marks", [0.45, 0.75])[1]
        names = s.get("names", ["PELUQ. A", "PELUQ. B"])
        if t > st: place(fr, shadowed(rich_shop(names[0], True, t)), 290, 1150, back((t - st) / 0.3) * 0.95, 1)
        if t > st2: place(fr, shadowed(rich_shop(names[1], False, t)), 790, 1150, back((t - st2) / 0.3) * 0.95, 1)
        return 30 * max(0, 1 - dt / 0.45)
    if t > IMPACT + 0.5:
        k = t - IMPACT - 0.5
        for j, sgn in enumerate([-1, 1, -1, 1]):
            place(fr, person(WHITE if j % 2 else MUTED, 1.1), W / 2 + sgn * (90 + j * 70 + 700 * (k / 2.6) ** 1.5), 1150 + (j % 2) * 60, 1, max(0, min(1, k / 0.15, 1 - (k - 2.0) / 0.6)))
    return 30 * max(0, 1 - dt / 0.45)  # sacudida

# ---------------- resto de planos ----------------
def sc_three(fr, t, dur, s):
    headline(fr, t, s.get("title", "3 ERRORES"), 330, 140, WHITE)
    for k, x in enumerate([230, 540, 850]):
        a = back((t - 0.15 - k * 0.15) / 0.3)
        L, d = layer(260, 320); d.rounded_rectangle([0, 0, 259, 319], 36, fill=NAVY_CARD, outline=ORANGE if k == 2 else (60, 90, 150), width=6)
        if k < 2: ctext(d, 80, str(k + 1), F("Black", 150), WHITE, 130)
        L = shadowed(L)
        sh = 9 * math.sin(t * 40) if (k == 2 and t > dur * 0.45) else 0
        place(fr, L, x + sh, 900, a, min(1, a))
        if k == 2 and a > 0: place(fr, lock(0.8), x + sh, 905, a, 1, sh)
    if t > dur * 0.45 and s.get("label", "¿EL TERCERO?"):
        L, d = layer(W, 110); ctext(d, 10, s.get("label", "¿EL TERCERO?"), F("Black", 80), ORANGE, stroke=5)
        place(fr, L, W / 2, 1200, back((t - dur * 0.45) / 0.3), 1)
    return 0

def loading(L, d, w, h, t):
    d.rounded_rectangle([40, 100, w - 40, 124], 12, fill=(222, 226, 238))
    d.rounded_rectangle([40, 100, 40 + (w - 80) * min(0.33, 0.06 + t * 0.07), 124], 12, fill=ORANGE)
    cx, cy, r = w // 2, h // 2 + 30, 90
    a0 = (t * 400) % 360; d.arc([cx - r, cy - r, cx + r, cy + r], a0, a0 + 270, fill=ORANGE, width=18)
    ctext(d, cy + 130, "Cargando...", F("Bold", 40), GREY, cx)
def sc_slow(fr, t, dur, s):
    badge(fr, t, "ERROR 1")
    place(fr, shadowed(browser(820, 640, content=loading, t=t)), W / 2, 760, 0.9 + 0.1 * ease(t / 0.3), ease(t / 0.15))
    L, d = layer(W, 220); secs = 0.4 + t * 1.4
    ctext(d, 10, f"{secs:.1f} s", F("Black", 170), ORANGE, stroke=6)
    place(fr, L, W / 2, 1270, 1, ease((t - 0.2) / 0.2))
    return 0

def sc_leave(fr, t, dur, s):
    place(fr, shadowed(browser(820, 640, content=loading, t=t + 3)), W / 2, 700, 0.8, 0.55)
    L, d = layer(W, 220); ctext(d, 10, f"{4.2 + t * 1.4:.1f} s", F("Black", 120), (255, 122, 26, 150), stroke=4)
    place(fr, L, W / 2, 330, 1, 1)
    for j in range(5):
        st = 0.25 + j * 0.25; k = max(0, t - st); sgn = -1 if j % 2 else 1
        x = 180 + j * 180 + sgn * 900 * ease(k / 1.0) * (k > 0)
        place(fr, person(WHITE if j % 2 else MUTED, 0.9), x, 1180, 1, 1 - ease(k / 1.0) * 0.9)
    headline(fr, t, "SE VAN", 1380, 130, ORANGE, 0.5)
    return 0

def warn(s=1.0):
    L, d = layer(int(360 * s), int(320 * s))
    d.polygon([(180 * s, 0), (360 * s, 320 * s), (0, 320 * s)], fill=ORANGE)
    ctext(d, 100 * s, "!", F("Black", int(190 * s)), WHITE, int(180 * s)); return L
def sc_loop2(fr, t, dur, s):
    sh = 14 * math.sin(t * 50) * max(0, 1 - t / 0.8)
    L, d = layer(W, 420); ctext(d, 10, "#2", F("Black", 360), WHITE, stroke=8)
    place(fr, L, W / 2 + sh, 640, 2 - back(t / 0.3), ease(t / 0.1))
    place(fr, warn(0.9), W / 2 - sh, 1080, back((t - 0.25) / 0.3), 1, sh)
    headline(fr, t, "TODAVÍA PEOR", 1380, 120, ORANGE, 0.5)
    return sh * 0.6

def squeezed(L, d, w, h, t):
    d.rounded_rectangle([18, 70, w - 18, h - 18], 50, fill=(245, 246, 252))
    d.rectangle([18, 110, w + 300, 190], fill=(200, 205, 220)); d.text((40, 128), "MI NEGOCIO  ·  Inicio  ·  Servicios  ·  Contacto  ·  Blog", font=F("Bold", 34), fill=(60, 60, 80))
    for r in range(14): d.rectangle([40, 230 + r * 26, 40 + 700, 240 + r * 26], fill=(200, 203, 214))
    d.rectangle([300, 640, 900, 900], fill=(215, 218, 230)); d.text((320, 700), "Pide presupuesto", font=F("Bold", 50), fill=(140, 140, 160))
def sc_mobile(fr, t, dur, s):
    badge(fr, t, "ERROR 2")
    pinch = 1 + 0.05 * math.sin(t * 6)
    place(fr, shadowed(phone(520, 1000, squeezed)), W / 2, 860, (0.9 + 0.1 * ease(t / 0.3)) * pinch, ease(t / 0.15))
    if t > dur * 0.45:
        k = (t - dur * 0.45)
        L, d = layer(500, 500); d.line([60, 60, 440, 440], fill=ORANGE, width=70); d.line([440, 60, 60, 440], fill=ORANGE, width=70)
        place(fr, L, W / 2, 860, 2 - back(k / 0.25), ease(k / 0.08))
        headline(fr, t, "SE VE FATAL", 1440, 120, WHITE, dur * 0.45 + 0.1)
    return 18 * max(0, 1 - abs(t - dur * 0.45 - 0.05) / 0.25) if t > dur * 0.45 else 0

def sc_loop3(fr, t, dur, s):
    sh = 12 * math.sin(t * 45)
    L, d = layer(330, 380); d.rounded_rectangle([0, 0, 329, 379], 40, fill=NAVY_CARD, outline=ORANGE, width=8)
    place(fr, shadowed(L), W / 2 + sh, 700, back(t / 0.3), 1); place(fr, lock(1.1), W / 2 + sh, 705, back(t / 0.3), 1, sh * 0.5)
    for j in range(9):
        st = 0.35 + j * 0.12; k = t - st
        if k <= 0: continue
        x = W / 2 + (j - 4) * 70 + (j - 4) * 140 * k; y = 900 + 900 * k * k + 250 * k
        place(fr, coin(1.0), x, y, 1, max(0, 1 - k / 1.6), j * 40 * k)
    headline(fr, t, "MÁS DINERO TE CUESTA", 1420, 96, ORANGE, dur * 0.4)
    return 0

def page_nobutton(L, d, w, h, t):
    d.text((40, 100), "TU NEGOCIO", font=F("Black", 40), fill=(30, 30, 50))
    d.rounded_rectangle([40, 170, w - 40, 400], 22, fill=(220, 225, 240))
    for r in range(7): d.rectangle([40, 440 + r * 34, 40 + (r * 131) % 400 + 260, 456 + r * 34], fill=(205, 208, 220))
def sc_nobutton(fr, t, dur, s):
    badge(fr, t, "ERROR 3")
    bx, by = W / 2, 820
    place(fr, shadowed(browser(860, 760, content=page_nobutton)), bx, by, 0.9 + 0.1 * ease(t / 0.3), ease(t / 0.15))
    pts = [(300, 600), (800, 650), (650, 1000), (300, 1050), (780, 900), (540, 760)]
    u = min(t / max(dur, 0.1) * (len(pts) - 1), len(pts) - 1.001); i = int(u); f = u - i
    f = f * f * (3 - 2 * f)
    cx = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f; cy = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f
    for q in range(int(u) + 1):
        L, d = layer(120, 140); ctext(d, 0, "?", F("Black", 120), ORANGE, 60, stroke=6)
        place(fr, L, pts[q][0] + 50, pts[q][1] - 90, back((u - q) / 0.4), 1)
    place(fr, cursor(1.2), cx + 30, cy + 45)
    headline(fr, t, "¿DÓNDE ESCRIBO?", 1380, 100, WHITE, dur * 0.35)
    return 0

def shop(name, lit):
    L, d = layer(380, 420); col = ORANGE if lit else (60, 70, 95)
    d.polygon([(0, 120), (190, 0), (380, 120)], fill=col)
    d.rounded_rectangle([20, 120, 360, 420], 20, fill=NAVY_CARD if lit else (30, 38, 60), outline=col, width=6)
    d.rounded_rectangle([140, 260, 240, 420], 12, fill=col)
    f = F("Black", 34 if len(name) > 10 else 40); ctext(d, 160, name, f, WHITE if lit else GREY, 190)
    return L
def bubble(txt, col=ORANGE):
    f = F("Black", 50); L, d = layer(int(d0.textlength(txt, font=f)) + 80, 140)
    d.rounded_rectangle([0, 0, L.width - 1, 110], 50, fill=col); d.polygon([(30, 100), (70, 100), (20, 138)], fill=col)
    d.text((40, 24), txt, font=f, fill=WHITE); return L
d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
def sc_competitor(fr, t, dur, s):
    mid = dur * 0.45; lit = t > mid + 0.35
    place(fr, shadowed(shop("TU NEGOCIO", False)), 290, 620, back(t / 0.3), 1 - 0.5 * ease((t - mid) / 0.3))
    place(fr, shadowed(shop("COMPETENCIA", lit)), 790, 620, back((t - 0.1) / 0.3), 1)
    if lit:
        gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse([560, 380, 1020, 860], fill=ORANGE + (90,))
        fr.alpha_composite(gl.filter(ImageFilter.GaussianBlur(80)))
    place(fr, person(WHITE, 1.3), W / 2, 1230, back((t - 0.15) / 0.3), 1)
    k = (t - mid) / 0.4
    if 0 < k:
        k = min(k, 1); x = W / 2 + (790 - W / 2) * ease(k); y = 1060 - 380 * math.sin(math.pi * min(k, 1) / 2) * 1.0
        if k >= 1: y = 820
        place(fr, bubble("Hola!"), x, y, 1, 1)
    headline(fr, t, "EN UN CLIC", 1450, 110, ORANGE, 0.2)
    return 0

def sc_fix(fr, t, dur, s):
    L, d = layer(W, 220); fo = F("Black", 150); ow = d.textlength("Obra", font=fo); tw = ow + d.textlength("Web", font=fo)
    d.text(((W - tw) / 2, 20), "Obra", font=fo, fill=WHITE); d.text(((W - tw) / 2 + ow, 20), "Web", font=fo, fill=ORANGE)
    place(fr, L, W / 2, 330, back(t / 0.3), 1)
    items = ["Carga rápida", "Perfecta en el móvil", "Botón para escribirte"]
    for k, it in enumerate(items):
        st = 0.2 + k * dur * 0.22; a = back((t - st) / 0.3)
        if t < st: continue
        R, d = layer(900, 170); d.rounded_rectangle([0, 0, 899, 169], 40, fill=NAVY_CARD, outline=(44, 70, 130), width=3)
        d.ellipse([40, 40, 130, 130], fill=ORANGE)
        ck = ease((t - st - 0.12) / 0.2)
        if ck > 0: d.line([(62, 86), (80, 105), (62 + 48 * ck, 105 - 39 * ck)][:2 if ck < 0.5 else 3], fill=WHITE, width=12)
        d.text((170, 52), it, font=F("Bold", 54), fill=WHITE)
        place(fr, shadowed(R, 18, 90), W / 2 + 220 * (1 - min(1, a)), 640 + k * 210, 1, min(1, a))
    return 0

def sc_price(fr, t, dur, s):
    L, d = layer(W, 120); ctext(d, 10, "2 cuotas de", F("Bold", 84), MUTED)
    place(fr, L, W / 2, 520, back(t / 0.3), 1)
    st = dur * 0.4
    if t > st:
        P, d = layer(W, 420); ctext(d, 30, "135€", F("Black", 340), ORANGE, stroke=8)
        place(fr, P.filter(ImageFilter.GaussianBlur(40)), W / 2, 860, 2.2 - 1.2 * back((t - st) / 0.3), 0.8)
        place(fr, P, W / 2, 860, 2.2 - 1.2 * back((t - st) / 0.3), ease((t - st) / 0.08))
        N, d = layer(W, 90); ctext(d, 10, "270 € en total", F("Medium", 50), MUTED)
        place(fr, N, W / 2, 1150, 1, ease((t - st - 0.3) / 0.3))
        return 22 * max(0, 1 - (t - st) / 0.3)
    return 0

def chat(L, d, w, h, t):
    d.rectangle([12, 70, w - 12, 170], fill=(18, 30, 64)); d.ellipse([40, 90, 100, 150], fill=ORANGE)
    d.text((120, 98), "ObraWeb", font=F("Bold", 40), fill=WHITE)
    d.rounded_rectangle([30, h - 120, w - 30, h - 40], 40, fill=(30, 44, 84))
    typed = "WEB"[: int(max(0, t - 0.2) * 8)]
    if t < 0.9: d.text((70, h - 106), typed + ("|" if int(t * 4) % 2 else ""), font=F("Bold", 44), fill=WHITE)
def sc_dm(fr, t, dur, s):
    headline(fr, t, "ESCRÍBENOS «WEB»", 300, 104, WHITE)
    px, py = W / 2, 930
    place(fr, shadowed(phone(560, 980, chat, t)), px, py, back(t / 0.3), 1)
    if t > 0.9:
        k = t - 0.9; L, d = layer(240, 110); d.rounded_rectangle([0, 0, 239, 109], 50, fill=ORANGE); ctext(d, 20, "WEB", F("Black", 60), WHITE, 120)
        place(fr, L, px + 120, py + 300 - 420 * ease(k / 0.35), 1, 1)
    if t > 1.5:
        k = t - 1.5; L, d = layer(420, 110); d.rounded_rectangle([0, 0, 419, 109], 50, fill=(40, 60, 110))
        d.text((36, 26), "¡Hola! Vamos a ello", font=F("Bold", 42), fill=WHITE)
        place(fr, L, px - 30, py + 20, back(k / 0.3), 1)
    return 0

# ---- planos del reel "¿y si te cierran Instagram?" ----
def notif(txt, sub):
    L, d = layer(900, 170); d.rounded_rectangle([0, 0, 899, 169], 40, fill=(250, 250, 252))
    d.ellipse([30, 40, 120, 130], fill=ORANGE); ctext(d, 52, "!", F("Black", 64), WHITE, 75)
    d.text((150, 34), txt, font=F("Black", 44), fill=(20, 20, 40)); d.text((150, 98), sub, font=F("Medium", 30), fill=(110, 110, 130))
    return shadowed(L, 20, 110)
def sc_suspended(fr, t, dur, s):
    items = [("Cuenta suspendida", "Tu cuenta incumple las normas"), ("Acceso bloqueado", "No puedes iniciar sesión"),
             ("Cuenta desactivada", "Tus seguidores ya no te ven")]
    sh = 0
    for k, (a, b) in enumerate(items):
        st = 0.05 + k * dur * 0.28
        if t < st: continue
        p = back((t - st) / 0.25); sh = 16 * max(0, 1 - (t - st) / 0.2)
        place(fr, notif(a, b), W / 2, 520 + k * 230, p, 1, (-3, 2, -2)[k])
    headline(fr, t, "PASA MÁS DE LO QUE CREES", 1340, 84, ORANGE, dur * 0.4)
    return sh
def sc_secret(fr, t, dur, s):
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = 520 + 60 * math.sin(t * 5)
    ImageDraw.Draw(gl).ellipse([W / 2 - g / 2, 800 - g / 2, W / 2 + g / 2, 800 + g / 2], fill=ORANGE + (120,))
    fr.alpha_composite(gl.filter(ImageFilter.GaussianBlur(90)))
    L, d = layer(360, 400); d.rounded_rectangle([0, 0, 359, 399], 44, fill=NAVY_CARD, outline=ORANGE, width=8)
    ctext(d, 90, "?", F("Black", 230), WHITE, 180)
    place(fr, shadowed(L), W / 2, 800, back(t / 0.3), 1, 4 * math.sin(t * 9))
    h1, h2 = s.get("h", ["NADIE TE LO", "PUEDE QUITAR"])
    headline(fr, t, h1, 1210, 104, WHITE, 0.35); headline(fr, t, h2, 1330, 104, ORANGE, 0.5)
    return 0
def own_site(L, d, w, h, t):
    d.text((40, 100), "TU NEGOCIO", font=F("Black", 40), fill=(20, 20, 40))
    d.rounded_rectangle([40, 170, w - 40, 420], 26, fill=ORANGE)
    d.text((80, 205), "Pide tu cita", font=F("Black", 64), fill=WHITE); d.text((80, 285), "en un clic", font=F("Black", 64), fill=WHITE)
    d.rounded_rectangle([80, 365, 330, 405], 20, fill=WHITE)
    for k in range(3): d.rounded_rectangle([40 + k * 255, 450, 270 + k * 255, 600], 20, fill=(225, 228, 240))
def sc_ownweb(fr, t, dur, s):
    place(fr, shadowed(browser(860, 660, content=own_site)), W / 2, 760, 2 - back(t / 0.3), ease(t / 0.1))
    if t > dur * 0.25:
        k = t - dur * 0.25; L, d = layer(600, 200)
        d.rounded_rectangle([10, 10, 589, 189], 30, fill=(6, 16, 40, 200), outline=ORANGE, width=14); ctext(d, 38, "100% TUYA", F("Black", 104), ORANGE, 300)
        place(fr, L, W / 2, 1120, 1.8 - 0.8 * back(k / 0.15), ease(k / 0.05), -6)
        return 20 * max(0, 1 - k / 0.2)
    return 0
def sc_yours(fr, t, dur, s):
    labels = ["TU WEB", "TUS CLIENTES", "TUS REGLAS"]
    for k, lab in enumerate(labels):
        st = s["pin"] + k * s["vd"] / 3
        if t < st: continue
        a = back((t - st) / 0.25); y = 520 + k * 330
        L, d = layer(900, 280); d.rounded_rectangle([0, 0, 899, 279], 44, fill=NAVY_CARD, outline=(44, 70, 130), width=4)
        if k == 0:
            d.rounded_rectangle([50, 70, 250, 210], 16, fill=WHITE); d.rectangle([50, 70, 250, 100], fill=(222, 226, 238)); d.rounded_rectangle([70, 120, 230, 170], 10, fill=ORANGE)
        elif k == 1:
            for j in range(3): L.alpha_composite(person(WHITE if j != 1 else ORANGE, 0.75), (40 + j * 75, 55))
        else:
            d.ellipse([70, 60, 230, 220], fill=ORANGE); d.line([(110, 140), (140, 172), (195, 110)], fill=WHITE, width=18)
        d.text((300, 95), lab, font=F("Black", 74), fill=WHITE)
        place(fr, shadowed(L, 20, 90), W / 2 - 300 * (1 - min(1, a)), y, 1, min(1, a))
    return 0
def sc_pricetease(fr, t, dur, s):
    sh = 10 * math.sin(t * 40)
    L, d = layer(560, 340)
    d.polygon([(0, 170), (110, 0), (559, 0), (559, 339), (110, 339)], fill=ORANGE)
    d.ellipse([70, 145, 110, 185], fill=(6, 16, 40)); ctext(d, 70, "? €", F("Black", 170), WHITE, 340)
    place(fr, shadowed(L), W / 2 + sh, 820, back(t / 0.3), 1, -8 + sh * 0.4)
    headline(fr, t, "LO MEJOR:", 420, 110, WHITE, 0.0); headline(fr, t, "LO QUE CUESTA", 1220, 110, ORANGE, dur * 0.35)
    return 0

def sc_logo(fr, t, dur, s):
    L, d = layer(W, 300); fo = F("Black", 190); ow = d.textlength("Obra", font=fo); tw = ow + d.textlength("Web", font=fo)
    d.text(((W - tw) / 2, 30), "Obra", font=fo, fill=WHITE); d.text(((W - tw) / 2 + ow, 30), "Web", font=fo, fill=ORANGE)
    place(fr, L.filter(ImageFilter.GaussianBlur(40)), W / 2, 720, 2 - back(t / 0.3), 0.7); place(fr, L, W / 2, 720, 2 - back(t / 0.3), ease(t / 0.08))
    k = t - dur * 0.45
    if k > 0:
        x0, x1 = 160, 160 + 760 * ease(k / 0.6)
        Lb, d = layer(W, 120); d.rounded_rectangle([160, 40, 920, 80], 20, fill=(30, 50, 100)); d.rounded_rectangle([160, 40, x1, 80], 20, fill=ORANGE)
        place(fr, Lb, W / 2, 1000, 1, 1)
    headline(fr, t, s.get("tag", "DE PRINCIPIO A FIN"), 1180, 96, WHITE, dur * 0.45)
    return 20 * max(0, 1 - t / 0.25)

# ---- planos del reel "11 de la noche" ----
def clock_face(hh, mm, s=1.0, col=WHITE):
    L, d = layer(int(320 * s), int(320 * s)); r = 150 * s; c = 160 * s
    d.ellipse([c - r, c - r, c + r, c + r], fill=NAVY_CARD, outline=col, width=int(14 * s))
    for k in range(12):
        a = k * math.pi / 6; d.line([c + math.sin(a) * r * 0.8, c - math.cos(a) * r * 0.8, c + math.sin(a) * r * 0.92, c - math.cos(a) * r * 0.92], fill=MUTED, width=int(6 * s))
    ah = (hh % 12 + mm / 60) * math.pi / 6; am = mm * math.pi / 30
    d.line([c, c, c + math.sin(ah) * r * 0.5, c - math.cos(ah) * r * 0.5], fill=WHITE, width=int(14 * s))
    d.line([c, c, c + math.sin(am) * r * 0.78, c - math.cos(am) * r * 0.78], fill=ORANGE, width=int(9 * s))
    d.ellipse([c - 14 * s, c - 14 * s, c + 14 * s, c + 14 * s], fill=ORANGE); return L
def store(name, lit, shutter=0.0):
    L, d = layer(520, 560); col = ORANGE if lit else (60, 70, 95)
    d.rounded_rectangle([0, 0, 519, 130], 26, fill=col); ctext(d, 34, name, F("Black", 56 if len(name) < 12 else 44), WHITE if lit else GREY, 260)
    d.rectangle([20, 130, 499, 559], fill=NAVY_CARD if lit else (24, 30, 50))
    d.rectangle([60, 180, 460, 559], fill=(255, 210, 150) if lit else (40, 48, 72))
    if shutter > 0:
        hgt = int(380 * shutter)
        d.rectangle([60, 180, 460, 180 + hgt], fill=(110, 118, 140))
        for y in range(180, 180 + hgt, 26): d.line([60, y, 460, y], fill=(80, 88, 110), width=6)
    return L
def sc_clock(fr, t, dur, s):
    place(fr, shadowed(store("TU NEGOCIO", False, ease(t / 0.6))), W / 2, 980, back(t / 0.3), 1)
    place(fr, shadowed(clock_face(23, 0, 1.0)), W / 2, 470, back((t - 0.1) / 0.3), 1)
    headline(fr, t, s.get("h", "CERRADO"), 1420, 120, ORANGE, dur * 0.3)
    return 0
def sc_nightsearch(fr, t, dur, s):
    def c(L, d, w, h, tt):
        d.rounded_rectangle([18, 70, w - 18, h - 18], 50, fill=(20, 26, 48))
        d.rounded_rectangle([40, 120, w - 40, 200], 40, fill=(40, 50, 84))
        q = s.get("query", "fontanero urgente")[: int(max(0, tt - 0.1) * 22)]
        d.text((80, 140), q + ("|" if int(tt * 4) % 2 else ""), font=F("Medium", 38), fill=WHITE)
        d.text((w - 140, 90 - 60), "23:04", font=F("Bold", 30), fill=MUTED)
    place(fr, shadowed(phone(520, 900, c, t)), W / 2, 820, back(t / 0.3), 1)
    if t > dur * 0.45:
        L, d = layer(W, 260); ctext(d, 0, "?", F("Black", 220), ORANGE, stroke=6)
        place(fr, L, W / 2 + 260, 520, back((t - dur * 0.45) / 0.3), 1, 8 * math.sin(t * 20))
    headline(fr, t, s.get("h", "¿TE COMPRA O NO?"), 1420, 104, WHITE, dur * 0.5)
    return 0
def sc_other(fr, t, dur, s):
    mid = dur * 0.35
    place(fr, shadowed(store("TU NEGOCIO", False, 1.0)), 290, 760, 0.85, 1)
    place(fr, shadowed(store("OTRO", t > mid)), 790, 760, 0.85, 1)
    if t > mid:
        gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse([560, 480, 1020, 1040], fill=ORANGE + (90,))
        fr.alpha_composite(gl.filter(ImageFilter.GaussianBlur(80)))
    k = max(0, t - mid * 0.6)
    place(fr, person(WHITE, 1.2), W / 2 + 260 * ease(k / 1.0), 1220 - 120 * ease(k / 1.0), 1, 1 - 0.6 * ease((k - 0.8) / 0.4))
    headline(fr, t, s.get("h", "SE VA CON OTRO"), 1440, 110, ORANGE, mid)
    return 0
def sc_nightweb(fr, t, dur, s):
    v = s["vd"]; p0 = s["pin"]
    def c(L, d, w, h, tt):
        d.rounded_rectangle([18, 70, w - 18, h - 18], 50, fill=(245, 246, 252))
        d.text((50, 100), "TU NEGOCIO", font=F("Black", 36), fill=(20, 20, 40))
        if tt > p0:
            d.rounded_rectangle([40, 160, w - 40, 330], 24, fill=ORANGE); d.text((70, 200), "Servicios", font=F("Black", 50), fill=WHITE)
            d.text((70, 262), "Urgencias · Instalaciones", font=F("Medium", 28), fill=WHITE)
        if tt > p0 + v * 0.35:
            cols = [(255, 180, 120), (90, 130, 220), (255, 210, 160), (60, 90, 170)]
            for k in range(4): d.rounded_rectangle([40 + (k % 2) * 225, 350 + (k // 2) * 170, 250 + (k % 2) * 225, 505 + (k // 2) * 170], 18, fill=cols[k])
        if tt > p0 + v * 0.65:
            d.rounded_rectangle([40, h - 200, w - 40, h - 60], 40, fill=(40, 200, 110)); ctext(d, h - 162, "Escribir ahora", F("Black", 44), WHITE, w // 2)
    place(fr, shadowed(phone(520, 1000, c, t)), W / 2 - 80, 860, back(t / 0.3), 1)
    if t > p0 + v * 0.75:
        k = t - p0 - v * 0.75; L, d = layer(460, 120); d.rounded_rectangle([0, 0, 459, 119], 50, fill=ORANGE)
        d.text((36, 30), "¿Mañana a las 10?", font=F("Bold", 44), fill=WHITE)
        place(fr, L, W / 2 + 190, 420 - 60 * ease(k / 0.3), back(k / 0.3), 1)
    return 0
def sc_morning(fr, t, dur, s):
    sun = Image.new("RGBA", (W, H), (0, 0, 0, 0)); r = 260; cy = 1100 - 250 * ease(t / 1.2)
    ImageDraw.Draw(sun).ellipse([W / 2 - r, cy - r, W / 2 + r, cy + r], fill=ORANGE + (110,))
    fr.alpha_composite(sun.filter(ImageFilter.GaussianBlur(90)))
    place(fr, shadowed(clock_face(8, 0, 1.1, ORANGE)), W / 2, 560, back(t / 0.3), 1, 6 * math.sin(t * 40) * max(0, 1 - t / 0.6))
    if t > dur * 0.4:
        k = t - dur * 0.4; L, d = layer(900, 170); d.rounded_rectangle([0, 0, 899, 169], 40, fill=(250, 250, 252))
        d.ellipse([30, 40, 120, 130], fill=ORANGE); ctext(d, 52, "1", F("Black", 64), WHITE, 75)
        n1, n2 = s.get("notif", ["Nuevo cliente", "Te escribió a las 23:06"])
        d.text((150, 34), n1, font=F("Black", 46), fill=(20, 20, 40)); d.text((150, 98), n2, font=F("Medium", 30), fill=(110, 110, 130))
        place(fr, shadowed(L, 20, 110), W / 2, 1000 - 60 * ease(k / 0.3), back(k / 0.3), 1)
    headline(fr, t, s.get("h", "CLIENTE NUEVO"), 1400, 116, ORANGE, dur * 0.5)
    return 0

# ---- planos del reel "tarjeta de visita" ----
def bin_icon(s=1.0):
    L, d = layer(int(360 * s), int(420 * s))
    d.rounded_rectangle([10 * s, 0, 350 * s, 60 * s], int(20 * s), fill=(90, 100, 130))
    d.polygon([(40 * s, 70 * s), (320 * s, 70 * s), (290 * s, 420 * s), (70 * s, 420 * s)], fill=(60, 70, 100))
    for k in range(4): d.line([(100 + k * 55) * s, 110 * s, (105 + k * 50) * s, 380 * s], fill=(40, 48, 75), width=int(14 * s))
    return L
def sc_trash(fr, t, dur, s):
    place(fr, shadowed(bin_icon(1.0)), W / 2, 1060, back(t / 0.3), 1)
    k = min(1.0, t / max(0.6, dur * 0.6))
    card = biz_card().resize((410, 260))
    if k < 1: place(fr, card, W / 2 + 160 * (1 - k), 420 + 560 * k * k, 1 - 0.5 * k, 1, 300 * k)
    headline(fr, t, "A LA BASURA", 1420, 116, ORANGE, dur * 0.5)
    return 10 * max(0, 1 - abs(k - 1) * 5) if k >= 0.95 else 0
def sc_phonepop(fr, t, dur, s):
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = 640 + 40 * math.sin(t * 6)
    ImageDraw.Draw(gl).ellipse([W / 2 - g / 2, 860 - g / 2, W / 2 + g / 2, 860 + g / 2], fill=ORANGE + (110,))
    fr.alpha_composite(gl.filter(ImageFilter.GaussianBlur(90)))
    def c(L, d, w, h, tt):
        d.rounded_rectangle([18, 70, w - 18, h - 18], 50, fill=(20, 26, 48))
        ctext(d, h // 2 - 60, "12:30", F("Black", 110), WHITE, w // 2)
    place(fr, shadowed(phone(460, 880, c, t)), W / 2, 860, 2 - back(t / 0.3), ease(t / 0.08), -4)
    headline(fr, t, "SU MÓVIL", 1420, 130, ORANGE, 0.1)
    return 18 * max(0, 1 - t / 0.25)
def qr_code(size=420):
    L, d = layer(size, size); d.rounded_rectangle([0, 0, size - 1, size - 1], 30, fill=WHITE)
    n = 21; m = 30; cell = (size - 2 * m) / n; rg = np.random.default_rng(11)
    for y in range(n):
        for x in range(n):
            finder = (x < 7 and y < 7) or (x >= n - 7 and y < 7) or (x < 7 and y >= n - 7)
            if finder:
                fx, fy = x % 14 if x < 7 else x - (n - 7), y if y < 7 else y - (n - 7)
                on = fx in (0, 6) or fy in (0, 6) or (2 <= fx <= 4 and 2 <= fy <= 4)
            else:
                on = rg.random() < 0.5
            if on: d.rectangle([m + x * cell, m + y * cell, m + (x + 1) * cell, m + (y + 1) * cell], fill=(10, 16, 40))
    return L
def sc_qr(fr, t, dur, s):
    place(fr, shadowed(qr_code(360)), W / 2, 470, back(t / 0.3), 1)
    if t > 0.3:
        k = (t - 0.3) % 0.9 / 0.9; L, d = layer(500, 20); d.rounded_rectangle([0, 0, 499, 19], 10, fill=ORANGE + (220,))
        place(fr, L.resize((420, 20)), W / 2, 320 + 300 * k, 1, 1)
    def c(L, d, w, h, tt):
        d.rounded_rectangle([18, 70, w - 18, h - 18], 50, fill=(245, 246, 252))
        if tt > dur * 0.55:
            d.text((44, 96), "TU NEGOCIO", font=F("Black", 32), fill=(20, 20, 40))
            d.rounded_rectangle([36, 150, w - 36, 300], 22, fill=ORANGE); d.text((60, 190), "Bienvenido", font=F("Black", 42), fill=WHITE)
        else:
            ctext(d, h // 2 - 30, "Escaneando...", F("Bold", 34), GREY, w // 2)
    place(fr, shadowed(phone(340, 560, c, t)), W / 2, 1000, back((t - 0.15) / 0.3), 1)
    headline(fr, t, "1 SEGUNDO", 1420, 110, ORANGE, dur * 0.55)
    return 0
def sc_showcase(fr, t, dur, s):
    labels = s.get("labels", ["TUS TRABAJOS", "TUS OPINIONES", "TE ESCRIBEN"])
    for k, lab in enumerate(labels):
        st = s["pin"] + k * s["vd"] / 3
        if t < st: continue
        a = back((t - st) / 0.25); y = 520 + k * 330
        L, d = layer(900, 280); d.rounded_rectangle([0, 0, 899, 279], 44, fill=NAVY_CARD, outline=(44, 70, 130), width=4)
        icon = s.get("icons", ["photos", "stars", "chat"])[k]
        if icon == "magnet":
            d.arc([60, 50, 230, 220], 0, 180, fill=(230, 40, 50), width=46); d.rectangle([60, 100, 106, 140], fill=(230, 40, 50)); d.rectangle([184, 100, 230, 140], fill=(230, 40, 50))
            d.rectangle([60, 80, 106, 108], fill=(200, 205, 220)); d.rectangle([184, 80, 230, 108], fill=(200, 205, 220))
        elif icon == "calendar":
            d.rounded_rectangle([60, 60, 240, 230], 18, fill=WHITE); d.rounded_rectangle([60, 60, 240, 110], 18, fill=ORANGE); d.rectangle([60, 90, 240, 110], fill=ORANGE)
            d.line([(110, 170), (140, 200), (195, 135)], fill=(40, 200, 110), width=16)
        elif k == 0 and icon == "photos":
            cols = [(255, 160, 90), (90, 130, 220), (255, 200, 150), (60, 90, 170)]
            for j in range(4): d.rounded_rectangle([40 + (j % 2) * 110, 50 + (j // 2) * 95, 140 + (j % 2) * 110, 135 + (j // 2) * 95], 12, fill=cols[j])
        elif icon == "stars":
            for j in range(5):
                cx, cy, r = 60 + j * 48, 140, 22
                pts = [(cx + r * math.cos(math.pi / 2 + i * math.pi / 5) * (1 if i % 2 == 0 else 0.45), cy - r * math.sin(math.pi / 2 + i * math.pi / 5) * (1 if i % 2 == 0 else 0.45)) for i in range(10)]
                d.polygon(pts, fill=ORANGE)
        elif icon == "chat":
            d.rounded_rectangle([40, 90, 250, 190], 46, fill=ORANGE); d.polygon([(70, 180), (110, 180), (60, 225)], fill=ORANGE)
            d.text((80, 115), "Hola!", font=F("Black", 44), fill=WHITE)
        fl = F("Black", 68)
        while d.textlength(lab, font=fl) > 560: fl = F("Black", fl.size - 3)
        d.text((300, 140 - fl.size * 0.62), lab, font=fl, fill=WHITE)
        place(fr, shadowed(L, 20, 90), W / 2 - 300 * (1 - min(1, a)), y, 1, min(1, a))
    return 0

# ---- planos del reel "3 segundos" ----
def sc_countdown(fr, t, dur, s):
    k = min(2, int(t / (dur / 3))); num = 3 - k; lt = t - k * dur / 3
    L, d = layer(W, 560); ctext(d, 0, str(num), F("Black", 520), ORANGE if num == 1 else WHITE, stroke=10)
    place(fr, L, W / 2, 780, 1.6 - 0.6 * back(lt / 0.2), ease(lt / 0.06))
    headline(fr, t, "Y DECIDE", 1400, 120, ORANGE, dur * 0.4)
    return 14 * max(0, 1 - lt / 0.15)
def sc_photos(fr, t, dur, s):
    badge(fr, t, "COSA 1")
    def c(L, d, w, h, tt):
        d.text((40, 96), "NUESTROS TRABAJOS", font=F("Black", 34), fill=(20, 20, 40))
        cols = [(255, 160, 90), (90, 130, 220), (255, 200, 150), (60, 90, 170), (255, 122, 26), (150, 175, 230)]
        for k in range(6):
            if tt > 0.15 + k * 0.12:
                x, y = 40 + (k % 3) * 255, 160 + (k // 3) * 230
                d.rounded_rectangle([x, y, x + 235, y + 210], 18, fill=cols[k])
                d.polygon([(x + 30, y + 180), (x + 100, y + 90), (x + 160, y + 180)], fill=(255, 255, 255, 120)); d.ellipse([x + 160, y + 40, x + 200, y + 80], fill=(255, 255, 255, 150))
    place(fr, shadowed(browser(860, 680, content=c, t=t)), W / 2, 820, back(t / 0.3), 1)
    headline(fr, t, "FOTOS REALES", 1400, 120, ORANGE, dur * 0.4)
    return 0
def sc_goodmobile(fr, t, dur, s):
    badge(fr, t, "COSA 2")
    def c(L, d, w, h, tt):
        d.rounded_rectangle([18, 70, w - 18, h - 18], 50, fill=(245, 246, 252))
        d.text((44, 100), "TU NEGOCIO", font=F("Black", 34), fill=(20, 20, 40))
        d.rounded_rectangle([36, 160, w - 36, 360], 24, fill=ORANGE); d.text((64, 200), "Lo que", font=F("Black", 54), fill=WHITE); d.text((64, 264), "necesitas", font=F("Black", 54), fill=WHITE)
        for k in range(3): d.rounded_rectangle([36, 390 + k * 130, w - 36, 500 + k * 130], 20, fill=(225, 228, 240))
    place(fr, shadowed(phone(480, 940, c, t)), W / 2, 830, back(t / 0.3), 1)
    if t > dur * 0.5:
        k = t - dur * 0.5; L, d = layer(200, 200); d.ellipse([0, 0, 199, 199], fill=ORANGE); d.line([(50, 100), (88, 140), (152, 66)], fill=WHITE, width=24)
        place(fr, L, W / 2 + 250, 560, back(k / 0.25), 1)
    headline(fr, t, "SIN HACER ZOOM", 1420, 110, WHITE, dur * 0.4)
    return 0
def sc_button(fr, t, dur, s):
    badge(fr, t, "COSA 3")
    L, d = layer(800, 200); d.rounded_rectangle([0, 0, 799, 199], 100, fill=(40, 200, 110)); ctext(d, 52, "Escribir ahora", F("Black", 80), WHITE, 400)
    press = 0.92 if (dur * 0.6 < t < dur * 0.6 + 0.15) else 1.0
    place(fr, shadowed(L), W / 2, 800, back(t / 0.3) * press, 1)
    if t > dur * 0.6:
        k = t - dur * 0.6; r = 120 + 500 * ease(k / 0.5)
        R, d = layer(W, H); d.ellipse([W / 2 - r, 800 - r * 0.45, W / 2 + r, 800 + r * 0.45], outline=(255, 255, 255, int(200 * max(0, 1 - k / 0.5))), width=10)
        fr.alpha_composite(R)
    cx = W / 2 + 330 - 200 * ease(t / (dur * 0.6)); cy = 1100 - 240 * ease(t / (dur * 0.6))
    place(fr, cursor(1.4), cx, cy)
    headline(fr, t, "LA QUE MÁS SE OLVIDA", 1420, 90, ORANGE, 0.1)
    return 0

# ---- planos del reel "¿cuándo entraste en tu web?" ----
def sc_visitors(fr, t, dur, s):
    place(fr, shadowed(browser(820, 560, content=own_site)), W / 2, 640, back(t / 0.3), 1)
    n = int(1 + 46 * ease(t / dur)); L, d = layer(W, 200)
    ctext(d, 10, f"{n} visitas hoy", F("Black", 96), ORANGE, stroke=5)
    place(fr, L, W / 2, 1060, 1, ease(t / 0.2))
    for j in range(5):
        st = 0.1 + j * dur * 0.15; k = t - st
        if k <= 0: continue
        x = -100 + (W / 2 - 300 + j * 150 + 100) * ease(k / 0.5)
        place(fr, person(WHITE if j % 2 else MUTED, 0.75), x, 1300, 1, 1)
    return 0
def sc_brokenlist(fr, t, dur, s):
    place(fr, shadowed(browser(860, 620, content=own_site)), W / 2, 600, 1, 0.5)
    items = [("Horario de 2019", "Ya no abres a esas horas"), ("Teléfono antiguo", "Nadie contesta"), ("Enlace roto", "Error 404")]
    sh = 0
    for k, (a, b) in enumerate(items):
        st = s["pin"] + k * s["vd"] / 3
        if t < st: continue
        p = back((t - st) / 0.25); sh = 14 * max(0, 1 - (t - st) / 0.2)
        L, d = layer(900, 170); d.rounded_rectangle([0, 0, 899, 169], 40, fill=(250, 250, 252))
        d.ellipse([30, 40, 120, 130], fill=(200, 30, 40)); d.line([55, 65, 95, 105], fill=WHITE, width=12); d.line([95, 65, 55, 105], fill=WHITE, width=12)
        d.text((150, 34), a, font=F("Black", 46), fill=(20, 20, 40)); d.text((150, 98), b, font=F("Medium", 30), fill=(110, 110, 130))
        place(fr, shadowed(L, 20, 110), W / 2, 820 + k * 210, p, 1, (-2, 2, -1)[k])
    headline(fr, t, "LOS ESPANTA", 1460, 110, ORANGE, dur * 0.6)
    return sh
def sc_silentbell(fr, t, dur, s):
    L, d = layer(420, 460)
    d.pieslice([60, 40, 360, 340], 180, 360, fill=MUTED); d.rectangle([60, 190, 360, 330], fill=MUTED)
    d.rounded_rectangle([20, 320, 400, 370], 20, fill=MUTED); d.ellipse([170, 370, 250, 450], fill=MUTED)
    place(fr, shadowed(L), W / 2, 720, back(t / 0.3), 1, 6 * math.sin(t * 3))
    for k in range(3):
        st = 0.3 + k * 0.3
        if t > st:
            Z, d = layer(140, 140); d.text((10, 0), "z", font=F("Black", 90 - k * 15), fill=WHITE)
            place(fr, Z, W / 2 + 200 + k * 70, 480 - k * 90 - 30 * ((t - st) % 1), 1, 0.9)
    L, d = layer(W, 140); ctext(d, 10, "0 avisos", F("Black", 110), WHITE, stroke=5)
    place(fr, L, W / 2, 1100, 1, ease((t - 0.2) / 0.3))
    headline(fr, t, "NADIE TE AVISA", 1420, 110, ORANGE, dur * 0.45)
    return 0
def sc_inspect(fr, t, dur, s):
    place(fr, shadowed(browser(860, 660, content=own_site)), W / 2, 720, back(t / 0.3), 1)
    k = t / max(dur, 0.1); cx = W / 2 - 250 + 500 * k; cy = 640 + 120 * math.sin(k * math.pi * 2)
    L, d = layer(300, 300); d.ellipse([10, 10, 210, 210], outline=ORANGE, width=22); d.line([180, 180, 280, 280], fill=ORANGE, width=36)
    place(fr, L, cx, cy)
    headline(fr, t, "MÍRALA COMO UN CLIENTE", 1420, 84, ORANGE, 0.2)
    return 0

# ---- planos de la estrategia de retención (revelaciones, chatbot, recompensa DEMO) ----
def sc_notthis(fr, t, dur, s):
    """Tarjetas que se van tachando una a una al ritmo de la voz ("No es por X. Ni por Y.")."""
    items = s.get("items", ["TUS PRECIOS", "TU COMPETENCIA"])
    for k, lab in enumerate(items):
        st = s["pin"] + k * s["vd"] / len(items)
        if t < st: continue
        a = back((t - st) / 0.25); y = 640 + k * 380
        L, d = layer(860, 260); d.rounded_rectangle([0, 0, 859, 259], 44, fill=NAVY_CARD, outline=(44, 70, 130), width=4)
        ctext(d, 80, lab, F("Black", 88), WHITE, 430)
        place(fr, shadowed(L), W / 2, y, a, 1)
        cut = ease((t - st - 0.3) / 0.25)
        if cut > 0:
            X, d = layer(900, 300); d.line([40, 150, 40 + 820 * cut, 150 - 60 * cut], fill=(230, 40, 50), width=26)
            place(fr, X, W / 2, y, 1, 1)
    headline(fr, t, s.get("h", "NO ES ESO"), 300, 120, ORANGE, 0.0)
    return 0
def sc_chatbot(fr, t, dur, s):
    """Chat de WhatsApp-like: cliente pregunta, asistente IA escribe y reserva."""
    msgs = s.get("msgs", ["¿Tenéis hueco mañana?", "¡Sí! Te reservo a las 10:00", "Reserva confirmada"])
    def c(L, d, w, h, tt):
        d.rounded_rectangle([18, 70, w - 18, h - 18], 50, fill=(236, 229, 221))
        d.rectangle([18, 70, w - 18, 170], fill=(18, 36, 78)); d.ellipse([40, 92, 100, 152], fill=ORANGE)
        d.text((120, 92), "Asistente IA", font=F("Bold", 34), fill=WHITE); d.text((120, 132), "en línea · 23:41", font=F("Medium", 24), fill=MUTED)
        T = [0.15, dur * 0.45, dur * 0.7]
        if tt > T[0]:
            d.rounded_rectangle([w - 420, 210, w - 40, 300], 26, fill=(220, 248, 198)); d.text((w - 395, 236), msgs[0], font=F("Medium", 30), fill=(20, 20, 40))
        if T[0] + 0.3 < tt < T[1]:
            for j in range(3):
                yy = 360 + 8 * math.sin(tt * 12 + j); d.ellipse([70 + j * 36, yy, 92 + j * 36, yy + 22], fill=(150, 150, 160))
        if tt > T[1]:
            d.rounded_rectangle([40, 340, 440, 430], 26, fill=WHITE); d.text((64, 366), msgs[1], font=F("Medium", 30), fill=(20, 20, 40))
        if tt > T[2]:
            d.rounded_rectangle([40, 460, 440, 610], 26, fill=WHITE)
            d.rounded_rectangle([64, 486, 416, 586], 18, fill=ORANGE); d.text((90, 520), msgs[2], font=F("Black", 30), fill=WHITE)
    place(fr, shadowed(phone(520, 980, c, t)), W / 2, 830, back(t / 0.3), 1)
    headline(fr, t, s.get("h", "RESPONDE POR TI"), 1440, 108, ORANGE, dur * 0.5)
    return 0
def sc_gift(fr, t, dur, s):
    """Caja de regalo que tiembla y se abre: recompensa por llegar al final."""
    op = ease((t - dur * 0.45) / 0.3); sh = 10 * math.sin(t * 40) * (1 - op)
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = 500 + 300 * op
    ImageDraw.Draw(gl).ellipse([W / 2 - g / 2, 800 - g / 2, W / 2 + g / 2, 800 + g / 2], fill=ORANGE + (int(60 + 80 * op),))
    fr.alpha_composite(gl.filter(ImageFilter.GaussianBlur(90)))
    B, d = layer(460, 360); d.rectangle([0, 0, 459, 359], fill=ORANGE); d.rectangle([200, 0, 260, 359], fill=WHITE)
    place(fr, shadowed(B), W / 2 + sh, 900, back(t / 0.3), 1)
    Lid, d = layer(520, 110); d.rectangle([0, 0, 519, 109], fill=(255, 150, 70)); d.rectangle([230, 0, 290, 109], fill=WHITE)
    place(fr, Lid, W / 2 + sh - 160 * op, 690 - 320 * op, back(t / 0.3), 1, -35 * op)
    if s.get("reveal") and op > 0.3:
        k = (op - 0.3) / 0.7
        place(fr, shadowed(browser(700, 480, url="tunegocio.com", content=own_site)), W / 2, 760 - 160 * ease(k), 0.4 + 0.6 * back(k), 1)
        T, d = layer(620, 120); d.rounded_rectangle([0, 0, 619, 119], 60, fill=ORANGE); ctext(d, 28, s["reveal"], F("Black", 58), WHITE, 310)
        place(fr, T, W / 2, 1000, back((op - 0.6) / 0.4), 1, -5)
    headline(fr, t, s.get("h", "TENGO ALGO PARA TI"), 1440, 104, WHITE, 0.1)
    return 0
def sc_giftpromise(fr, t, dur, s):
    """Promesa temprana: «al final te daré un regalo». Caja cerrada con candado de tiempo."""
    sh = 8 * math.sin(t * 30)
    B, d = layer(420, 330); d.rectangle([0, 0, 419, 329], fill=ORANGE); d.rectangle([185, 0, 235, 329], fill=WHITE)
    place(fr, shadowed(B), W / 2 + sh, 880, back(t / 0.3), 1)
    Lid, d = layer(470, 100); d.rectangle([0, 0, 469, 99], fill=(255, 150, 70)); d.rectangle([210, 0, 260, 99], fill=WHITE)
    place(fr, Lid, W / 2 + sh, 690, back(t / 0.3), 1)
    T, d = layer(520, 110); d.rounded_rectangle([0, 0, 519, 109], 55, fill=NAVY_CARD, outline=ORANGE, width=6); ctext(d, 22, "AL FINAL", F("Black", 60), ORANGE, 260)
    place(fr, T, W / 2, 470, back((t - 0.2) / 0.3), 1, -4)
    headline(fr, t, s.get("h", "TE DARÉ UN REGALO"), 1300, 110, WHITE, 0.15)
    return 0
def sc_steps(fr, t, dur, s):
    """Pasos numerados para conseguir el regalo, cada uno entra cuando la voz lo dice."""
    steps = s.get("steps", [["SÍGUEME", "follow"], ["COMENTA «DEMO»", "comment"]])
    headline(fr, t, s.get("h", "CÓMO CONSEGUIRLA"), 330, 104, WHITE, 0.0)
    marks = s.get("marks", [0.35, 0.68])
    for k, (lab, icon) in enumerate(steps):
        st = s["pin"] + marks[k] * s["vd"] - 0.15
        if t < st: continue
        a = back((t - st) / 0.25); y = 720 + k * 420
        L, d = layer(940, 340); d.rounded_rectangle([0, 0, 939, 339], 50, fill=NAVY_CARD, outline=ORANGE, width=6)
        d.ellipse([40, 110, 160, 230], fill=ORANGE); ctext(d, 120, str(k + 1), F("Black", 90), WHITE, 100)
        d.text((200, 70), lab, font=F("Black", 66), fill=WHITE)
        if icon == "follow":
            on = t > st + 0.6
            d.rounded_rectangle([200, 180, 520, 270], 26, fill=(60, 70, 95) if on else (0, 149, 246)); ctext(d, 196, "Siguiendo" if on else "Seguir", F("Black", 44), WHITE, 360)
        else:
            d.rounded_rectangle([200, 180, 760, 270], 45, fill=(30, 44, 84)); typed = "DEMO"[: int(max(0, t - st - 0.2) * 10)]
            d.text((236, 194), typed, font=F("Black", 48), fill=WHITE); d.rounded_rectangle([620, 190, 750, 260], 35, fill=ORANGE)
            ctext(d, 202, "Enviar", F("Bold", 30), WHITE, 685)
        place(fr, shadowed(L), W / 2 - 280 * (1 - min(1, a)), y, 1, min(1, a))
    return 0
def sc_delivery(fr, t, dur, s):
    """Te llega por mensaje la demo de tu web, gratis y sin compromiso."""
    def c(L, d, w, h, tt):
        d.rounded_rectangle([18, 70, w - 18, h - 18], 50, fill=(20, 26, 48))
        d.rectangle([18, 70, w - 18, 170], fill=(18, 36, 78)); d.ellipse([40, 92, 100, 152], fill=ORANGE); d.text((120, 104), "ObraWeb", font=F("Bold", 36), fill=WHITE)
        if tt > 0.25:
            d.rounded_rectangle([40, 210, w - 60, 300], 26, fill=(40, 60, 110)); d.text((64, 234), "¡Aquí tienes tu demo!", font=F("Bold", 32), fill=WHITE)
        if tt > 0.6:
            d.rounded_rectangle([40, 320, w - 60, 640], 26, fill=(245, 246, 252))
            d.text((64, 340), "TU NEGOCIO", font=F("Black", 28), fill=(20, 20, 40)); d.rounded_rectangle([60, 390, w - 80, 520], 18, fill=ORANGE)
            d.text((84, 430), "Tu web, lista", font=F("Black", 36), fill=WHITE)
            for j in range(3): d.rounded_rectangle([60 + j * 130, 545, 170 + j * 130, 620], 12, fill=(225, 228, 240))
    place(fr, shadowed(phone(520, 900, c, t)), W / 2, 780, back(t / 0.3), 1)
    for k, lab in enumerate(s.get("tags", ["GRATIS", "SIN COMPROMISO"])):
        st = dur * (0.45 + 0.2 * k)
        if t < st: continue
        T, d = layer(560, 110); d.rounded_rectangle([0, 0, 559, 109], 55, fill=ORANGE if k == 0 else WHITE)
        ctext(d, 22, lab, F("Black", 56), WHITE if k == 0 else ORANGE, 280)
        place(fr, T, W / 2 + (-180 if k == 0 else 180), 1310 + k * 140, back((t - st) / 0.25), 1, (-5, 4)[k])
    return 0
def sc_demo(fr, t, dur, s):
    """Comentario 'DEMO' que se escribe y envía, y aparece 'tu web' de demo gratis."""
    L, d = layer(900, 150); d.rounded_rectangle([0, 0, 899, 149], 75, fill=(30, 44, 84))
    d.ellipse([24, 30, 114, 120], fill=(150, 175, 230))
    word = s.get("word", "DEMO"); typed = word[: int(max(0, t - 0.2) * 10)]
    d.text((140, 42), typed + ("|" if t < 0.9 and int(t * 4) % 2 else ""), font=F("Black", 60), fill=WHITE)
    d.rounded_rectangle([720, 30, 870, 120], 45, fill=ORANGE); ctext(d, 52, "Enviar", F("Bold", 34), WHITE, 795)
    place(fr, L, W / 2, 1180 if t < 1.0 else 1180 - 600 * ease((t - 1.0) / 0.3), 1, 1 - ease((t - 1.2) / 0.2) if t > 1.2 else 1)
    if t > 1.2:
        k = t - 1.2
        place(fr, shadowed(browser(820, 600, url="tunegocio.com", content=own_site)), W / 2, 820, back(k / 0.3), 1)
        T, d = layer(560, 120); d.rounded_rectangle([0, 0, 559, 119], 60, fill=ORANGE); ctext(d, 28, "DEMO GRATIS", F("Black", 62), WHITE, 280)
        place(fr, T, W / 2 + 180, 1140, back((k - 0.2) / 0.3), 1, -6)
    headline(fr, t, s.get("h", "COMENTA «DEMO»"), 300, 110, WHITE, 0.0)
    return 0
def sc_follow(fr, t, dur, s):
    """Botón Seguir que se pulsa y pasa a Siguiendo, con el logo de ObraWeb."""
    L, d = layer(W, 220); fo = F("Black", 150); ow = d.textlength("Obra", font=fo); tw = ow + d.textlength("Web", font=fo)
    d.text(((W - tw) / 2, 20), "Obra", font=fo, fill=WHITE); d.text(((W - tw) / 2 + ow, 20), "Web", font=fo, fill=ORANGE)
    place(fr, L, W / 2, 620, back(t / 0.3), 1)
    on = t > dur * 0.45
    B, d = layer(560, 150); d.rounded_rectangle([0, 0, 559, 149], 40, fill=(60, 70, 95) if on else (0, 149, 246))
    ctext(d, 38, "Siguiendo" if on else "Seguir", F("Black", 64), WHITE, 280)
    place(fr, shadowed(B), W / 2, 960, 0.92 if dur * 0.45 < t < dur * 0.45 + 0.12 else 1, 1)
    if not on: place(fr, cursor(1.3), W / 2 + 120 + 80 * (1 - ease(t / (dur * 0.45))), 1040 + 80 * (1 - ease(t / (dur * 0.45))))
    headline(fr, t, s.get("h", "SÍGUEME"), 1300, 120, ORANGE, 0.1)
    return 0

# ---- negocios "literales": lleno de clientes comprando vs. vacío con el dueño y telarañas ----
def shopper(col, s=1.0, bag=False):
    L, d = layer(int(110 * s), int(210 * s))
    d.ellipse([30 * s, 0, 80 * s, 50 * s], fill=col); d.rounded_rectangle([12 * s, 58 * s, 98 * s, 200 * s], int(32 * s), fill=col)
    if bag:
        d.rounded_rectangle([70 * s, 120 * s, 108 * s, 175 * s], int(6 * s), fill=ORANGE); d.arc([76 * s, 104 * s, 102 * s, 132 * s], 180, 360, fill=ORANGE, width=int(5 * s))
    return L
def cobweb(d, x, y, r, flip=1):
    for k in range(5):
        a = math.radians(k * 22.5); d.line([x, y, x + flip * r * math.cos(a), y + r * math.sin(a)], fill=(210, 215, 230, 200), width=3)
    for rr in (0.35, 0.6, 0.85):
        pts = [(x + flip * r * rr * math.cos(math.radians(k * 22.5)), y + r * rr * math.sin(math.radians(k * 22.5))) for k in range(5)]
        d.line(pts, fill=(210, 215, 230, 180), width=2)
def rich_shop(name, full, t=0.0, w=470, h=620):
    """Fachada con escaparate. full=True: luz cálida, cartel ABIERTO y clientes comprando con bolsas.
    full=False: oscura, el dueño solo detrás del mostrador, telarañas y polvo."""
    L, d = layer(w, h)
    col = ORANGE if full else (60, 70, 95)
    d.rounded_rectangle([0, 0, w - 1, 120], 24, fill=col)
    f = F("Black", 50)
    while d.textlength(name, font=f) > w - 40: f = F("Black", f.size - 3)
    ctext(d, 60 - f.size * 0.6, name, f, WHITE if full else GREY, w // 2)
    d.rectangle([14, 120, w - 15, h - 1], fill=(30, 40, 66) if full else (22, 26, 40))
    d.rectangle([40, 160, w - 40, h - 40], fill=(255, 214, 160) if full else (40, 46, 64))
    d.rectangle([40, h - 110, w - 40, h - 70], fill=(200, 150, 100) if full else (55, 60, 78))  # mostrador
    if full:
        d.rounded_rectangle([w - 170, 175, w - 55, 215], 10, fill=(40, 200, 110)); ctext(d, 181, "ABIERTO", F("Black", 24), WHITE, w - 112)
        for j in range(5):
            x = 60 + j * 78 + 6 * math.sin(t * 3 + j); L.alpha_composite(shopper((60, 80, 130) if j % 2 else (110, 70, 60), 0.85, bag=j % 2 == 0), (int(x), h - 260))
    else:
        L.alpha_composite(shopper((90, 96, 115), 0.7), (w // 2 - 38, h - 245))  # el dueño, solo, detrás del mostrador
        cobweb(d, 40, 160, 120, 1); cobweb(d, w - 40, 160, 110, -1)
        for k in range(14):
            x = 60 + (k * 53) % (w - 120); y = 230 + (k * 37) % 200; d.ellipse([x, y, x + 4, y + 4], fill=(120, 125, 140, 160))
    return L
def scissors(size=90, col=WHITE):
    L, d = layer(size, size); r = size * 0.18
    d.ellipse([size * 0.05, size * 0.6, size * 0.05 + 2 * r, size * 0.6 + 2 * r], outline=col, width=int(size * 0.07))
    d.ellipse([size * 0.6, size * 0.6, size * 0.6 + 2 * r, size * 0.6 + 2 * r], outline=col, width=int(size * 0.07))
    d.line([size * 0.3, size * 0.62, size * 0.85, size * 0.05], fill=col, width=int(size * 0.08))
    d.line([size * 0.7, size * 0.62, size * 0.15, size * 0.05], fill=col, width=int(size * 0.08))
    return L
def price_tag(size=90, col=WHITE):
    L, d = layer(size, size)
    d.polygon([(size * 0.05, size * 0.5), (size * 0.35, size * 0.15), (size * 0.95, size * 0.15), (size * 0.95, size * 0.85), (size * 0.35, size * 0.85)], outline=col, width=int(size * 0.07))
    d.ellipse([size * 0.3, size * 0.42, size * 0.42, size * 0.54], fill=col); return L
def barber_chair(size=90, col=WHITE):
    L, d = layer(size, size)
    d.rounded_rectangle([size * 0.25, size * 0.05, size * 0.75, size * 0.5], int(size * 0.1), fill=col)
    d.rectangle([size * 0.15, size * 0.45, size * 0.85, size * 0.6], fill=col)
    d.rectangle([size * 0.45, size * 0.6, size * 0.55, size * 0.85], fill=col); d.rectangle([size * 0.2, size * 0.85, size * 0.8, size * 0.95], fill=col)
    return L
ICONS = dict(tag=price_tag, chair=barber_chair, scissors=scissors)

# ---- planos del reel "dos peluquerías" ----
def sc_twins(fr, t, dur, s):
    """Dos negocios idénticos lado a lado; las igualdades entran al ritmo de la voz."""
    names = s.get("names", ["PELUQ. A", "PELUQ. B"])
    for j, x in enumerate((290, 790)):
        St = store(names[j], True); St.alpha_composite(barber_chair(200, (80, 60, 50)), (160, 300)); St.alpha_composite(scissors(110, (60, 70, 95)), (60, 210))
        place(fr, shadowed(St), x, 640, 0.85 * back((t - 0.1 * j) / 0.3), 1)
    for k, lab in enumerate(s.get("items", ["MISMO PRECIO", "MISMO SERVICIO", "MISMAS TIJERAS"])):
        st = s["pin"] + k * s["vd"] / 3
        if t < st: continue
        L, d = layer(900, 130); d.rounded_rectangle([0, 0, 899, 129], 65, fill=NAVY_CARD, outline=ORANGE, width=5)
        ic = s.get("icons", ["tag", "chair", "scissors"])[k]
        L.alpha_composite(ICONS[ic](84, ORANGE), (40, 23))
        ctext(d, 30, "=  " + lab, F("Black", 60), WHITE, 480)
        place(fr, L, W / 2, 1060 + k * 160, back((t - st) / 0.25), 1)
    return 0
def sc_bare(fr, t, dur, s):
    """Lo único que encuentra el cliente de la peluquería B: un teléfono y 'cerrado ahora'."""
    def c(L, d, w, h, tt):
        d.rounded_rectangle([18, 70, w - 18, h - 18], 50, fill=(245, 246, 252))
        d.rounded_rectangle([40, 140, w - 40, 520], 30, fill=(232, 235, 245))
        d.ellipse([70, 180, 170, 280], fill=GREY); d.text((200, 196), s.get("name", "Peluquería B"), font=F("Black", 40), fill=(20, 20, 40))
        d.text((200, 250), "Tel. 600 000 000", font=F("Bold", 32), fill=(110, 110, 130))
        d.text((70, 330), "Sin fotos · Sin opiniones", font=F("Medium", 30), fill=(140, 140, 160))
        if tt > dur * 0.45:
            d.rounded_rectangle([70, 400, w - 70, 480], 40, fill=(200, 30, 40)); ctext(d, 418, "Cerrado ahora", F("Black", 38), WHITE, w // 2)
    place(fr, shadowed(phone(520, 900, c, t)), W / 2, 820, back(t / 0.3), 1)
    headline(fr, t, s.get("h", "SOLO UN TELÉFONO"), 1440, 104, ORANGE, 0.2)
    return 0
def sc_verdict(fr, t, dur, s):
    """Una tienda llena de gente y la otra apagada y vacía."""
    names = s.get("names", ["PELUQ. A", "PELUQ. B"])
    place(fr, shadowed(rich_shop(names[0], True, t)), 290, 720, 0.95, 1)
    if t > s["pin"] + s["vd"] * 0.55: place(fr, shadowed(rich_shop(names[1], False, t)), 790, 720, back((t - s["pin"] - s["vd"] * 0.55) / 0.3) * 0.95, 1)
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse([60, 420, 520, 980], fill=ORANGE + (90,))
    fr.alpha_composite(gl.filter(ImageFilter.GaussianBlur(80)))
    L, d = layer(W, 140); ctext(d, 10, "LLENA", F("Black", 90), ORANGE, 290)
    if t > s["pin"] + s["vd"] * 0.55: ctext(d, 10, "VACÍA", F("Black", 90), GREY, 790)
    place(fr, L, W / 2, 1150, 1, ease((t - 0.3) / 0.3))
    return 0

# ---- planos del reel "contestar tú mismo" ----
def worker(t=0.0, happy=False):
    """Fontanero con casco naranja apretando con una llave inglesa grande (dos manos) la tuerca de una
    tubería que salpica agua; móvil en el bolsillo. happy=True: tubería arreglada y móvil en verde."""
    L, d = layer(780, 820)
    PIPE = (160, 170, 190)
    d.rectangle([500, 60, 570, 660], fill=PIPE); d.rectangle([500, 600, 780, 670], fill=PIPE)  # tubería
    nx, ny = 535, 330
    d.regular_polygon((nx, ny, 62), 6, fill=(120, 128, 150))  # tuerca
    if not happy:  # agua saliendo a presión de la junta
        for k in range(10):
            ph = (t * 2.2 + k * 0.1) % 1.0; ang = -0.9 + (k % 5) * 0.45
            x = nx + 70 + 220 * ph * math.cos(ang) * 0.8; y = ny + 220 * ph * math.sin(ang) + 260 * ph * ph
            d.ellipse([x, y, x + 16, y + 22], fill=(110, 180, 255, int(255 * (1 - ph))))
    ang = (0.12 * math.sin(t * 7)) if not happy else 0.0
    hx, hy = nx - 260 * math.cos(0.75 + ang), ny + 260 * math.sin(0.75 + ang)  # extremo del mango
    d.line([nx, ny, hx, hy], fill=(190, 195, 210), width=34)  # mango de la llave
    d.arc([nx - 78, ny - 78, nx + 78, ny + 78], 120, 420, fill=(190, 195, 210), width=30)  # boca de la llave abrazando la tuerca
    gx, gy = nx + (hx - nx) * 0.62, ny + (hy - ny) * 0.62  # donde agarran las manos
    d.ellipse([110, 150, 250, 290], fill=(230, 180, 140))  # cabeza
    d.pieslice([94, 104, 266, 270], 180, 360, fill=ORANGE); d.rectangle([76, 178, 284, 196], fill=ORANGE)  # casco
    if not happy:
        for k in range(2): d.ellipse([255 + k * 22, 200 + k * 30, 269 + k * 22, 220 + k * 30], fill=(140, 200, 255))  # sudor
    d.rounded_rectangle([80, 300, 290, 620], 60, fill=(40, 70, 140))  # mono azul
    d.rectangle([90, 610, 160, 800], fill=(30, 50, 100)); d.rectangle([210, 610, 280, 800], fill=(30, 50, 100))
    d.line([270, 350, gx - 20, gy], fill=(40, 70, 140), width=44); d.line([230, 400, gx + 20, gy + 18], fill=(40, 70, 140), width=44)  # brazos
    d.ellipse([gx - 34, gy - 30, gx + 14, gy + 18], fill=(230, 180, 140)); d.ellipse([gx, gy - 10, gx + 48, gy + 38], fill=(230, 180, 140))  # manos
    d.rounded_rectangle([110, 470, 180, 580], 12, fill=(20, 26, 48))  # móvil en el bolsillo
    if happy: d.rounded_rectangle([116, 480, 174, 570], 10, fill=(40, 200, 110))
    return L
def sc_busy(fr, t, dur, s):
    happy = s.get("happy", False)
    place(fr, shadowed(worker(t, happy)), W / 2 - 40, 840, back(t / 0.3), 1)
    if not happy:
        for k in range(3):  # el móvil vibra en el bolsillo
            r = 50 + k * 30 + 10 * math.sin(t * 20); L, d = layer(300, 300)
            d.arc([150 - r, 150 - r, 150 + r, 150 + r], -40, 40, fill=ORANGE, width=8); d.arc([150 - r, 150 - r, 150 + r, 150 + r], 140, 220, fill=ORANGE, width=8)
            place(fr, L, W / 2 - 40 - 390 + 145, 840 - 410 + 525, 1, 0.8)
    else:
        L, d = layer(560, 120); d.rounded_rectangle([0, 0, 559, 119], 60, fill=(40, 200, 110)); ctext(d, 28, "Cita confirmada", F("Black", 52), WHITE, 280)
        place(fr, L, W / 2, 380, back((t - 0.3) / 0.3), 1)
    headline(fr, t, s.get("h", "MANOS OCUPADAS"), 1440, 110, ORANGE, dur * 0.4)
    return 0
def sc_pile(fr, t, dur, s):
    msgs = s.get("msgs", ["¿Hacéis presupuestos?", "¿Podéis venir hoy?", "¿Qué horario tenéis?", "¿Hola? ¿Estáis?", "¿Me llamáis?"])
    n = min(len(msgs), 1 + int(t / (dur / len(msgs))))
    for k in range(n):
        y = 300 + k * 190; st = k * dur / len(msgs)
        L, d = layer(900, 160); d.rounded_rectangle([0, 0, 899, 159], 40, fill=(250, 250, 252))
        d.ellipse([30, 35, 120, 125], fill=(40, 200, 110)); d.text((150, 30), "Cliente " + str(k + 1), font=F("Black", 40), fill=(20, 20, 40))
        d.text((150, 88), msgs[k], font=F("Medium", 34), fill=(90, 95, 120))
        place(fr, shadowed(L, 18, 100), W / 2 + 6 * math.sin(t * 30) * (k == n - 1), y, back((t - st) / 0.2), 1)
    B, d = layer(200, 200); d.ellipse([0, 0, 199, 199], fill=(230, 40, 50)); ctext(d, 50, str(20 + int(t * 6)), F("Black", 80), WHITE, 100)
    place(fr, B, W - 170, 230, 1 + 0.08 * math.sin(t * 12), 1)
    return 6 * (t % 0.5 < 0.08)
def sc_late(fr, t, dur, s):
    k = ease(t / (dur * 0.6)); hh = 14 + 2 * k
    place(fr, shadowed(clock_face(int(hh), int((hh % 1) * 60), 1.2)), W / 2, 560, back(t / 0.3), 1, 3 * math.sin(t * 25) * (1 - k))
    L, d = layer(W, 160); ctext(d, 10, "+2 HORAS", F("Black", 120), ORANGE, stroke=5)
    place(fr, L, W / 2, 900, back((t - 0.3) / 0.3), 1)
    if t > dur * 0.6:
        B, d = layer(860, 140); d.rounded_rectangle([0, 0, 859, 139], 40, fill=(220, 248, 198))
        d.text((40, 42), s.get("reply", "Perdona, ¿sigues interesado?"), font=F("Bold", 44), fill=(20, 20, 40))
        place(fr, shadowed(B, 18, 100), W / 2, 1180, back((t - dur * 0.6) / 0.25), 1)
    return 0
def sc_gone(fr, t, dur, s):
    def c(L, d, w, h, tt):
        d.rounded_rectangle([18, 70, w - 18, h - 18], 50, fill=(236, 229, 221))
        d.rectangle([18, 70, w - 18, 170], fill=(18, 36, 78)); d.ellipse([40, 92, 100, 152], fill=(150, 175, 230)); d.text((120, 104), "Cliente", font=F("Bold", 36), fill=WHITE)
        d.rounded_rectangle([w - 450, 210, w - 40, 300], 26, fill=(220, 248, 198)); d.text((w - 425, 236), "¿Sigues interesado?", font=F("Medium", 30), fill=(20, 20, 40))
        if tt > 0.35:
            d.rounded_rectangle([40, 330, w - 100, 470], 26, fill=WHITE)
            d.text((64, 350), "Ya lo he contratado", font=F("Bold", 32), fill=(20, 20, 40)); d.text((64, 400), "con otro, gracias.", font=F("Bold", 32), fill=(20, 20, 40))
    place(fr, shadowed(phone(520, 760, c, t)), W / 2 - 160, 760, back(t / 0.3), 1)
    if t > dur * 0.5:
        place(fr, shadowed(rich_shop("OTRO", True, t, 400, 520)), W / 2 + 290, 1080, back((t - dur * 0.5) / 0.3) * 0.8, 1)
    headline(fr, t, s.get("h", "CONTRATÓ A OTRO"), 1460, 104, ORANGE, dur * 0.4)
    return 0

# ---- planos del reel "3 cosas que automatizar" ----
def chair_icon(occupied, s=1.0):
    L, d = layer(int(300 * s), int(380 * s))
    d.rounded_rectangle([60 * s, 20 * s, 240 * s, 200 * s], int(30 * s), fill=(70, 80, 110))
    d.rectangle([40 * s, 190 * s, 260 * s, 250 * s], fill=(70, 80, 110)); d.rectangle([135 * s, 250 * s, 165 * s, 340 * s], fill=(70, 80, 110))
    d.rectangle([60 * s, 340 * s, 240 * s, 370 * s], fill=(70, 80, 110))
    if occupied: L.alpha_composite(shopper((60, 90, 160), 1.25 * s), (int(80 * s), int(0 * s)))
    return L
def sc_reminder(fr, t, dur, s):
    """«Recordar las citas»: silla vacía con NO VINO → llega el recordatorio → la silla se ocupa."""
    badge(fr, t, s.get("badge", "Nº 1"))
    full = t > dur * 0.62
    place(fr, shadowed(chair_icon(full, 1.0)), 300, 900, back(t / 0.3), 1)
    if not full:
        L, d = layer(360, 110); d.rounded_rectangle([0, 0, 359, 109], 55, fill=(200, 30, 40)); ctext(d, 24, "NO VINO", F("Black", 58), WHITE, 180)
        place(fr, L, 300, 600, back((t - 0.15) / 0.3), 1, -6)
    def c(L, d, w, h, tt):
        d.rounded_rectangle([18, 70, w - 18, h - 18], 44, fill=(20, 26, 48))
        if tt > dur * 0.3:
            d.rounded_rectangle([30, 200, w - 30, 420], 26, fill=(250, 250, 252)); d.ellipse([50, 225, 120, 295], fill=(40, 200, 110))
            d.text((135, 225), "Recordatorio", font=F("Black", 30), fill=(20, 20, 40))
            d.text((50, 310), "Tu cita es mañana", font=F("Medium", 28), fill=(90, 95, 120)); d.text((50, 352), "a las 10:00", font=F("Bold", 28), fill=(20, 20, 40))
    place(fr, shadowed(phone(420, 760, c, t)), 790, 880, back((t - 0.1) / 0.3), 1)
    headline(fr, t, s.get("h", "RECORDAR LAS CITAS"), 1450, 100, ORANGE, 0.2)
    return 0
def sc_reviewask(fr, t, dur, s):
    """«Pedir opiniones»: mensaje automático tras el servicio y 5 estrellas que se rellenan."""
    badge(fr, t, s.get("badge", "Nº 2"))
    def c(L, d, w, h, tt):
        d.rounded_rectangle([18, 70, w - 18, h - 18], 50, fill=(236, 229, 221))
        d.rectangle([18, 70, w - 18, 170], fill=(18, 36, 78)); d.ellipse([40, 92, 100, 152], fill=ORANGE); d.text((120, 104), "Tu negocio", font=F("Bold", 34), fill=WHITE)
        if tt > 0.2:
            d.rounded_rectangle([40, 210, w - 60, 380], 26, fill=WHITE)
            d.text((64, 232), "¿Qué tal ha ido?", font=F("Bold", 32), fill=(20, 20, 40)); d.text((64, 282), "Déjanos tu opinión", font=F("Medium", 30), fill=(90, 95, 120))
            d.rounded_rectangle([64, 326, 300, 366], 20, fill=ORANGE); ctext(d, 330, "Opinar", F("Bold", 26), WHITE, 182)
    place(fr, shadowed(phone(520, 720, c, t)), W / 2, 680, back(t / 0.3), 1)
    n = int(max(0, min(5, (t - dur * 0.45) / (dur * 0.4) * 5 + 0.999)))
    L, d = layer(800, 170)
    for j in range(5):
        cx, cy, r = 80 + j * 160, 85, 70
        pts = [(cx + r * math.cos(math.pi / 2 + i * math.pi / 5) * (1 if i % 2 == 0 else 0.45), cy - r * math.sin(math.pi / 2 + i * math.pi / 5) * (1 if i % 2 == 0 else 0.45)) for i in range(10)]
        d.polygon(pts, fill=ORANGE if j < n else (60, 70, 95))
    place(fr, L, W / 2, 1180, 1, ease((t - dur * 0.4) / 0.2))
    headline(fr, t, s.get("h", "PEDIR OPINIONES"), 1440, 104, WHITE, 0.2)
    return 0
def sc_leadform(fr, t, dur, s):
    """«Tu web capta clientes»: formulario que se rellena solo y llega el cliente al móvil con sus datos."""
    badge(fr, t, s.get("badge", "Nº 3"))
    fields = s.get("fields", [["Nombre", "Laura"], ["Servicio", "Reforma de baño"], ["Teléfono", "6XX XXX XXX"]])
    def c(L, d, w, h, tt):
        d.text((40, 90), "PIDE PRESUPUESTO", font=F("Black", 34), fill=(20, 20, 40))
        for k, (lab, val) in enumerate(fields):
            y = 150 + k * 120; d.text((40, y), lab, font=F("Bold", 24), fill=(110, 110, 130))
            d.rounded_rectangle([40, y + 34, w - 40, y + 94], 14, fill=(232, 235, 245))
            st = 0.2 + k * dur * 0.15; typed = val[: int(max(0, tt - st) * 24)]
            d.text((60, y + 46), typed, font=F("Bold", 30), fill=(20, 20, 40))
        on = tt > 0.2 + len(fields) * dur * 0.15
        d.rounded_rectangle([40, h - 110, w - 40, h - 40], 35, fill=(40, 200, 110) if on else ORANGE)
        ctext(d, h - 98, "Enviado ✓" if on else "Enviar", F("Black", 36), WHITE, w // 2)
    place(fr, shadowed(browser(760, 620, content=c, t=t)), W / 2, 680, back(t / 0.3), 1)
    if t > dur * 0.68:
        k = t - dur * 0.68; L, d = layer(900, 230); d.rounded_rectangle([0, 0, 899, 229], 40, fill=(250, 250, 252))
        d.ellipse([30, 30, 130, 130], fill=ORANGE); ctext(d, 46, "+1", F("Black", 52), WHITE, 80)
        d.text((160, 26), "Nuevo cliente", font=F("Black", 46), fill=(20, 20, 40))
        d.text((160, 90), f"{fields[0][1]} · {fields[1][1]}", font=F("Bold", 34), fill=(90, 95, 120)); d.text((160, 146), "Recibido a las 23:14", font=F("Medium", 30), fill=(130, 130, 150))
        place(fr, shadowed(L, 18, 110), W / 2, 1210 - 60 * ease(k / 0.3), back(k / 0.25), 1)
    return 0
def sc_nocalls(fr, t, dur, s):
    """«Sin llamadas. Sin perder tiempo.»: teléfono tachado y reloj que se para."""
    L, d = layer(360, 360); d.ellipse([0, 0, 359, 359], fill=NAVY_CARD)
    d.arc([80, 70, 280, 290], 200, 340, fill=WHITE, width=46)
    d.rounded_rectangle([60, 150, 150, 230], 26, fill=WHITE); d.rounded_rectangle([210, 150, 300, 230], 26, fill=WHITE)
    place(fr, shadowed(L), 300, 760, back(t / 0.3), 1)
    k = ease((t - 0.3) / 0.25)
    if k > 0:
        X, d = layer(420, 420); d.line([40, 380, 40 + 340 * k, 380 - 340 * k], fill=(230, 40, 50), width=34); place(fr, X, 300, 760, 1, 1)
    if t > s["pin"] + s["vd"] * 0.5:
        place(fr, shadowed(clock_face(10, 10, 1.1, ORANGE)), 790, 760, back((t - s["pin"] - s["vd"] * 0.5) / 0.3), 1)
    L, d = layer(W, 300); ctext(d, 0, "SIN LLAMADAS", F("Black", 96), WHITE, 300 + 240)
    if t > s["pin"] + s["vd"] * 0.5: ctext(d, 130, "SIN PERDER TIEMPO", F("Black", 86), ORANGE, 540)
    place(fr, L, W / 2, 1260, 1, ease(t / 0.2))
    return 0

# ---- planos del reel "nadie busca tu nombre" ----
def search_bar(text, w=920, h=140, cursor_on=True):
    L, d = layer(w, h); d.rounded_rectangle([0, 0, w - 1, h - 1], h // 2, fill=(245, 246, 252))
    d.ellipse([40, 40, 100, 100], outline=GREY, width=9); d.line([92, 92, 116, 116], fill=GREY, width=10)
    f = F("Bold", 50)
    while d.textlength(text, font=f) > w - 200: f = F("Bold", f.size - 2)
    d.text((140, h / 2 - f.size * 0.62), text + ("|" if cursor_on else ""), font=f, fill=(20, 20, 40)); return L
def sc_typesearch(fr, t, dur, s):
    """Se escribe una búsqueda en Google y se marca como lo que NO escriben (✗ rojo) o lo que SÍ escriben (✓ verde)."""
    q = s.get("query", "electricista cerca de mí"); ok = s.get("ok", True)
    typed = q[: int(max(0, t - 0.1) * 26)]
    place(fr, shadowed(search_bar(typed, cursor_on=int(t * 4) % 2 == 0)), W / 2, 820, back(t / 0.3), 1)
    done = t > 0.1 + len(q) / 26 + 0.15
    if done:
        k = t - (0.1 + len(q) / 26 + 0.15)
        if ok:
            L, d = layer(220, 220); d.ellipse([0, 0, 219, 219], fill=(40, 200, 110)); d.line([(55, 112), (95, 152), (165, 72)], fill=WHITE, width=26)
            place(fr, L, W / 2, 1080, back(k / 0.25), 1)
        else:
            X, d = layer(960, 200); d.line([20, 100, 20 + 920 * ease(k / 0.25), 100], fill=(230, 40, 50), width=22)
            place(fr, X, W / 2, 820, 1, 1)
            L, d = layer(220, 220); d.ellipse([0, 0, 219, 219], fill=(230, 40, 50)); d.line([65, 65, 155, 155], fill=WHITE, width=26); d.line([155, 65, 65, 155], fill=WHITE, width=26)
            place(fr, L, W / 2, 1080, back(k / 0.25), 1)
    headline(fr, t, s.get("h", "LO QUE ESCRIBEN"), 420, 104, ORANGE if ok else WHITE, 0.0)
    return 0
def sc_results(fr, t, dur, s):
    """Resultados de Google: aparece primero quien lo explica en su web; tu negocio no sale."""
    items = s.get("items", [["Electricidad García", "Electricista en tu zona · Web", True], ["Instalaciones Ruiz", "Electricista · Web", True], ["Electro Sur", "Averías 24 h · Web", True]])
    place(fr, shadowed(search_bar(s.get("query", "electricista cerca de mí"), cursor_on=False)), W / 2, 330, 1, 1)
    for k, (n, sub, web) in enumerate(items):
        st = 0.15 + k * 0.3
        if t < st: continue
        L, d = layer(920, 220); d.rounded_rectangle([0, 0, 919, 219], 34, fill=(245, 246, 252), outline=ORANGE if k == 0 else (220, 224, 236), width=6 if k == 0 else 2)
        d.ellipse([34, 50, 144, 160], fill=ORANGE if k == 0 else (90, 130, 220)); d.text((176, 50), n, font=F("Black", 50), fill=(20, 20, 40))
        d.text((176, 122), sub, font=F("Bold", 36), fill=ORANGE if k == 0 else (90, 95, 120))
        place(fr, shadowed(L, 18, 100), W / 2, 580 + k * 250, back((t - st) / 0.25), 1)
    if t > dur * 0.6:
        L, d = layer(860, 120); d.rounded_rectangle([0, 0, 859, 119], 60, fill=(200, 30, 40)); ctext(d, 26, s.get("missing", "Electricidad Pérez: no sale"), F("Black", 54), WHITE, 430)
        place(fr, L, W / 2, 1360, back((t - dur * 0.6) / 0.25), 1, -3)
    return 0
def sc_vagueweb(fr, t, dur, s):
    """Una web que no dice qué haces ni dónde: huecos con interrogantes."""
    def c(L, d, w, h, tt):
        d.text((40, 96), s.get("brand", "ELECTRICIDAD PÉREZ"), font=F("Black", 34), fill=(20, 20, 40))
        d.rounded_rectangle([40, 160, w - 40, 400], 24, fill=(225, 228, 240)); d.text((70, 250), "Bienvenidos a nuestra web", font=F("Bold", 40), fill=(150, 155, 175))
        for k, lab in enumerate(["¿QUÉ HACES?", "¿DÓNDE?"]):
            st = 0.3 + k * dur * 0.3
            x = 40 + k * (w // 2 - 20)
            d.rounded_rectangle([x, 430, x + w // 2 - 60, 600], 22, outline=(200, 30, 40) if tt > st else (215, 218, 230), width=6)
            if tt > st: ctext(d, 490, lab, F("Black", 40), (200, 30, 40), x + (w // 2 - 60) // 2)
    place(fr, shadowed(browser(860, 660, url="electricidadperez.com", content=c, t=t)), W / 2, 760, back(t / 0.3), 1)
    headline(fr, t, s.get("h", "NO APARECES"), 1420, 120, ORANGE, dur * 0.55)
    return 0
def sc_servicepages(fr, t, dur, s):
    """Una página por servicio, cada una conectada a la búsqueda que la encuentra."""
    pages = s.get("pages", [["Instalaciones", "instalación eléctrica"], ["Averías urgentes", "electricista urgente"], ["Boletines", "boletín eléctrico"]])
    for k, (title, q) in enumerate(pages):
        st = s["pin"] + k * s["vd"] * 0.22
        if t < st: continue
        a = back((t - st) / 0.3); y = 470 + k * 360
        def c(L, d, w, h, tt, title=title):
            d.text((30, 80), title.upper(), font=F("Black", 30), fill=(20, 20, 40)); d.rounded_rectangle([30, 130, w - 30, 220], 16, fill=ORANGE)
        place(fr, shadowed(browser(460, 260, url="tunegocio.com/" + title.split()[0].lower(), content=c)), 300, y, a * 0.95, 1)
        Q, d = layer(470, 110); d.rounded_rectangle([0, 0, 469, 109], 55, fill=(245, 246, 252)); d.text((30, 30), q, font=F("Bold", 36), fill=(20, 20, 40))
        place(fr, Q, 790, y, a, 1)
        A, d = layer(120, 60); d.line([10, 30, 100, 30], fill=ORANGE, width=10); d.polygon([(100, 10), (118, 30), (100, 50)], fill=ORANGE)
        place(fr, A, 560, y, a, 1, 180)
    headline(fr, t, s.get("h", "MÁS BÚSQUEDAS"), 1440, 110, ORANGE, dur * 0.6)
    return 0

# ---- planos del reel "3 errores al pedir tu web" ----
def sc_prettyweb(fr, t, dur, s):
    """«Pedirla solo bonita»: web preciosa con «¡QUÉ BONITA!»; al decir «no vende», contador «0 mensajes»."""
    badge(fr, t, s.get("badge", "ERROR 1"))
    turn = s["pin"] + s["vd"] * s.get("mark", 0.45)
    place(fr, shadowed(pretty_web(clients=False)), W / 2, 820, back(t / 0.3) * 0.9, 1)
    if t < turn:
        L, d = layer(560, 130); d.rounded_rectangle([0, 0, 559, 129], 65, fill=(255, 90, 140)); ctext(d, 28, "¡QUÉ BONITA!", F("Black", 62), WHITE, 280)
        place(fr, L, W / 2 + 160, 380, back((t - 0.2) / 0.3), 1, -6)
    else:
        k = t - turn
        L, d = layer(860, 170); d.rounded_rectangle([0, 0, 859, 169], 40, fill=(250, 250, 252))
        d.ellipse([30, 35, 130, 135], fill=(200, 30, 40)); ctext(d, 52, "0", F("Black", 60), WHITE, 80)
        d.text((160, 32), "0 mensajes", font=F("Black", 52), fill=(20, 20, 40)); d.text((160, 100), "este mes", font=F("Medium", 36), fill=(110, 110, 130))
        place(fr, shadowed(L, 18, 110), W / 2, 1280, back(k / 0.25), 1)
        return 14 * max(0, 1 - k / 0.2)
    return 0
def sc_locked(fr, t, dur, s):
    """«No poder tocarla tú»: el horario con un candado; llamas y esperas días."""
    badge(fr, t, s.get("badge", "ERROR 2"))
    def c(L, d, w, h, tt):
        d.text((40, 96), "HORARIO", font=F("Black", 36), fill=(20, 20, 40))
        d.rounded_rectangle([40, 160, w - 40, 300], 20, fill=(232, 235, 245)); d.text((70, 196), "Lun–Vie 9:00–19:00", font=F("Bold", 46), fill=(20, 20, 40))
        d.line([60, 230, w - 60, 230], fill=(200, 30, 40), width=6)
        d.text((70, 330), "(ya no abres así)", font=F("Medium", 32), fill=(200, 30, 40))
    place(fr, shadowed(browser(780, 460, content=c, t=t)), W / 2, 560, back(t / 0.3), 1)
    place(fr, lock(0.9), W / 2 + 300, 470, back((t - 0.25) / 0.3), 1, 6 * math.sin(t * 25))
    turn = s["pin"] + s["vd"] * s.get("mark", 0.4)
    if t > turn:
        k = t - turn
        def c2(L, d, w, h, tt):
            d.rounded_rectangle([18, 70, w - 18, h - 18], 44, fill=(20, 26, 48)); ctext(d, 160, "Llamando…", F("Black", 40), WHITE, w // 2)
            d.ellipse([w // 2 - 70, 240, w // 2 + 70, 380], fill=(40, 200, 110))
        place(fr, shadowed(phone(360, 560, c2, k)), 300, 1180, back(k / 0.3), 1)
        days = min(3, 1 + int(k / 0.5)); L, d = layer(460, 200); ctext(d, 10, f"{days} DÍA{'S' if days > 1 else ''}", F("Black", 110), ORANGE, 230)
        ctext(d, 140, "esperando", F("Bold", 44), MUTED, 230)
        place(fr, L, 780, 1180, back(k / 0.3), 1)
    return 0
def sc_tumbleweed(fr, t, dur, s):
    """«Pensar que con tenerla ya está»: la web sola, en un desierto, con una bola de paja rodando."""
    badge(fr, t, s.get("badge", "ERROR 3"))
    sand = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(sand)
    g.ellipse([-300, 1080, W + 300, 1440], fill=(214, 170, 110, 255)); fr.alpha_composite(sand)
    place(fr, shadowed(browser(620, 480, content=own_site)), W / 2, 830, back(t / 0.3) * 0.95, 1)
    L, d = layer(420, 110); d.rounded_rectangle([0, 0, 419, 109], 55, fill=(250, 250, 252)); ctext(d, 24, "0 visitas", F("Black", 56), (200, 30, 40), 210)
    place(fr, L, W / 2, 500, back((t - 0.3) / 0.3), 1)
    x = -150 + (W + 300) * ((t / max(dur, 0.1)) % 1.0); ang = x * 1.2
    B, d = layer(200, 200)
    for k in range(9):
        a = math.radians(k * 40 + ang); d.arc([20 + k * 3, 20 + k * 2, 180 - k * 2, 180 - k * 3], k * 40 + ang, k * 40 + ang + 220, fill=(150, 110, 60), width=7)
    place(fr, B, x, 1190 - 20 * abs(math.sin(t * 6)), 1, 1)
    headline(fr, t, s.get("h", "CON TENERLA NO BASTA"), 1500, 92, ORANGE, dur * 0.35)
    return 0

DRAW = dict(prettyweb=sc_prettyweb, locked=sc_locked, tumbleweed=sc_tumbleweed, typesearch=sc_typesearch, results=sc_results, vagueweb=sc_vagueweb, servicepages=sc_servicepages, reminder=sc_reminder, reviewask=sc_reviewask, leadform=sc_leadform, nocalls=sc_nocalls, busy=sc_busy, pile=sc_pile, late=sc_late, gone=sc_gone, twins=sc_twins, bare=sc_bare, verdict=sc_verdict, giftpromise=sc_giftpromise, steps=sc_steps, delivery=sc_delivery, notthis=sc_notthis, chatbot=sc_chatbot, gift=sc_gift, demo=sc_demo, follow=sc_follow, visitors=sc_visitors, brokenlist=sc_brokenlist, silentbell=sc_silentbell, inspect=sc_inspect, countdown=sc_countdown, photos=sc_photos, goodmobile=sc_goodmobile, button=sc_button, trash=sc_trash, phonepop=sc_phonepop, qr=sc_qr, showcase=sc_showcase, clock=sc_clock, nightsearch=sc_nightsearch, other=sc_other, nightweb=sc_nightweb, morning=sc_morning, logo=sc_logo, suspended=sc_suspended, secret=sc_secret, ownweb=sc_ownweb, yours=sc_yours, pricetease=sc_pricetease, boom=sc_boom, three=sc_three, slow=sc_slow, leave=sc_leave, loop2=sc_loop2, mobile=sc_mobile, loop3=sc_loop3,
            nobutton=sc_nobutton, competitor=sc_competitor, fix=sc_fix, price=sc_price, dm=sc_dm)

# ---------------- subtítulos ----------------
FS = F("Black", 74); MAXW = W - 140
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
            d.text((x, 20 + li * lh), wd, font=f, fill=ORANGE if k == hi else WHITE, stroke_width=9, stroke_fill=(0, 0, 0))
            x += d.textlength(wd + " ", font=f); k += 1
    return L

# ---------------- portada ----------------
def make_cover(lines):
    fr = BG.copy(); d = ImageDraw.Draw(fr)
    place(fr, OLD, W / 2, 900, 0.85, 0.35, -6)
    rows = []
    for ln in lines:
        big = ln.startswith("*"); txt = ln.lstrip("*"); f = F("Black", 210 if big else 112)
        while d.textlength(txt, font=f) > W - 110: f = F("Black", f.size - 6)
        rows.append((txt, f, ORANGE if big else WHITE))
    y = 940 - sum(int(f.size * 1.12) for _, f, _ in rows) / 2 - 40
    for txt, f, col in rows:
        ctext(d, y, txt, f, col, stroke=9); y += int(f.size * 1.12)
    fo = F("Black", 90); ow = d.textlength("Obra", font=fo); tw = ow + d.textlength("Web", font=fo)
    d.text(((W - tw) / 2, 1520), "Obra", font=fo, fill=WHITE); d.text(((W - tw) / 2 + ow, 1520), "Web", font=fo, fill=ORANGE)
    fr.convert("RGB").save(os.path.join(D, "videos", NAME + "_portada.jpg"), quality=92)
make_cover(scenes[0].get("cover", [scenes[0]["text"].upper()]))

# ---------------- render ----------------
out_v = os.path.join(B, "video.mp4")
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                       "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", out_v], stdin=subprocess.PIPE)
for si, s in enumerate(scenes):
    words = s.get("sub", s["text"]).upper().split()
    groups = [words[i:i + 3] for i in range(0, len(words), 3)]
    wt = np.array([len(w) + 2 for w in words], float)
    wb = np.concatenate([[0], np.cumsum(wt) / wt.sum()]) * s["vd"] + s["pin"]
    nfr = int(round(s["dur"] * FPS))
    for fi in range(nfr):
        t = fi / FPS
        fr = BG.copy()
        shake = abs(DRAW[s["kind"]](fr, t, s["dur"], s) or 0)
        if t >= s["pin"] * 0.5:
            wi = int(min(max(np.searchsorted(wb, t, side="right") - 1, 0), len(words) - 1))
            acc = 0
            for g in groups:
                if wi < acc + len(g): break
                acc += len(g)
            pop = ease((t - wb[acc]) / 0.1) if t >= wb[acc] else 1
            place(fr, sub_layer(g, wi - acc), W / 2, 1640, 0.86 + 0.14 * pop)
        if shake:
            ox, oy = rng.uniform(-shake, shake), rng.uniform(-shake, shake)
            fr = fr.transform(fr.size, Image.AFFINE, (1, 0, ox, 0, 1, oy), resample=Image.BILINEAR, fillcolor=(6, 16, 40, 255))
        if s.get("cut") and t < 0.08:  # corte con flash corto
            fr.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(120 * (1 - t / 0.08)))))
        ff.stdin.write(fr.convert("RGB").tobytes())
    print("plano", si, s["kind"], "ok", flush=True)
ff.stdin.close(); ff.wait()

# ---------------- audio: voz + música + efectos ----------------
SR = 24000
voice, starts = [], []
pos = 0
for s in scenes:
    a = s["audio"] if s["sr"] == SR else np.interp(np.linspace(0, len(s["audio"]) - 1, int(len(s["audio"]) * SR / s["sr"])), np.arange(len(s["audio"])), s["audio"])
    n = int(round(s["dur"] * FPS)) * SR // FPS
    seg = np.zeros(n, np.float32); st = int(s["pin"] * SR); seg[st:st + len(a)] = a[: n - st]
    voice.append(seg); starts.append(pos); pos += n
voice = np.concatenate(voice); n = len(voice); tt = np.arange(n) / SR
fx = np.zeros(n, np.float32)
# BOOM + cristales en el impacto
i0 = int(IMPACT * SR); L = int(1.2 * SR); k = np.arange(L) / SR
boom = np.sin(2 * np.pi * (60 * k - 25 * k * k)) * np.exp(-k * 4) * 1.0
noise = np.random.default_rng(1).standard_normal(L) * np.exp(-k * 9) * 0.6
glass = np.zeros(L)
gr = np.random.default_rng(2)
for _ in range(40):
    o = int(gr.uniform(0, 0.5) * SR); f = gr.uniform(2500, 7000); m = L - o
    glass[o:] += np.sin(2 * np.pi * f * k[:m]) * np.exp(-k[:m] * gr.uniform(20, 45)) * 0.12
fx[i0:i0 + L] += (boom + noise + glass)[: n - i0]
# golpes: "cut" + whoosh en planos de impacto
for s, st in zip(scenes, starts):
    if s.get("cut"):
        Lw = int(0.3 * SR); nz = np.random.default_rng(st).standard_normal(Lw)
        nz = np.convolve(nz, np.ones(10) / 10, "same") * np.sin(np.linspace(0, np.pi, Lw)) ** 2 * 0.35
        a0 = max(0, st - Lw // 2); fx[a0:a0 + Lw] += nz[: n - a0]
        kk = np.arange(int(0.25 * SR)) / SR; hit = np.sin(2 * np.pi * 80 * kk) * np.exp(-kk * 18) * 0.5
        fx[st:st + len(hit)] += hit[: n - st]
# música rápida (128 bpm) que entra justo tras la explosión
bpm = 128; beat = 60 / bpm; music = np.zeros(n, np.float32); roots = [110.0, 87.31, 130.81, 98.0]
b = 0
while True:
    a0 = int((IMPACT + 0.4 + b * beat) * SR)
    if a0 >= n: break
    kk = np.arange(min(int(beat * SR), n - a0)) / SR
    music[a0:a0 + len(kk)] += np.sin(2 * np.pi * 55 * np.exp(-kk * 18) * kk * 8) * np.exp(-kk * 9) * 0.55
    h0 = int(beat / 2 * SR)
    if len(kk) > h0: music[a0 + h0:a0 + len(kk)] += np.random.default_rng(b).standard_normal(len(kk) - h0) * np.exp(-kk[: len(kk) - h0] * 60) * 0.06
    r = roots[(b // 4) % 4]
    music[a0:a0 + len(kk)] += np.sin(2 * np.pi * r / 2 * kk) * np.minimum(1, kk * 30) * np.exp(-kk * 5) * 0.14
    for m in (1, 1.19, 1.5): music[a0:a0 + len(kk)] += np.sin(2 * np.pi * r * m * kk) * np.exp(-kk * 4) * 0.03
    b += 1
music *= np.minimum(1, (tt[-1] - tt) / 0.6)
env = np.convolve(np.abs(voice), np.ones(2400) / 2400, "same"); duck = 1 - 0.55 * np.clip(env / 0.04, 0, 1)
mix = voice * 1.15 + music * 0.5 * duck + fx * 0.7
mix /= np.abs(mix).max() / 0.95
with wave.open(os.path.join(B, "audio.wav"), "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
final = os.path.join(D, "videos", NAME + ".mp4")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", out_v, "-i", os.path.join(B, "audio.wav"), "-c:v", "copy", "-c:a", "aac",
                "-b:a", "192k", "-shortest", "-movflags", "+faststart", final], check=True)
print("listo", final, round(n / SR, 1), "s")
