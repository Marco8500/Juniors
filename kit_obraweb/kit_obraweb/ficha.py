"""Genera la ficha de un reel (los 10 puntos de la estrategia) y el .txt para publicar.
Uso: python3 -I ficha.py guiones/XXX.json  ->  videos/XXX_ficha.md + videos/XXX.txt
Solo para guiones en formato nuevo {"meta": {...}, "escenas": [...]}; con los antiguos no hace nada."""
import json, os, sys, wave

D = os.path.dirname(os.path.abspath(__file__))
GUION = os.path.abspath(sys.argv[1]); NAME = os.path.splitext(os.path.basename(GUION))[0]
g = json.load(open(GUION))
if not isinstance(g, dict):
    sys.exit(0)
m, esc = g["meta"], g["escenas"]

# tiempos reales de cada escena (mismos márgenes que reel.py)
t, tiempos = 0.0, []
for i, s in enumerate(esc):
    wav = os.path.join(D, "build", NAME, f"v{i}.wav")
    vd = (lambda w: w.getnframes() / w.getframerate())(wave.open(wav)) if os.path.exists(wav) else 0
    dur = (0.3 if i == 0 else 0.06) + vd + 0.1
    tiempos.append((t, t + dur)); t += dur

L = [f"# {m['titulo']}", "",
     f"**Formato:** {m['formato']} · **Duración:** {t:.0f} s · **Objetivo:** {m.get('objetivo', 'retención → seguidores → clientes')}", "",
     "## 1. Concepto", m["concepto"], "",
     "## 2. Gancho inicial", f"«{esc[0]['text']}»", "",
     "## 3–6. Guion por escenas", ""]
for i, (s, (a, b)) in enumerate(zip(esc, tiempos)):
    L += [f"### Escena {i + 1} · {a:.1f}–{b:.1f} s",
          f"- **Voz:** «{s['text']}»",
          f"- **Texto en pantalla:** {s.get('screen', s.get('sub', s['text']))}",
          f"- **Qué se ve:** {s.get('visual', '—')}",
          f"- **Técnica:** {s.get('tecnica', '—')}", ""]
L += ["## 7. Técnicas de retención", *[f"- {x}" for x in m["tecnicas"]], "",
      "## 8. CTA final", m["cta"], "",
      "## 9. Descripción para publicar", "**Instagram:**", "", m["descripcion_ig"], "", "**TikTok:**", "", m["descripcion_tt"], "",
      "## 10. Hashtags", " ".join(m["hashtags"]), " ".join(m.get("hashtags_tt", m["hashtags"][:7] + ["#fyp", "#parati"])), ""]
if m.get("recompensa"):
    L += ["## Compromiso de la recompensa", m["recompensa"], ""]
open(os.path.join(D, "videos", NAME + "_ficha.md"), "w").write("\n".join(L))

txt = ["===== INSTAGRAM =====", m["descripcion_ig"], "", " ".join(m["hashtags"]), "",
       "===== TIKTOK =====", m["descripcion_tt"], "", " ".join(m.get("hashtags_tt", m["hashtags"][:7] + ["#fyp", "#parati"])), ""]
open(os.path.join(D, "videos", NAME + ".txt"), "w").write("\n".join(txt))
print("ficha", os.path.join(D, "videos", NAME + "_ficha.md"))
