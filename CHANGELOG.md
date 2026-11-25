# Changelog

## 0.1.0 — 2026-11-24 (research preview)

- Native16-workspace desktop terminal with dark/light themes, sorting/search/filtering and interactive price charts.
- Isolated fictional demonstration data and personal research SQLite; atomic authorized USD CSV imports with provenance.
- Deterministic indicators, exploratory patterns, chronological SMA diagnostic and evidence-aware abstention.
- Options trade/aggregate distinction, award obligation/ceiling separation, individual disclosure workspaces with collection disabled.
- Local watchlist/threshold evaluator, decimal long-only paper ledger, weekly snapshots/archive and four export formats.
- Optional session-only CoinGecko Demo, Alpaca IEX and USAspending previews; no mandatory accounts or paid APIs.
- Official research, independent financial/security/product reviews, regression tests and continued-development handoff.

This does not establish comprehensive market coverage, validated predictions, recommendation profitability or production release readiness. See docs/REQUIREMENTS.md.

## Unreleased

- Startup recovery screen preserves the failed data folder and can open another checked workspace, recover a backup into a unique folder, or start fresh separately. Optional next-launch folder preference honors explicit overrides; existing empty/corrupt files are checked before initialization. Store paths are absolute and failed initialization closes its connection.
- Backup creation rejects hard-link aliases of the active database before opening a destination connection.

- SEC annual US-GAAP fundamentals preview and offline companyfacts JSON normalization, source/filing provenance, conservative cutoff and aligned ratios. Session-only; no score changes or new dependencies.

- Exact SEC ticker-to-CIK lookup for annual fundamentals, with ambiguous/missing matches rejected and current-directory provenance retained.

- Per-user Windows desktop installer with a permanent application/runtime folder, custom icon, Desktop/Start menu shortcuts, and console-free launch.

- VS Code Run/Debug, test/lint/type tasks and isolated development data. SEC free cash flow now remains available with matching cash-flow facts when revenue is missing/zero; its reporting period is shown and margin remains unavailable.

- Session-only SEC contact in Settings, with immediate use and no persistence. Independent SEC review fixes reject overlapping revenue periods and correctly report a decline to zero revenue.

- Settings backup inspection/restore with staged validation, canonical schema checks, automatic pre-restore safety copy, rollback/error handling and explicit concurrency limits. Startup refuses unknown/future database structures before modifying them.
- Lazy Qt table models replace eager per-cell widgets; full-result numeric sorting preserved. Report Archive now opens numeric-ID records independently of display formatting.
