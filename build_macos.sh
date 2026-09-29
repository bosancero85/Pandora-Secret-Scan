#!/usr/bin/env bash
# ============================================================
#  Pandora Secret Scan - lokaler Build fuer macOS
#  Ergebnis: Pandora-Secret-Scan-Mac.dmg
#  Ausfuehren im Repo-Hauptordner (neben pandora_secret_scan.py): ./build_macos.sh
#  Falls noetig zuerst: chmod +x build_macos.sh
# ============================================================
set -euo pipefail
cd "$(dirname "$0")"

ENTRY_FILE="pandora_secret_scan.py"
APP_NAME="Pandora-Secret-Scan"
ICON_ICO="pandora_secret_scan_icon.ico"
ICON_PNG="pandora_secret_scan_icon.png"
ICON_PNG_256="pandora_secret_scan_icon_256.png"
VENV=".build-venv"

echo "[1/6] Startdatei und Icons prüfen ..."
for f in "$ENTRY_FILE" "$ICON_ICO" "$ICON_PNG" "$ICON_PNG_256"; do
  test -e "$f" || { echo "FEHLER: Datei/Ordner fehlt im Repo-Hauptordner: $f"; exit 1; }
done

echo "[2/6] Virtuelle Umgebung einrichten ..."
command -v python3 >/dev/null || { echo "FEHLER: python3 nicht gefunden (Python 3.11 empfohlen)."; exit 1; }
[ -d "$VENV" ] || python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"

echo "[3/6] Abhängigkeiten installieren ..."
python -m pip install --upgrade pip
# Pillow wandelt das PNG-Icon für PyInstaller automatisch in .icns um
pip install pyinstaller pillow
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

echo "[4/6] Import-Test ..."
QT_QPA_PLATFORM=offscreen python -c "import pandora_secret_scan; print('Import ok')" \
  || { echo "FEHLER: Import-Test fehlgeschlagen. Programmfehler zuerst beheben."; exit 1; }

echo "[5/6] App bauen ..."
pyinstaller --windowed --noconfirm \
  --name "$APP_NAME" \
  --icon "$ICON_PNG" \
  --osx-bundle-identifier "de.pandora.secretscan" \
  "$ENTRY_FILE"

echo "[6/6] DMG erstellen ..."
rm -f "Pandora-Secret-Scan-Mac.dmg"
hdiutil create -volname "Pandora Secret Scan" \
  -srcfolder "dist/$APP_NAME.app" \
  -ov -format UDZO "Pandora-Secret-Scan-Mac.dmg"

test -f "Pandora-Secret-Scan-Mac.dmg" || { echo "FEHLER: DMG wurde nicht erzeugt."; exit 1; }
echo
echo "Fertig: Pandora-Secret-Scan-Mac.dmg"
echo "Hinweis: Die App ist nicht signiert. Beim ersten Start: Rechtsklick -> Öffnen."
