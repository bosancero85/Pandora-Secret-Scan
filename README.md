# Pandora® Secret SCAN

Desktop-Werkzeug, das Projektordner nach versehentlich eingecheckten Zugangsdaten durchsucht:
API-Keys, Tokens, private Schlüssel und Passwort-Zuweisungen. Alles läuft lokal auf deinem Rechner.

Landingpage: https://bosancero85.github.io/Pandora-Secret-Scan/

## Funktionen

- **Muster-Erkennung** für Anthropic- und OpenAI-Keys, AWS Access Key IDs, GitHub-Tokens, private Schlüssel und Zuweisungen wie `api_key = "…"`
- **Entropie-Analyse** (optional): meldet lange Zeichenketten mit hoher Shannon-Entropie, auch wenn kein bekanntes Muster passt
- **Scan im Hintergrund** mit Fortschrittsbalken, Statusprotokoll und Stopp-Knopf
- **Ergebnistabelle** mit Datei, Zeile, Typ, Fundstelle und Entropie
- **JSON-Report** zum Speichern der Ergebnisse
- Überspringt `.git`-Ordner und Binärdateien (Bilder, Archive, Programme, Datenbanken)

## Downloads

Die fertigen Programme liegen unter **Releases**:

| System  | Datei                                 |
|---------|---------------------------------------|
| Windows | `Pandora-Secret-Scan-Win.exe`         |
| macOS   | `Pandora-Secret-Scan-Mac.dmg`         |
| Linux   | `Pandora-Secret-Scan-Linux.AppImage`  |

Die Programme sind nicht signiert. Unter Windows kann SmartScreen warnen, unter macOS hilft
Rechtsklick → Öffnen, unter Linux vorher `chmod +x Pandora-Secret-Scan-Linux.AppImage`.

Die ausführliche Schritt-für-Schritt-Hilfe steht in [anleitung.md](anleitung.md).

## Aus dem Quellcode starten

Voraussetzung: Python 3.10 oder neuer.

```bash
git clone https://github.com/bosancero85/Pandora-Secret-Scan.git
cd Pandora-Secret-Scan
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python pandora_secret_scan.py
```

## Selbst bauen

Die Build-Skripte liegen im Hauptordner neben `pandora_secret_scan.py` und brauchen Python 3.11.
Jedes Skript baut nur für das System, auf dem es läuft.

| System  | Befehl               | Ergebnis                              |
|---------|----------------------|---------------------------------------|
| Windows | `build_windows.bat`  | `dist\Pandora-Secret-Scan-Win.exe`    |
| macOS   | `./build_macos.sh`   | `Pandora-Secret-Scan-Mac.dmg`         |
| Linux   | `./build_linux.sh`   | `Pandora-Secret-Scan-Linux.AppImage`  |

## Automatischer Release über GitHub

Tag pushen, z. B. `git tag v0.1.0 && git push origin v0.1.0`. Der Workflow
`.github/workflows/release.yml` baut alle drei Dateien und hängt sie an das Release.
Ohne Tag lässt er sich unter Actions → *Build & Release Pandora Secret Scan* → *Run workflow*
manuell starten; die Dateien liegen dann als Artifacts am Lauf.

## Wichtig beim Umgang mit den Ergebnissen

Treffer sind Verdachtsfälle, keine Beweise. Der JSON-Report enthält die Anfänge der gefundenen
Zeichenketten im Klartext und sollte wie ein Secret behandelt werden.

## Lizenz

MIT, siehe `LICENCE`.
