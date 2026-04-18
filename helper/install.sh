#!/bin/bash
set -e

if [[ $EUID -ne 0 ]]; then
    echo "Run this installer as root."
    exit 1
fi

INSTALL_USER="${SUDO_USER:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[+] Installing OpenVPN Desk helper"

install -d -m755 -o root -g root /etc/openvpn-desk
install -d -m755 -o root -g root /etc/openvpn-desk/profiles

install -Dm755 "${SCRIPT_DIR}/helper.py" /usr/lib/openvpn-desk/helper.py
install -Dm644 "${SCRIPT_DIR}/in.openvpndesk.helper.policy" /usr/share/polkit-1/actions/in.openvpndesk.helper.policy
install -Dm644 "${SCRIPT_DIR}/49-openvpn-desk.rules" /etc/polkit-1/rules.d/49-openvpn-desk.rules
install -Dm644 "${SCRIPT_DIR}/openvpn-desk@.service" /etc/systemd/system/openvpn-desk@.service

systemctl daemon-reload

echo "[+] Installation complete."
if [[ -n "${INSTALL_USER}" && "${INSTALL_USER}" != "root" ]]; then
    echo "[+] Local users can now access the OpenVPN Desk helper without extra group setup."
fi
