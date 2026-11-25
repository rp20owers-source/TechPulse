"""Validated, atomic local persistence. No network, secrets or silent demo fallback."""

from __future__ import annotations

import csv
import io
import json
import math
import re
import sqlite3
from contextlib import closing
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from itertools import islice
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlparse

from .paths import data_directory

MODES = {"demo", "research"}
KINDS = {"equity", "crypto", "benchmark"}

SCHEMA_SQL = """
        CREATE TABLE IF NOT EXISTS assets(mode TEXT, symbol TEXT, payload TEXT NOT NULL, PRIMARY KEY(mode,symbol));
        CREATE TABLE IF NOT EXISTS bars(mode TEXT, symbol TEXT, date TEXT, payload TEXT NOT NULL, PRIMARY KEY(mode,symbol,date));
        CREATE TABLE IF NOT EXISTS records(mode TEXT, kind TEXT, id TEXT, payload TEXT NOT NULL, PRIMARY KEY(mode,kind,id));
        CREATE TABLE IF NOT EXISTS watchlist(mode TEXT, symbol TEXT, PRIMARY KEY(mode,symbol));
        CREATE TABLE IF NOT EXISTS paper(id INTEGER PRIMARY KEY, mode TEXT, symbol TEXT, side TEXT, quantity TEXT, price TEXT, fee TEXT, date TEXT);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS reports(id INTEGER PRIMARY KEY, mode TEXT, created_at TEXT, title TEXT, payload TEXT);
        PRAGMA user_version=1;
        """


def check_schema(connection):
    """Reject unfamiliar schemas before initialization, recovery or journal writes."""
    with closing(sqlite3.connect(":memory:")) as expected:
        expected.executescript(SCHEMA_SQL)
        query = "SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"

        def normalized(rows):
            return [
                (kind, name, table, re.sub(r"\s+", "", sql or "").casefold())
                for kind, name, table, sql in rows
            ]

        if normalized(connection.execute(query).fetchall()) != normalized(expected.execute(query).fetchall()):
            raise ValueError("Database structure is not a supported TechPulse schema; it was not changed")
        for (table,) in expected.execute("SELECT name FROM sqlite_master WHERE type='table'"):
            if [tuple(r) for r in connection.execute(f'PRAGMA table_info("{table}")')] != [
                tuple(r) for r in expected.execute(f'PRAGMA table_info("{table}")')
            ]:
                raise ValueError("Database column constraints are incompatible; it was not changed")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def number(value, field: str, *, minimum=None, optional=False):
    if value is None or str(value).strip() == "":
        if optional:
            return None
        raise ValueError(f"{field} is required")
    try:
        result = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not math.isfinite(result) or (minimum is not None and result < minimum):
        raise ValueError(f"{field} must be finite and >= {minimum}")
    return result


def iso_date(value, field="date", optional=False):
    if optional and not value:
        return None
    try:
        result = date.fromisoformat(str(value))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{field} must be YYYY-MM-DD") from exc
    if result > date.today():
        raise ValueError(f"{field} cannot be in the future")
    return result.isoformat()


def symbol_value(value):
    result = str(value).strip().upper()
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9./_-]{0,23}", result):
        raise ValueError("symbol must contain 1–24 letters, digits, . / _ or -")
    return result


def safe_url(value):
    result = str(value).strip()
    parsed = urlparse(result)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("Source URL must be a credential-free https:// URL")
    sensitive = {
        "key",
        "apikey",
        "secret",
        "token",
        "accesstoken",
        "authorization",
        "auth",
        "password",
        "credential",
        "signature",
    }
    pairs = parse_qsl(parsed.query) + parse_qsl(parsed.fragment)
    if any(
        (normalized := re.sub(r"[^a-z]", "", k.lower())) in sensitive
        or normalized.endswith(
            ("apikey", "secretkey", "secret", "token", "signature", "password", "credential")
        )
        for k, _ in pairs
    ):
        raise ValueError("Remove credentials from the source URL query or fragment")
    return result


