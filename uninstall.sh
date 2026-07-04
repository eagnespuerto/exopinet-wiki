#!/usr/bin/env bash
# Remove ExoPiNet Wiki. Leaves the cached data in ~/.local/share/exopinet-wiki
# alone so re-installing preserves the local catalogue.

set -euo pipefail

APP_NAME="exopinet-wiki"
INSTALL_DIR="/opt/${APP_NAME}"
BIN_LINK="/usr/local/bin/${APP_NAME}"
DESKTOP_FILE="/usr/share/applications/${APP_NAME}.desktop"

if [[ $EUID -ne 0 ]]; then
    echo "This uninstaller needs root. Run with: sudo ./uninstall.sh" >&2
    exit 1
fi

rm -f "${BIN_LINK}"
rm -f "${DESKTOP_FILE}"
rm -rf "${INSTALL_DIR}"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications || true
fi

echo "ExoPiNet Wiki removed."
echo "Cached data at ~/.local/share/exopinet-wiki was NOT deleted."
