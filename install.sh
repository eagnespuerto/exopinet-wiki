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
# Wipe any prior install so stale files (removed modules, old assets, etc.)
# don't shadow the fresh checkout. The user's data cache at
# ~/.local/share/exopinet-wiki/ lives outside this directory and is preserved.
mkdir -p "${INSTALL_DIR}"
rm -rf \
    "${INSTALL_DIR}/exopinet_wiki" \
    "${INSTALL_DIR}/assets" \
    "${INSTALL_DIR}/${APP_NAME}" \
    "${INSTALL_DIR}/README.md" \
    "${INSTALL_DIR}/LICENSE"
cp -r \
    "${SRC_DIR}/exopinet_wiki" \
    "${SRC_DIR}/assets" \
    "${SRC_DIR}/${APP_NAME}" \
    "${SRC_DIR}/README.md" \
    "${SRC_DIR}/LICENSE" \
    "${INSTALL_DIR}/"
chmod +x "${INSTALL_DIR}/${APP_NAME}"
# Drop any stale bytecode from a previous install.
find "${INSTALL_DIR}" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true

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

INSTALLED_VERSION="$(
    python3 -c "import sys; sys.path.insert(0, '${INSTALL_DIR}'); \
                from exopinet_wiki import __version__; print(__version__)" \
        2>/dev/null || echo unknown
)"

cat <<MSG

ExoPiNet Wiki ${INSTALLED_VERSION} installed under ${INSTALL_DIR}.

  Launch from the menu (Science or Education), or run:
      exopinet-wiki

  On first run, choose "File -> Update Data" to download the catalogues.

  To update later:
      cd <this-checkout>
      git pull
      sudo ./install.sh
MSG
