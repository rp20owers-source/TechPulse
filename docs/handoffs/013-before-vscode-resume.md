# TechPulse — current project handoff

Updated2026-11-24 by Codex (lead engineer), task H01: reconcile documentation with verified source, installation and CI. This is a documentation-only pass. The user requested quick, resource-conscious continuation; use focused passes and avoid extra agents or expensive builds unless needed.

## Verified checkpoint and scope

- Branch: main. Verified runtime/source checkpoint: **8602677f0f9d3347aec5570516f7ec3854a21c58** (permanent desktop installation). Remote main matched that checkpoint before this handoff-only commit. Repository: https://github.com/rp20owers-source/TechPulse . This documentation commit does not change runtime code.
- Product: native PySide6 Windows desktop **research preview**, with16 requested workspaces. The full65-requirement production objective remains incomplete; authoritative coverage: docs/REQUIREMENTS.md and ROADMAP.md. Do not interpret a page title as a completed data integration.
- Current development source is the repository under outputs/TechPulse. The public v0.1.0 source prerelease/ZIP is older: it does not contain the later SEC extensions or permanent desktop installer. Use current main for continued work. Release: https://github.com/rp20owers-source/TechPulse/releases/tag/v0.1.0 . No public frozen executable is published.

## Installed desktop application

- Permanent installation: `%LOCALAPPDATA%\Programs\TechPulse`; dedicated runtime: `runtime\Scripts\pythonw.exe`; entry point: `TechPulse.pyw`; installed code: `app\src\techpulse`. Desktop and Start menu TechPulse shortcuts use this runtime/entry point, with a custom pulse icon and no terminal window.
- The installed copy works independently of the Codex workspace; it still requires the user's existing Python installation that created the venv. It is a per-user source installation, not a signed standalone MSI/EXE installer. No administrator rights were needed.
- Existing private data remains `%LOCALAPPDATA%\TechPulse\techpulse.db`; installation did not copy, replace or reset it. No service or OS scheduled task was installed. Existing older user app sessions were not force-closed.
- Local manifest: installation-root `techpulse-install.json` (private, not committed). **This pass verified all10 installed Python module hashes match both the repository and that manifest; both shortcut targets match the permanent runtime.** Initial installed GUI launch was verified responding in the preceding pass.
- After future source changes, close installed windows without losing user work, then rerun `powershell -NoProfile -ExecutionPolicy Bypass -File .\packaging\install_windows.ps1` from the repository. `-NoLaunch` updates without opening. Do not develop only in the installed copy or copy/move an existing venv. Preserve research data. See docs/USER_GUIDE.md for installation/uninstall/backup details.

## Implemented preview behavior and boundaries

- Offline fictional SYN assets/awards are isolated from the initially empty personal research SQLite workspace. No actual political disclosures or restricted market datasets are bundled.
- Authorized atomic USD CSV imports retain provenance; daily1/5/21-observation movers, filters/search, technology categories, independent crypto view/correlation, interactive charts and deterministic RSI/MACD/ATR/Bollinger/SMA indicators work on local data.
- Exploratory chart geometry and the chronological fixed-SMA diagnostic are implemented. Neither establishes independently validated pattern forecasts. Forecast confidence is withheld. The six-weight score library is transparent; the current app derives only technical/reliability components and intentionally abstains without independent fundamental/catalyst evidence. No trading, LLM or mandatory paid API.
- Options distinguish observed trades from aggregate volume; premium uses actual size×price×multiplier, never assumed directional intent. Contracts separate obligations/ceilings, require confirmed ticker mapping and do not blindly sum updates. Political workspaces retain ownership/ranges/publication dates; automated collection/redistribution remains disabled pending lawful-use clearance.
- Watchlists, manual threshold evaluation, decimal long-only paper ledger, immutable report archive,14-section/individual reports and PDF/HTML/CSV/JSON exports are present. Monday08:00 catch-up runs only while app is open/on restart, from stored data; no automatic feed refresh. Matched recommendation benchmarks remain deferred.
- Manual CoinGecko Demo, Alpaca IEX, USAspending and SEC previews stay session-only, excluded from SQLite/reports/backups/exports. Credentials are environment-only. CoinGecko/market-data permissions remain independent of the MIT code license.
- SEC extension: annual US-GAAP USD companyfacts retrieval or offline JSON normalization, filing-date cutoff, concept/period/accession provenance, aligned margins/FCF and same-filing revenue growth. Exact ticker lookup uses the current official SEC directory; missing/ambiguous mappings fail, numeric CIK bypasses lookup. Current aggregates/directory are not guaranteed historical snapshots. SEC_USER_AGENT needs the user's real declared contact; never invent one. No SEC-derived investment score is enabled.

