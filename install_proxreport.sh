#!/usr/bin/env bash
set -e

[[ $EUID -ne 0 ]] && echo "Run as root" && exit 1

REPO_URL="https://github.com/N3tGarde/proxreport.git"
INSTALL_DIR="/opt/proxreport"
CONFIG_DIR="/etc/proxreport"
SERVICE_FILE="/etc/systemd/system/proxreport.service"

echo "=== ProxReport Installer ==="
echo

read -rp "Puerto HTTP (default 8080): " HTTP_PORT
HTTP_PORT=${HTTP_PORT:-8080}

read -rp "Puerto HTTPS (default 8443): " HTTPS_PORT
HTTPS_PORT=${HTTPS_PORT:-8443}

read -rp "Do you want to use 80/443? [y/N]: " USE_PRIV
USE_PRIV=${USE_PRIV,,}

### Repo
if [[ ! -d $INSTALL_DIR ]]; then
  git clone "$REPO_URL" "$INSTALL_DIR"
else
  git -C "$INSTALL_DIR" pull
fi

mkdir -p "$CONFIG_DIR/tls"

### TLS
if [[ ! -f "$CONFIG_DIR/tls/cert.pem" ]]; then
  openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout "$CONFIG_DIR/tls/key.pem" \
    -out "$CONFIG_DIR/tls/cert.pem" \
    -days 365 \
    -subj "/CN=$(hostname)"
fi

### Config
if [[ ! -f "$CONFIG_DIR/config.ini" ]]; then
  cp "$INSTALL_DIR/config.example.ini" "$CONFIG_DIR/config.ini"
  sed -i \
    -e "s/^http_port.*/http_port = $HTTP_PORT/" \
    -e "s/^https_port.*/https_port = $HTTPS_PORT/" \
    "$CONFIG_DIR/config.ini"
fi

### User
if [[ ! -f "$CONFIG_DIR/users.txt" ]]; then
  echo "Creating admin user"
  python3 -m proxreport hash-password --username admin > "$CONFIG_DIR/users.txt"
  chmod 600 "$CONFIG_DIR/users.txt"
fi

### Systemd
cp "$INSTALL_DIR/systemd/proxreport.service" "$SERVICE_FILE"

if [[ "$USE_PRIV" != "y" ]]; then
  sed -i '/CAP_NET_BIND_SERVICE/d' "$SERVICE_FILE"
fi

systemctl daemon-reload
systemctl enable --now proxreport

echo
echo "✔ Installation ProxReport completed"
echo "URL: https://$(hostname):$HTTPS_PORT"