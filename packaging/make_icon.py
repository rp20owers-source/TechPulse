"""Render the project's SVG into the Windows shortcut icon using installed Qt."""

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication([])
    image = QImage(256, 256, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer = QSvgRenderer(str(Path(sys.argv[1])))
    if not renderer.isValid():
        raise SystemExit("Project SVG could not be loaded")
    renderer.render(painter)
    painter.end()
    if not image.save(sys.argv[2], "ICO"):
        raise SystemExit("Shortcut icon could not be saved")
