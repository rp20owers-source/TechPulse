"""Local SQLite recovery with validation, staging and a pre-restore safety copy."""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import time
from contextlib import closing
from decimal import Decimal
from pathlib import Path

from .analytics import score_candidate
from .store import (
    KINDS,
    MODES,
    Store,
    check_schema,
    iso_date,
    number,
    symbol_value,
    validate_bar,
    validate_record,
)

SCHEMA = {
    "assets": ("mode", "symbol", "payload"),
    "bars": ("mode", "symbol", "date", "payload"),
    "records": ("mode", "kind", "id", "payload"),
    "watchlist": ("mode", "symbol"),
    "paper": ("id", "mode", "symbol", "side", "quantity", "price", "fee", "date"),
    "settings": ("key", "value"),
    "reports": ("id", "mode", "created_at", "title", "payload"),
}
MAX_BACKUP_BYTES = 2 * 1024**3
MAX_ROWS = 1_000_000
MAX_PAYLOAD_BYTES = 32 * 1024**2


class RecoveryError(ValueError):
    """A user-facing local recovery failure; existing data is not silently discarded."""


def _json(value):
    def reject_constant(value):
        raise ValueError("Nonfinite JSON value")

    return json.loads(value, parse_constant=reject_constant)


def _check_deadline(deadline):
    if time.monotonic() >= deadline:
        raise RecoveryError("Recovery time limit reached; close other database users and retry")


def _copy(source, destination, deadline):
    page_size = source.execute("PRAGMA page_size").fetchone()[0]
    if source.execute("PRAGMA page_count").fetchone()[0] * page_size > MAX_BACKUP_BYTES:
        raise RecoveryError("Logical backup size exceeds the 2 GiB recovery limit")

    def progress(status, remaining, total):
        if status != sqlite3.SQLITE_DONE:
            if total * page_size > MAX_BACKUP_BYTES:
                raise RecoveryError("Logical backup size exceeds the recovery limit")
            _check_deadline(deadline)

    _check_deadline(deadline)
    source.backup(destination, pages=128, progress=progress, sleep=0.02)


def _open_readonly(path):
    path = Path(path).resolve()
    if not path.is_file() or not 0 < path.stat().st_size <= MAX_BACKUP_BYTES:
        raise RecoveryError("Choose a nonempty SQLite backup of at most 2 GiB")
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2)
    try:
        connection.execute("PRAGMA query_only=ON")
        connection.execute("PRAGMA trusted_schema=OFF")
        return connection
    except sqlite3.Error:
        connection.close()
        raise


def _validate(connection, deadline):
    connection.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
    try:
        if connection.execute("PRAGMA user_version").fetchone()[0] != 1:
            raise RecoveryError("Backup schema version is unsupported; current app supports version 1")
        if (
            connection.execute("PRAGMA page_count").fetchone()[0]
            * connection.execute("PRAGMA page_size").fetchone()[0]
            > MAX_BACKUP_BYTES
        ):
            raise RecoveryError("Logical backup size exceeds the 2 GiB recovery limit")
        check_schema(connection)
        objects = connection.execute(
            "SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
        ).fetchall()
        if {row[1] for row in objects if row[0] == "table"} != set(SCHEMA):
            raise RecoveryError("This is not a recognized TechPulse backup")
        if any(
            kind != "table" or (sql and "CREATE VIRTUAL TABLE" in sql.upper()) for kind, _, sql in objects
        ):
            raise RecoveryError("Backup contains unsupported views, triggers or custom indexes")
        counts = {}
        total = 0
        for name, columns in SCHEMA.items():
            _check_deadline(deadline)
            actual = tuple(row[1] for row in connection.execute(f'PRAGMA table_info("{name}")'))
            if actual != columns:
                raise RecoveryError(f"Backup table {name} has an incompatible structure")
            counts[name] = connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
            total += counts[name]
        if total > MAX_ROWS:
            raise RecoveryError(
                "Backup exceeds this preview's one-million-row recovery limit; use manual recovery"
            )
        for table, column in (
            ("assets", "payload"),
            ("bars", "payload"),
            ("records", "payload"),
            ("reports", "payload"),
            ("settings", "value"),
        ):
            if connection.execute(
                f'SELECT 1 FROM "{table}" WHERE length(CAST("{column}" AS BLOB)) > ? LIMIT 1',
                (MAX_PAYLOAD_BYTES,),
            ).fetchone():
                raise RecoveryError("Backup contains a JSON field above this preview's 32 MiB recovery limit")
        if connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise RecoveryError("SQLite integrity check failed; backup was not restored")
        for name in ("assets", "bars", "records", "watchlist", "paper", "reports"):
            if connection.execute(
                f'SELECT 1 FROM "{name}" WHERE mode NOT IN (?,?) OR mode IS NULL LIMIT 1',
                tuple(sorted(MODES)),
            ).fetchone():
                raise RecoveryError(f"Backup {name} contains an invalid workspace")
        # Parse payloads rather than trusting SQLite page integrity alone.
        for symbol, payload in connection.execute("SELECT symbol,payload FROM assets"):
            symbol_value(symbol)
            value = _json(payload)
            if not isinstance(value, dict) or value.get("symbol") != symbol or value.get("kind") not in KINDS:
                raise RecoveryError("Backup contains invalid asset metadata")
            for field in ("market_cap", "revenue", "pe", "shares_outstanding"):
                number(value.get(field), field, minimum=0, optional=True)
        for stamp, payload in connection.execute("SELECT date,payload FROM bars"):
            value = _json(payload)
            if not isinstance(value, dict) or value.get("date") != stamp:
                raise RecoveryError("Backup contains invalid price identities")
            validate_bar(value)
        for kind, identity, payload in connection.execute("SELECT kind,id,payload FROM records"):
            value = _json(payload)
            if (
                kind not in {"options", "contracts", "disclosures"}
                or not isinstance(value, dict)
                or not value.get("id")
                or Store.record_key(kind, value) != identity
            ):
                raise RecoveryError("Backup contains invalid research record identities")
            validate_record(kind, value)
        for mode, payload in connection.execute("SELECT mode,payload FROM reports"):
            value = _json(payload)
            if not isinstance(value, dict) or not isinstance(value.get("sections"), dict):
                raise RecoveryError("Backup contains an invalid archived report")
            if value.get("workspace") != mode or any(
                not isinstance(value.get(key), str) for key in ("title", "created_at", "warning")
            ):
                raise RecoveryError("Backup report metadata does not match its workspace")
        for key, value in connection.execute("SELECT key,value FROM settings"):
            setting = _json(value)
            if key == "theme" and setting not in ("dark", "light"):
                raise RecoveryError("Backup theme setting is invalid")
            if key == "score_weights":
                if (
                    not isinstance(setting, dict)
                    or any(type(v) is not int or not 0 <= v <= 100 for v in setting.values())
                    or sum(setting.values()) != 100
                    or setting.get("reliability", 0) == 0
                ):
                    raise RecoveryError("Backup research weights are invalid")
                score_candidate({}, setting)
            if key in ("weekly_demo", "weekly_research") and not isinstance(setting, bool):
                raise RecoveryError("Backup report schedule setting is invalid")
        balances: dict[tuple[str, str], Decimal] = {}
        for mode, symbol, side, quantity, price, fee, stamp in connection.execute(
            "SELECT mode,symbol,side,quantity,price,fee,date FROM paper ORDER BY date,id"
        ):
            symbol_value(symbol)
            if iso_date(stamp) != stamp or side not in ("buy", "sell"):
                raise RecoveryError("Backup paper ledger contains an invalid transaction")
            if any(not isinstance(value, str) or len(value) > 256 for value in (quantity, price, fee)):
                raise RecoveryError("Backup paper amounts are invalid")
            q, p, f = (Decimal(value) for value in (quantity, price, fee))
            if not all(value.is_finite() for value in (q, p, f)) or q <= 0 or p <= 0 or f < 0:
                raise RecoveryError("Backup paper amounts are invalid")
            balance_key = (mode, symbol)
            balances[balance_key] = balances.get(balance_key, Decimal(0)) + q * (1 if side == "buy" else -1)
            if balances[balance_key] < 0:
                raise RecoveryError("Backup paper ledger would create a short position")
        _check_deadline(deadline)
        return {"schema_version": 1, "rows": counts, "total_rows": total}
    except (sqlite3.Error, TypeError, ValueError, KeyError, RecursionError, ArithmeticError) as exc:
        if isinstance(exc, RecoveryError):
            raise
        raise RecoveryError("Backup validation failed; current data was not replaced") from exc
    finally:
        connection.set_progress_handler(None, 0)


