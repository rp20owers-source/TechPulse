import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QDialog, QLabel

from techpulse import paths, recovery, startup
from techpulse.store import Store


@pytest.fixture
def isolated_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.delenv("TECHPULSE_DATA_DIR", raising=False)
    return tmp_path


def make_backup(path):
    store = Store(path)
    store.set_setting("synthetic_marker", "saved research")
    store.save_asset("research", {"symbol": "SYNTHETIC", "name": "Synthetic fixture", "kind": "equity"})
    store.db.commit()
    store.toggle_watch("research", "SYNTHETIC")
    store.close()
    return path


def test_saved_directory_and_explicit_override_precedence(isolated_paths, monkeypatch):
    directory = isolated_paths / "chosen"
    make_backup(directory / "techpulse.db")
    paths.remember_directory(directory)
    assert paths.data_directory() == directory.resolve()
    monkeypatch.setenv("TECHPULSE_DATA_DIR", str(isolated_paths / "explicit"))
    assert paths.data_directory() == (isolated_paths / "explicit").resolve()


@pytest.mark.parametrize("payload", ["broken", "[]", '{"version":2}', '{"version":1}', '"x"'])
def test_broken_preference_never_falls_back_to_new_database(isolated_paths, payload):
    pointer = paths.preference_path()
    pointer.parent.mkdir(parents=True)
    pointer.write_text(payload, encoding="utf8")
    with pytest.raises(ValueError, match="saved workspace"):
        paths.data_directory()
    assert not (pointer.parent / "techpulse.db").exists()


def test_missing_saved_database_is_rejected_without_recreating_folder(isolated_paths):
    missing = isolated_paths / "missing"
    pointer = paths.preference_path()
    pointer.parent.mkdir(parents=True)
    pointer.write_text(json.dumps({"version": 1, "data_directory": str(missing)}))
    with pytest.raises(ValueError):
        paths.data_directory()
    assert not missing.exists()


def test_failed_preference_replace_preserves_previous_choice(isolated_paths, monkeypatch):
    old = isolated_paths / "old"
    new = isolated_paths / "new"
    make_backup(old / "techpulse.db")
    make_backup(new / "techpulse.db")
    paths.remember_directory(old)

    def fail(*args):
        raise OSError("Synthetic disk failure")

    monkeypatch.setattr(paths.os, "replace", fail)
    with pytest.raises(OSError):
        paths.remember_directory(new)
    assert paths.data_directory() == old.resolve()
    assert not list(paths.preference_path().parent.glob(".workspace-*"))


def test_recover_new_copy_retains_source_and_original_directory(tmp_path):
    backup = make_backup(tmp_path / "backup.db")
    original_bytes = backup.read_bytes()
    failed = tmp_path / "original"
    failed.mkdir()
    damaged = failed / "techpulse.db"
    damaged.write_bytes(b"synthetic damaged original")
    result = recovery.recover_to_directory(backup, failed)
    directory = Path(result["data_directory"])
    assert directory.parent == failed.resolve()
    assert damaged.read_bytes() == b"synthetic damaged original"
    assert backup.read_bytes() == original_bytes
    store = Store(directory / "techpulse.db")
    assert store.setting("synthetic_marker") == "saved research"
    assert store.watchlist("research") == ["SYNTHETIC"]
    store.close()


def test_invalid_backup_does_not_publish_recovered_folder(tmp_path):
    backup = tmp_path / "bad.db"
    backup.write_bytes(b"invalid backup")
    with pytest.raises(recovery.RecoveryError):
        recovery.recover_to_directory(backup, tmp_path)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["bad.db"]


def test_publish_failure_cleans_only_new_empty_destination(tmp_path, monkeypatch):
    backup = make_backup(tmp_path / "backup.db")
    sentinel = tmp_path / "user-file.txt"
    sentinel.write_text("keep")

    def fail(*args):
        raise OSError("Synthetic move failure")

    monkeypatch.setattr(Path, "replace", fail)
    with pytest.raises(recovery.RecoveryError):
        recovery.recover_to_directory(backup, tmp_path)
    assert sentinel.read_text() == "keep"
    assert not list(tmp_path.glob("TechPulse-recovered-*"))


