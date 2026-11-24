import json
import sqlite3
from contextlib import closing
from decimal import Decimal

import pytest

from techpulse.demo import seed_demo
from techpulse.store import Store, safe_url


@pytest.fixture
def store(tmp_path):
    instance = Store(tmp_path / "research.db")
    yield instance
    instance.close()


def import_bars(store, rows=None, source="Bars provider"):
    content = "symbol,date,open,high,low,close,volume,currency\n" + (
        rows or "TEST,2026-11-19,100,112,99,110,1000,USD\nTEST,2026-11-20,110,112,108,110,1200,USD\n"
    )
    return store.import_csv(content, "bars", source, "https://example.org/bars")


def test_demo_isolated_from_empty_personal_data(store):
    seed_demo(store)
    assert len(store.assets("demo")) == 13
    assert store.assets("research") == []
    assert all(a["symbol"].startswith("SYN-") for a in store.assets("demo"))
    assert not store.records("demo", "disclosures")
    assert len(store.bars("demo", "SYN-AI")) == 180
    seed_demo(store)
    assert len(store.bars("demo", "SYN-AI")) == 180


@pytest.mark.parametrize(
    "rows",
    [
        "TEST,2026-11-20,100,99,99,110,1,USD\n",
        "TEST,2026-11-20,100,112,99,nan,1,USD\n",
        "TEST,2026-11-20,100,112,99,110,-1,USD\n",
        "TEST,2026-11-20,100,112,99,110,1,EUR\n",
        "TEST,2099-01-01,100,112,99,110,1,USD\n",
        "TEST,2026-11-20,100,112,99,110,1,USD\nTEST,2026-11-20,100,112,99,110,1,USD\n",
    ],
)
def test_rejects_invalid_and_duplicate_bars_atomically(store, rows):
    with pytest.raises(ValueError):
        import_bars(store, rows)
    assert store.assets("research") == []
    assert store.bars("research", "TEST") == []


def test_bad_last_row_does_not_write_good_first_row(store):
    with pytest.raises(ValueError, match="row 3"):
        import_bars(
            store, "TEST,2026-11-19,100,112,99,110,1000,USD\nTEST,2026-11-20,100,90,99,110,1000,USD\n"
        )
    assert store.assets("research") == []


def test_update_identity_replaces_instead_of_double_counting(store):
    import_bars(store)
    import_bars(store)
    assert len(store.bars("research", "TEST")) == 2


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "http://example.org",
        "https://u:p@example.org",
        "https://example.org/?api_key=FAKE",
        "https://example.org/#access_token=FAKE",
        "https://example.org/?x_cg_demo_api_key=FAKE",
        "https://example.org/?X-Amz-Signature=FAKE",
    ],
)
def test_rejects_unsafe_and_credential_bearing_sources(url):
    with pytest.raises(ValueError):
        safe_url(url)


def test_malformed_csv_and_oversized_field_become_validation_error(store):
    with pytest.raises(ValueError, match="CSV"):
        store.import_csv('symbol,name\nTEST,"' + "x" * 140000 + '"', "assets", "A", "https://example.org")
    with pytest.raises(ValueError, match="Duplicate CSV"):
        store.import_csv("symbol,symbol\nA,B", "assets", "A", "https://example.org")


def test_options_aliases_and_premium_inputs(store):
    csv = "id,symbol,date,record_type,option_type,expiry,strike,size,price,multiplier,historical_volume,implied_volatility,previous_iv,currency\na,TEST,2026-11-20,trade,call,2026-12-18,100,2,3,100,5,.4,.3,USD\n"
    store.import_csv(csv, "options", "A", "https://example.org")
    r = store.records("research", "options")[0]
    assert r["historical_average_volume"] == 5
    assert r["iv"] == 0.4
    from techpulse.analytics import option_metrics

    assert option_metrics(r)["estimated_trade_premium"] == 600
    with pytest.raises(ValueError):
        store.import_csv(csv.replace(",2,3,100,", ",0,3,100,"), "options", "A", "https://example.org")


