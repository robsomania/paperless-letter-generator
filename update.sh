#!/usr/bin/env bash
set -euo pipefail

SRC="/mnt/paperless/paperless-letter-generator"
DST="/opt/paperless-letter-generator"

echo "=== Paperless Letter Generator Update ==="

# Nur Python-Dateien und Frontend kopieren (nicht node_modules, .venv, etc.)
echo "[1/3] Copying updated files..."
rsync -av --delete \
  --exclude='.venv' \
  --exclude='frontend/node_modules' \
  --exclude='frontend/dist' \
  --exclude='static' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.git' \
  "$SRC/" "$DST/"

# Falls rsync nicht installiert, fallback auf cp
# cp -r "$SRC/app" "$DST/"
# cp -r "$SRC/frontend/src" "$DST/frontend/src/"
# cp -r "$SRC/systemd" "$DST/systemd/"
# cp "$SRC/install.sh" "$DST/"
# cp "$SRC/pyproject.toml" "$DST/"

echo "[2/3] Rebuilding frontend..."
cd "$DST/frontend"
npm run build

echo "[3/3] Restarting service..."
systemctl restart paperless-letter-generator

echo "=== Update complete ==="
