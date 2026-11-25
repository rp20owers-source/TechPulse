import sqlite3
from contextlib import closing

import pytest

from techpulse import recovery
from techpulse.demo import seed_demo
from techpulse.recovery import RecoveryError, inspect_backup, restore_database
from techpulse.store import Store


def populated(path, name):
    store = Store(path)
    store.save_asset("research", {"symbol": name, "name": name, "kind": "equity"})
    store.db.commit()
    store.toggle_watch("research", name)
    store.set_setting("test_marker", name)
    return store


def test_restore_replaces_state_and_keeps_exact_previous_snapshot(tmp_path):
    source = populated(tmp_path / "source.db", "OLD")
    seed_demo(source)
    backup = tmp_path / "backup.db"
    source.backup(backup)
    source.close()
    inspected = inspect_backup(backup)
    assert inspected["schema_version"] == 1 and inspected["rows"]["assets"] == 14
    target = populated(tmp_path / "target.db", "CURRENT")
    result = restore_database(target, backup)
    assert target.watchlist("research") == ["OLD"]
    assert target.setting("test_marker") == "OLD"
    safety = Store(result["recovery_point"])
    assert safety.watchlist("research") == ["CURRENT"]
    assert safety.setting("test_marker") == "CURRENT"
    safety.close()
    assert len(target.bars("demo", "SYN-AI")) == 180
    # Restored connection remains usable for future writes and backups.
    target.set_setting("after_restore", True)
    target.backup(tmp_path / "after.db")
    target.close()
    backup.unlink()  # No source connection left locked on Windows.


@pytest.mark.parametrize("kind", ["not_sqlite", "unrelated", "future", "invalid_json", "trigger", "bad_bar"])
def test_invalid_backups_do_not_replace_current_data(tmp_path, kind):
    backup = tmp_path / "invalid.db"
    if kind == "not_sqlite":
        backup.write_text("Not a SQLite file")
    elif kind == "unrelated":
        with closing(sqlite3.connect(backup)) as db:
            db.execute("CREATE TABLE unrelated(x)")
            db.commit()
    else:
        fixture = populated(backup, "SAVED")
        if kind == "future":
            fixture.db.execute("PRAGMA user_version=2")
        elif kind == "invalid_json":
            fixture.db.execute("UPDATE assets SET payload='broken'")
        elif kind == "trigger":
            fixture.db.execute(
                "CREATE TRIGGER surprise AFTER INSERT ON settings BEGIN DELETE FROM watchlist; END"
            )
        elif kind == "bad_bar":
            fixture.save_bars(
                "research",
                "SAVED",
                [{"date": "2025-01-01", "open": 10, "high": 1, "low": 2, "close": 10, "volume": 1}],
            )
        fixture.db.commit()
        fixture.close()
    target = populated(tmp_path / "current.db", "CURRENT")
    with pytest.raises(RecoveryError):
        inspect_backup(backup)
    with pytest.raises(RecoveryError):
        restore_database(target, backup)
    assert target.watchlist("research") == ["CURRENT"]
    assert target.setting("test_marker") == "CURRENT"
    assert not (tmp_path / "recovery").exists()
    target.close()


def test_failed_final_copy_rolls_back_and_retains_safety_copy(tmp_path, monkeypatch):
    source = populated(tmp_path / "source.db", "OLD")
    # More than one page, so interruption is genuinely before completion.
    source.set_setting("large_fixture", "x" * 200000)
    source.backup(tmp_path / "backup.db")
    source.close()
    target = populated(tmp_path / "current.db", "CURRENT")
    original = recovery._copy
    calls = []

    def interrupted(source, destination, deadline):
        calls.append(True)
        if len(calls) == 3:

            def stop(*args):
                raise RecoveryError("Injected interruption")

            source.backup(destination, pages=1, progress=stop)
        else:
            original(source, destination, deadline)

    monkeypatch.setattr(recovery, "_copy", interrupted)
    with pytest.raises(RecoveryError, match="safety copy"):
        restore_database(target, tmp_path / "backup.db")
    assert target.watchlist("research") == ["CURRENT"]
    assert target.setting("test_marker") == "CURRENT"
    assert "large_fixture" not in dict(target.db.execute("SELECT key,value FROM settings"))
    assert len(list((tmp_path / "recovery").glob("*.db"))) == 1
    target.close()


def test_active_source_alias_and_pending_transaction_rejected(tmp_path):
    store = populated(tmp_path / "current.db", "CURRENT")
    with pytest.raises(RecoveryError, match="active database"):
        restore_database(store, store.path)
    store.backup(tmp_path / "backup.db")
    store.db.execute("INSERT INTO settings VALUES('pending','true')")
    with pytest.raises(RecoveryError, match="pending"):
        restore_database(store, tmp_path / "backup.db")
    store.db.rollback()
    store.close()


def test_timeout_and_missing_file_are_non_destructive(tmp_path):
    store = populated(tmp_path / "current.db", "CURRENT")
    with pytest.raises(RecoveryError):
        inspect_backup(tmp_path / "missing.db")
    store.backup(tmp_path / "backup.db")
    with pytest.raises(RecoveryError):
        restore_database(store, tmp_path / "backup.db", timeout=0)
    assert store.setting("test_marker") == "CURRENT"
    store.close()


