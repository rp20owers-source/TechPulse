"""Deterministic, dependency-free research calculations; no predictive guarantees.

OHLC bars must be ascending, unique ISO calendar dates. Prices must be finite,
positive and internally coherent; volume is finite and nonnegative. Inputs are
never silently sorted, forward-filled or adjusted for corporate actions.
"""

from __future__ import annotations

from datetime import date
from math import isfinite, sqrt
from statistics import fmean
from typing import Any

DEFAULT_WEIGHTS = {
    "technical": 25.0,
    "fundamentals": 25.0,
    "catalysts": 20.0,
    "options": 15.0,
    "political": 5.0,
    "reliability": 10.0,
}


def _number(value, name, *, minimum=None, strictly_positive=False):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not isfinite(result):
        raise ValueError(f"{name} must be a finite number")
    if strictly_positive and result <= 0:
        raise ValueError(f"{name} must be positive")
    if minimum is not None and result < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return result


def validate_bars(bars):
    """Return numeric copies; reject bad chronology and incoherent OHLC."""
    result = []
    previous = None
    for bar in bars:
        stamp = str(bar.get("date", ""))
        try:
            parsed = date.fromisoformat(stamp)
        except ValueError as exc:
            raise ValueError("Bars require ISO calendar dates") from exc
        if parsed.isoformat() != stamp:
            raise ValueError("Bars require YYYY-MM-DD dates")
        if previous is not None and parsed <= previous:
            raise ValueError("Bars must have ascending unique dates")
        row = {"date": stamp}
        for field in ("open", "high", "low", "close"):
            row[field] = _number(bar.get(field), field, strictly_positive=True)
        row["volume"] = _number(bar.get("volume"), "volume", minimum=0)
        if row["high"] < max(row["open"], row["close"], row["low"]):
            raise ValueError("High must contain open, close and low")
        if row["low"] > min(row["open"], row["close"], row["high"]):
            raise ValueError("Low must contain open, close and high")
        result.append(row)
        previous = parsed
    return result


def _ema(values, period):
    """SMA-seeded EMA, first available at period-1; warm-up stays None."""
    result: list[float | None] = [None] * len(values)
    if len(values) < period:
        return result
    current = fmean(values[:period])
    result[period - 1] = current
    alpha = 2 / (period + 1)
    for i in range(period, len(values)):
        current = alpha * values[i] + (1 - alpha) * current
        result[i] = current
    return result


def indicators(bars):
    """Latest indicators: Wilder RSI/ATR, SMA-seeded MACD, population BB(20,2).

    ATR initial seed includes first bar's high-low (14 bars); RSI needs 14
    close-to-close changes (15 bars). Constant closes return neutral RSI=50.
    MACD signal needs 26+9-1=34 bars. Support/resistance are the previous 20
    bars' extrema excluding the latest bar, rather than fitted forecasts.
    """
    rows = validate_bars(bars)
    closes = [b["close"] for b in rows]
    n = len(rows)
    out: dict[str, Any] = dict.fromkeys(
        (
            "sma20",
            "sma50",
            "rsi14",
            "macd",
            "macd_signal",
            "atr14",
            "bb_upper",
            "bb_lower",
            "support",
            "resistance",
        )
    )
    out["warnings"] = []
    if n < 50:
        out["warnings"].append("Some indicators unavailable: fewer than 50 bars.")
    if not n:
        return out
    for period in (20, 50):
        if n >= period:
            out[f"sma{period}"] = fmean(closes[-period:])
    if n >= 20:
        mean = fmean(closes[-20:])
        deviation = sqrt(fmean([(v - mean) ** 2 for v in closes[-20:]]))
        out["bb_upper"], out["bb_lower"] = mean + 2 * deviation, mean - 2 * deviation
    if n >= 21:
        out["support"] = min(row["low"] for row in rows[-21:-1])
        out["resistance"] = max(row["high"] for row in rows[-21:-1])
    if n >= 15:
        changes = [closes[i] - closes[i - 1] for i in range(1, n)]
        gain = fmean([max(v, 0) for v in changes[:14]])
        loss = fmean([max(-v, 0) for v in changes[:14]])
        for change in changes[14:]:
            gain = (gain * 13 + max(change, 0)) / 14
            loss = (loss * 13 + max(-change, 0)) / 14
        out["rsi14"] = 50.0 if gain == loss == 0 else (100.0 if loss == 0 else 100 - 100 / (1 + gain / loss))
    true_ranges = []
    for i, row in enumerate(rows):
        prev = closes[i - 1] if i else row["close"]
        true_ranges.append(
            max(
                row["high"] - row["low"],
                abs(row["high"] - prev),
                abs(row["low"] - prev),
            )
        )
    if n >= 14:
        atr = fmean(true_ranges[:14])
        for value in true_ranges[14:]:
            atr = (atr * 13 + value) / 14
        out["atr14"] = atr
    fast, slow = _ema(closes, 12), _ema(closes, 26)
    macds = [fast[i] - slow[i] for i in range(25, n)]
    if macds:
        out["macd"] = macds[-1]
        out["macd_signal"] = _ema(macds, 9)[-1]
    return out


