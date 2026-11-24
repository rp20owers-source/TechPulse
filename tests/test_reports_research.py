import csv
import io
import json

from techpulse.demo import seed_demo
from techpulse.reports import SECTIONS, _pdf_text, csv_text, export_report, html_text, snapshot
from techpulse.research import asset_rows, disclosure_performance, opportunity
from techpulse.store import Store


def test_snapshot_exports_all_formats_and_escapes_html(tmp_path):
    store = Store(tmp_path / "local.db")
    seed_demo(store)
    report = snapshot(store, "demo")
    assert len(report["sections"]) == 14
    assert "FICTIONAL" in report["warning"]
    assert all(c["decision"] == "Abstain" for c in report["sections"][SECTIONS[9]])
    report["sections"]["User evidence"] = "<script>alert('test')</script>"
    text = html_text(report)
    assert "<script>" not in text
    assert "&lt;script&gt;" in text
    for ext in ("json", "html", "csv", "pdf"):
        path = tmp_path / ("report." + ext)
        export_report(report, path)
        assert path.stat().st_size > 500
        if ext == "pdf":
            assert path.read_bytes().startswith(b"%PDF-")
    rows = list(csv.reader(io.StringIO(csv_text(report))))
    assert rows[0] == ["workspace", "created_at", "section", "observation_json"]
    assert json.loads(rows[1][3])["workspace"] == "demo"
    store.archive_report("demo", report["title"], report)
    original = store.reports("demo")[0]["payload"]
    report["warning"] = "changed after archive"
    assert store.reports("demo")[0]["payload"] == original
    store.close()


def test_empty_personal_report_does_not_use_demo_and_sections_export(tmp_path):
    store = Store(tmp_path / "local.db")
    seed_demo(store)
    report = snapshot(store, "research", SECTIONS[9])
    assert list(report["sections"]) == [SECTIONS[9]]
    assert "SYN-" not in json.dumps(report)
    assert "Abstain" in report["sections"][SECTIONS[9]]
    store.close()


def test_price_source_is_distinct_from_metadata_and_updates(tmp_path):
    store = Store(tmp_path / "local.db")
    assets = (
        "symbol,name,kind,category,as_of,market_cap,currency\nTEST,Test,equity,Cloud,2026-11-20,1000,USD\n"
    )
    store.import_csv(assets, "assets", "Metadata A", "https://example.org/a")
    bars = "symbol,date,open,high,low,close,volume,currency\nTEST,2026-11-20,100,111,99,110,1000,USD\n"
    store.import_csv(bars, "bars", "Prices B", "https://example.org/b")
    row = asset_rows(store, "research")[0]
    assert row["source"] == "Metadata A"
    assert row["price_source"] == "Prices B"
    sources = snapshot(store, "research")["sections"][SECTIONS[13]]["sources"]
    assert sources[0]["price_source"] == "Prices B"
    assert sources[0]["price_source_url"] == "https://example.org/b"
    store.close()


def test_disclosure_return_starts_strictly_after_publication(tmp_path):
    store = Store(tmp_path / "local.db")
    store.save_bars(
        "research",
        "TEST",
        [
            {"date": "2026-11-18", "close": 10},
            {"date": "2026-11-19", "close": 20},
            {"date": "2026-11-20", "close": 30},
            {"date": "2026-11-23", "close": 60},
        ],
    )
    result, start = disclosure_performance(
        store, "research", {"symbol": "TEST", "publication_date": "2026-11-19"}
    )
    assert result == 100 and start == "2026-11-20"
    assert disclosure_performance(
        store, "research", {"symbol": "TEST", "publication_date": "2026-11-23"}
    ) == (None, None)
    store.close()


def test_only_real_observations_used_for_abstaining_score(tmp_path):
    store = Store(tmp_path / "local.db")
    seed_demo(store)
    assert opportunity(store, "demo", store.assets("demo")[0])["decision"] == "Abstain"
    empty = opportunity(store, "research", {"symbol": "TEST"})
    assert empty["coverage"] == 0 and empty["decision"] == "Abstain"
    store.close()


