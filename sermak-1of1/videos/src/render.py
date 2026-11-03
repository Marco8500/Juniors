"""SERMAK · Ónix Rosé · "BRASAS" — 9:16 reel rendered from the real product still."""
import math, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont

W, H, FPS, DUR = 1080, 1920, 24, 16.0
N = int(FPS * DUR)
SRC = '/root/.claude/uploads/991c2645-f33f-5280-bb02-a9e38d88eda3/c3efb48f-image.jpg'
LOGO = '/root/.claude/uploads/991c2645-f33f-5280-bb02-a9e38d88eda3/f251a9f7-image.png'
OUT = sys.argv[1] if len(sys.argv) > 1 else 'video_noaudio.mp4'
PREVIEW = sys.argv[2:]  # optional list of frame indices to dump as PNG

rng = np.random.default_rng(7)

# ---------- source: upscale 2x once for better resampling ----------
src0 = Image.open(SRC).convert('RGB')
S = 2.0
src = src0.resize((int(src0.width * S), int(src0.height * S)), Image.LANCZOS)
src = src.filter(ImageFilter.UnsharpMask(radius=2.2, percent=70, threshold=2))
BASE_CW = src0.height * W / H  # crop width (src px) at zoom 1 (full height)

# watch landmarks in original-image coords
DIAL = (445, 562)
CROWN = (630, 520)
EMBER_SRC = (520, 760)  # where the "ember" light comes from (below-left of case side)


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def view(cx, cy, zoom):
    cw = BASE_CW / zoom
    ch = src0.height / zoom
    x0, y0 = cx - cw / 2, cy - ch / 2
    box = (x0 * S, y0 * S, (x0 + cw) * S, (y0 + ch) * S)
    im = src.transform((W, H), Image.EXTENT, box, Image.BICUBIC)
    a = np.asarray(im, dtype=np.float32) / 255.0
    return a, (x0, y0, cw / W)  # mapping: src = x0 + px*scale


def to_out(pt, m):
    x0, y0, sc = m
    return ((pt[0] - x0) / sc, (pt[1] - y0) / sc)


yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
vign = 1.0 - 0.55 * np.clip(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.58)) ** 2, 0, 1) ** 1.3
vign = vign[..., None]


def lum(a):
    return (0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2])[..., None]


def grade(a):
    # deep blacks, keep rose gold rosy (slightly cool the yellow), gentle contrast
    a = np.clip((a - 0.025) / 0.975, 0, 1)
    a = a ** 1.08
    a[..., 2] *= 1.03
    a[..., 1] *= 0.985
    s = a * a * (3 - 2 * a)
    return 0.7 * a + 0.3 * s


def flicker(t, seed=0.0):
    return (0.62 + 0.18 * math.sin(t * 7.1 + seed) + 0.12 * math.sin(t * 13.7 + 1.3 + seed)
            + 0.08 * math.sin(t * 23.3 + 0.4 + seed))


EMBER = np.array([1.0, 0.42, 0.12], np.float32)


def ember_light(a, m, t, strength, pos=EMBER_SRC, radius=260.0, base=None):
    if strength <= 0:
        return a
    ex, ey = to_out((pos[0] + 6 * math.sin(t * 2.3), pos[1] + 4 * math.sin(t * 3.1)), m)
    sc = m[2]
    r = np.sqrt((xx - ex) ** 2 + (yy - ey) ** 2) * sc  # in src px
    fall = np.exp(-(r / radius) ** 2)[..., None]
    L = lum(a if base is None else base)
    refl = (L ** 1.6) * fall * EMBER * 1.9          # reflection on metal highlights
    haze = fall ** 2 * EMBER * 0.10                  # faint air glow
    k = strength * flicker(t)
    return a * (1 - 0.25 * strength * fall) + k * (refl + haze)


def sweep(a, t, t0, t1):
    if not (t0 <= t <= t1):
        return a
    p = (t - t0) / (t1 - t0)
    pos = -0.3 + 1.6 * ease(p)
    d = (xx / W * 0.9 + yy / H * 0.35) - (pos * 1.25)
    band = np.exp(-(d / 0.07) ** 2)[..., None]
    L = lum(a)
    warm = np.array([1.0, 0.86, 0.72], np.float32)
    return a + band * (0.12 + 1.5 * L ** 1.4) * warm * 0.55