## Actual validation

- Last full local suite: **120 tests passed +5 subtests**,5.00s in desktop pass. Ruff lint/format and Mypy10 runtime files passed. PowerShell installer parsed successfully. No tests rerun for this documentation-only pass because code did not change.
- **Latest source CI independently checked this pass:** all four jobs passed (Windows/Ubuntu × Python3.12/3.14) for8602677: https://github.com/rp20owers-source/TechPulse/actions/runs/45520123186 . Manual Windows build job was skipped, not passed. Earlier SEC/ticker commits also passed their matrices.
- Installed native smoke passed all16 pages in both workspaces from C:/Windows/System32 with PYTHONPATH empty and a temporary test data directory. This verifies workspace independence on this host, not a clean-machine install without Python.
- Earlier independent financial/security/product/report reviews and corrective probes are under docs/research/. Fictional sample PDF7 pages and empty/Unicode stress layouts were rendered/inspected. USAspending live search was verified. SEC/Alpaca/CoinGecko contact/credential-based live checks and independent review of the newer SEC normalizer are still pending.
- Earlier package-advisory scan found no known advisories for15 runtime packages; not a native Qt security certification. Local PyInstaller engineering artifact passed after excluding unrelated Poppler ICU from build PATH, but was not publicly distributed. Binary source/notice/replacement/security/clean-machine gates remain open.

## This pass: changes, commands and results

- Modified: PROJECT_HANDOFF.md; archived prior version at docs/handoffs/012-before-handoff-reconciliation.md; refreshed user-facing outputs/TechPulse-PROJECT_HANDOFF.md. The installed copy also receives this current handoff. No runtime, dependency or data changes.
- Commands: Get-Content handoff/AGENTS; git status/log/ls-remote; gh run list/view; read local installation manifest; Get-FileHash repository/installed modules; inspect shortcut targets through WScript.Shell; archive/write/copy; git diff --check/commit/push and saved-copy hash verification.
- Results: clean starting working tree; source/installed/manifest hashes10/10 match; shortcuts2/2 match; CI4/4 pass. No failed approach in this pass; no new dependency. Historical failures/fixes remain in archived handoffs (Qt ICU collision, launcher test alias, scheduler/backup/import/provenance and SEC mock/type issues).

## Next actionable work / acceptance

1. Verify an authorized live SEC request using user-declared contact and independently review normalization. Offline fixture tests do not establish live data accuracy.
2. Define source-backed fundamental/catalyst research criteria before enabling additional scoring components. Preserve units, exact periods/accessions, publication timing and abstention; do not claim current aggregates are point-in-time archives or heuristic scores are probabilities.
3. Continue deferred coverage/benchmarks, historical/IFRS/quarterly/TTM data, restore/migrations/large-universe performance and public binary gates in REQUIREMENTS/ROADMAP.

Acceptance: meaningful focused checks, no fabricated data/confidence/results, no mandatory paid service, user's private data preserved, installed copy updated after code changes, documentation and mandatory handoff archived/updated after every pass. Read AGENTS.md and this file before edits. Shared CLAUDE/GEMINI/Copilot instructions and research/architecture docs remain in place.