def test_readable_report_preserves_complete_snapshot_and_financial_evidence(tmp_path):
    store = Store(tmp_path / "local.db")
    seed_demo(store)
    report = snapshot(store, "demo")
    original = json.dumps(report, sort_keys=True)
    text = html_text(report)
    assert "<pre>" not in text and "<table>" in text
    assert "Trade premium USD" in text
    assert "57,600.00" in text
    assert "Actually obligated USD" in text and "120,000,000" in text
    assert "Business implications / assumptions" in text
    assert "Possible expansion" in text and "Original award source" in text
    assert "Entry conditions" in text and "Thesis invalidation" in text
    assert "Missing evidence" in text and "Evidence component" in text
    assert "Metadata source" in text and "Price retrieved UTC" in text
    assert "Display is truncated" in text
    assert json.dumps(report, sort_keys=True) == original
    options = report["sections"][SECTIONS[3]]
    trade = next(r for r in options if r["record_type"] == "trade")
    aggregate = next(r for r in options if r["record_type"] == "aggregate")
    assert trade["metrics"]["estimated_trade_premium"] == 57600
    assert aggregate["metrics"]["estimated_trade_premium"] is None
    assert aggregate["metrics"]["volume_ratio"] == 6
    store.close()


def test_visible_movers_keep_both_extremes_but_json_csv_keep_every_asset():
    assets = [{"symbol": f"TEST{i:03}", "week_pct": 12 - i} for i in range(25)]
    report = {
        "title": "Fictional test",
        "created_at": "2026-11-24T12:00:00Z",
        "workspace": "demo",
        "warning": "FICTIONAL",
        "sections": {SECTIONS[1]: assets},
    }
    text = html_text(report)
    assert "TEST000" in text and "TEST024" in text
    assert "TEST012" not in text
    assert "Showing 20 of 25 assets" in text
    assert "Display is truncated; JSON/CSV retain the complete snapshot" in text
    assert len(report["sections"][SECTIONS[1]]) == 25
    assert len(list(csv.reader(io.StringIO(csv_text(report))))) == 26


def test_unknown_returns_do_not_hide_known_laggards():
    assets = [{"symbol": f"UNKNOWN{i}", "week_pct": None} for i in range(30)]
    assets += [{"symbol": "LOSER", "week_pct": -12}, {"symbol": "WINNER", "week_pct": 12}]
    report = {
        "title": "Fictional test",
        "created_at": "2026-11-24",
        "workspace": "demo",
        "warning": "FICTIONAL",
        "sections": {SECTIONS[1]: assets},
    }
    text = html_text(report)
    assert "LOSER" in text and "WINNER" in text
    assert "Unavailable" in text


def test_unicode_remains_exact_in_html_and_portable_pdf_has_explicit_fallback(tmp_path):
    evidence = "Café 数据 🚀 — <untrusted>"
    report = {
        "title": "TechPulse test",
        "created_at": "2026-11-24",
        "workspace": "demo",
        "warning": "FICTIONAL",
        "sections": {"User evidence": evidence},
    }
    assert "Café 数据 🚀" in html_text(report)
    assert "&lt;untrusted&gt;" in html_text(report)
    assert _pdf_text(evidence) == "Cafe [U+6570][U+636E] [U+1F680] - <untrusted>"
    path = tmp_path / "unicode.pdf"
    export_report(report, path)
    assert path.read_bytes().startswith(b"%PDF-")


def test_zero_revenue_contract_does_not_break_report(tmp_path):
    store = Store(tmp_path / "local.db")
    store.save_asset("research", {"symbol": "TEST", "kind": "equity", "revenue": 0, "market_cap": 0})
    store.save_record(
        "research",
        "contracts",
        {
            "id": "test-award",
            "company": "Fictional test",
            "ticker": "TEST",
            "obligated": 100,
            "ceiling": 1000,
        },
    )
    report = snapshot(store, "research")
    award = report["sections"][SECTIONS[5]][0]
    assert award["metrics"]["obligated_to_revenue_pct"] is None
    assert award["metrics"]["obligated_to_market_cap_pct"] is None
    store.close()
