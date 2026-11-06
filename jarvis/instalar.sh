#!/usr/bin/env bash
# Instala OpenJarvis + la pestaña "Jarvis" con orbe animado + un modelo local gratis (Ollama).
# Funciona en macOS, Linux y Windows (dentro de WSL2). Uso:  bash instalar.sh
set -euo pipefail

AQUI="$(cd "$(dirname "$0")" && pwd)"
DESTINO="${DESTINO:-$HOME/OpenJarvis}"
COMMIT="103b1227cb65af71fa930de0945e8d11844aef11"   # versión con la que se probó el parche
MODELO="${MODELO:-qwen2.5:3b}"

paso() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }

paso "Comprobando git, curl y Node.js"
for c in git curl; do command -v "$c" >/dev/null || { echo "Falta '$c'. Instálalo y vuelve a ejecutar."; exit 1; }; done
if ! command -v node >/dev/null || [ "$(node -p 'process.versions.node.split(".")[0]')" -lt 22 ]; then
  echo "Necesitas Node.js 22 o más nuevo: https://nodejs.org (descarga la versión LTS) y vuelve a ejecutar."
  exit 1
fi

paso "Instalando uv (gestor de Python) si hace falta"
if ! command -v uv >/dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

paso "Descargando OpenJarvis en $DESTINO"
if [ ! -d "$DESTINO/.git" ]; then
  git clone https://github.com/open-jarvis/OpenJarvis.git "$DESTINO"
fi
cd "$DESTINO"
git fetch --quiet origin "$COMMIT" 2>/dev/null || git fetch --quiet origin
git checkout --quiet "$COMMIT"

paso "Añadiendo la pestaña Jarvis"
if git apply --check "$AQUI/jarvis-tab.patch" 2>/dev/null; then
  git apply "$AQUI/jarvis-tab.patch"
else
  echo "(la pestaña ya estaba añadida)"
fi

paso "Instalando dependencias de Python"
uv sync

paso "Instalando dependencias de la interfaz"
(cd frontend && npx -y npm@11 ci --no-audit --no-fund)

paso "Instalando Ollama (modelos locales gratis)"
if ! command -v ollama >/dev/null; then
  if [ "$(uname)" = "Darwin" ]; then
    echo "En Mac instala Ollama desde https://ollama.com/download, ábrelo una vez y vuelve a ejecutar este script."
    exit 1
  fi
  command -v zstd >/dev/null || { sudo apt-get update && sudo apt-get install -y zstd; } || true
  curl -fsSL https://ollama.com/install.sh | sh
fi
if ! curl -s -m 2 http://127.0.0.1:11434/api/version >/dev/null; then
  (ollama serve >/dev/null 2>&1 &)
  sleep 3
fi

paso "Descargando el modelo $MODELO (unos 2 GB, solo la primera vez)"
ollama pull "$MODELO"

paso "Configurando OpenJarvis para usar Ollama"
mkdir -p "$HOME/.openjarvis"
CFG="$HOME/.openjarvis/config.toml"
if ! grep -q '^\[engine\]' "$CFG" 2>/dev/null; then
  cat >> "$CFG" <<CONF

[engine]
default = "ollama"

[intelligence]
default_model = "$MODELO"
CONF
fi

paso "¡Listo! Abriendo Jarvis…"
echo "Cuando se abra el navegador, entra en la pestaña 'Jarvis' del menú (usa Chrome o Edge)."
echo "Para volver a abrirlo otro día:  bash $AQUI/abrir.sh"
uv run jarvis gui
