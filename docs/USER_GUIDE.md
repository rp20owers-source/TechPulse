# Using TechPulse 0.1

## Start

On Windows, double-click **Start-TechPulse.cmd** from the source folder. It needs Python3.12–3.14 installed and internet on first setup to download the free locked packages from PyPI. The launcher creates a dedicated runtime in `%LOCALAPPDATA%\TechPulse\runtime-0.1`. It never asks for a brokerage connection. Alternatively use the README uv commands.

The application starts in **Fictional demo**. All `SYN-` assets and awards are deterministic training fixtures dated November2025. They do not describe actual companies, cryptocurrency prices, awards or political trades. A separate **Personal research** workspace starts empty. Switching workspaces never imports demo records into personal research.

## Bring your own authorized data

Use **Import CSV**, select a record type, supply the original provider/document name and public HTTPS URL, and acknowledge permission to use/retain/export that data. Every row requires `currency=USD`. SQLite is unencrypted: do not import data requiring encrypted storage. A checkbox cannot override provider terms or statutory restrictions. See IMPORT_FORMATS.md and the fictional templates under examples/.

Daily OHLCV imports create an asset if needed. Import an assets file to add names, category, fundamentals and capitalization. Invalid files fail atomically; duplicate identities in one file fail. Across imports, dates/record identities update rather than blindly adding values. Corporate-action adjustment and observation cadence are the user's responsibility. The app does not mix dates or fill missing prices silently.

## Research workflow

1. **Technology Movers**: search, sort, filter market capitalization and latest dollar volume. Double-click an asset for the chart. One/five/21-period returns use observations, so daily crypto and US trading sessions represent different calendar durations.
2. **Chart Analysis**: inspect price/SMA20, indicator values and exploratory geometry. Drag to pan, wheel to zoom. Support/resistance exclude the latest observation. Forecasts abstain; the SMA diagnostic is a chronological rule evaluation, not pattern validation. Its historical benchmark is not a matched portfolio benchmark.
3. **Options**: double-click a record for original evidence; only an individual trade has estimated size×price×multiplier premium. Volume anomalies and IV changes do not establish intent.
4. **Contracts**: double-click for complete normalized evidence. Obligations can be revised or deobligated. Ceiling, funding and future revenue are different. Supply verified ticker mapping and complete issuer identity.
5. **Political trackers**: automated collection disabled. No actual records bundled. Lawful imports preserve owner and disclosed value ranges. Performance begins at first available close strictly after publication, since intraday publication time is unknown; it does not simulate execution or copying.
6. **Investment Opportunities**: inspect transparent earned points, evidence coverage, missing/supporting/contradictory considerations and conditional scenarios. The current app only derives technical/reliability components and intentionally abstains without independent fundamental/catalyst evidence. The scoring library supports all six components, but complete multi-source thesis automation is deferred.

## Watchlist, paper ledger and reports

Watchlists are independent per workspace. Alerts are a user-invoked threshold evaluation of the latest stored watched observations, with no continuous feed, notifications or hidden background service.

Paper trades are manual long-only transactions with explicit quantity, fill price, fee and date. Chronological sells cannot exceed holdings. Total P/L includes realized and unrealized net cash effects, not an investment return percentage. Marks predating the latest trade are withheld. No portfolio bankroll, trade execution, benchmark attribution or automatic recommendation tracking exists yet.

Weekly Reports can generate all14 sections or one section. Previewing also archives an immutable local snapshot. Export PDF, HTML, CSV or JSON only as your data permissions allow. Presentation limits are stated in reports; machine-readable exports preserve the snapshot. No earnings calendar is connected, so that section explicitly says unavailable.

The optional Monday08:00 setting runs **only while TechPulse is open**, using the OS local timezone. A restart catches up the latest due briefing from current cached data; it does not invent old historical reports or refresh feeds. Turn the checkbox off per workspace to stop it.

## Provider previews

Data Sources & Health includes manual official-provider queries. Provider results are session-only, move to Personal research, and are never retained/exported by the app. Switching away from Personal research discards an in-flight result. CoinGecko Demo requires a free personal key and has usage/retention restrictions; Alpaca IEX requires optional provider credentials and covers only a limited feed. USAspending needs no key, returns a bounded US prime-award search, and does not infer ticker mappings.

Set `COINGECKO_DEMO_API_KEY`, or `ALPACA_API_KEY` plus `ALPACA_SECRET_KEY`, in your environment before launch. Never paste credentials into a CSV or source URL. Calls may take up to roughly65seconds under the cooperative budget; close is deferred while a request finishes. This is an operation guard, not a total wall-clock guarantee.

## Storage, backup and recovery

Default database: `%LOCALAPPDATA%\TechPulse\techpulse.db`. Override with `TECHPULSE_DATA_DIR` or `python -m techpulse --data-dir PATH`. Backups in Settings use SQLite's consistent backup API and include personal imports, paper trades and reports; protect them as private data. Provider previews and environment credentials are excluded.

To restore, close the application, preserve a copy of the current data directory, verify a selected backup using SQLite `PRAGMA integrity_check`, and copy that backup to `techpulse.db` in a new data directory. Launch with `--data-dir` pointing there. Do not overwrite a running database or copy stale WAL/SHM files over a restored backup. Automatic migration/restore GUI is deferred.

If a provider fails, the app shows an error and does not replace it with synthetic data. If imports fail, fix the reported row and retry. For startup database corruption, preserve the files and launch with a fresh data directory rather than deleting the damaged database.
