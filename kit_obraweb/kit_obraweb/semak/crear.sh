#!/bin/bash
# SEMAK · Uso: ./crear.sh guiones/XXX.json -> videos/XXX.mp4 + _portada.jpg + .txt + _ficha.md
set -e; P=$(cd "$(dirname "$0")" && pwd)
bash $P/voz.sh "$1" && python3 -I $P/reel_semak.py "$1"
python3 -I $P/ficha.py "$1"
