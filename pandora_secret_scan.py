import sys
import os
import re
import math
import json
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar, QTextEdit,
    QCheckBox, QGroupBox, QMessageBox, QSplitter
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QColor


# -------------------------------------------------------------------
# SECRETS DETECTION ENGINE
# -------------------------------------------------------------------
SECRET_PATTERNS = {
    "Anthropic API Key": r"sk-ant-[a-zA-Z0-9\-_]{80,}",
    "OpenAI API Key": r"sk-[a-zA-Z0-9]{32,}",
    "AWS Access Key ID": r"AKIA[0-9A-Z]{16}",
    "GitHub Personal Access Token": r"ghp_[a-zA-Z0-9]{36}",
    "Generic API Key Assignment": r"(?i)(api[_\-]?key|secret|password|auth[_\-]?token)\s*=\s*['\"]([a-zA-Z0-9_\-]{16,})['\"]",
    "Private Key": r"-----BEGIN (RSA|OPENSSH|EC|DSA|PGP) PRIVATE KEY-----"
}

IGNORED_EXTENSIONS = {
    '.exe', '.dll', '.so', '.dylib', '.png', '.jpg', '.jpeg', '.gif',
    '.ico', '.zip', '.tar', '.gz', '.7z', '.pdf', '.pyc', '.db', '.sqlite'
}


def calculate_entropy(data: str) -> float:
    """Berechnet die Shannon-Entropie einer Zeichenkette (Zufälligkeit)."""
    if not data:
        return 0.0
    entropy = 0.0
    length = len(data)
    for char in set(data):
        p_x = data.count(char) / length
        entropy -= p_x * math.log2(p_x)
    return round(entropy, 2)


# -------------------------------------------------------------------
# THREADING / WORKER FOR ASYNCHRONOUS SCANNING
# -------------------------------------------------------------------
class ScanWorker(QThread):
    progress_signal = pyqtSignal(int, int)  # (current, total)
    result_signal = pyqtSignal(dict)       # Secret details
    status_signal = pyqtSignal(str)       # Status logs
    finished_signal = pyqtSignal(int)      # Total secrets found

    def __init__(self, target_dir: str, check_entropy: bool):
        super().__init__()
        self.target_dir = target_dir
        self.check_entropy = check_entropy
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        self.status_signal.emit("Indiziere Dateien im Zielverzeichnis...")
        file_list = []
        for root, dirs, files in os.walk(self.target_dir):
            if not self._is_running:
                return
            # Versteckte Git-Ordner überspringen
            if '.git' in dirs:
                dirs.remove('.git')
            for file in files:
                ext = Path(file).suffix.lower()
                if ext not in IGNORED_EXTENSIONS:
                    file_list.append(os.path.join(root, file))

        total_files = len(file_list)
        secrets_found = 0
        compiled_patterns = {name: re.compile(pat) for name, pat in SECRET_PATTERNS.items()}

        self.status_signal.emit(f"Starte Scan von {total_files} Dateien...")

        for idx, file_path in enumerate(file_list, 1):
            if not self._is_running:
                self.status_signal.emit("Scan abgebrochen.")
                return

            self.progress_signal.emit(idx, total_files)

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        clean_line = line.strip()
                        if not clean_line:
                            continue

                        # Regex-Muster abgleichen
                        for secret_type, pattern in compiled_patterns.items():
                            match = pattern.search(clean_line)
                            if match:
                                secret_val = match.group(0)
                                entropy = calculate_entropy(secret_val)
                                secrets_found += 1
                                self.result_signal.emit({
                                    "file": file_path,
                                    "line": line_num,
                                    "type": secret_type,
                                    "match": secret_val[:40] + "..." if len(secret_val) > 40 else secret_val,
                                    "entropy": entropy
                                })

                        # Optionale Entropie-Prüfung für lange Wörter/Tokens
                        if self.check_entropy:
                            words = re.findall(r'[A-Za-z0-9_\-\+]{24,}', clean_line)
                            for word in words:
                                ent = calculate_entropy(word)
                                if ent >= 4.5:  # Schwellenwert für hohe Entropie
                                    secrets_found += 1
                                    self.result_signal.emit({
                                        "file": file_path,
                                        "line": line_num,
                                        "type": "High Entropy Token",
                                        "match": word[:40] + "...",
                                        "entropy": ent
                                    })
            except Exception as e:
                pass  # Verarbeitungsfehler stumm übergehen

        self.status_signal.emit("Scan erfolgreich abgeschlossen!")
        self.finished_signal.emit(secrets_found)


