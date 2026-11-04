#!/usr/bin/env bash
# Look "Formato B" a nivel de píxel (ver estilo.md): negros limpios, contraste, neutro-frío, nitidez en brillos.
# Uso: preparar_clip.sh entrada.mp4 salida.mp4 [inicio_s] [duracion_s]
#   IA=1 -> el clip ya viene escalado con IA: sin hqdn3d ni unsharp.
set -euo pipefail
IN="$1"; OUT="$2"; SS="${3:-0}"; T="${4:-3.067}"
if [ "${IA:-0}" = "1" ]; then LIMPIEZA=""; NITIDEZ=""; else LIMPIEZA="hqdn3d=3:2:4:3,"; NITIDEZ=",unsharp=5:5:0.6:5:5:0.0"; fi
ffmpeg -v error -y -ss "$SS" -i "$IN" -an -vf "\
scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,fps=30,\
${LIMPIEZA}\
curves=all='0/0 0.07/0 0.25/0.18 0.6/0.62 0.9/0.95 1/1',\
eq=contrast=1.12:saturation=0.82:gamma=0.98,\
colorbalance=bs=0.015:bm=0.005${NITIDEZ},\
tpad=stop_mode=clone:stop=6" \
 -frames:v $(python3 -c "print(round($T*30))") -c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p "$OUT"
