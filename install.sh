#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="/opt/paperless-letter-generator"
DATA_DIR="/var/lib/paperless-letter-generator"
SERVICE_NAME="paperless-letter-generator"
SERVICE_USER="paperless-letter"
ENV_FILE="/etc/paperless-letter-generator.env"

echo "=== Paperless Letter Generator Installation / Update ==="
echo ""

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root (sudo)." >&2
  exit 1
fi

echo "[1/8] Installing system packages..."
apt-get update -qq
apt-get install -y -qq \
  python3 python3-venv python3-pip \
  nodejs npm \
  texlive-latex-base texlive-latex-extra \
  texlive-fonts-recommended texlive-lang-german \
  build-essential curl rsync 2>/dev/null

echo "[2/8] Creating system user..."
id -u "$SERVICE_USER" &>/dev/null || useradd -r -s /bin/false -m -d "$DATA_DIR" "$SERVICE_USER"

echo "[3/8] Copying files..."
mkdir -p "$INSTALL_DIR" "$DATA_DIR"
rsync -a --delete \
  --exclude='node_modules' \
  --exclude='.venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.git' \
  . "$INSTALL_DIR"
find "$INSTALL_DIR" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
find "$INSTALL_DIR" -name '*.pyc' -delete 2>/dev/null || true
chown -R "$SERVICE_USER:$SERVICE_USER" "$DATA_DIR"
chown -R root:root "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"

echo "[4/8] Setting up Python virtual environment..."
cd "$INSTALL_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet --upgrade -e .

echo "[5/8] Building frontend..."
if [[ -f "static/index.html" ]]; then
  echo "Using pre-built frontend from repository."
else
  cd frontend
  NODE_OPTIONS="--max-old-space-size=512" npm install
  NODE_OPTIONS="--max-old-space-size=512" npm run build
  cd ..
fi

echo "[6/8] Configuring..."
if [[ ! -f "$ENV_FILE" ]]; then
  echo ""
  echo "--- Paperless-ngx API Configuration ---"
  read -rp "Paperless-ngx URL (z.B. http://192.168.1.100:8000): " PAPERLESS_URL
  read -rp "Paperless-ngx API Token: " PAPERLESS_TOKEN
  read -rp "Listen port [8050]: " LISTEN_PORT
  LISTEN_PORT=${LISTEN_PORT:-8050}
  cat > "$ENV_FILE" <<EOF
PAPERLESS_API_URL=${PAPERLESS_URL}
PAPERLESS_API_TOKEN=${PAPERLESS_TOKEN}
LISTEN_HOST=0.0.0.0
LISTEN_PORT=${LISTEN_PORT}
DATABASE_URL=sqlite:///${DATA_DIR}/data.db
DATA_DIR=${DATA_DIR}
LOG_LEVEL=info
EOF
  chmod 600 "$ENV_FILE"
  echo "Configuration written to $ENV_FILE"
else
  echo "Config file already exists, skipping."
  source "$ENV_FILE"
fi

echo "[7/8] Running database migrations..."
source .venv/bin/activate
cd "$INSTALL_DIR"
mkdir -p "$DATA_DIR"
export $(grep -v '^#' "$ENV_FILE" | xargs)
DATABASE_URL="sqlite:///${DATA_DIR}/data.db"
alembic upgrade head

echo "[8/8] Installing systemd service..."
cp "$INSTALL_DIR/systemd/$SERVICE_NAME.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

echo ""
echo "=== Installation / Update complete! ==="
echo ""
echo "Service: $SERVICE_NAME"
source "$ENV_FILE"
echo "URL: http://$(hostname -I | awk '{print $1}'):${LISTEN_PORT:-8050}"
echo ""
echo "Add this as a Custom Link in Paperless-ngx:"
echo "  Settings -> Custom Links -> Name: 'Letter Generator', URL: http://YOUR_VM_IP:${LISTEN_PORT:-8050}"
echo ""
echo "Check status: systemctl status $SERVICE_NAME"
echo "View logs: journalctl -u $SERVICE_NAME -f"
