"""Non-destructive startup recovery for unavailable or incompatible local databases."""

from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from .paths import data_directory, default_directory, remember_directory
from .recovery import inspect_backup, recover_to_directory
from .store import Store


class StartupRecoveryDialog(QDialog):
    def __init__(self, error, attempted, *, can_remember=True):
        super().__init__()
        self.selection: Path | None = None
        self.warning = ""
        self.setWindowTitle("TechPulse · Recover your workspace")
        self.setWindowIcon(QIcon(str(Path(__file__).parent / "assets" / "techpulse.svg")))
        self.resize(680, 560)
        self.setStyleSheet("""
            QWidget {background:#0b1220;color:#e8eef7;font-family:'Segoe UI';font-size:13px;}
            QLabel#heading {font-size:25px;font-weight:650;}
            QTextBrowser {background:#111d2f;border:1px solid #223248;border-radius:7px;padding:10px;}
            QPushButton {background:#111d2f;border:1px solid #31516a;border-radius:6px;padding:10px;text-align:left;}
            QPushButton:hover {border-color:#37c5b1;}
            QCheckBox {padding:5px;}
            QCheckBox:disabled {color:#91a2b9;}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(12)
        heading = QLabel("Let's reopen your research")
        heading.setObjectName("heading")
        layout.addWidget(heading)
        explanation = QLabel(
            "TechPulse couldn't open its data. Keep the original folder for recovery. "
            "A backup can be checked and opened in a new folder. "
            "Your choice applies to this session unless you save it as the default below."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        self.details = QTextBrowser()
        self.details.setPlainText(f"Attempted folder:\n{attempted}\n\nStartup detail:\n{error}")
        self.details.setMinimumHeight(115)
        layout.addWidget(self.details, 1)
        for title, action in (
            ("Open another existing data folder…", self.open_existing),
            ("Recover a backup into a new folder…", self.recover_backup),
            ("Start fresh in a new folder…", self.start_fresh),
        ):
            control = QPushButton(title)
            control.setAutoDefault(False)
            control.clicked.connect(action)
            layout.addWidget(control)
        self.remember = QCheckBox("Use the selected folder by default on future desktop launches")
        self.remember.setEnabled(can_remember)
        if not can_remember:
            self.remember.setToolTip("An explicit data-directory override applies to this launch.")
        layout.addWidget(self.remember)
        exit_button = QPushButton("Exit")
        exit_button.setDefault(True)
        exit_button.clicked.connect(self.reject)
        layout.addWidget(exit_button)

    def error(self, message):
        box = QMessageBox(self)
        box.setWindowTitle("TechPulse recovery")
        box.setIcon(QMessageBox.Icon.Warning)
        box.setTextFormat(Qt.TextFormat.PlainText)
        box.setText(str(message))
        box.exec()

    def checked(self, operation):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            return operation()
        finally:
            QApplication.restoreOverrideCursor()

    def open_existing(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose an existing TechPulse data folder")
        if not folder:
            return
        try:
            self.checked(lambda: inspect_backup(Path(folder) / "techpulse.db"))
            self.selection = Path(folder).resolve()
            self.accept()
        except (OSError, ValueError) as exc:
            self.error(exc)

    def recover_backup(self):
        backup, _ = QFileDialog.getOpenFileName(
            self, "Choose a TechPulse backup", "", "SQLite (*.db);;All files (*)"
        )
        if not backup:
            return
        parent = QFileDialog.getExistingDirectory(self, "Choose a parent folder for the recovered copy")
        if not parent:
            return
        try:
            result = self.checked(lambda: recover_to_directory(backup, parent))
            self.selection = Path(result["data_directory"])
            self.warning = result.get("warning", "")
            self.accept()
        except (OSError, ValueError) as exc:
            self.error(exc)

    def start_fresh(self):
        parent = QFileDialog.getExistingDirectory(
            self, "Choose a parent folder for new empty personal research (original data is preserved)"
        )
        if not parent:
            return
        try:
            self.selection = Path(tempfile.mkdtemp(prefix="TechPulse-fresh-", dir=Path(parent).resolve()))
            self.accept()
        except OSError as exc:
            self.error(exc)


def checked_store(directory):
    """Validate existing files before opening; also used by noninteractive smoke checks."""
    database = Path(directory) / "techpulse.db"
    if database.exists() or database.is_symlink():
        inspect_backup(database)
    return Store(database)


def open_window(factory):
    """Open the main window, offering explicit recovery choices after startup failure.

    Smoke tests use their separate noninteractive path. No preference is saved until
    a complete main window has initialized successfully.
    """
    explicit = bool(os.environ.get("TECHPULSE_DATA_DIR"))
    selected = None
    remember = False
    warning = ""
    while True:
        store = None
        attempted = selected or default_directory()
        try:
            directory = selected or data_directory()
            attempted = directory
            store = checked_store(directory)
            window = factory(store)
        except (sqlite3.Error, OSError, ValueError, TypeError, KeyError) as exc:
            if store is not None:
                store.close()
            dialog = StartupRecoveryDialog(str(exc), attempted, can_remember=not explicit)
            if dialog.exec() != QDialog.DialogCode.Accepted or dialog.selection is None:
                return None
            selected = dialog.selection
            remember = dialog.remember.isEnabled() and dialog.remember.isChecked()
            warning = dialog.warning
            continue
        if selected is not None:
            # Existing Settings/report-folder helpers use the active session directory.
            os.environ["TECHPULSE_DATA_DIR"] = str(directory)
            if remember:
                try:
                    remember_directory(directory)
                except (OSError, ValueError) as exc:
                    warning = f"Workspace opened for this session; could not save its default location: {exc}"
        if warning:
            window.status.setText(warning)
        return window