# -------------------------------------------------------------------
# MAIN GUI WINDOW (PyQt6)
# -------------------------------------------------------------------
class PandoraSecretScanApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pandora® Secret SCAN — Advanced Credential Detector")
        self.resize(1100, 720)
        self.worker = None

        self.init_ui()
        self.apply_cyberpunk_style()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Header Banner
        header_label = QLabel("PANDORA® SECRET SCAN")
        header_font = QFont("Consolas", 18, QFont.Weight.Bold)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header_label)

        sub_header = QLabel("Codebase Audit & Credentials Leak Prevention Engine")
        sub_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_header.setStyleSheet("color: #8A8FAD; font-size: 11px;")
        main_layout.addWidget(sub_header)

        # Target Selection Group
        config_group = QGroupBox("Scan-Konfiguration")
        config_layout = QVBoxLayout(config_group)

        dir_layout = QHBoxLayout()
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("Verzeichnispfad zum Scannen auswählen...")
        self.btn_browse = QPushButton("Durchsuchen...")
        self.btn_browse.clicked.connect(self.browse_directory)
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(self.btn_browse)
        config_layout.addLayout(dir_layout)

        options_layout = QHBoxLayout()
        self.cb_entropy = QCheckBox("Hohe Shannon-Entropie analysieren (Erkennt unbekannte Zufallstokens)")
        self.cb_entropy.setChecked(True)
        options_layout.addWidget(self.cb_entropy)

        self.btn_start = QPushButton("Scan Starten")
        self.btn_start.clicked.connect(self.start_scan)
        self.btn_stop = QPushButton("Stopp")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_scan)

        options_layout.addWidget(self.btn_start)
        options_layout.addWidget(self.btn_stop)
        config_layout.addLayout(options_layout)

        main_layout.addWidget(config_group)

        # Main Content Splitter (Table + Logs)
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Results Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Datei", "Zeile", "Typ", "Gefundener Match", "Entropie"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        splitter.addWidget(self.table)

        # Log Window
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(120)
        splitter.addWidget(self.log_output)

        main_layout.addWidget(splitter)

        # Progress & Status Bar
        status_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.btn_export = QPushButton("Report Exportieren (.JSON)")
        self.btn_export.clicked.connect(self.export_report)

        status_layout.addWidget(self.progress_bar)
        status_layout.addWidget(self.btn_export)
        main_layout.addLayout(status_layout)

        self.findings = []

    def apply_cyberpunk_style(self):
        """Design im Cyberpunk-Stil (Neon-Violett #9D00FF und Dark Navy)."""
        style = """
            QMainWindow, QWidget {
                background-color: #0B0D14;
                color: #E2E8F0;
                font-family: 'Segoe UI', Consolas, sans-serif;
            }
            QGroupBox {
                border: 1px solid #9D00FF;
                border-radius: 6px;
                margin-top: 10px;
                font-weight: bold;
                color: #00FFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit {
                background-color: #16192B;
                border: 1px solid #2E3456;
                border-radius: 4px;
                padding: 6px;
                color: #FFFFFF;
            }
            QLineEdit:focus {
                border: 1px solid #9D00FF;
            }
            QPushButton {
                background-color: #16192B;
                border: 1px solid #9D00FF;
                color: #00FFFF;
                padding: 6px 14px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9D00FF;
                color: #FFFFFF;
            }
            QPushButton:disabled {
                border-color: #2E3456;
                color: #555A7B;
                background-color: #0F111D;
            }
            QTableWidget {
                background-color: #111322;
                border: 1px solid #1F243D;
                gridline-color: #1F243D;
                color: #E2E8F0;
            }
            QHeaderView::section {
                background-color: #16192B;
                color: #9D00FF;
                padding: 4px;
                font-weight: bold;
                border: 1px solid #1F243D;
            }
            QProgressBar {
                border: 1px solid #2E3456;
                border-radius: 4px;
                text-align: center;
                background-color: #16192B;
                color: #FFFFFF;
            }
            QProgressBar::chunk {
                background-color: #9D00FF;
            }
            QTextEdit {
                background-color: #0A0C13;
                border: 1px solid #1F243D;
                color: #00FF88;
                font-family: Consolas;
            }
        """
        self.setStyleSheet(style)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Zielverzeichnis auswählen")
        if directory:
            self.dir_input.setText(directory)

    def start_scan(self):
        target_dir = self.dir_input.text().strip()
        if not target_dir or not os.path.isdir(target_dir):
            QMessageBox.warning(self, "Ungültiges Verzeichnis", "Bitte wähle ein gültiges Verzeichnis aus.")
            return

        self.table.setRowCount(0)
        self.findings.clear()
        self.log_output.clear()
        self.progress_bar.setValue(0)

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

        self.worker = ScanWorker(target_dir, self.cb_entropy.isChecked())
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.result_signal.connect(self.add_result)
        self.worker.status_signal.connect(self.log_status)
        self.worker.finished_signal.connect(self.scan_finished)
        self.worker.start()

    def stop_scan(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.btn_stop.setEnabled(False)

    def update_progress(self, current, total):
        if total > 0:
            val = int((current / total) * 100)
            self.progress_bar.setValue(val)

    def add_result(self, data):
        self.findings.append(data)
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(data["file"]))
        self.table.setItem(row, 1, QTableWidgetItem(str(data["line"])))
        self.table.setItem(row, 2, QTableWidgetItem(data["type"]))

        match_item = QTableWidgetItem(data["match"])
        match_item.setForeground(QColor("#FF0055"))  # Rot hervorheben
        self.table.setItem(row, 3, match_item)

        self.table.setItem(row, 4, QTableWidgetItem(str(data["entropy"])))

    def log_status(self, msg):
        self.log_output.append(f"[PANDORA] {msg}")

    def scan_finished(self, total_found):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        QMessageBox.information(
            self,
            "Scan Beendet",
            f"Der Scan ist abgeschlossen.\nEs wurden {total_found} potenzielle Secrets gefunden."
        )

    def export_report(self):
        if not self.findings:
            QMessageBox.warning(self, "Keine Daten", "Es liegen keine Scan-Ergebnisse zum Exportieren vor.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Report Speichern", "pandora_secret_scan_report.json", "JSON Files (*.json)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.findings, f, indent=4)
            QMessageBox.information(self, "Erfolg", f"Report erfolgreich unter {file_path} gespeichert.")


# -------------------------------------------------------------------
# ENTRY POINT
# -------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PandoraSecretScanApp()
    window.show()
    sys.exit(app.exec())