def summarize(bars):
    """Latest close returns for 1/5/21 observations; no calendar-day claims."""
    rows = validate_bars(bars)
    n = len(rows)
    result = {
        "price": rows[-1]["close"] if n else None,
        "data_points": n,
        "as_of": rows[-1]["date"] if n else None,
        "day_pct": None,
        "week_pct": None,
        "month_pct": None,
        "relative_volume": None,
    }
    for key, lag in (("day_pct", 1), ("week_pct", 5), ("month_pct", 21)):
        if n > lag:
            result[key] = 100 * (rows[-1]["close"] / rows[-1 - lag]["close"] - 1)
    if n >= 21:
        baseline = fmean([b["volume"] for b in rows[-21:-1]])
        result["relative_volume"] = rows[-1]["volume"] / baseline if baseline > 0 else None
    return result


def detect_patterns(bars):
    """Exploratory geometric labels, never a validated forecast.

    Uses the latest 60 bars and two-sided radius-2 pivots that are confirmed
    only after two following bars. Pattern thresholds are predeclared in
    TECHNICAL_ANALYSIS.md and intentionally conservative. Labels may overlap.
    """
    rows = validate_bars(bars)[-60:]
    if len(rows) < 25:
        return []
    closes = [r["close"] for r in rows]
    price = closes[-1]
    results = []

    def emit(name, direction, evidence, confirmed=False):
        results.append(
            {
                "name": name,
                "direction": direction,
                "status": "Confirmed geometry" if confirmed else "Developing geometry",
                "evidence": evidence,
                "confidence": None,
                "sample_size": 0,
                "validated": False,
            }
        )

    highs, lows = [], []
    for i in range(2, len(rows) - 2):
        window = closes[i - 2 : i + 3]
        if closes[i] == max(window) and window.count(closes[i]) == 1:
            highs.append((i, closes[i]))
        if closes[i] == min(window) and window.count(closes[i]) == 1:
            lows.append((i, closes[i]))
    for pivots, inverted in ((highs, False), (lows, True)):
        if len(pivots) >= 2:
            (a, av), (b, bv) = pivots[-2:]
            if 5 <= b - a <= 40 and abs(av - bv) / ((av + bv) / 2) <= 0.025:
                between = closes[a + 1 : b]
                neckline = max(between) if inverted else min(between)
                depth = (neckline - max(av, bv)) if inverted else (min(av, bv) - neckline)
                if depth / neckline >= 0.03:
                    confirmed = price > neckline if inverted else price < neckline
                    emit(
                        "Double bottom" if inverted else "Double top",
                        "Bullish conditional" if inverted else "Bearish conditional",
                        f"Two confirmed pivots {b - a} bars apart, within 2.5%; "
                        f"neckline {neckline:.4f}; latest close {price:.4f}. "
                        "Geometry only; volume and predictive reliability unvalidated.",
                        confirmed,
                    )
        if len(pivots) >= 3:
            (a, av), (b, bv), (c, cv) = pivots[-3:]
            shoulder_match = abs(av - cv) / ((av + cv) / 2) <= 0.03
            head_depth = min(av, cv) - bv if inverted else bv - max(av, cv)
            if 4 <= b - a <= 20 and 4 <= c - b <= 20 and shoulder_match and head_depth / bv >= 0.03:
                left = max(closes[a + 1 : b]) if inverted else min(closes[a + 1 : b])
                right = max(closes[b + 1 : c]) if inverted else min(closes[b + 1 : c])
                neckline = (left + right) / 2
                confirmed = price > max(left, right) if inverted else price < min(left, right)
                emit(
                    "Inverse head and shoulders" if inverted else "Head and shoulders",
                    "Bullish conditional" if inverted else "Bearish conditional",
                    f"Three confirmed pivots; shoulders within 3%, head at least 3% beyond; "
                    f"approximate neckline {neckline:.4f}. Geometry only.",
                    confirmed,
                )
    # Trendline labels need three distinct confirmed pivots on each boundary.
    if len(highs) >= 3 and len(lows) >= 3:
        hs, ls = highs[-3:], lows[-3:]
        span = min(hs[-1][0], ls[-1][0]) - max(hs[0][0], ls[0][0])
        if span >= 8:

            def fit(points):
                xs, ys = [p[0] for p in points], [p[1] for p in points]
                xmean, ymean = fmean(xs), fmean(ys)
                slope = sum((x - xmean) * (y - ymean) for x, y in points) / sum((x - xmean) ** 2 for x in xs)
                error = max(abs(y - (ymean + slope * (x - xmean))) for x, y in points) / price
                return slope / price, error

            hslope, herr = fit(hs)
            lslope, lerr = fit(ls)
            if max(herr, lerr) <= 0.015:
                if abs(hslope) <= 0.0005 and lslope >= 0.001:
                    emit(
                        "Ascending triangle",
                        "Bullish conditional",
                        "Three high and low pivots; flat highs, rising lows; fit error <=1.5%.",
                    )
                elif abs(lslope) <= 0.0005 and hslope <= -0.001:
                    emit(
                        "Descending triangle",
                        "Bearish conditional",
                        "Three high and low pivots; falling highs, flat lows; fit error <=1.5%.",
                    )
                elif hslope < -0.0005 and lslope < -0.0005 and hslope < lslope:
                    emit(
                        "Falling wedge",
                        "Bullish conditional",
                        "Both pivot boundaries declining; upper boundary declines faster; fit error <=1.5%.",
                    )
                elif hslope > 0.0005 and lslope > 0.0005 and hslope < lslope:
                    emit(
                        "Rising wedge",
                        "Bearish conditional",
                        "Both pivot boundaries rising; lower boundary rises faster; fit error <=1.5%.",
                    )
                elif hslope < -0.0005 and lslope > 0.0005:
                    emit(
                        "Symmetric triangle",
                        "Neutral",
                        "Falling highs and rising lows; fit error <=1.5%; direction unknown.",
                    )
    prior = rows[-21:-1]
    resistance, support = max(r["high"] for r in prior), min(r["low"] for r in prior)
    average_volume = fmean([r["volume"] for r in prior])
    volume_note = (
        "Volume >=1.5x prior20."
        if average_volume > 0 and rows[-1]["volume"] >= 1.5 * average_volume
        else "No 1.5x volume confirmation."
    )
    if price > resistance:
        emit(
            "20-bar breakout",
            "Bullish conditional",
            f"Close exceeds previous20 high {resistance:.4f}. {volume_note}",
            True,
        )
    if price < support:
        emit(
            "20-bar breakdown",
            "Bearish conditional",
            f"Close below previous20 low {support:.4f}. {volume_note}",
            True,
        )
    if (resistance - support) / price <= 0.06:
        emit(
            "Consolidation",
            "Neutral",
            "Previous20 high-low range <=6% of latest close.",
        )
    if abs(rows[-1]["open"] / rows[-2]["close"] - 1) >= 0.02:
        emit(
            "Opening gap",
            "Neutral",
            "Latest open differs from previous close by >=2%; corporate-action adjustment unverified.",
        )
    # Flags/pennants/cup-and-handle/candlesticks intentionally not inferred from
    # weak approximate shapes; listed as unsupported in the methodology.
    return results


