"""Escalado x4 con Real-ESRGAN (CPU). Uso: escalar_ia.py entrada.mp4 salida.mp4 inicio duracion [modelo.pth]
Salida 1080x1920 (escala x4 y luego ajusta a 1080x1920 con lanczos)."""
import sys, subprocess, numpy as np, torch, time
from spandrel import ModelLoader
src, out, ss, t = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
mp = sys.argv[5] if len(sys.argv) > 5 else "/home/user/Juniors/editor/modelos/realesr-general-x4v3.pth"
torch.set_num_threads(4)
m = ModelLoader().load_from_file(mp).eval()
probe = subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height","-of","csv=p=0",src],capture_output=True,text=True).stdout.strip().split(",")
w, h = int(probe[0]), int(probe[1])
dec = subprocess.Popen(["ffmpeg","-v","error","-ss",ss,"-t",t,"-i",src,"-vf","fps=30","-f","rawvideo","-pix_fmt","rgb24","-"],stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{w*4}x{h*4}","-r","30","-i","-",
  "-vf","scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920","-c:v","libx264","-crf","14","-preset","medium","-pix_fmt","yuv420p",out],stdin=subprocess.PIPE)
n, t0 = 0, time.time()
with torch.inference_mode():
    while True:
        buf = dec.stdout.read(w*h*3)
        if len(buf) < w*h*3: break
        x = torch.from_numpy(np.frombuffer(buf,np.uint8).reshape(h,w,3).copy()).permute(2,0,1).float().div(255).unsqueeze(0)
        y = m(x).clamp(0,1).mul(255).round().byte()[0].permute(1,2,0).numpy()
        enc.stdin.write(y.tobytes()); n += 1
enc.stdin.close(); enc.wait()
print(f"{n} frames en {time.time()-t0:.1f}s")
