#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="/opt/paperless-letter-generator"
DATA_DIR="/var/lib/paperless-letter-generator"
SERVICE_NAME="paperless-letter-generator"
SERVICE_USER="paperless-letter"
ENV_FILE="/etc/paperless-letter-generator.env"

echo "=== Paperless Letter Generator Installation ==="
echo ""

# --- Prerequisites ---
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
  build-essential curl 2>/dev/null

# --- Create user ---
echo "[2/8] Creating system user..."
id -u "$SERVICE_USER" &>/dev/null || useradd -r -s /bin/false -m -d "$DATA_DIR" "$SERVICE_USER"

# --- Create directories ---
echo "[3/8] Creating directories..."
mkdir -p "$INSTALL_DIR" "$DATA_DIR"
cp -r . "$INSTALL_DIR"
chown -R "$SERVICE_USER:$SERVICE_USER" "$DATA_DIR"
chown -R root:root "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"

# --- Python venv ---
echo "[4/8] Setting up Python virtual environment..."
cd "$INSTALL_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -e .

# --- Build frontend ---
echo "[5/8] Building frontend..."
if [[ -f "$INSTALL_DIR/static/index.html" ]]; then
  echo "Frontend already built, skipping."
else
  cd "$INSTALL_DIR/frontend"
  npm install
  npm run build
  cd "$INSTALL_DIR"
fi

# --- Configuration ---
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

# --- Database migration ---
echo "[7/8] Running database migrations..."
source .venv/bin/activate
cd "$INSTALL_DIR"
mkdir -p "$DATA_DIR"
export $(grep -v '^#' "$ENV_FILE" | xargs)
DATABASE_URL="sqlite:///${DATA_DIR}/data.db"
alembic upgrade head

# --- Seed default templates ---
python3 -c "
import sqlite3, uuid
db_path = '$DATA_DIR/data.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()
count = cur.execute('SELECT COUNT(*) FROM latex_templates').fetchone()[0]
if count == 0:
    import json
    templates = [
        ('Formeller Geschäftsbrief', 'Standard Geschäftsbrief nach DIN 5008 mit scrlttr2',
         open('$INSTALL_DIR/app/default_templates/formal_business.tex').read(),
         json.dumps({
             'sender_name': {'label': 'Absender Name', 'type': 'text', 'required': True},
             'sender_street': {'label': 'Straße', 'type': 'text', 'required': True},
             'sender_zip_city': {'label': 'PLZ Ort', 'type': 'text', 'required': True},
             'sender_email': {'label': 'E-Mail', 'type': 'text', 'required': False},
             'sender_phone': {'label': 'Telefon', 'type': 'text', 'required': False},
             'recipient_name': {'label': 'Empfänger Name', 'type': 'text', 'required': True},
             'recipient_gender': {'label': 'Anrede (e/r)', 'type': 'text', 'required': False},
             'recipient_company': {'label': 'Firma', 'type': 'text', 'required': False},
             'recipient_street': {'label': 'Straße', 'type': 'text', 'required': True},
             'recipient_zip_city': {'label': 'PLZ Ort', 'type': 'text', 'required': True},
             'subject': {'label': 'Betreff', 'type': 'text', 'required': True},
             'place': {'label': 'Ort', 'type': 'text', 'required': False},
             'date': {'label': 'Datum', 'type': 'date', 'required': True},
             'body': {'label': 'Text', 'type': 'textarea', 'required': True},
         })),
        ('Persönlicher Brief', 'Informeller persönlicher Brief',
         open('$INSTALL_DIR/app/default_templates/personal.tex').read(),
         json.dumps({
             'sender_name': {'label': 'Absender Name', 'type': 'text', 'required': True},
             'sender_street': {'label': 'Straße', 'type': 'text', 'required': True},
             'sender_zip_city': {'label': 'PLZ Ort', 'type': 'text', 'required': True},
             'recipient_name': {'label': 'Empfänger Name', 'type': 'text', 'required': True},
             'recipient_gender': {'label': 'Anrede (e/r)', 'type': 'text', 'required': False},
             'recipient_street': {'label': 'Straße', 'type': 'text', 'required': True},
             'recipient_zip_city': {'label': 'PLZ Ort', 'type': 'text', 'required': True},
             'subject': {'label': 'Betreff', 'type': 'text', 'required': False},
             'place': {'label': 'Ort', 'type': 'text', 'required': False},
             'date': {'label': 'Datum', 'type': 'date', 'required': True},
             'body': {'label': 'Text', 'type': 'textarea', 'required': True},
             'closing': {'label': 'Grußformel', 'type': 'text', 'required': False},
         })),
    ]
    cur.executemany(
        'INSERT INTO latex_templates (name, description, latex_source, variable_config, created_at, updated_at) VALUES (?, ?, ?, ?, datetime(), datetime())',
        templates
    )
    conn.commit()
    print('Default templates seeded.')
else:
    print('Templates already exist, skipping seed.')
conn.close()
"

echo "[8/8] Installing systemd service..."
cp "$INSTALL_DIR/systemd/$SERVICE_NAME.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

echo ""
echo "=== Installation complete! ==="
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