def score_candidate(components, weights=None):
    """Weighted evidence points, not probability; missing evidence earns zero.

    Candidate eligibility is an explicit conservative product policy: >=70%
    weighted evidence coverage, >=60/100 reliability, at least three observed
    non-reliability components, and at least one fundamentals/catalyst input.
    The score is withheld as a candidate unless >=60 points. This policy is
    unvalidated; values supplied by callers must reflect sourced observations.
    """
    selected = DEFAULT_WEIGHTS.copy() if weights is None else dict(weights)
    if set(selected) != set(DEFAULT_WEIGHTS):
        raise ValueError("Weights must contain exactly the six documented components")
    selected = {k: _number(v, k, minimum=0) for k, v in selected.items()}
    total = sum(selected.values())
    if total <= 0:
        raise ValueError("At least one weight must be positive")
    normalized = {k: v / total * 100 for k, v in selected.items()}
    values: dict[str, Any] = {}
    for key in selected:
        value = components.get(key)
        values[key] = None if value is None else _number(value, key, minimum=0)
        if values[key] is not None and values[key] > 100:
            raise ValueError("Component values must be within 0..100")
    score = sum(normalized[k] * v / 100 for k, v in values.items() if v is not None)
    coverage = sum(normalized[k] for k, v in values.items() if v is not None) / 100
    observed = [k for k, v in values.items() if v is not None and normalized[k] > 0]
    reasons = []
    if coverage < 0.70:
        reasons.append("Weighted evidence coverage is below 70%.")
    if values["reliability"] is None or values["reliability"] < 60:
        reasons.append("Data reliability is absent or below 60/100.")
    if len([k for k in observed if k != "reliability"]) < 3:
        reasons.append("Fewer than three non-reliability evidence components.")
    if not any(k in observed for k in ("fundamentals", "catalysts")):
        reasons.append("Fundamentals or a verified corporate catalyst is required.")
    if score < 60:
        reasons.append("Evidence score is below the 60-point research threshold.")
    return {
        "score": score,
        "coverage": coverage,
        "decision": "Abstain" if reasons else "Research candidate",
        "components": values,
        "weights": normalized,
        "missing": [k for k, v in values.items() if v is None],
        "reasons": reasons,
        "confidence": None,
        "limitations": "Unvalidated heuristic priorities; not a probability, personalized advice or trading instruction.",
    }