# ---------- sparks ----------
NSP = 90
sp = {
    'x': rng.uniform(0, W, NSP), 'y': rng.uniform(H * 0.2, H * 1.1, NSP),
    'vy': rng.uniform(-70, -25, NSP), 'vx': rng.uniform(-10, 10, NSP),
    'ph': rng.uniform(0, 6.28, NSP), 'sz': rng.uniform(1.2, 3.2, NSP),
    'life': rng.uniform(0.4, 1.0, NSP),
}


def sparks_layer(t, amount, m):
    if amount <= 0:
        return None
    lay = Image.new('L', (W // 2, H // 2), 0)
    d = ImageDraw.Draw(lay)
    cx, cy = to_out(DIAL, m)
    rad = 230 / m[2]  # keep sparks off the watch case
    for i in range(NSP):
        y = (sp['y'][i] + sp['vy'][i] * t) % (H * 1.1)
        x = sp['x'][i] + sp['vx'][i] * t + 18 * math.sin(t * 1.3 + sp['ph'][i])
        if (x - cx) ** 2 + ((y - cy) / 1.35) ** 2 < rad ** 2:
            continue
        b = 0.5 + 0.5 * math.sin(t * 5 + sp['ph'][i] * 3)
        v = int(255 * sp['life'][i] * b)
        r = sp['sz'][i] / 2
        d.ellipse([x / 2 - r, y / 2 - r, x / 2 + r, y / 2 + r], fill=v)
    lay = lay.filter(ImageFilter.GaussianBlur(1.6)).resize((W, H), Image.BILINEAR)
    s = np.asarray(lay, np.float32)[..., None] / 255.0
    return s * EMBER * 1.4 * amount


def finish(a, t, bright=1.0):
    a = a * vign * bright
    g = rng.normal(0, 0.018, (H // 2, W // 2, 1)).astype(np.float32)
    g = np.repeat(np.repeat(g, 2, 0), 2, 1)
    a = a + g * (0.4 + 0.6 * (1 - np.clip(a, 0, 1)))
    return a


# ---------- text / logo ----------
def text_img(txt, font_path, size, tracking, wght=None, color=(242, 238, 233)):
    f = ImageFont.truetype(font_path, size)
    if wght:
        try:
            f.set_variation_by_axes([wght])
        except Exception:
            pass
    widths = [f.getbbox(c)[2] - f.getbbox(c)[0] if c != ' ' else size * 0.3 for c in txt]
    tw = int(sum(widths) + tracking * (len(txt) - 1)) + 20
    img = Image.new('L', (tw, int(size * 1.5)), 0)
    d = ImageDraw.Draw(img)
    x = 10
    for c, w in zip(txt, widths):
        if c != ' ':
            d.text((x - f.getbbox(c)[0], int(size * 0.15)), c, font=f, fill=255)
        x += w + tracking
    return img.crop(img.getbbox())


def logo_img(width):
    lg = Image.open(LOGO).convert('RGB')
    a = np.asarray(lg, np.float32)
    L = a.mean(axis=2)
    bg = np.median(L)
    alpha = np.clip((L - bg - 25) / (235 - bg - 25), 0, 1)
    im = Image.fromarray((alpha * 255).astype(np.uint8))
    bb = im.point(lambda v: 255 if v > 90 else 0).getbbox()
    im = im.crop((bb[0] - 6, bb[1] - 6, bb[2] + 6, bb[3] + 6))
    h = int(im.height * width / im.width)
    return im.resize((width, h), Image.LANCZOS)


T_ONE = text_img('1 / 1', 'Cinzel.ttf', 170, 30, wght=400)
T_NAME = text_img('ÓNIX ROSÉ', 'Cinzel.ttf', 46, 22, wght=400)
T_LOGO = logo_img(700)


def paste(canvas, mask, cy, alpha):
    if alpha <= 0:
        return canvas
    m = np.asarray(mask, np.float32) / 255.0 * alpha
    h, w = m.shape
    x0, y0 = (W - w) // 2, int(cy - h / 2)
    col = np.array([242, 238, 233], np.float32) / 255.0
    reg = canvas[y0:y0 + h, x0:x0 + w]
    canvas[y0:y0 + h, x0:x0 + w] = reg * (1 - m[..., None]) + col * m[..., None]
    return canvas


def fade(t, a, b, d=0.35):
    return ease((t - a) / d) * (1 - ease((t - (b - d)) / d))


# ---------- timeline ----------
def frame(i):
    t = i / FPS
    if t < 2.0:  # S1 HOOK — macro of case side, ember breathing
        p = t / 2.0
        a, m = view(CROWN[0] - 22, CROWN[1] + 70, 4.3 + 0.25 * p)
        b = grade(a)
        a = ember_light(b * 0.10, m, t, 1.5, pos=(612, 625), radius=105.0, base=b)
        a = finish(a, t, ease(t / 0.6))
    elif t < 5.0:  # S2 reveal — pull back to full watch
        p = ease((t - 2.0) / 3.0)
        cx = CROWN[0] - 22 + (DIAL[0] + 8 - (CROWN[0] - 22)) * p
        cy = CROWN[1] + 70 + (DIAL[1] + 10 - (CROWN[1] + 70)) * p
        z = math.exp(math.log(4.55) + (math.log(1.22) - math.log(4.55)) * p)
        a, m = view(cx, cy, z)
        b = grade(a)
        a = b * (0.10 + 0.78 * p)
        a = ember_light(a, m, t, 1.5 * (1 - p), pos=(612, 625), radius=105.0 + 250 * p, base=b)
        a = ember_light(a, m, t, 0.7 * p)
        sl = sparks_layer(t, 0.5 * p, m)
        if sl is not None:
            a = a + sl
        a = finish(a, t, 1.0 - 0.9 * ease((t - 4.85) / 0.15))
    elif t < 8.0:  # S3 dial macro with warm light sweep
        p = (t - 5.0) / 3.0
        a, m = view(DIAL[0], DIAL[1] + 4, 2.0 + 0.12 * p)
        a = grade(a) * 0.62
        a = ember_light(a, m, t, 0.35)
        a = sweep(a, t, 5.25, 7.7)
        a = finish(a, t, ease((t - 5.0) / 0.2) * (1 - 0.9 * ease((t - 7.85) / 0.15)))
    elif t < 13.0:  # S4 world (lateral slider) -> S5 embers die out
        p = (t - 8.0) / 5.0
        a, m = view(DIAL[0] - 22 + 50 * ease(p), DIAL[1] + 40, 1.04 + 0.05 * p)
        a = grade(a)
        die = ease((t - 11.0) / 1.8)
        # S5: only the highlights survive
        a = a * (0.95 - 0.55 * die)
        if die > 0:
            L = lum(a)
            a = a * (1 - die) + a * np.clip((L - 0.18) / 0.5, 0, 1) ** 1.2 * die
        a = ember_light(a, m, t, 0.75 * (1 - die))
        sl = sparks_layer(t, 1.0 * (1 - die), m)
        if sl is not None:
            a = a + sl
        a = finish(a, t, ease((t - 8.0) / 0.2) * (1 - ease((t - 12.6) / 0.4)))
    else:  # S6 end card
        a = np.zeros((H, W, 3), np.float32)
        a = paste(a, T_ONE, H * 0.47, fade(t, 13.15, 14.55, 0.4))
        lf = ease((t - 14.65) / 0.45)
        a = paste(a, T_LOGO, H * 0.45, lf)
        a = paste(a, T_NAME, H * 0.58, ease((t - 14.95) / 0.45))
        a = finish(a, t, 1.0) * 1.0
    return np.clip(a, 0, 1)


def main():
    if PREVIEW:
        for s in PREVIEW:
            i = int(s)
            Image.fromarray((frame(i) * 255).astype(np.uint8)).save(f'prev_{i:03d}.jpg', quality=90)
        return
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                           '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'slow',
                           '-crf', '16', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT],
                          stdin=subprocess.PIPE)
    for i in range(N):
        ff.stdin.write((frame(i) * 255 + 0.5).astype(np.uint8).tobytes())
        if i % 48 == 0:
            print('frame', i, flush=True)
    ff.stdin.close()
    ff.wait()


if __name__ == '__main__':
    main()
