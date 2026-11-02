#!/usr/bin/env bash
set -euo pipefail

APP_NAME="Music Downloader"
APP_ID="music-downloader"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${HOME}/.local/share/${APP_ID}"
DESKTOP_DIR="${HOME}/.local/share/applications"

if ! command -v pacman >/dev/null 2>&1; then
    echo "This installer is for Arch Linux (pacman) only."
    echo "For other operating systems, follow the manual instructions in README.md."
    exit 1
fi

if [[ ! -f "${SCRIPT_DIR}/music_downloader.py" ]]; then
    echo "Cannot find music_downloader.py beside this installer."
    exit 1
fi

echo "Installing required Arch Linux packages..."
sudo pacman -S --needed python tk yt-dlp ffmpeg

mkdir -p "${INSTALL_DIR}" "${DESKTOP_DIR}"
install -m 644 "${SCRIPT_DIR}/music_downloader.py" "${INSTALL_DIR}/music_downloader.py"

cat > "${DESKTOP_DIR}/${APP_ID}.desktop" <<EOF
[Desktop Entry]
Name=${APP_NAME}
Comment=Save authorized audio as MP3 with artwork
Exec=/usr/bin/python ${INSTALL_DIR}/music_downloader.py
Icon=audio-x-generic
Terminal=false
Type=Application
Categories=AudioVideo;Audio;
EOF

chmod 644 "${DESKTOP_DIR}/${APP_ID}.desktop"

echo
echo "Installation complete."
echo "Search for '${APP_NAME}' in your desktop application menu."
echo "To launch from a terminal:"
echo "  /usr/bin/python '${INSTALL_DIR}/music_downloader.py'"
