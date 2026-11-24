"""Deterministic FICTIONAL training fixtures. Never observations or backtest evidence."""

import math
from datetime import date, timedelta

from .store import utc_now


def seed_demo(store):
    if store.setting("demo_fixture_version") == 1:
        return
    dates: list[str] = []
    current = date(2025, 11, 21)
    while len(dates) < 180:
        if current.weekday() < 5:
            dates.append(current.isoformat())
        current -= timedelta(days=1)
    dates.reverse()
    definitions = [
        ("SYN-AI", "Synthetic Neural Systems", "equity", "Artificial intelligence", 68, 0.0027),
        ("SYN-CHIP", "Synthetic Silicon Works", "equity", "Semiconductors", 124, 0.0018),
        ("SYN-SEC", "Synthetic Cipher Labs", "equity", "Cybersecurity", 42, 0.0014),
        ("SYN-CLOUD", "Synthetic Cloud Grid", "equity", "Cloud computing", 82, -0.0008),
        ("SYN-Q", "Synthetic Quantum Research", "equity", "Quantum computing", 12, -0.0019),
        ("SYN-BOT", "Synthetic Robotics", "equity", "Robotics", 36, 0.0008),
        ("SYN-SPACE", "Synthetic Orbital Labs", "equity", "Space technology", 24, -0.0012),
        ("SYN-DC", "Synthetic Data Centers", "equity", "Data centers", 93, 0.0011),
        ("SYN-BTC", "Synthetic Bitcoin analogue", "crypto", "Layer 1", 62000, 0.0012),
        ("SYN-ETH", "Synthetic Ethereum analogue", "crypto", "Layer 1", 2400, 0.0008),
        ("SYN-USD", "Synthetic Dollar token", "crypto", "Stablecoin", 1, 0),
        ("SYN-MEME", "Synthetic Meme token", "crypto", "Memecoin", 0.12, -0.0022),
        ("SYN-INDEX", "Synthetic technology benchmark", "benchmark", "Benchmark", 100, 0.0008),
    ]
    provenance = {
        "currency": "USD",
        "source": "Fictional deterministic demo fixture v1",
        "source_url": "https://example.invalid/techpulse-demo",
        "fetched_at": utc_now(),
        "coverage": "SYNTHETIC · not market data",
        "as_of": dates[-1],
    }
    with store.db:
        for j, (symbol, name, kind, category, base, drift) in enumerate(definitions):
            bars = []
            previous = base
            for i, day in enumerate(dates):
                wave = (
                    0.0
                    if category == "Stablecoin"
                    else 0.025 * math.sin(i / 9 + j) + 0.01 * math.sin(i / 2.8)
                )
                close = base * math.exp(drift * i) * (1 + wave)
                spread = 0.0002 if category == "Stablecoin" else 0.012
                bar = {
                    "date": day,
                    "open": previous,
                    "high": max(previous, close) * (1 + spread),
                    "low": min(previous, close) * (1 - spread),
                    "close": round(close, 8),
                    "volume": round(
                        (800000 + j * 240000)
                        * (1 + 0.25 * math.sin(i / 7 + j))
                        * (2.3 if i == 179 and j == 0 else 1)
                    ),
                } | provenance
                bars.append(bar)
                previous = close
            store.save_asset(
                "demo",
                {
                    "symbol": symbol,
                    "name": name,
                    "kind": kind,
                    "category": category,
                    "market_cap": base * (j + 1) * 280000000,
                    "revenue": base * 80000000,
                    "pe": 17 + j * 4,
                }
                | provenance,
            )
            store.save_bars("demo", symbol, bars)
        store.save_record(
            "demo",
            "options",
            {
                "id": "fictional-trade-1",
                "symbol": "SYN-AI",
                "date": dates[-1],
                "record_type": "trade",
                "option_type": "call",
                "expiry": "2025-12-19",
                "strike": 110,
                "size": 240,
                "price": 2.4,
                "multiplier": 100,
                "open_interest": 2000,
                "volume": 2800,
                "historical_volume": 450,
            }
            | provenance,
        )
        store.save_record(
            "demo",
            "options",
            {
                "id": "fictional-aggregate-1",
                "symbol": "SYN-CHIP",
                "date": dates[-1],
                "record_type": "aggregate",
                "option_type": "put",
                "expiry": "2025-12-19",
                "strike": 160,
                "volume": 4200,
                "open_interest": 5000,
                "historical_volume": 700,
            }
            | provenance,
        )
        store.save_record(
            "demo",
            "contracts",
            {
                "id": "fictional-award-1",
                "company": "Synthetic Neural Systems",
                "ticker": "SYN-AI",
                "mapping_confirmed": True,
                "government": "Fictional Republic",
                "country": "DEMO",
                "agency": "Demonstration Science Agency",
                "purpose": "Fictional research computing infrastructure",
                "award_date": "2025-11-17",
                "announcement_date": "2025-11-18",
                "duration": "3 fictional years",
                "ceiling": 120000000,
                "obligated": 18000000,
                "technology": "AI research infrastructure",
                "expansion": "Unfunded options; uncertain",
                "implications": "Illustration only: delivery and margin determine economic value",
                "risks": "Synthetic example; ceiling is not revenue",
                "status": "funded",
                "value_basis": "Award-level fictional observation",
            }
            | provenance,
        )
    store.set_setting("demo_fixture_version", 1)