def test_startup_cancel_preserves_damaged_file(qtbot, isolated_paths, monkeypatch):
    directory = paths.default_directory()
    directory.mkdir(parents=True)
    original = directory / "techpulse.db"
    original.write_bytes(b"synthetic corrupt original")
    monkeypatch.setattr(startup.StartupRecoveryDialog, "exec", lambda self: QDialog.DialogCode.Rejected)
    assert startup.open_window(lambda store: pytest.fail("Must not open damaged Store")) is None
    assert original.read_bytes() == b"synthetic corrupt original"


@pytest.mark.parametrize("contents", [b"", b"not sqlite"])
def test_existing_invalid_files_are_not_initialized(qtbot, isolated_paths, monkeypatch, contents):
    directory = paths.default_directory()
    directory.mkdir(parents=True)
    original = directory / "techpulse.db"
    original.write_bytes(contents)
    monkeypatch.setattr(startup.StartupRecoveryDialog, "exec", lambda self: QDialog.DialogCode.Rejected)
    assert startup.open_window(lambda store: None) is None
    assert original.read_bytes() == contents


def test_startup_selected_workspace_saved_only_after_success(qtbot, isolated_paths, monkeypatch):
    pointer = paths.preference_path()
    pointer.parent.mkdir(parents=True)
    pointer.write_text("broken")
    selected = isolated_paths / "recovered"
    make_backup(selected / "techpulse.db")

    def choose(self):
        self.selection = selected
        self.remember.setChecked(True)
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(startup.StartupRecoveryDialog, "exec", choose)
    window = startup.open_window(lambda store: SimpleNamespace(store=store, status=QLabel()))
    assert window.store.setting("synthetic_marker") == "saved research"
    assert os.environ["TECHPULSE_DATA_DIR"] == str(selected)
    assert json.loads(pointer.read_text())["data_directory"] == str(selected)
    window.store.close()


def test_explicit_override_disables_remember(qtbot, isolated_paths):
    dialog = startup.StartupRecoveryDialog("synthetic failure", isolated_paths, can_remember=False)
    qtbot.addWidget(dialog)
    assert not dialog.remember.isEnabled()
    assert not dialog.remember.isChecked()
    assert dialog.selection is None


def test_existing_folder_missing_database_is_not_initialized(qtbot, tmp_path, monkeypatch):
    dialog = startup.StartupRecoveryDialog("synthetic failure", tmp_path)
    qtbot.addWidget(dialog)
    errors = []
    monkeypatch.setattr(startup.QFileDialog, "getExistingDirectory", lambda *args: str(tmp_path))
    monkeypatch.setattr(dialog, "error", errors.append)
    dialog.open_existing()
    assert errors and dialog.selection is None
    assert not (tmp_path / "techpulse.db").exists()