def validate_bar(row):
    result = {"date": iso_date(row.get("date"))}
    for field in ("open", "high", "low", "close"):
        result[field] = number(row.get(field), field, minimum=0.000000001)
    result["volume"] = number(row.get("volume"), "volume", minimum=0)
    if (
        result["low"] > min(result["open"], result["close"])
        or result["high"] < max(result["open"], result["close"])
        or result["low"] > result["high"]
    ):
        raise ValueError("OHLC prices are inconsistent")
    return result


def validate_record(kind: str, raw: dict) -> dict:
    r = {k: v for k, v in raw.items() if v is not None and str(v).strip() != ""}
    if r.get("currency") != "USD":
        raise ValueError(
            "Explicit currency=USD is required; non-USD amounts need documented conversion before import"
        )
    if kind == "options":
        for required in ("id", "symbol", "date", "record_type", "option_type", "expiry", "strike"):
            if not r.get(required):
                raise ValueError(f"Options {required} is required")
        r["symbol"] = symbol_value(r["symbol"])
        r["date"] = iso_date(r["date"])
        # Expiry may be in the future.
        r["expiry"] = date.fromisoformat(r["expiry"]).isoformat()
        if r["expiry"] < r["date"]:
            raise ValueError("Option expiry precedes observation")
        if r["record_type"] not in {"trade", "aggregate"} or r["option_type"] not in {"call", "put"}:
            raise ValueError("Use record_type trade/aggregate and option_type call/put")
        r["strike"] = number(r["strike"], "strike", minimum=0.000000001)
        fields = ("size", "price", "multiplier") if r["record_type"] == "trade" else ("volume",)
        for field in fields:
            r[field] = number(
                r.get(field), field, minimum=0.000000001 if field in {"size", "multiplier"} else 0
            )
        for field in ("open_interest", "historical_volume", "implied_volatility", "previous_iv"):
            r[field] = number(r.get(field), field, minimum=0, optional=True)
    elif kind == "contracts":
        for field in ("id", "company", "government", "country", "agency", "purpose", "status"):
            if not r.get(field):
                raise ValueError(f"Contract {field} is required")
        if r["status"] not in {"proposal", "announced", "award", "funded"}:
            raise ValueError("Contract status must be proposal/announced/award/funded")
        if r.get("ticker"):
            r["ticker"] = symbol_value(r["ticker"])
            if str(r.get("mapping_confirmed", "")).lower() != "true":
                raise ValueError("Ticker mapping requires mapping_confirmed=true and a verified source")
        for field in ("award_date", "announcement_date"):
            r[field] = iso_date(r.get(field), field, optional=True)
        r["ceiling"] = number(r.get("ceiling"), "ceiling", minimum=0, optional=True)
        r["obligated"] = number(r.get("obligated"), "obligated", optional=True)
        for field in ("duration", "technology", "expansion", "implications", "risks"):
            r.setdefault(field, "Not disclosed")
        r.setdefault("value_basis", "Award-level observation; not additive across updates")
    elif kind == "disclosures":
        if r.get("person") not in {"Nancy Pelosi", "Donald Trump"}:
            raise ValueError("Person must be Nancy Pelosi or Donald Trump")
        for field in ("id", "owner", "asset", "transaction_type", "publication_date"):
            if not r.get(field):
                raise ValueError(f"Disclosure {field} is required")
        if r["owner"] not in {"personal", "spouse", "dependent", "associated", "unspecified"}:
            raise ValueError("Invalid disclosure owner classification")
        r["publication_date"] = iso_date(r["publication_date"], "publication_date")
        r["transaction_date"] = iso_date(r.get("transaction_date"), "transaction_date", optional=True)
        if r["transaction_date"] and r["transaction_date"] > r["publication_date"]:
            raise ValueError("Transaction date cannot follow publication")
        r["value_min"] = number(r.get("value_min"), "value_min", minimum=0, optional=True)
        r["value_max"] = number(r.get("value_max"), "value_max", minimum=0, optional=True)
        if r["value_min"] is not None and r["value_max"] is not None and r["value_min"] > r["value_max"]:
            raise ValueError("Invalid disclosed value range")
        if r.get("symbol"):
            r["symbol"] = symbol_value(r["symbol"])
    else:
        raise ValueError("Unknown record kind")
    if len(str(r["id"])) > 200:
        raise ValueError("Record ID too long")
    if kind == "options":
        r["historical_average_volume"] = r.get("historical_volume")
        r["iv"] = r.get("implied_volatility")
    return r