def option_metrics(record):
    """Individual trade premium only when actual size/price/multiplier supplied.

    `kind` (or `record_type`) must be 'trade' for estimated_trade_premium.
    Aggregate records may provide aggregate_premium only if independently
    observed; volume*last_price is never used. IV values are decimal fractions.
    """
    kind = record.get("kind", record.get("record_type", "aggregate"))
    if kind not in ("trade", "aggregate"):
        raise ValueError("Option record kind must be trade or aggregate")
    result = {
        "kind": kind,
        "estimated_trade_premium": None,
        "aggregate_premium": None,
        "volume_ratio": None,
        "volume_open_interest_ratio": None,
        "iv_change_points": None,
        "intent": "Unknown: hedging, spreads, closing positions or directional exposure are possible.",
    }
    fields = (
        "size",
        "price",
        "multiplier",
        "volume",
        "historical_average_volume",
        "open_interest",
        "aggregate_premium",
        "iv",
        "previous_iv",
    )
    numeric = {
        k: _number(record[k], k, minimum=0)
        for k in fields
        if record.get(k) is not None and record.get(k) != ""
    }
    if kind == "trade" and all(k in numeric for k in ("size", "price", "multiplier")):
        if numeric["size"] <= 0 or numeric["multiplier"] <= 0:
            raise ValueError("Trade size and multiplier must be positive")
        result["estimated_trade_premium"] = numeric["size"] * numeric["price"] * numeric["multiplier"]
    if kind == "aggregate":
        result["aggregate_premium"] = numeric.get("aggregate_premium")
    if "volume" in numeric:
        if numeric.get("historical_average_volume", 0) > 0:
            result["volume_ratio"] = numeric["volume"] / numeric["historical_average_volume"]
        if numeric.get("open_interest", 0) > 0:
            result["volume_open_interest_ratio"] = numeric["volume"] / numeric["open_interest"]
    if "iv" in numeric and "previous_iv" in numeric:
        result["iv_change_points"] = 100 * (numeric["iv"] - numeric["previous_iv"])
    for key, value in result.items():
        if isinstance(value, float) and not isfinite(value):
            raise ValueError(f"{key} overflowed; check input scale")
    return result


