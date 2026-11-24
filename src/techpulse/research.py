"""Explainable observations assembled from the user's local evidence."""

import math
from datetime import date

from .analytics import detect_patterns, indicators, score_candidate, summarize


def asset_rows(store, mode, kind=None):
    result = []
    for asset in store.assets(mode):
        if kind and asset.get("kind") != kind:
            continue
        bars = store.bars(mode, asset["symbol"])
        summary = summarize(bars) if bars else {}
        row = dict(asset) | summary
        row["bar_as_of"] = bars[-1]["date"] if bars else None
        row["price_source"] = bars[-1].get("source") if bars else None
        row["price_source_url"] = bars[-1].get("source_url") if bars else None
        row["price_fetched_at"] = bars[-1].get("fetched_at") if bars else None
        row["price_sources"] = sorted({(b.get("source", "Unknown"), b.get("source_url", "")) for b in bars})
        row["data_points"] = len(bars)
        row["liquidity_usd"] = bars[-1]["close"] * bars[-1]["volume"] if bars else None
        shares = asset.get("shares_outstanding")
        row["cap_change_estimate"] = (
            (bars[-1]["close"] - bars[-2]["close"]) * shares if shares and len(bars) > 1 else None
        )
        result.append(row)
    return result


def opportunity(store, mode, asset):
    bars = store.bars(mode, asset["symbol"])
    metrics = summarize(bars) if bars else {}
    ind = indicators(bars) if bars else {}
    components = dict.fromkeys(
        ("technical", "fundamentals", "catalysts", "options", "political", "reliability")
    )
    support: list[str] = []
    contradiction: list[str] = []
    if len(bars) >= 50:
        above = bars[-1]["close"] > ind["sma50"]
        momentum = (metrics.get("month_pct") or 0) > 0
        components["technical"] = 50 * above + 50 * momentum
        (support if above else contradiction).append(
            "Close above 50-session average" if above else "Close below 50-session average"
        )
        (support if momentum else contradiction).append(
            "Positive 21-session momentum" if momentum else "Nonpositive 21-session momentum"
        )
        stale_days = (date.today() - date.fromisoformat(bars[-1]["date"])).days
        components["reliability"] = 80 if stale_days <= 4 else 20
        if stale_days > 4:
            contradiction.append(f"Price observations are {stale_days} calendar days old")
    if asset.get("pe") is not None:
        support.append(
            f"Reported P/E {asset['pe']:.1f}; sector/growth/cash-flow context needed; valuation score withheld"
        )
    # No options direction, political imitation or ceiling-size bonus is fabricated.
    contracts = [c for c in store.records(mode, "contracts") if c.get("ticker") == asset["symbol"]]
    if contracts:
        support.append(f"{len(contracts)} mapped contract observation(s); economic impact not established")
    weights = store.setting("score_weights", None)
    scored = score_candidate(components, weights)
    return {
        "symbol": asset["symbol"],
        "name": asset.get("name", asset["symbol"]),
        "source": asset.get("source"),
        "source_url": asset.get("source_url"),
        **scored,
        "supporting": support,
        "contradictory": contradiction or ["Missing independent evidence remains a material limitation"],
        "entry_condition": "Only investigate after fresh prices and independently verified fundamentals/catalysts are available",
        "horizon": "Unspecified; no validated investment horizon",
        "invalidation": "Stale or invalid data, deteriorating fundamentals, or failed thesis assumptions",
        "scenarios": {
            "bullish": "Trend continues only if price holds above measured support and business evidence confirms",
            "bearish": "Breakdown below support or weaker business evidence undermines the thesis",
            "neutral": "Insufficient evidence: observe without opening a position",
        },
        "patterns": detect_patterns(bars) if len(bars) >= 50 else [],
    }


def correlations(store, mode, left, right):
    a = {r["date"]: r["close"] for r in store.bars(mode, left)}
    b = {r["date"]: r["close"] for r in store.bars(mode, right)}

    # Calculate each asset's own one-observation return first, then require identical interval endpoints.
    def returns(values):
        dates = sorted(values)
        return {
            (dates[i - 1], dates[i]): values[dates[i]] / values[dates[i - 1]] - 1
            for i in range(1, len(dates))
        }

    ra, rb = returns(a), returns(b)
    intervals = sorted(ra.keys() & rb.keys())
    if len(intervals) < 30:
        return None, len(intervals)
    x, y = [ra[d] for d in intervals], [rb[d] for d in intervals]
    mx, my = sum(x) / len(x), sum(y) / len(y)
    denom = math.sqrt(sum((v - mx) ** 2 for v in x) * sum((v - my) ** 2 for v in y))
    return (sum((u - mx) * (v - my) for u, v in zip(x, y)) / denom if denom else None), len(intervals)


def disclosure_performance(store, mode, record):
    """First available close on/after publication; no before-publication trade simulation."""
    if not record.get("symbol"):
        return None, None
    bars = [b for b in store.bars(mode, record["symbol"]) if b["date"] >= record["publication_date"]]
    # Publication time unknown: conservatively use first trading date strictly AFTER publication.
    bars = [b for b in bars if b["date"] > record["publication_date"]]
    if len(bars) < 2:
        return None, None
    return (bars[-1]["close"] / bars[0]["close"] - 1) * 100, bars[0]["date"]
