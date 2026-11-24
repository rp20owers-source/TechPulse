"""Optional, read-only official HTTP providers; no scraping or trading endpoints.

Adapters return observations with provenance, never recommendations. They do not
persist data or credentials. The caller must enforce its own use, retention and
export permissions. CoinGecko observations are explicitly not redistributable.
Coverage is bounded and reported, rather than implying a complete market feed.
"""

from __future__ import annotations

import json
import math
import re
import threading
import time
from datetime import UTC, date, datetime
from email.utils import parsedate_to_datetime
from typing import Any, ClassVar, Self
from urllib.parse import quote

import httpx


class ProviderError(RuntimeError):
    """A safe diagnostic which does not include request headers or response data."""


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _number(value: Any, *, nonnegative: bool = False) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ProviderError("Provider returned an invalid numeric observation.")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ProviderError("Provider returned an invalid numeric observation.") from None
    if not math.isfinite(result) or (nonnegative and result < 0):
        raise ProviderError("Provider returned an invalid numeric observation.")
    return result


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if not isinstance(value, (str, int)) or isinstance(value, bool):
        raise ProviderError("Provider returned an invalid text observation.")
    return str(value)[:4000]


class _RateGate:
    """Serialize process-local requests per host, including separate adapters."""

    lock = threading.Lock()
    last: ClassVar[dict[str, float]] = {}

    @classmethod
    def wait(cls, host: str, minimum_interval: float) -> None:
        with cls.lock:
            remaining = cls.last.get(host, -math.inf) + minimum_interval - time.monotonic()
            if remaining > 0:
                time.sleep(remaining)
            cls.last[host] = time.monotonic()


