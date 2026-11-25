from PySide6.QtCore import Qt

from techpulse.app import fmt
from techpulse.tables import ResearchTable


def test_input_order_global_numeric_sort_and_detail_mapping(qtbot):
    rows = [{"symbol": "B", "value": 10}, {"symbol": "A", "value": 2}, {"symbol": "C", "value": 30}]
    grid = ResearchTable(rows, [("Symbol", "symbol"), ("Value", "value")], fmt)
    qtbot.addWidget(grid)
    assert [grid.item(i, 0).text() for i in range(3)] == ["B", "A", "C"]
    grid.sortByColumn(1, Qt.SortOrder.AscendingOrder)
    assert [grid.item(i, 0).text() for i in range(3)] == ["A", "B", "C"]
    grid.sortByColumn(1, Qt.SortOrder.DescendingOrder)
    assert grid.item(0, 0).text() == "C"
    assert grid.record(0) == rows[2]
    opened = []
    grid.cellDoubleClicked.connect(lambda r, c: opened.append(grid.item(r, 0).text()))
    grid._open_row(grid.proxy.index(0, 0))
    assert opened == ["C"]


def test_large_table_formats_visible_rows_lazily(qtbot):
    rows = [{"symbol": f"S{i}", "value": 20000 - i} for i in range(20000)]
    calls = []

    def formatting(value):
        calls.append(value)
        return fmt(value)

    grid = ResearchTable(rows, [("Symbol", "symbol"), ("Value", "value")], formatting)
    qtbot.addWidget(grid)
    grid.resize(800, 400)
    grid.show()
    qtbot.wait(30)
    assert grid.model().rowCount() == 20000
    assert len(calls) < 2000  # No eager item/formatting allocation for 40,000 cells.
    grid.sortByColumn(1, Qt.SortOrder.AscendingOrder)
    assert grid.item(0, 0).text() == "S19999"


def test_empty_table_has_readable_placeholder_and_no_detail_action(qtbot):
    grid = ResearchTable([], [("Symbol", "symbol")], fmt)
    qtbot.addWidget(grid)
    assert grid.model().rowCount() == 1
    assert "No observations" in grid.item(0, 0).text()
    opened = []
    grid.cellDoubleClicked.connect(lambda *args: opened.append(args))
    grid._open_row(grid.proxy.index(0, 0))
    assert not opened