def test_startup_rejects_future_and_unrelated_databases_without_modifying_them(tmp_path):
    future = tmp_path / "future.db"
    store = populated(future, "KEEP")
    store.db.execute("PRAGMA user_version=2")
    store.db.commit()
    store.close()
    before = future.read_bytes()
    with pytest.raises(ValueError, match="schema version"):
        Store(future)
    assert future.read_bytes() == before
    unrelated = tmp_path / "unrelated.db"
    with closing(sqlite3.connect(unrelated)) as db:
        db.execute("CREATE TABLE unrelated(x)")
        db.commit()
    before = unrelated.read_bytes()
    with pytest.raises(ValueError, match="not an initialized"):
        Store(unrelated)
    assert unrelated.read_bytes() == before


def test_done_callback_after_commit_does_not_raise_timeout(tmp_path, monkeypatch):
    source = populated(tmp_path / "source.db", "OLD")
    source.backup(tmp_path / "backup.db")
    source.close()
    target = populated(tmp_path / "current.db", "CURRENT")
    original = recovery._copy
    calls = []
    actual_time = recovery.time.monotonic

    # Deadline advances exactly when SQLite reports its already committed DONE.
    def wrap(source, destination, deadline):
        calls.append(True)
        if len(calls) == 3:

            class DoneClockConnection:
                def execute(self, *args):
                    return source.execute(*args)

                def backup(self, destination, **kwargs):
                    progress = kwargs["progress"]

                    def done(status, remaining, total):
                        if status == sqlite3.SQLITE_DONE:
                            monkeypatch.setattr(recovery.time, "monotonic", lambda: deadline + 1)
                        progress(status, remaining, total)

                    kwargs["progress"] = done
                    return source.backup(destination, **kwargs)

            original(DoneClockConnection(), destination, deadline)
        else:
            original(source, destination, deadline)

    monkeypatch.setattr(recovery, "_copy", wrap)
    result = restore_database(target, tmp_path / "backup.db")
    monkeypatch.setattr(recovery.time, "monotonic", actual_time)
    assert target.setting("test_marker") == "OLD"
    assert result["recovery_point"]
    target.close()


def test_unrelated_version_one_and_missing_constraints_rejected(tmp_path):
    unrelated = tmp_path / "unrelated-v1.db"
    with closing(sqlite3.connect(unrelated)) as db:
        db.execute("CREATE TABLE unrelated(x)")
        db.execute("PRAGMA user_version=1")
        db.commit()
    before = unrelated.read_bytes()
    with pytest.raises(ValueError, match="structure"):
        Store(unrelated)
    assert unrelated.read_bytes() == before
    fake = tmp_path / "no-constraints.db"
    with closing(sqlite3.connect(fake)) as db:
        for table, columns in recovery.SCHEMA.items():
            db.execute(f'CREATE TABLE "{table}" (' + ",".join(c + " TEXT" for c in columns) + ")")
        db.execute("PRAGMA user_version=1")
        db.commit()
    with pytest.raises(RecoveryError):
        inspect_backup(fake)


def test_wal_logical_size_limit_checked_before_staging(tmp_path, monkeypatch):
    source = populated(tmp_path / "wal.db", "OLD")
    source.db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    source.set_setting("big_fixture", "x" * 200000)
    monkeypatch.setattr(recovery, "MAX_BACKUP_BYTES", 100000)
    assert source.path.stat().st_size < recovery.MAX_BACKUP_BYTES
    target = populated(tmp_path / "current.db", "CURRENT")
    with pytest.raises(RecoveryError):
        inspect_backup(source.path)
    with pytest.raises(RecoveryError):
        restore_database(target, source.path)
    assert target.setting("test_marker") == "CURRENT"
    assert not (tmp_path / "recovery").exists()
    target.close()
    source.close()


@pytest.mark.parametrize("kind", ["bad_weights", "bad_theme", "bad_ledger", "nan_json", "bad_report"])
def test_invalid_logical_values_rejected_before_restore(tmp_path, kind):
    source = populated(tmp_path / "source.db", "SAVED")
    if kind == "bad_weights":
        source.set_setting("score_weights", {"technical": "100"})
    elif kind == "bad_theme":
        source.set_setting("theme", ["dark"])
    elif kind == "bad_ledger":
        source.db.execute(
            "INSERT INTO paper(mode,symbol,side,quantity,price,fee,date) VALUES('research','SAVED','sell','1','10','0','2025-01-01')"
        )
    elif kind == "nan_json":
        source.db.execute("INSERT INTO settings VALUES('not_standard_json','NaN')")
    elif kind == "bad_report":
        source.archive_report("research", "Broken", {"sections": {}, "workspace": "demo"})
    source.db.commit()
    source.backup(tmp_path / "backup.db")
    source.close()
    target = populated(tmp_path / "current.db", "CURRENT")
    with pytest.raises(RecoveryError):
        restore_database(target, tmp_path / "backup.db")
    assert target.setting("test_marker") == "CURRENT"
    assert not (tmp_path / "recovery").exists()
    target.close()


@pytest.mark.parametrize("limit", ["rows", "payload"])
def test_recovery_preview_caps_reject_before_safety_copy(tmp_path, monkeypatch, limit):
    source = populated(tmp_path / "source.db", "SAVED")
    source.set_setting("large_field", "x" * 200)
    source.backup(tmp_path / "backup.db")
    source.close()
    if limit == "rows":
        monkeypatch.setattr(recovery, "MAX_ROWS", 2)
    else:
        monkeypatch.setattr(recovery, "MAX_PAYLOAD_BYTES", 100)
    target = populated(tmp_path / "current.db", "CURRENT")
    with pytest.raises(RecoveryError):
        restore_database(target, tmp_path / "backup.db")
    assert target.setting("test_marker") == "CURRENT"
    assert not (tmp_path / "recovery").exists()
    target.close()