class _HTTPProvider:
    name = "Provider"
    base_url = ""
    interval = 1.0
    max_bytes = 8 * 1024 * 1024

    def __init__(self, *, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(
            timeout=httpx.Timeout(20.0, connect=10.0),
            follow_redirects=False,
            headers={"User-Agent": "TechPulse/0.1 (local research desktop)"},
        )
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _request(
        self, method: str, path: str, *, headers: dict | None = None,
        params: dict | None = None, payload: dict | None = None,
    ) -> Any:
        """At most three attempts; obey short Retry-After, defer long cooldowns.

        Errors intentionally omit provider response bodies and exception text,
        which can contain API keys or untrusted HTML. Redirects are never followed.
        """
        url = self.base_url + path
        for attempt in range(3):
            _RateGate.wait(self.base_url, self.interval)
            try:
                with self._client.stream(
                    method, url, headers=headers, params=params, json=payload,
                    timeout=httpx.Timeout(20.0, connect=10.0),
                    follow_redirects=False,
                ) as response:
                    status = response.status_code
                    if status in (429, 502, 503, 504):
                        if attempt == 2:
                            raise ProviderError(f"{self.name} temporarily unavailable (HTTP {status}); retry later.")
                        delay = self._retry_delay(response.headers.get("Retry-After"), attempt)
                        if delay > 10:
                            raise ProviderError(f"{self.name} requests a cooldown; retry later.")
                        time.sleep(delay)
                        continue
                    if status in (401, 403):
                        raise ProviderError(f"{self.name} access denied; check credentials, terms and free-feed entitlement.")
                    if not 200 <= status < 300:
                        raise ProviderError(f"{self.name} request failed (HTTP {status}).")
                    content = bytearray()
                    for chunk in response.iter_bytes():
                        content.extend(chunk)
                        if len(content) > self.max_bytes:
                            raise ProviderError(f"{self.name} response exceeded the safe size limit; narrow the query.")
                    try:
                        return json.loads(content)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        raise ProviderError(f"{self.name} returned invalid JSON.") from None
            except httpx.RequestError:
                if attempt == 2:
                    raise ProviderError(f"{self.name} network request failed; cached data was not replaced.") from None
                time.sleep(float(2**attempt))
        raise ProviderError(f"{self.name} request exhausted its retry limit.")

    @staticmethod
    def _retry_delay(raw: str | None, attempt: int) -> float:
        if raw:
            try:
                value = float(raw)
                if math.isfinite(value):
                    return max(0.0, value)
            except ValueError:
                try:
                    target = parsedate_to_datetime(raw)
                    if target.tzinfo is not None:
                        return max(0.0, (target - datetime.now(UTC)).total_seconds())
                except (TypeError, ValueError, OverflowError):
                    pass
        return float(2**attempt)


class CoinGeckoProvider(_HTTPProvider):
    """Personal local Demo API snapshot, top 100 USD coins by market cap.

    `markets()` returns id, symbol, name, kind, category, price, market_cap,
    volume, day_pct, week_pct, month_pct, as_of, source, source_url, fetched_at,
    coverage, redistributable=False. Missing observations remain None.
    Categories are explicitly unclassified: symbols do not prove asset category.
    No histories, images, stablecoin inference or global dominance are invented.
    """

    name = "CoinGecko Demo"
    base_url = "https://api.coingecko.com"
    interval = 2.0  # conservative 30/min, under current 100/min Demo allowance

    def __init__(self, api_key: str, *, client: httpx.Client | None = None) -> None:
        if not isinstance(api_key, str) or not api_key.strip():
            raise ProviderError("A free CoinGecko Demo key is required for this optional source.")
        super().__init__(client=client)
        self._headers = {"x-cg-demo-api-key": api_key.strip()}

    def markets(self) -> list[dict]:
        rows = self._request(
            "GET", "/api/v3/coins/markets", headers=self._headers,
            params={"vs_currency": "usd", "order": "market_cap_desc", "per_page": 100,
                    "page": 1, "sparkline": "false", "price_change_percentage": "24h,7d,30d"},
        )
        if not isinstance(rows, list) or len(rows) > 100:
            raise ProviderError("CoinGecko returned an unexpected market snapshot schema.")
        fetched = _now()
        result = []
        seen = set()
        for row in rows:
            if not isinstance(row, dict) or not row.get("id"):
                raise ProviderError("CoinGecko returned an invalid coin record.")
            coin_id = _text(row["id"])
            if coin_id in seen:
                raise ProviderError("CoinGecko returned duplicate coin identifiers.")
            seen.add(coin_id)
            result.append({
                "id": coin_id, "symbol": _text(row.get("symbol")).upper(),
                "name": _text(row.get("name")), "kind": "crypto", "category": "Unclassified",
                "price": _number(row.get("current_price"), nonnegative=True),
                "market_cap": _number(row.get("market_cap"), nonnegative=True),
                "volume": _number(row.get("total_volume"), nonnegative=True),
                "day_pct": _number(row.get("price_change_percentage_24h")),
                "week_pct": _number(row.get("price_change_percentage_7d_in_currency")),
                "month_pct": _number(row.get("price_change_percentage_30d_in_currency")),
                "as_of": _text(row.get("last_updated")) or None,
                "source": "Data provided by CoinGecko",
                "source_url": "https://www.coingecko.com/en/coins/" + quote(coin_id, safe=""),
                "fetched_at": fetched,
                "coverage": "Top 100 USD coins by market cap only; snapshot, unclassified categories; not the entire crypto market.",
                "redistributable": False,
            })
        return result


class AlpacaProvider(_HTTPProvider):
    """Explicit IEX daily adjusted OHLCV; not consolidated US market volume.

    `daily_bars(symbols, start, end)` returns dict[symbol, list[bar]], ascending
    unique daily dates. Bar keys date/open/high/low/close/volume, source,
    source_url, fetched_at, coverage, adjustment='all', redistributable=False.
    Retrieval is all-or-error within max_pages; no silently partial history.
    Use date-only inclusive inputs and at most 100 explicitly selected symbols.
    """

    name = "Alpaca IEX"
    base_url = "https://data.alpaca.markets"
    interval = 0.6  # conservative 100/min, below current Basic 200/min

    def __init__(
        self, key: str, secret: str, *, client: httpx.Client | None = None,
        max_pages: int = 20,
    ) -> None:
        if not key or not secret:
            raise ProviderError("Optional Alpaca data access requires a key and secret.")
        if not isinstance(max_pages, int) or isinstance(max_pages, bool) or not 1 <= max_pages <= 100:
            raise ValueError("max_pages must be between 1 and 100.")
        super().__init__(client=client)
        self._headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}
        self._max_pages = max_pages

    def daily_bars(self, symbols: list[str], start: str, end: str) -> dict[str, list[dict]]:
        if not isinstance(symbols, (list, tuple)) or not 1 <= len(symbols) <= 100:
            raise ValueError("Select between 1 and 100 explicit symbols.")
        normalized = list(dict.fromkeys(s.strip().upper() for s in symbols if isinstance(s, str)))
        if not normalized or any(not re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,14}", s) for s in normalized):
            raise ValueError("Invalid stock symbol.")
        if len(normalized) != len(symbols):
            raise ValueError("Symbols must be valid and unique after normalization.")
        try:
            if not all(isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) for value in (start, end)):
                raise ValueError
            first, last = date.fromisoformat(start), date.fromisoformat(end)
        except (ValueError, TypeError):
            raise ValueError("Start and end must be ISO dates.") from None
        if first > last:
            raise ValueError("Start must be on or before end.")
        params = {"symbols": ",".join(normalized), "timeframe": "1Day", "start": start,
                  "end": end + "T23:59:59Z", "limit": 10000, "feed": "iex", "adjustment": "all", "sort": "asc"}
        result: dict[str, list[dict]] = {symbol: [] for symbol in normalized}
        fetched = _now()
        seen_tokens = set()
        for page in range(self._max_pages):
            data = self._request("GET", "/v2/stocks/bars", headers=self._headers, params=params)
            if not isinstance(data, dict) or not isinstance(data.get("bars"), dict):
                raise ProviderError("Alpaca returned an unexpected bars schema.")
            for symbol, rows in data["bars"].items():
                if symbol not in result or not isinstance(rows, list):
                    raise ProviderError("Alpaca returned unexpected symbols or bars.")
                for row in rows:
                    if not isinstance(row, dict):
                        raise ProviderError("Alpaca returned an invalid bar.")
                    timestamp = _text(row.get("t"))
                    try:
                        observation = datetime.fromisoformat(timestamp)
                        if observation.tzinfo is None:
                            raise ValueError
                        day = observation.date().isoformat()
                    except ValueError:
                        raise ProviderError("Alpaca returned an invalid bar timestamp.") from None
                    if not start <= day <= end:
                        raise ProviderError("Alpaca returned bars outside the requested date range.")
                    numbers = {full: _number(row.get(short), nonnegative=True) for full, short in
                               (("open", "o"), ("high", "h"), ("low", "l"), ("close", "c"), ("volume", "v"))}
                    o, h, low, c = (numbers[k] for k in ("open", "high", "low", "close"))
                    if o is None or h is None or low is None or c is None or numbers["volume"] is None:
                        raise ProviderError("Alpaca returned an incomplete OHLCV bar.")
                    if min(o, h, low, c) <= 0 or low > min(o, c) or h < max(o, c) or low > h:
                        raise ProviderError("Alpaca returned incoherent OHLC prices.")
                    result[symbol].append({"date": day, **numbers,
                        "source": "Alpaca IEX", "source_url": "https://alpaca.markets/data",
                        "fetched_at": fetched, "adjustment": "all", "redistributable": False,
                        "coverage": "IEX exchange feed only; adjusted prices; volume is not consolidated US volume."})
            token = data.get("next_page_token")
            if not token:
                break
            if not isinstance(token, str) or token in seen_tokens:
                raise ProviderError("Alpaca pagination did not advance; cached data was not replaced.")
            seen_tokens.add(token)
            params["page_token"] = token
        else:
            raise ProviderError("Alpaca history exceeded the page budget; narrow dates or symbols. No partial history returned.")
        for rows in result.values():
            rows.sort(key=lambda r: r["date"])
            if len({r["date"] for r in rows}) != len(rows):
                raise ProviderError("Alpaca returned duplicate daily bars; cached data was not replaced.")
        return result


