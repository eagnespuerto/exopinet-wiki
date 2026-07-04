#!/usr/bin/env bash
# ExoPiNet Wiki installer for 32-bit Raspberry Pi OS (Zero and above).
#
# Copies the app to /opt/exopinet-wiki, installs the launcher on PATH, and
# registers a menu entry under Science and Education.

set -euo pipefail

APP_NAME="exopinet-wiki"
INSTALL_DIR="/opt/${APP_NAME}"
BIN_LINK="/usr/local/bin/${APP_NAME}"
DESKTOP_DIR="/usr/share/applications"

if [[ $EUID -ne 0 ]]; then
    echo "This installer needs root. Run with: sudo ./install.sh" >&2
    exit 1
fi

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Installing apt dependencies"
apt-get update
apt-get install -y --no-install-recommends \
    python3 \
    python3-tk \
    python3-requests \
    python3-pil \
    python3-pil.imagetk

echo "==> Copying files to ${INSTALL_DIR}"
mkdir -p "${INSTALL_DIR}"
cp -r \
    "${SRC_DIR}/exopinet_wiki" \
    "${SRC_DIR}/assets" \
    "${SRC_DIR}/${APP_NAME}" \
    "${SRC_DIR}/README.md" \
    "${SRC_DIR}/LICENSE" \
    "${INSTALL_DIR}/"
chmod +x "${INSTALL_DIR}/${APP_NAME}"

echo "==> Linking launcher to ${BIN_LINK}"
ln -sf "${INSTALL_DIR}/${APP_NAME}" "${BIN_LINK}"

echo "==> Installing desktop entry"
install -Dm644 "${SRC_DIR}/${APP_NAME}.desktop" "${DESKTOP_DIR}/${APP_NAME}.desktop"
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${DESKTOP_DIR}" || true
fi

# Provide a lightweight icon fallback if one wasn't shipped in assets/.
if [[ ! -f "${INSTALL_DIR}/assets/icon.png" ]]; then
    cp "${INSTALL_DIR}/assets/bmp/terrestrial.bmp" "${INSTALL_DIR}/assets/icon.png" 2>/dev/null || true
fi

cat <<MSG

ExoPiNet Wiki installed.

  Launch from the menu (Science or Education), or run:
      exopinet-wiki

  On first run, choose "File -> Update Data" to download the catalogues.
MSG