def contract_metrics(record, revenue=None, market_cap=None):
    """Compare award-level cumulative obligations, not ceiling, against company.

    Negative obligations are allowed (deobligation) and remain negative. A
    ceiling is optional/nonnegative. Caller must supply a deduplicated award
    snapshot; this function does not sum modifications or infer contractors.
    """
    obligations = record.get("obligated", record.get("obligations"))
    ceiling = record.get("ceiling")
    obligations = None if obligations in (None, "") else _number(obligations, "obligations")
    ceiling = None if ceiling in (None, "") else _number(ceiling, "ceiling", minimum=0)
    result: dict[str, Any] = {
        "obligated": obligations,
        "ceiling": ceiling,
        "obligated_to_revenue_pct": None,
        "obligated_to_market_cap_pct": None,
        "funded_fraction": None,
        "warnings": [
            "Contract ceiling is not guaranteed revenue. Obligations are not recognized company revenue."
        ],
    }
    for label, denominator in (("revenue", revenue), ("market_cap", market_cap)):
        if denominator not in (None, ""):
            denominator = _number(denominator, label, strictly_positive=True)
            if obligations is not None:
                result[f"obligated_to_{label}_pct"] = obligations / denominator * 100
    if obligations is not None and ceiling is not None and ceiling > 0:
        result["funded_fraction"] = obligations / ceiling
        if obligations > ceiling:
            result["warnings"].append(
                "Obligations exceed supplied ceiling; verify scope/currency/as-of date."
            )
    if obligations is not None and obligations < 0:
        result["warnings"].append(
            "Negative obligation indicates deobligation; verify cumulative award versus modification scope."
        )
    return result


def walk_forward(bars, horizon=5, cost_bps=10):
    """Diagnostic expanding-window SMA20>SMA50 rule, not pattern validation.

    First signal uses first50 closes; entry is next bar's open. Exit is the
    close of the horizon-th held bar. Signals use prior observations only;
    trades do not overlap. `cost_bps` is each side's proportional cost, with
    return = exit*(1-cost)/(entry*(1+cost))-1. Benchmark is a matched holding
    period buy-and-hold return for each evaluated block (including no-signal
    blocks), net of the same costs. No fitting, tuning or confidence estimate.
    """
    rows = validate_bars(bars)
    if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon < 1:
        raise ValueError("horizon must be a positive integer")
    cost = _number(cost_bps, "cost_bps", minimum=0) / 10000
    if cost >= 1:
        raise ValueError("cost_bps must be below 10000")
    trades, blocks = [], []
    for signal_index in range(49, len(rows) - horizon, horizon):
        history = rows[: signal_index + 1]
        close = [r["close"] for r in history]
        signal = fmean(close[-20:]) > fmean(close[-50:])
        entry, exit_row = rows[signal_index + 1], rows[signal_index + horizon]
        value = exit_row["close"] * (1 - cost) / (entry["open"] * (1 + cost)) - 1
        blocks.append(value)
        if signal:
            trades.append(
                {
                    "signal_date": rows[signal_index]["date"],
                    "entry_date": entry["date"],
                    "exit_date": exit_row["date"],
                    "entry_price": entry["open"],
                    "exit_price": exit_row["close"],
                    "return_pct": value * 100,
                }
            )
    returns = [t["return_pct"] for t in trades]
    return {
        "sample_size": len(trades),
        "evaluation_blocks": len(blocks),
        "win_rate": sum(r > 0 for r in returns) / len(returns) if returns else None,
        "mean_return_pct": fmean(returns) if returns else None,
        "benchmark_return_pct": fmean(blocks) * 100 if blocks else None,
        "trades": trades,
        "confidence": None,
        "status": "Diagnostic only; forecasts withheld",
        "limitations": [
            "Fixed SMA20/50 rule only; does not validate geometric pattern labels.",
            "Single supplied asset; point-in-time universe and survivorship controls unavailable.",
            "Costs are assumptions; excludes spreads beyond cost, slippage, taxes, dividends and corporate actions.",
            "Block means are not portfolio cumulative returns; benchmark is matched-block buy and hold.",
            "No data-snooping correction, bootstrap calibration or independent held-out validation.",
        ],
    }