class USAspendingProvider(_HTTPProvider):
    """Bounded award-level US federal contract search, no automatic ticker mapping.

    `search(keyword)` returns at most 100 recent-starting awards with award_id,
    company, ticker=None, government, country, agency, purpose, award_date,
    announcement_date=None, start_date, end_date, duration, ceiling=None,
    obligated, status, technology=None, expansion=None, implications, risks,
    source, source_url, fetched_at and coverage. Award Amount is cumulative
    obligations, not a contract ceiling, revenue or transaction increment.
    Never sum this result with transaction-level modifications of the same award.
    """

    name = "USAspending"
    base_url = "https://api.usaspending.gov"
    interval = 1.0

    def search(self, keyword: str) -> list[dict]:
        if not isinstance(keyword, str) or not 2 <= len(keyword.strip()) <= 200:
            raise ValueError("Search keyword must contain 2 to 200 characters.")
        payload = {
            "filters": {"keywords": [keyword.strip()], "award_type_codes": ["A", "B", "C", "D"]},
            "fields": ["Award ID", "Recipient Name", "Awarding Agency", "Award Amount", "Description",
                       "Start Date", "End Date", "Base Obligation Date", "generated_internal_id"],
            "page": 1, "limit": 100, "sort": "Start Date", "order": "desc", "subawards": False,
        }
        data = self._request("POST", "/api/v2/search/spending_by_award/", payload=payload)
        if not isinstance(data, dict) or not isinstance(data.get("results"), list) or len(data["results"]) > 100:
            raise ProviderError("USAspending returned an unexpected search schema.")
        fetched = _now()
        result = []
        seen = set()
        for row in data["results"]:
            if not isinstance(row, dict):
                raise ProviderError("USAspending returned an invalid award.")
            internal = _text(row.get("generated_internal_id"))
            award_id = _text(row.get("Award ID"))
            identity = internal or award_id
            if not identity:
                raise ProviderError("USAspending returned an award without an identifier.")
            if identity in seen:
                continue
            seen.add(identity)
            start, end = _text(row.get("Start Date")), _text(row.get("End Date"))
            result.append({
                "award_id": identity, "award_number": award_id,
                "company": _text(row.get("Recipient Name"), "Unknown recipient"), "ticker": None,
                "government": "United States", "country": "US",
                "agency": _text(row.get("Awarding Agency"), "Unavailable"),
                "purpose": _text(row.get("Description"), "Unavailable"),
                "award_date": _text(row.get("Base Obligation Date")) or None,
                "announcement_date": None, "start_date": start or None, "end_date": end or None,
                "duration": f"{start or 'unknown'} to {end or 'unknown'}", "ceiling": None,
                "obligated": _number(row.get("Award Amount")), "status": "award",
                "technology": None, "expansion": None,
                "implications": "Requires verified public-company mapping and company financial context before investment interpretation.",
                "risks": "Obligations may be revised or deobligated; not recognized revenue. Contract ceiling unavailable in this search.",
                "source": "USAspending.gov", "source_url": (
                    "https://www.usaspending.gov/award/" + quote(internal, safe="") if internal else
                    "https://www.usaspending.gov/search"),
                "fetched_at": fetched,
                "coverage": "At most 100 recent-starting US prime contract awards matching keyword; not global procurement or confirmed listed-company exposure.",
            })
        return result
