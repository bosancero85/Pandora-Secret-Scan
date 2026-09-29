@echo off
REM ============================================================
REM  Pandora Secret Scan - lokaler Build fuer Windows
REM  Ergebnis: dist\Pandora-Secret-Scan-Win.exe
REM  Ausfuehren im Repo-Hauptordner (neben pandora_secret_scan.py): build_windows.bat
REM ============================================================
setlocal
cd /d "%~dp0"

set ENTRY_FILE=pandora_secret_scan.py
set APP_NAME=Pandora-Secret-Scan
set ICON_ICO=pandora_secret_scan_icon.ico
set ICON_PNG=pandora_secret_scan_icon.png
set ICON_PNG_256=pandora_secret_scan_icon_256.png
set VENV=.build-venv

echo [1/5] Startdatei und Icons pruefen ...
for %%F in (%ENTRY_FILE% %ICON_ICO% %ICON_PNG% %ICON_PNG_256%) do (
  if not exist "%%F" (
    echo FEHLER: Datei/Ordner fehlt im Repo-Hauptordner: %%F
    exit /b 1
  )
)

echo [2/5] Virtuelle Umgebung einrichten ...
where python >nul 2>nul || (echo FEHLER: Python 3.11 wurde nicht gefunden. & exit /b 1)
if not exist "%VENV%\Scripts\python.exe" (
  python -m venv "%VENV%" || exit /b 1
)
call "%VENV%\Scripts\activate.bat" || exit /b 1

echo [3/5] Abhaengigkeiten installieren ...
python -m pip install --upgrade pip || exit /b 1
pip install pyinstaller || exit /b 1
if exist requirements.txt (
  pip install -r requirements.txt || exit /b 1
)

echo [4/5] Import-Test ...
set QT_QPA_PLATFORM=offscreen
python -c "import pandora_secret_scan; print('Import ok')" || (
  echo FEHLER: Import-Test fehlgeschlagen. Programmfehler zuerst beheben.
  exit /b 1
)
set QT_QPA_PLATFORM=

echo [5/5] EXE bauen ...
pyinstaller --onefile --windowed --noconfirm ^
  --name "Pandora-Secret-Scan-Win" ^
  --icon "%ICON_ICO%" ^
  "%ENTRY_FILE%" || exit /b 1

if not exist "dist\Pandora-Secret-Scan-Win.exe" (
  echo FEHLER: dist\Pandora-Secret-Scan-Win.exe wurde nicht erzeugt.
  exit /b 1
)
echo.
echo Fertig: dist\Pandora-Secret-Scan-Win.exe
endlocal
