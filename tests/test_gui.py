import json

from PySide6.QtWidgets import QLabel, QTableWidget

from techpulse.app import PAGES, MainWindow
from techpulse.reports import snapshot
from techpulse.store import Store


def test_all_pages_both_workspaces_and_themes(qtbot, tmp_path):
    window = MainWindow(Store(tmp_path / "ui.db"))
    qtbot.addWidget(window)
    window.show()
    for theme in ("dark", "light"):
        window.theme = theme
        window.apply_theme()
        for index in (0, 1):
            window.workspace.setCurrentIndex(index)
            for row, page in enumerate(PAGES):
                window.nav.setCurrentRow(row)
                assert window.page == page
                assert window.title.text() == page
    assert window.page_errors == []
    window.close()


def test_watchlist_schedule_and_memory_preview_isolation(qtbot, tmp_path):
    window = MainWindow(Store(tmp_path / "ui.db"))
    qtbot.addWidget(window)
    window.store.toggle_watch("demo", "SYN-AI")
    window.nav.setCurrentRow(10)
    assert window.findChildren(QTableWidget)
    window.live_results = [{"secret_marker": "SESSION_ONLY_SYNTHETIC_MARKER"}]
    report = snapshot(window.store, "demo")
    assert "SESSION_ONLY_SYNTHETIC_MARKER" not in json.dumps(report)
    window.store.set_setting("weekly_demo", True)
    window.check_schedule()
    assert len(window.store.reports("demo")) == 1
    window.check_schedule()
    assert len(window.store.reports("demo")) == 1
    window.workspace.setCurrentIndex(1)
    assert window.live_results == []
    assert any("PERSONAL RESEARCH" in item.text() for item in window.findChildren(QLabel))
    window.close()