def test_political_identity_scoped_by_person_and_ranges_preserved(store):
    columns = "id,person,owner,asset,transaction_type,publication_date,transaction_date,value_min,value_max,currency\n"
    for person in ("Nancy Pelosi", "Donald Trump"):
        store.import_csv(
            columns + f"1,{person},spouse,TEST,purchase,2026-11-20,2026-11-19,1000,15000,USD\n",
            "disclosures",
            "Official filing",
            "https://example.org/filing",
        )
    records = store.records("research", "disclosures")
    assert len(records) == 2
    assert {r["person"] for r in records} == {"Nancy Pelosi", "Donald Trump"}
    assert records[0]["value_max"] == 15000


def test_contract_award_update_and_currency_gate(store):
    columns = "id,company,government,country,agency,purpose,status,obligated,ceiling,currency\n"
    row = "AW1,TEST,United States,US,Science,Compute,award,100,1000,USD\n"
    store.import_csv(columns + row, "contracts", "Official award", "https://example.org/award")
    store.import_csv(
        columns + row.replace(",100,1000", ",120,1000"),
        "contracts",
        "Official award",
        "https://example.org/award",
    )
    records = store.records("research", "contracts")
    assert len(records) == 1 and records[0]["obligated"] == 120
    with pytest.raises(ValueError, match="USD"):
        store.import_csv(
            columns + row.replace("USD", "EUR"), "contracts", "Official award", "https://example.org/award"
        )


def test_long_only_paper_accounting_and_chronology(store):
    import_bars(store)
    store.paper_trade("research", "TEST", "buy", "2", "100", "1", "2026-11-19")
    store.paper_trade("research", "TEST", "sell", "1", "120", "1", "2026-11-20")
    p = store.paper_positions("research")[0]
    assert p["quantity"] == Decimal(1)
    assert p["net_cost"] == Decimal(82)
    assert p["pnl"] == Decimal(28)
    with pytest.raises(ValueError, match="short"):
        store.paper_trade("research", "TEST", "sell", "2", "100", "0", "2026-11-20")
    with pytest.raises(ValueError, match="short"):
        store.paper_trade("research", "TEST", "sell", "1", "100", "0", "2026-11-18")
    with pytest.raises(ValueError):
        store.paper_trade("research", "TEST", "buy", "nan", "100", "0", "2026-11-20")


def test_realized_pnl_without_mark_and_old_mark_withheld(store):
    store.save_asset("research", {"symbol": "TEST", "kind": "equity"})
    store.db.commit()
    store.paper_trade("research", "TEST", "buy", 1, 100, 1, "2026-11-19")
    store.paper_trade("research", "TEST", "sell", 1, 120, 1, "2026-11-20")
    p = store.paper_positions("research")[0]
    assert p["value"] == 0 and p["pnl"] == 18
    import_bars(store)
    store.paper_trade("research", "TEST", "buy", 1, 110, 0, "2026-11-23")
    assert store.paper_positions("research")[0]["pnl"] is None


def test_settings_watchlists_backup_and_snapshot_are_local(store, tmp_path):
    import_bars(store)
    store.toggle_watch("research", "TEST")
    assert store.watchlist("research") == ["TEST"]
    assert store.watchlist("demo") == []
    store.set_setting("theme", "light")
    assert store.setting("theme") == "light"
    backup = tmp_path / "backup.db"
    store.backup(backup)
    with closing(sqlite3.connect(backup)) as db:
        assert json.loads(db.execute("SELECT payload FROM assets").fetchone()[0])["symbol"] == "TEST"
    backup.unlink()  # Windows destination connection must be closed.
    invalid = tmp_path / "invalid.db"
    invalid.write_bytes(b"not a sqlite database")
    with pytest.raises(sqlite3.Error):
        store.backup(invalid)
    invalid.unlink()
