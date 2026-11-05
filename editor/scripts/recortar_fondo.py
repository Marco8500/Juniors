"""Deja solo el producto (y brazo/mano) sobre negro, sin destellos.
Uso: recortar_fondo.py entrada.mp4 salida.mp4 modelo [paso] [mascara.npy]
  modelo: isnet-general-use (macros) | birefnet-general-lite (muñeca/brazo)
  paso: calcula la máscara cada N frames e interpola (por defecto 2)
  mascara.npy: caché de máscaras (540x960). Si existe no se vuelve a pasar la IA.
Estabilización (estilo.md): percentil 80 en ventana temporal de 7 frames
(un píxel que la IA pierde 1-2 frames se mantiene), dilatación de 6 px y borde suave."""
import os, sys, subprocess, numpy as np, cv2
from PIL import Image

src, out, model = sys.argv[1], sys.argv[2], sys.argv[3]
paso = int(sys.argv[4]) if len(sys.argv) > 4 else 2
cache = sys.argv[5] if len(sys.argv) > 5 else None
W, H, w, h = 1080, 1920, 540, 960
VENTANA = int(os.environ.get('VENTANA', 7)); PERCENTIL = float(os.environ.get('PERCENTIL', 80))
DILATA, BORDE = 6, 3
UNION = os.environ.get('UNION') == '1'  # máscara = unión de todo el plano (macros inestables)

raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                     capture_output=True, check=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3); del raw
n = len(fr)

if cache and os.path.exists(cache):
    masks = np.load(cache).astype(np.float32) / 255
else:
    from rembg import remove, new_session
    s = new_session(model)
    idx = sorted(set(list(range(0, n, paso)) + [n - 1]))
    mk = {}
    for i in idx:
        small = Image.fromarray(fr[i]).resize((w, h), Image.BILINEAR)
        mk[i] = np.asarray(remove(small, session=s, only_mask=True)).astype(np.float32) / 255
        print(f"máscara {i + 1}/{n}", flush=True)
    masks = np.empty((n, h, w), np.float32)
    for i in range(n):
        if i in mk:
            masks[i] = mk[i]; continue
        a = max(k for k in mk if k < i); b = min(k for k in mk if k > i); t = (i - a) / (b - a)
        masks[i] = mk[a] * (1 - t) + mk[b] * t
    if cache:
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        np.save(cache, (masks * 255).astype(np.uint8))

# Estabilización temporal: percentil alto en ventana -> sin huecos momentáneos
r = VENTANA // 2
est = np.empty_like(masks)
if UNION:
    u = np.percentile(masks, 90, axis=0)
    est[:] = u
else:
    for i in range(n):
        est[i] = np.percentile(masks[max(0, i - r):i + r + 1], PERCENTIL, axis=0)
kern = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * DILATA // 2 + 1, 2 * DILATA // 2 + 1))

enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                        "-r", "30", "-i", "-", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                        "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
for i in range(n):
    m = cv2.dilate(est[i], kern)
    m = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)
    m = cv2.GaussianBlur(m, (0, 0), BORDE)
    m = np.clip((m - 0.05) / 0.75, 0, 1)[..., None]
    enc.stdin.write((fr[i].astype(np.float32) * m).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); print("OK", out)
