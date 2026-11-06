#!/usr/bin/env bash
# Abre Jarvis otra vez (después de haber ejecutado instalar.sh una vez).
set -e
DESTINO="${DESTINO:-$HOME/OpenJarvis}"
export PATH="$HOME/.local/bin:$PATH"
curl -s -m 2 http://127.0.0.1:11434/api/version >/dev/null || { (ollama serve >/dev/null 2>&1 &); sleep 3; }
cd "$DESTINO" && uv run jarvis gui
