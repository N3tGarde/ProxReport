#!/usr/bin/env bash
set -e

[[ $EUID -ne 0 ]] && echo "Run as root" && exit 1

echo "=== ProxReport Uninstaller ==="
echo

systemctl stop proxreport || true
systemctl disable proxreport || true
rm -f /etc/systemd/system/proxreport.service
systemctl daemon-reload

read -rp "Delete /opt/proxreport? [y/N]: " R1
[[ $R1 == "y" ]] && rm -rf /opt/proxreport

read -rp "Delete /etc/proxreport (config, users, TLS)? [y/N]: " R2
[[ $R2 == "y" ]] && rm -rf /etc/proxreport

echo "✔ ProxReport removed"
