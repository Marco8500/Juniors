#!/bin/bash
# Instala lo necesario: voz (piper + modelo es_ES-davefx-medium desde github) y la fuente Inter si falta.
set -e; P=$(cd "$(dirname "$0")" && pwd); M=$P/modelos; mkdir -p $M
pip install -q piper-tts pillow numpy
[ -d $M/vits-piper-es_ES-davefx-medium ] || curl -sSL https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-es_ES-davefx-medium.tar.bz2 | tar xj -C $M
F=/usr/share/fonts/opentype/inter
[ -f $F/Inter-Black.otf ] || { mkdir -p $F && cp $P/assets/fonts/*.otf $F/; }
which ffmpeg >/dev/null || echo "FALTA ffmpeg: instálalo (apt-get install -y ffmpeg)"
echo "instalado"
