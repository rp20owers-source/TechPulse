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


def test_zero_company_denominators_do_not_break_contracts(qtbot, tmp_path):
    window = MainWindow(Store(tmp_path / "zero.db"))
    qtbot.addWidget(window)
    asset = next(a for a in window.store.assets("demo") if a["symbol"] == "SYN-AI")
    asset.update(revenue=0, market_cap=0)
    window.store.save_asset("demo", asset)
    window.store.db.commit()
    window.nav.setCurrentRow(6)
    assert window.page_errors == []
    window.close()
    window.check_schedule()  # A pending startup timer must also be harmless after close.


def test_sec_session_preview_renders_without_polluting_reports(qtbot, tmp_path):
    from techpulse.sec import normalize_company_facts

    window = MainWindow(Store(tmp_path / "sec-ui.db"))
    qtbot.addWidget(window)
    window.workspace.setCurrentIndex(1)
    window.live_results = [
        normalize_company_facts(
            {"cik": 1, "entityName": "Fictional SEC UI probe", "facts": {"us-gaap": {}}}, "2025-03-01"
        )
    ]
    window.nav.setCurrentRow(14)
    assert window.page_errors == []
    assert "Fictional SEC UI probe" not in json.dumps(snapshot(window.store, "research"))
    window.close()


def test_sec_contact_is_validated_session_only_and_resets(qtbot, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QLineEdit

    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    path = tmp_path / "contact.db"
    window = MainWindow(Store(path))
    qtbot.addWidget(window)
    errors = []
    monkeypatch.setattr(window, "error", errors.append)
    window.nav.setCurrentRow(15)
    assert window.findChild(QLineEdit, "secContact") is not None
    marker = "TechPulse SESSION_ONLY_CONTACT@example.invalid"
    assert window.set_sec_contact(marker)
    assert window.sec_user_agent == marker
    assert not window.set_sec_contact("invalid")
    assert errors and window.sec_user_agent == marker
    assert marker not in "\n".join(window.store.db.iterdump())
    assert marker not in json.dumps(snapshot(window.store, "demo"))
    assert window.set_sec_contact("") and not window.sec_user_agent
    window.set_sec_contact(marker)
    window.close()
    reopened = MainWindow(Store(path))
    qtbot.addWidget(reopened)
    assert not reopened.sec_user_agent
    reopened.close()


def test_sec_fetch_uses_session_contact_then_environment(qtbot, tmp_path, monkeypatch):
    from techpulse import app as app_module
    from techpulse import sec as sec_module

    calls = []

    class FakeProvider:
        def __init__(self, contact):
            calls.append(contact)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def fundamentals_for(self, *args):
            return []

    monkeypatch.setenv("SEC_USER_AGENT", "Environment env@example.invalid")
    monkeypatch.setattr(sec_module, "SECProvider", FakeProvider)
    monkeypatch.setattr(app_module.QInputDialog, "getText", lambda *args, **kwargs: ("1", True))
    window = MainWindow(Store(tmp_path / "fetch-contact.db"))
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "run_provider", lambda title, fn: fn())
    window.set_sec_contact("Session session@example.invalid")
    window.fetch_sec()
    window.set_sec_contact("")
    window.fetch_sec()
    assert calls == ["Session session@example.invalid", "Environment env@example.invalid"]
    window.close()
