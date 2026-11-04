"""Historia (1080x1920): «Responde DEMO a esta historia» → demo gratis de la web de su negocio.
Uso: python3 -I historia_demo.py"""
import math, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

D = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
F = lambda w, s: ImageFont.truetype(f"/usr/share/fonts/opentype/inter/Inter-{w}.otf", s)
ORANGE, WHITE, MUTED, NAVY_CARD, BLUE = (255, 122, 26), (255, 255, 255), (176, 190, 220), (18, 36, 78), (40, 90, 200)

img = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(img)
for y in range(H):
    t = y / H; d.line([0, y, W, y], fill=(int(6 + 6 * t), int(16 + 14 * t), int(40 + 32 * t), 255))
bl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(bl)
g.ellipse([-300, 150, 600, 1050], fill=BLUE + (110,)); g.ellipse([300, 600, 1100, 1400], fill=ORANGE + (70,))
img.alpha_composite(bl.filter(ImageFilter.GaussianBlur(160)))
d = ImageDraw.Draw(img)

def ctext(y, txt, f, fill, x=W // 2, stroke=0):
    d.text((x - d.textlength(txt, font=f) / 2, y), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
def shadowed(L, blur=26, alpha=130):
    a = L.getchannel("A").filter(ImageFilter.GaussianBlur(blur))
    sh = Image.new("RGBA", L.size, (0, 0, 0, 0)); sh.putalpha(a.point(lambda v: v * alpha // 255))
    out = Image.new("RGBA", L.size, (0, 0, 0, 0)); out.alpha_composite(sh, (0, 16)); out.alpha_composite(L); return out

# logo (por debajo de la barra superior de Instagram)
fo = F("Black", 58); ow = d.textlength("Obra", font=fo); tw = ow + d.textlength("Web", font=fo)
d.text(((W - tw) / 2, 230), "Obra", font=fo, fill=WHITE); d.text(((W - tw) / 2 + ow, 230), "Web", font=fo, fill=ORANGE)

ctext(340, "¿QUIERES VER CÓMO", F("Black", 82), WHITE)
ctext(440, "QUEDARÍA LA WEB", F("Black", 82), WHITE)
ctext(540, "DE TU NEGOCIO?", F("Black", 92), ORANGE, stroke=4)

# web de ejemplo con la etiqueta DEMO GRATIS (lo que se regala, visto)
B = Image.new("RGBA", (800, 560), (0, 0, 0, 0)); b = ImageDraw.Draw(B)
b.rounded_rectangle([0, 0, 799, 559], 30, fill=(245, 246, 252))
b.rounded_rectangle([0, 0, 799, 64], 30, fill=(222, 226, 238)); b.rectangle([0, 40, 799, 64], fill=(222, 226, 238))
for i, c in enumerate([(255, 95, 87), (255, 189, 46), (40, 200, 64)]): b.ellipse([22 + i * 36, 20, 46 + i * 36, 44], fill=c)
b.rounded_rectangle([150, 14, 770, 50], 18, fill=WHITE); b.text((170, 19), "tunegocio.com", font=F("Medium", 26), fill=(90, 95, 120))
b.text((40, 90), "TU NEGOCIO", font=F("Black", 34), fill=(20, 20, 40))
b.rounded_rectangle([40, 150, 760, 350], 22, fill=ORANGE)
b.text((70, 185), "Tu web, lista", font=F("Black", 56), fill=WHITE); b.text((70, 255), "para conseguir clientes", font=F("Bold", 36), fill=WHITE)
for k in range(3): b.rounded_rectangle([40 + k * 245, 380, 255 + k * 245, 520], 18, fill=(225, 228, 240))
img.alpha_composite(shadowed(B), (140, 680))
T = Image.new("RGBA", (520, 120), (0, 0, 0, 0)); tt = ImageDraw.Draw(T)
tt.rounded_rectangle([0, 0, 519, 119], 60, fill=ORANGE); tw = tt.textlength("DEMO GRATIS", font=F("Black", 60)); tt.text(((520 - tw) / 2, 26), "DEMO GRATIS", font=F("Black", 60), fill=WHITE)
img.alpha_composite(T.rotate(-6, expand=True, resample=Image.BICUBIC), (520, 1150))
d = ImageDraw.Draw(img)

# instrucción clara: responder DEMO a esta historia (la barra de respuesta está justo debajo)
ctext(1360, "Responde «DEMO»", F("Black", 86), WHITE)
ctext(1460, "a esta historia", F("Black", 70), WHITE)
ctext(1555, "y te la preparo gratis, sin compromiso", F("Bold", 40), MUTED)
for k in range(3):  # flechas hacia la barra de «Enviar mensaje»
    x = W // 2 - 120 + k * 120; y = 1630 + (k % 2) * 10
    d.polygon([(x - 34, y), (x + 34, y), (x, y + 44)], fill=ORANGE)

out = os.path.join(D, "historias", "historia_003_responde_demo.png")
img.convert("RGB").save(out); print(out)
