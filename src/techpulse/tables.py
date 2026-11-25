"""Lazy Qt table rendering with whole-dataset numeric sorting."""

from dataclasses import dataclass

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QHeaderView, QTableView


class ObservationModel(QAbstractTableModel):
    def __init__(self, rows, columns, formatter, parent=None):
        super().__init__(parent)
        self.rows = rows
        self.columns = columns
        self.formatter = formatter

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else max(1, len(self.rows))

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.columns)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.columns[section][0]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if not self.rows:
            return (
                "No observations in this workspace"
                if role == Qt.ItemDataRole.DisplayRole and index.column() == 0
                else None
            )
        value = self.rows[index.row()].get(self.columns[index.column()][1])
        numeric = isinstance(value, (int, float)) and not isinstance(value, bool)
        if role == Qt.ItemDataRole.DisplayRole:
            return self.formatter(value)
        if role == Qt.ItemDataRole.ToolTipRole:
            return str(value) if value is not None else "Unavailable; not inferred"
        if role == Qt.ItemDataRole.TextAlignmentRole and numeric:
            return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        key = self.columns[index.column()][1]
        if role == Qt.ItemDataRole.ForegroundRole and numeric and ("pct" in key or key == "pnl"):
            app = QApplication.instance()
            dark = app is None or app.property("techpulse_theme") != "light"
            return QColor(
                ("#43cbb0" if value >= 0 else "#f58c9c") if dark else ("#116f61" if value >= 0 else "#b72848")
            )
        return None


class ObservationSort(QSortFilterProxyModel):
    def lessThan(self, left, right):
        model = self.sourceModel()
        if not isinstance(model, ObservationModel) or not model.rows:
            return False

        def key(index):
            value = model.rows[index.row()].get(model.columns[index.column()][1])
            if value is None:
                return (2, "")
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return (0, value)
            return (1, model.formatter(value).casefold())

        return key(left) < key(right)


@dataclass
class DisplayCell:
    value: str

    def text(self):
        return self.value


class ResearchTable(QTableView):
    """Existing detail callbacks can use item(row,col).text() without per-cell widgets."""

    cellDoubleClicked = Signal(int, int)

    def __init__(self, rows, columns, formatter, min_height=280):
        super().__init__()
        self.observations = ObservationModel(rows, columns, formatter, self)
        self.proxy = ObservationSort(self)
        self.proxy.setSourceModel(self.observations)
        self.setModel(self.proxy)
        self.verticalHeader().hide()
        self.verticalHeader().setDefaultSectionSize(39)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.setShowGrid(False)
        self.horizontalHeader().setResizeContentsPrecision(100)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
        self.setSortingEnabled(True)
        self.setMinimumHeight(min_height)
        if not rows:
            self.setSpan(0, 0, 1, len(columns))
        self.doubleClicked.connect(self._open_row)

    def _open_row(self, index):
        if self.observations.rows:
            self.cellDoubleClicked.emit(index.row(), index.column())

    def item(self, row, column):
        index = self.proxy.index(row, column)
        return DisplayCell(str(index.data(Qt.ItemDataRole.DisplayRole) or ""))

    def record(self, row):
        """Return the selected underlying row; never use formatted IDs as identities."""
        if not self.observations.rows:
            return None
        index = self.proxy.mapToSource(self.proxy.index(row, 0))
        return self.observations.rows[index.row()] if index.isValid() else None