def inspect_backup(path, *, timeout=30):
    """Read-only schema/integrity/payload check; never initialize arbitrary files."""
    try:
        with closing(_open_readonly(path)) as source:
            return _validate(source, time.monotonic() + timeout)
    except (sqlite3.Error, OSError) as exc:
        raise RecoveryError("Cannot read this backup as a TechPulse SQLite database") from exc


def restore_database(store: Store, backup, *, timeout=30):
    """Replace a live connection from a validated staged snapshot, retaining old data.

    Must be called on the Store's thread with no uncommitted transaction. SQLite
    backup is transactional; a failed destination copy rolls back. A pre-restore
    snapshot is created before replacement, and is retained even on failure.
    """
    backup = Path(backup).resolve()
    if backup == store.path.resolve() or (backup.exists() and backup.samefile(store.path)):
        raise RecoveryError("Choose a separate backup file, not the active database")
    if store.db.in_transaction:
        raise RecoveryError("Finish or roll back pending data changes before restoring")
    deadline = time.monotonic() + timeout
    recovery_point = None
    completed = False
    summary = {}
    try:
        # Validate the copied snapshot, not a source which might change after preview.
        with tempfile.TemporaryDirectory(prefix=".techpulse-restore-", dir=store.path.parent) as temporary:
            if Path(temporary).resolve().parent != store.path.parent.resolve():
                raise RecoveryError("Recovery staging directory is outside the database folder")
            with closing(sqlite3.connect(Path(temporary) / "staged.db")) as staged:
                with closing(_open_readonly(backup)) as source:
                    _copy(source, staged, deadline)
                summary = _validate(staged, deadline)
                recovery_dir = store.path.parent / "recovery"
                recovery_dir.mkdir(exist_ok=True)
                descriptor, filename = tempfile.mkstemp(
                    prefix="before-restore-", suffix=".db", dir=recovery_dir
                )
                os.close(descriptor)
                recovery_point = Path(filename)
                with closing(sqlite3.connect(recovery_point)) as previous:
                    _copy(store.db, previous, deadline)
                _copy(staged, store.db, deadline)
                completed = True
        return {**summary, "recovery_point": str(recovery_point)}
    except (sqlite3.Error, OSError, RecoveryError) as exc:
        if completed:
            return {
                **summary,
                "recovery_point": str(recovery_point),
                "warning": "Data restored, but temporary recovery files could not be fully cleaned up",
            }
        detail = f" Previous data safety copy: {recovery_point}" if recovery_point else ""
        raise RecoveryError(
            "Restore did not complete." + detail + " Current database was not silently reset."
        ) from exc
