#!/usr/bin/env bash
# ============================================================
#  Pandora Secret Scan - lokaler Build fuer Linux (x86_64)
#  Ergebnis: Pandora-Secret-Scan-Linux.AppImage
#  Ausfuehren im Repo-Hauptordner (neben pandora_secret_scan.py): ./build_linux.sh
#  Falls noetig zuerst: chmod +x build_linux.sh
#
#  Benoetigte Systempakete (Debian/Ubuntu), falls noch nicht vorhanden:
#    sudo apt-get install -y libfuse2 libegl1 libgl1 libglib2.0-0 libfontconfig1 \
#      libxkbcommon0 libxkbcommon-x11-0 libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
#      libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 \
#      libxcb-xinerama0 libxcb-xkb1 libdbus-1-3
# ============================================================
set -euo pipefail
cd "$(dirname "$0")"

ENTRY_FILE="pandora_secret_scan.py"
APP_NAME="Pandora-Secret-Scan"
ICON_ICO="pandora_secret_scan_icon.ico"
ICON_PNG="pandora_secret_scan_icon.png"
ICON_PNG_256="pandora_secret_scan_icon_256.png"
VENV=".build-venv"
TOOL="appimagetool-x86_64.AppImage"

echo "[1/7] Startdatei und Icons prüfen ..."
for f in "$ENTRY_FILE" "$ICON_ICO" "$ICON_PNG" "$ICON_PNG_256"; do
  test -e "$f" || { echo "FEHLER: Datei/Ordner fehlt im Repo-Hauptordner: $f"; exit 1; }
done

echo "[2/7] Virtuelle Umgebung einrichten ..."
command -v python3 >/dev/null || { echo "FEHLER: python3 nicht gefunden (Python 3.11 empfohlen)."; exit 1; }
[ -d "$VENV" ] || python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"

echo "[3/7] Abhängigkeiten installieren ..."
python -m pip install --upgrade pip
pip install pyinstaller
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

echo "[4/7] Import-Test ..."
QT_QPA_PLATFORM=offscreen python -c "import pandora_secret_scan; print('Import ok')" \
  || { echo "FEHLER: Import-Test fehlgeschlagen. Programmfehler zuerst beheben."; exit 1; }

echo "[5/7] Binary bauen ..."
pyinstaller --onefile --noconfirm \
  --name "$APP_NAME" \
  "$ENTRY_FILE"

echo "[6/7] AppDir zusammenstellen ..."
rm -rf AppDir
mkdir -p AppDir/usr/bin
cp "dist/$APP_NAME" "AppDir/usr/bin/$APP_NAME"
cp "$ICON_PNG_256" AppDir/pandora-secret-scan.png
cp "$ICON_PNG_256" AppDir/.DirIcon

cat > AppDir/AppRun <<APPRUN
#!/bin/sh
HERE="\$(dirname "\$(readlink -f "\$0")")"
exec "\$HERE/usr/bin/$APP_NAME" "\$@"
APPRUN
chmod +x AppDir/AppRun

cat > AppDir/pandora-secret-scan.desktop <<DESKTOP
[Desktop Entry]
Type=Application
Name=Pandora Secret Scan
Exec=$APP_NAME
Icon=pandora-secret-scan
Categories=Development;Security;Utility;
DESKTOP

echo "[7/7] AppImage erstellen ..."
if [ ! -x "$TOOL" ]; then
  if command -v wget >/dev/null; then
    wget -q "https://github.com/AppImage/appimagetool/releases/download/continuous/$TOOL"
  else
    curl -fsSL -o "$TOOL" "https://github.com/AppImage/appimagetool/releases/download/continuous/$TOOL"
  fi
  chmod +x "$TOOL"
fi
rm -f "Pandora-Secret-Scan-Linux.AppImage"
APPIMAGE_EXTRACT_AND_RUN=1 ARCH=x86_64 "./$TOOL" AppDir Pandora-Secret-Scan-Linux.AppImage

test -f "Pandora-Secret-Scan-Linux.AppImage" || { echo "FEHLER: AppImage wurde nicht erzeugt."; exit 1; }
chmod +x Pandora-Secret-Scan-Linux.AppImage
echo
echo "Fertig: Pandora-Secret-Scan-Linux.AppImage"
