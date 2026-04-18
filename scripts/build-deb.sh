#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build"
PKG_ROOT="${BUILD_DIR}/openvpn-desk-pkg"
PKG_OUT="${BUILD_DIR}/openvpn-desk_1.0.0_all.deb"

rm -rf "${PKG_ROOT}"
mkdir -p "${PKG_ROOT}"

cp -a "${ROOT_DIR}/packaging/deb/." "${PKG_ROOT}/"

install -d "${PKG_ROOT}/usr/share/openvpn-desk/openvpndesk"
install -d "${PKG_ROOT}/usr/lib/openvpn-desk"
install -d "${PKG_ROOT}/usr/share/polkit-1/actions"
install -d "${PKG_ROOT}/etc/polkit-1/rules.d"
install -d "${PKG_ROOT}/etc/systemd/system"
install -d "${PKG_ROOT}/usr/share/icons/hicolor/256x256/apps"

cp -a "${ROOT_DIR}/openvpndesk/." "${PKG_ROOT}/usr/share/openvpn-desk/openvpndesk/"
find "${PKG_ROOT}/usr/share/openvpn-desk" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "${PKG_ROOT}/usr/share/openvpn-desk" -type f -name '*.pyc' -delete
install -m644 "${ROOT_DIR}/assets/openvpn-desk.png" "${PKG_ROOT}/usr/share/icons/hicolor/256x256/apps/openvpn-desk.png"
install -m755 "${ROOT_DIR}/helper/helper.py" "${PKG_ROOT}/usr/lib/openvpn-desk/helper.py"
install -m644 "${ROOT_DIR}/helper/in.openvpndesk.helper.policy" "${PKG_ROOT}/usr/share/polkit-1/actions/in.openvpndesk.helper.policy"
install -m644 "${ROOT_DIR}/helper/49-openvpn-desk.rules" "${PKG_ROOT}/etc/polkit-1/rules.d/49-openvpn-desk.rules"
install -m644 "${ROOT_DIR}/helper/openvpn-desk@.service" "${PKG_ROOT}/etc/systemd/system/openvpn-desk@.service"

chmod 755 "${PKG_ROOT}/usr/bin/openvpn-desk"
chmod 755 "${PKG_ROOT}/DEBIAN/postinst"
chmod 755 "${PKG_ROOT}/DEBIAN/prerm"
chmod 644 "${PKG_ROOT}/DEBIAN/control"
chmod 644 "${PKG_ROOT}/usr/share/applications/in.openvpndesk.app.desktop"
chmod 644 "${PKG_ROOT}/usr/share/polkit-1/actions/in.openvpndesk.helper.policy"
chmod 644 "${PKG_ROOT}/etc/polkit-1/rules.d/49-openvpn-desk.rules"
chmod 644 "${PKG_ROOT}/etc/systemd/system/openvpn-desk@.service"
chmod 644 "${PKG_ROOT}/usr/share/icons/hicolor/256x256/apps/openvpn-desk.png"
find "${PKG_ROOT}/usr/share/openvpn-desk" -type f \( -name '*.py' -o -name '*.css' \) -exec chmod 644 {} +

rm -f "${PKG_OUT}"
dpkg-deb --root-owner-group --build "${PKG_ROOT}" "${PKG_OUT}"
