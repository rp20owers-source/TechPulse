# Architecture and initial decisions

Native Windows-first Python / PySide6 application, source layout, SQLite local-first persistence. No LLM, brokerage connection or paid service is essential. Runtime financial data belongs under the platform local app-data directory; the repository contains only code, documentation and explicitly fictional fixtures.

## Ownership and module interfaces

- Lead: `app.py`, `store.py`, `demo.py`, `reports.py`, `__main__.py`, packaging, CI, integration tests and top-level docs.
- Analytics agent: `analytics.py`, `tests/test_analytics.py`, `docs/research/TECHNICAL_ANALYSIS.md`. Plain Python list/dict interfaces, no pandas needed. Functions: `indicators(bars) -> dict`, `summarize(bars) -> dict`, `detect_patterns(bars) -> list[dict]`, `score_candidate(components, weights=None) -> dict`, `option_metrics(record) -> dict`, `contract_metrics(record, revenue=None, market_cap=None) -> dict`, `walk_forward(bars, horizon=5, cost_bps=10) -> dict`. Bars: ascending unique ISO date, open/high/low/close/volume floats. Summary keys day_pct, week_pct, month_pct, relative_volume, price. Indicators keys sma20/sma50/rsi14/macd/macd_signal/atr14/bb_upper/bb_lower, missing values None. Components keys technical, fundamentals, catalysts, options, political, reliability; missing None. All unavailable/unvalidated predictive output must abstain. Tests establish formulas and chronology, not empirical prediction reliability.
- Provider agent: `providers.py`, `tests/test_providers.py`, `docs/research/DATA_PROVIDERS.md`. HTTPX, no GUI or database coupling. `ProviderError`; `CoinGeckoProvider(api_key).markets() -> list[dict]`; `AlpacaProvider(key, secret).daily_bars(symbols, start, end) -> dict[str,list[dict]]`; `USAspendingProvider().search(keyword) -> list[dict]`. Bounded timeout/retries, conservative throttling, pagination if necessary, clear incomplete coverage. No credential persistence/logging. Optional sources only, offline app must work. List returned normalized fields in module docs; no proprietary source fixtures in repository.
- Research agent: `docs/research/COMPETITIVE_ANALYSIS.md` and academic/feasibility overview if useful. Read-only research; cite official sources with access date, distinguish verified restrictions from assumptions. Later independent review.

## Data and financial boundaries

Data modes are separate SQLite namespaces: demo, research. Every instrument has source, source_url, fetched_at and optional as_of. Imported bars are validated as finite, positive coherent OHLC, nonnegative volume, unique chronological dates. Never silently substitute demo on live-provider failure. Local CSV imports require user-provided attribution and authorization. Political records are manually normalized from lawful research; no automated collection/public bundling. Confirmed contractor mapping is manual.

Research scores use the proposed weights (25/25/20/15/5/10), report weighted coverage and missing evidence, and must abstain when quality/coverage is insufficient. No forecast confidence until validated on appropriate out-of-sample data. Pattern detections are objective exploratory labels only.

Reports serialize actual local observations with source metadata, limitations and clear mode labels. Raw restricted provider data must not be bundled in releases. Reports and backups are local user-controlled outputs. Scheduler runs only while app is open and catches up on next launch; no hidden OS service.

## Dependency/license decision

MIT project code; PySide6 LGPLv3 obligations documented separately. Dynamically linked Qt wheels, accessible third-party license files and source/relinking guidance required for binary releases. Release is a preview until licensing, security and clean-machine acceptance gates pass. Prefer standard library over extra dependencies; add NumPy only for PyQtGraph.