class Store:
    def __init__(self, path: Path | str | None = None):
        self.path = (Path(path) if path else data_directory() / "techpulse.db").expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        try:
            version = self.db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise ValueError(
                    "This database requires a different TechPulse schema version; it was not changed"
                )
            if (
                version == 0
                and self.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' LIMIT 1").fetchone()
            ):
                raise ValueError("This is not an initialized TechPulse database; it was not changed")
            if version == 1:
                check_schema(self.db)
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.executescript(SCHEMA_SQL)
        except (sqlite3.Error, ValueError):
            self.db.close()
            raise

    @staticmethod
    def _mode(mode):
        if mode not in MODES:
            raise ValueError("Unknown workspace")

    def assets(self, mode):
        self._mode(mode)
        return [
            json.loads(r[0])
            for r in self.db.execute("SELECT payload FROM assets WHERE mode=? ORDER BY symbol", (mode,))
        ]

    def bars(self, mode, symbol):
        self._mode(mode)
        return [
            json.loads(r[0])
            for r in self.db.execute(
                "SELECT payload FROM bars WHERE mode=? AND symbol=? ORDER BY date", (mode, symbol)
            )
        ]

    def records(self, mode, kind):
        self._mode(mode)
        return [
            json.loads(r[0])
            for r in self.db.execute(
                "SELECT payload FROM records WHERE mode=? AND kind=? ORDER BY id", (mode, kind)
            )
        ]

    def save_asset(self, mode, asset):
        self._mode(mode)
        self.db.execute(
            "INSERT OR REPLACE INTO assets VALUES(?,?,?)",
            (mode, asset["symbol"], json.dumps(asset, allow_nan=False)),
        )

    def save_bars(self, mode, symbol, rows):
        self._mode(mode)
        self.db.executemany(
            "INSERT OR REPLACE INTO bars VALUES(?,?,?,?)",
            [(mode, symbol, b["date"], json.dumps(b, allow_nan=False)) for b in rows],
        )

    @staticmethod
    def record_key(kind, record):
        identity: tuple[Any, ...]
        if kind == "disclosures":
            identity = (record.get("person"), record["id"])
        elif kind == "contracts":
            identity = (record.get("country"), record.get("government"), record.get("agency"), record["id"])
        else:
            identity = (record.get("source"), record["id"])
        return json.dumps(identity, ensure_ascii=True)

    def save_record(self, mode, kind, record):
        self._mode(mode)
        self.db.execute(
            "INSERT OR REPLACE INTO records VALUES(?,?,?,?)",
            (mode, kind, self.record_key(kind, record), json.dumps(record, allow_nan=False)),
        )

    def import_csv(self, content: str, kind: str, source: str, source_url: str):
        """All-or-nothing personal research import. Duplicate IDs in a file rejected; cross-file IDs update."""
        if not source.strip():
            raise ValueError("A source name is required")
        provenance = {
            "source": source.strip(),
            "source_url": safe_url(source_url),
            "fetched_at": utc_now(),
            "coverage": "Authorized user import; coverage unverified",
        }
        if len(content) > 20_000_000:
            raise ValueError("Import exceeds 20 MB; split the file")
        try:
            reader = csv.DictReader(io.StringIO(content.lstrip("\ufeff")), strict=True)
            if reader.fieldnames and len(reader.fieldnames) != len(set(reader.fieldnames)):
                raise ValueError("Duplicate CSV column names")
            if not reader.fieldnames or any(not h or not h.strip() for h in reader.fieldnames):
                raise ValueError("CSV needs nonempty column names")
            rows = list(islice(reader, 100001))
        except csv.Error as exc:
            raise ValueError("Malformed CSV or oversized field; each field must be <=128 KiB") from exc
        if not rows or len(rows) > 100_000:
            raise ValueError("Import must contain 1–100,000 rows")
        checked: list[Any] = []
        seen: set[Any] = set()
        record: Any
        key: Any
        for i, row in enumerate(rows, 2):
            try:
                if None in row or any(v is None for v in row.values()):
                    raise ValueError("Row has the wrong number of fields")
                if row.get("currency") != "USD":
                    raise ValueError(
                        "Every row requires currency=USD; convert non-USD inputs with documented FX assumptions first"
                    )
                if kind == "bars":
                    sym = symbol_value(row.get("symbol", ""))
                    bar = validate_bar(row) | provenance
                    asset_kind = row.get("kind", "equity") or "equity"
                    if asset_kind not in KINDS:
                        raise ValueError("kind must be equity/crypto/benchmark")
                    record = (sym, bar, asset_kind, row.get("category") or "Unclassified")
                    key = (sym, bar["date"])
                elif kind == "assets":
                    sym = symbol_value(row.get("symbol", ""))
                    if not row.get("name", "").strip():
                        raise ValueError("Asset name is required")
                    if row.get("kind") not in KINDS:
                        raise ValueError("kind must be equity/crypto/benchmark")
                    record = dict(row) | provenance | {"symbol": sym}
                    for field in ("market_cap", "revenue", "pe", "shares_outstanding"):
                        record[field] = number(row.get(field), field, minimum=0, optional=True)
                    record["as_of"] = iso_date(row.get("as_of"), "as_of")
                    key = sym
                else:
                    record = validate_record(kind, row) | provenance
                    key = self.record_key(kind, record)
                if key in seen:
                    raise ValueError("Duplicate identity within file")
                seen.add(key)
                checked.append(record)
            except (ValueError, TypeError) as exc:
                raise ValueError(f"CSV row {i}: {exc}") from exc
        with self.db:
            if kind == "bars":
                known = {a["symbol"]: a for a in self.assets("research")}
                for sym, bar, asset_kind, category in checked:
                    if sym not in known:
                        asset = {
                            "symbol": sym,
                            "name": sym,
                            "kind": asset_kind,
                            "category": category,
                        } | provenance
                        self.save_asset("research", asset)
                        known[sym] = asset
                    elif known[sym]["kind"] != asset_kind:
                        raise ValueError(f"{sym}: asset kind conflicts with existing metadata")
                    self.save_bars("research", sym, [bar])
            elif kind == "assets":
                for record in checked:
                    self.save_asset("research", record)
            else:
                for record in checked:
                    self.save_record("research", kind, record)
        return len(checked)

    def setting(self, key, default=None):
        row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set_setting(self, key, value):
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO settings VALUES(?,?)", (key, json.dumps(value)))

    def watchlist(self, mode):
        self._mode(mode)
        return [
            r[0]
            for r in self.db.execute("SELECT symbol FROM watchlist WHERE mode=? ORDER BY symbol", (mode,))
        ]

    def toggle_watch(self, mode, symbol):
        self._mode(mode)
        if not any(a["symbol"] == symbol for a in self.assets(mode)):
            raise ValueError("Import the asset first")
        with self.db:
            if symbol in self.watchlist(mode):
                self.db.execute("DELETE FROM watchlist WHERE mode=? AND symbol=?", (mode, symbol))
            else:
                self.db.execute("INSERT INTO watchlist VALUES(?,?)", (mode, symbol))

    def paper_trades(self, mode):
        self._mode(mode)
        return [
            dict(r) for r in self.db.execute("SELECT * FROM paper WHERE mode=? ORDER BY date,id", (mode,))
        ]

    def paper_trade(self, mode, symbol, side, quantity, price, fee, trade_date):
        self._mode(mode)
        symbol = symbol_value(symbol)
        if symbol not in {a["symbol"] for a in self.assets(mode)}:
            raise ValueError("Import the asset before recording a paper trade")
        try:
            q, p, f = [Decimal(str(v)) for v in (quantity, price, fee)]
        except InvalidOperation as exc:
            raise ValueError("Invalid amount") from exc
        if (
            not all(v.is_finite() for v in (q, p, f))
            or q <= 0
            or p <= 0
            or f < 0
            or side not in {"buy", "sell"}
        ):
            raise ValueError("Use positive quantity/price, nonnegative fee and buy/sell")
        trade_date = iso_date(trade_date)
        current = self.paper_trades(mode)
        proposed = current + [
            {
                "symbol": symbol,
                "side": side,
                "quantity": str(q),
                "price": str(p),
                "fee": str(f),
                "date": trade_date,
                "id": 10**18,
            }
        ]
        balance = Decimal(0)
        for t in sorted((t for t in proposed if t["symbol"] == symbol), key=lambda t: (t["date"], t["id"])):
            balance += Decimal(t["quantity"]) * (1 if t["side"] == "buy" else -1)
            if balance < 0:
                raise ValueError("Paper portfolio is long-only; this creates a short position")
        with self.db:
            self.db.execute(
                "INSERT INTO paper(mode,symbol,side,quantity,price,fee,date) VALUES(?,?,?,?,?,?,?)",
                (mode, symbol, side, str(q), str(p), str(f), trade_date),
            )

    def paper_positions(self, mode):
        positions: dict[str, dict[str, Any]] = {}
        for t in self.paper_trades(mode):
            p = positions.setdefault(
                t["symbol"], {"symbol": t["symbol"], "quantity": Decimal(0), "net_cost": Decimal(0)}
            )
            qty, price, fee = (Decimal(t[k]) for k in ("quantity", "price", "fee"))
            sign = 1 if t["side"] == "buy" else -1
            p["quantity"] += qty * sign
            p["net_cost"] += qty * price * sign + fee
        result = []
        for p in positions.values():
            bars = self.bars(mode, p["symbol"])
            mark = Decimal(str(bars[-1]["close"])) if bars else None
            value: Decimal | None
            if p["quantity"] == 0:
                value = Decimal(0)
            else:
                last_trade = max(t["date"] for t in self.paper_trades(mode) if t["symbol"] == p["symbol"])
                if bars and bars[-1]["date"] < last_trade:
                    mark = None
                value = p["quantity"] * mark if mark is not None else None
            result.append(
                dict(
                    p,
                    mark=mark,
                    value=value,
                    pnl=value - p["net_cost"] if value is not None else None,
                    as_of=bars[-1]["date"] if bars else None,
                )
            )
        return result

    def archive_report(self, mode, title, payload):
        self._mode(mode)
        with self.db:
            cursor = self.db.execute(
                "INSERT INTO reports(mode,created_at,title,payload) VALUES(?,?,?,?)",
                (mode, utc_now(), title, json.dumps(payload, allow_nan=False)),
            )
        return cursor.lastrowid

    def reports(self, mode):
        self._mode(mode)
        return [
            dict(r) for r in self.db.execute("SELECT * FROM reports WHERE mode=? ORDER BY id DESC", (mode,))
        ]

    def backup(self, target):
        target = Path(target)
        if target.resolve() == self.path or (target.exists() and target.samefile(self.path)):
            raise ValueError("Choose a different backup path")
        target.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(target)) as destination:
            self.db.backup(destination)

    def close(self):
        self.db.close()
