#!/bin/bash
# Uso: ./crear.sh guiones/XXX.json  -> videos/XXX.mp4 + _portada.jpg + .txt (+ _ficha.md con guiones del formato nuevo)
# Elige el motor solo: reel.py (reels con explosión) o render.py (motor antiguo, guion 001).
set -e; P=$(cd "$(dirname "$0")" && pwd)
MOTOR=$(python3 -I -c "
import json, sys
g = json.load(open(sys.argv[1])); g = g['escenas'] if isinstance(g, dict) else g
print('render.py' if g[0]['kind'] == 'hook' else 'reel.py')" "$1")
bash $P/voz.sh "$1" && python3 -I $P/$MOTOR "$1"
python3 -I $P/ficha.py "$1"
T="${1%.json}.txt"; [ -f "$T" ] && cp "$T" $P/videos/ || true
