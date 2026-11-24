import csv
import io
import json

from techpulse.demo import seed_demo
from techpulse.reports import SECTIONS, csv_text, export_report, html_text, snapshot
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