def test_relative_store_path_stays_stable_after_cwd_change(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = Store("relative.db")
    monkeypatch.chdir(tmp_path.parent)
    assert store.path == (tmp_path / "relative.db").resolve()
    store.backup(tmp_path / "copy.db")
    store.close()


def test_store_initialization_failure_closes_connection(tmp_path, monkeypatch):
    real = sqlite3.connect
    connections = []

    class FailingConnection(sqlite3.Connection):
        def executescript(self, script):
            raise sqlite3.OperationalError("Synthetic initialization failure")

    def connect(path):
        connection = real(path, factory=FailingConnection)
        connections.append(connection)
        return connection

    monkeypatch.setattr("techpulse.store.sqlite3.connect", connect)
    with pytest.raises(sqlite3.OperationalError):
        Store(tmp_path / "failed.db")
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        connections[0].execute("SELECT 1")


def test_recovery_timeout_publishes_nothing(tmp_path):
    backup = make_backup(tmp_path / "backup.db")
    with pytest.raises(recovery.RecoveryError):
        recovery.recover_to_directory(backup, tmp_path, timeout=-1)
    assert not list(tmp_path.glob("TechPulse-recovered-*"))
    assert not list(tmp_path.glob(".techpulse-recover-*"))


def test_recovery_cleanup_failure_reports_published_copy(tmp_path, monkeypatch):
    backup = make_backup(tmp_path / "backup.db")
    real_temporary = recovery.tempfile.TemporaryDirectory

    class CleanupFailure:
        def __init__(self, *args, **kwargs):
            self.temporary = real_temporary(*args, **kwargs)

        def __enter__(self):
            return self.temporary.__enter__()

        def __exit__(self, *args):
            self.temporary.__exit__(*args)
            raise OSError("Synthetic cleanup error after publication")

    monkeypatch.setattr(recovery.tempfile, "TemporaryDirectory", CleanupFailure)
    result = recovery.recover_to_directory(backup, tmp_path)
    assert result["warning"]
    assert recovery.inspect_backup(Path(result["data_directory"]) / "techpulse.db")["rows"]["assets"] == 1


def test_fresh_folder_keeps_existing_data_and_cancel_creates_nothing(qtbot, tmp_path, monkeypatch):
    old = tmp_path / "techpulse.db"
    old.write_bytes(b"original")
    dialog = startup.StartupRecoveryDialog("synthetic failure", tmp_path)
    qtbot.addWidget(dialog)
    monkeypatch.setattr(startup.QFileDialog, "getExistingDirectory", lambda *args: "")
    dialog.start_fresh()
    assert dialog.selection is None
    assert list(tmp_path.iterdir()) == [old]
    monkeypatch.setattr(startup.QFileDialog, "getExistingDirectory", lambda *args: str(tmp_path))
    dialog.start_fresh()
    assert dialog.selection.parent == tmp_path
    assert dialog.selection.name.startswith("TechPulse-fresh-")
    assert old.read_bytes() == b"original"


def test_dialog_recovers_valid_backup_into_separate_folder(qtbot, tmp_path, monkeypatch):
    backup = make_backup(tmp_path / "backup.db")
    dialog = startup.StartupRecoveryDialog("synthetic failure", tmp_path)
    qtbot.addWidget(dialog)
    monkeypatch.setattr(startup.QFileDialog, "getOpenFileName", lambda *args: (str(backup), ""))
    monkeypatch.setattr(startup.QFileDialog, "getExistingDirectory", lambda *args: str(tmp_path))
    dialog.recover_backup()
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.selection != backup.parent
    assert recovery.inspect_backup(dialog.selection / "techpulse.db")["rows"]["assets"] == 1


def test_factory_failure_does_not_save_choice(qtbot, isolated_paths, monkeypatch):
    original = paths.default_directory() / "techpulse.db"
    original.parent.mkdir(parents=True)
    original.write_bytes(b"synthetic failure")
    selected = isolated_paths / "selected"
    make_backup(selected / "techpulse.db")
    calls = []

    def choose_then_cancel(self):
        calls.append(True)
        if len(calls) == 1:
            self.selection = selected
            self.remember.setChecked(True)
            return QDialog.DialogCode.Accepted
        return QDialog.DialogCode.Rejected

    def failing_factory(store):
        raise ValueError("Synthetic main window failure")

    monkeypatch.setattr(startup.StartupRecoveryDialog, "exec", choose_then_cancel)
    assert startup.open_window(failing_factory) is None
    assert not paths.preference_path().exists()
    assert original.read_bytes() == b"synthetic failure"
    # Failed construction closed the Store's handle.
    (selected / "techpulse.db").unlink()


def test_recovery_includes_committed_wal_rows_from_open_source(tmp_path):
    source = Store(tmp_path / "wal-source.db")
    source.db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    source.set_setting("committed_in_wal", "synthetic marker")
    result = recovery.recover_to_directory(source.path, tmp_path)
    restored = Store(Path(result["data_directory"]) / "techpulse.db")
    assert restored.setting("committed_in_wal") == "synthetic marker"
    restored.close()
    assert source.setting("committed_in_wal") == "synthetic marker"
    source.close()


def test_smoke_failure_is_noninteractive_and_preserves_empty_existing_file(tmp_path):
    original = tmp_path / "techpulse.db"
    original.write_bytes(b"")
    result = subprocess.run(
        [sys.executable, "-m", "techpulse", "--smoke-test", "--data-dir", str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=15,
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
    )
    assert result.returncode != 0
    assert "RecoveryError" in result.stderr
    assert original.read_bytes() == b""
