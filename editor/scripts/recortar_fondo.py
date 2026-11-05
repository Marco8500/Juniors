"""Deja solo el producto (y brazo/mano) sobre negro. Uso:
recortar_fondo.py entrada.mp4 salida.mp4 modelo [paso]
modelo: isnet-general-use (macros) | birefnet-general-lite (muñeca/brazo)
paso: calcula la máscara cada N frames e interpola (por defecto 2).
La máscara se suaviza en el tiempo (media de 3) y en el borde (blur 2 px) para que no parpadee."""
import sys, subprocess, numpy as np, cv2
from PIL import Image
from rembg import remove, new_session
src, out, model = sys.argv[1], sys.argv[2], sys.argv[3]
paso = int(sys.argv[4]) if len(sys.argv) > 4 else 2
W, H = 1080, 1920
raw = subprocess.run(["ffmpeg","-v","error","-i",src,"-f","rawvideo","-pix_fmt","rgb24","-"],capture_output=True,check=True).stdout
fr = np.frombuffer(raw,np.uint8).reshape(-1,H,W,3); del raw
n = len(fr); s = new_session(model)
idx = list(range(0,n,paso)); idx[-1:] = [idx[-1]] if idx[-1]==n-1 else [idx[-1], n-1]
mk = {}
for i in idx:
    small = Image.fromarray(fr[i]).resize((540,960), Image.BILINEAR)
    m = np.asarray(remove(small, session=s, only_mask=True)).astype(np.float32)/255
    mk[i] = m
    print(f"máscara {i+1}/{n}", flush=True)
masks = []
for i in range(n):
    if i in mk: masks.append(mk[i]); continue
    a = max(k for k in mk if k < i); b = min(k for k in mk if k > i); t = (i-a)/(b-a)
    masks.append(mk[a]*(1-t)+mk[b]*t)
masks = np.stack(masks)
sm = masks.copy()
for i in range(n):
    sm[i] = masks[max(0,i-1):i+2].mean(0)
enc = subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r","30","-i","-",
  "-c:v","libx264","-crf","16","-preset","medium","-pix_fmt","yuv420p",out],stdin=subprocess.PIPE)
for i in range(n):
    m = cv2.GaussianBlur(cv2.resize(sm[i],(W,H),interpolation=cv2.INTER_LINEAR),(0,0),2)
    m = np.clip((m-0.08)/0.84,0,1)[...,None]  # bordes limpios
    enc.stdin.write((fr[i].astype(np.float32)*m).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); print("OK", out)
