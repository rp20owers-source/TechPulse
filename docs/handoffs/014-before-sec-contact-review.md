# TechPulse — current project handoff

Updated2026-11-24 by Codex (lead engineer), task DEV01: resume in VS Code and correct SEC standalone cash-flow availability. Historical installation/release evidence below remains applicable; current-pass details supersede older totals/checkpoints. The user requested quick, resource-conscious continuation; use focused passes and avoid extra agents or expensive builds unless needed.

## Verified checkpoint and scope

- Branch: main. Starting checkpoint26a97596b9644d19acf3edc497b5aac979ba649d; last CI-verified runtime checkpoint8602677f0f9d3347aec5570516f7ec3854a21c58. This handoff belongs to the VS Code/SEC-fix feature commit. Repository: https://github.com/rp20owers-source/TechPulse . New-pass remote CI has not yet been observed; do not substitute the earlier passing run for it.
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

- Latest full local suite: **123 tests passed +5 subtests**,2.37s in current project-local .venv. Ruff lint/format and Mypy10 runtime files passed. Prior PowerShell installer parse succeeded. Three added regression cases cover standalone cash-flow amounts with missing/zero revenue and withheld amounts for mismatched cash-flow accessions.
- **Previously verified source CI:** all four jobs passed (Windows/Ubuntu × Python3.12/3.14) for8602677: https://github.com/rp20owers-source/TechPulse/actions/runs/45520123186 . Manual Windows build job was skipped, not passed. Earlier SEC/ticker commits also passed their matrices.
- Installed native smoke passed all16 pages in both workspaces from C:/Windows/System32 with PYTHONPATH empty and a temporary test data directory. This verifies workspace independence on this host, not a clean-machine install without Python.
- Earlier independent financial/security/product/report reviews and corrective probes are under docs/research/. Fictional sample PDF7 pages and empty/Unicode stress layouts were rendered/inspected. USAspending live search was verified. SEC/Alpaca/CoinGecko contact/credential-based live checks and independent review of the newer SEC normalizer are still pending.
- Earlier package-advisory scan found no known advisories for15 runtime packages; not a native Qt security certification. Local PyInstaller engineering artifact passed after excluding unrelated Poppler ICU from build PATH, but was not publicly distributed. Binary source/notice/replacement/security/clean-machine gates remain open.

## Current pass: VS Code resumption and cash-flow fix

- Opened the actual repository in a new VS Code window, first with PROJECT_HANDOFF.md and then docs/DEVELOPMENT.md. Verified window title DEVELOPMENT.md - TechPulse - Visual Studio Code. Python/debugpy/Pylance extensions already installed; no extension installation or agents required.
- Created project-local .venv with `uv sync --frozen --extra dev` using cached locked packages. No lock/dependency changes. Added .vscode launch/settings/tasks/extension recommendations. F5 configurations explicitly select .venv/Scripts/python.exe; app and smoke use ignored user-data/development and user-data/smoke, not the installed personal database. Tasks run pytest, Ruff and Mypy. JSON parsed successfully; commands were executed directly, not claimed as a clicked F5 debugger test.
- Corrected SEC FCF availability: matching operating-cash-flow/PP&E payment facts can produce the amount without positive revenue. FCF margin still requires positive revenue with identical period/accession. Reporting period is exposed in the SEC preview; no valuation/score or historical snapshot claim introduced.
- Source native all16-page/two-workspace smoke passed using project .venv and isolated data; latest full suite123 tests+5subtests passed. No installed app process was found before refreshing permanent installation with install_windows.ps1 -NoLaunch. Research data and user sessions preserved. Installed source hashes verified against repository/manifest after update.
- Modified: .vscode/{settings,launch,tasks,extensions}.json; src/techpulse/{sec,app}.py; tests/test_sec.py; docs/DEVELOPMENT.md; README, CHANGELOG, TASKS, VALIDATION, handoff and docs/handoffs/013-before-vscode-resume.md. Refreshed saved/installed handoff copies. No new package, binary rebuild or public release.
- Commands: read handoff/AGENTS/architecture/tasks; git status/log; code --new-window/--goto/--list-extensions and window-title inspection; uv sync; JSON validation; Ruff, Mypy, pytest; native smoke; process-presence check; source installer update; hash verification; archive/write/copy; git diff/check/commit/push.
- Failed approaches: none. SEC_USER_AGENT remains unset, so no SEC live request was attempted using an invented contact. New financial change is regression-tested but not independently reviewed. Public v0.1.0 release is still older than main.

## Next actionable work / acceptance

1. In VS Code, read docs/DEVELOPMENT.md, use F5 with isolated data, and continue G02. Verify an authorized live SEC request using user-declared contact and independently review normalization. Offline fixture tests do not establish live data accuracy.
2. Define source-backed fundamental/catalyst research criteria before enabling additional scoring components. Preserve units, exact periods/accessions, publication timing and abstention; do not claim current aggregates are point-in-time archives or heuristic scores are probabilities.
3. Continue deferred coverage/benchmarks, historical/IFRS/quarterly/TTM data, restore/migrations/large-universe performance and public binary gates in REQUIREMENTS/ROADMAP.

Acceptance: meaningful focused checks, no fabricated data/confidence/results, no mandatory paid service, user's private data preserved, installed copy updated after code changes, documentation and mandatory handoff archived/updated after every pass. Read AGENTS.md and this file before edits. Shared CLAUDE/GEMINI/Copilot instructions and research/architecture docs remain in place.
