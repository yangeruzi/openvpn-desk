#!/bin/bash
set -e

echo "[+] Installing YangzLinuxVpnClient helper"

install -Dm755 helper.py /usr/lib/yangzvpn/helper.py
install -Dm644 policy.xml /usr/share/polkit-1/actions/in.yangz.vpn.helper.policy

echo "[+] Installation complete."
echo "You may need to log out and log back in for polkit to refresh."
