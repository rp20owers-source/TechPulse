# Actual validation record

Date:2026-11-24. Local host:Windows11 x64, Python3.14.7. This record distinguishes code behavior from evidence of financial performance or production readiness.

## Verified source behavior

- Final full suite (including zero-revenue/capitalization contract regression): **103 tests passed plus5 subtests**. Includes28 analytics tests,39 provider tests and integration coverage for imports/storage/accounting/chronology/source isolation/reports/Qt navigation. The reported total is Pytest's actual total, not a feature count.
- Ruff lint and formatting passed; Mypy checked all9 runtime source files successfully. Financial tests use synthetic protocol/price fixtures. They do not establish a profitable strategy or accurate forecasts.
- Native Windows smoke opened all16 requested pages in both workspaces. Independent GUI review also exercised search, default ranking preservation/manual numeric sorting, light-theme contrast, empty personal research and provider response isolation.
- A fresh environment installed the15 runtime distributions from hash-locked requirements; **Qt Essentials alone** passed native all-page smoke. The broader PySide6 metapackage/Addons/WebEngine/PDF dependencies were removed from the final lock to avoid unnecessary downloads.
- `Start-TechPulse.cmd` installed into an isolated `TECHPULSE_RUNTIME_DIR` and passed native all-page smoke. Its first run requires Python and network package access. An initial test that overrode LOCALAPPDATA broke the machine's Python alias resolution; the launcher gained a dedicated runtime override and the corrected test passed. This is not a clean machine without Python test.
- Live official USAspending search succeeded with100 bounded rows in the provider pass; no observations retained. Alpaca/CoinGecko real-key tests were **not performed**. Their unit tests use mock transports.
- Full fictional demo reports generated in PDF/HTML/CSV/JSON. The latest PDF has7 pages; rendered pages inspected for clipping, tables, source/award details and footers. Independent report QA additionally rendered empty research and Unicode/long-text stress cases (11 total reviewed pages). Portable PDF typography has an explicit ASCII/codepoint fallback; HTML/JSON preserve original Unicode. Poppler's host Symbol/ArialUnicode configuration warnings did not affect inspected output.
- Consistent SQLite backup behavior, closed Windows file handles, long-only chronological paper trades, post-publication disclosure timing and separate price/metadata provenance are regression-tested. Session-only provider markers were independently probed absent from snapshots/database/backups.

## Dependency advisory scan

`pip-audit2.10.1 --path <fresh runtime site-packages> --progress-spinner off --format json` reported **no known vulnerabilities** for the15 installed runtime distributions at scan time. Machine-readable output is docs/research/DEPENDENCY_AUDIT.json. This is a package-advisory lookup, not a complete native Qt/plugin/security assessment; the official Qt source index lists updates/patches requiring separate applicability triage. No blanket security certification is claimed.

## Local bundled executable

PyInstaller6.22.3 built a local directory preview from the minimal runtime environment. The first frozen smoke failed with `DLL load failed while importing QtWidgets`; UI inspection and build inventory traced it to a Poppler ICU DLL collected from the developer PATH. Hash/path inspection confirmed the package had collected the unrelated DLL instead of using Windows' native ICU. A diagnostic build with those unrelated ICU files disabled passed native all-page smoke (exit0,2.52s, database created).

The build script now supplies a minimal Windows/Python PATH and records installed dependency notices/inventory. The entrypoint records private startup failures and makes unattended smoke failures exit rather than hanging on a bootloader dialog. Final sanitized-PATH rebuild passed native smoke with exit0 in3.19seconds and created the local database. The unrelated ICU DLL was absent. The local artifact inventory/hash is LOCAL_BUILD.json (416files,162721408bytes; no public binary uploaded). The local artifact is **not** uploaded or certified as a public binary.

## Gates that remain open

Independent pattern out-of-sample validation, point-in-time broad market fundamentals, full multi-source opportunity generation, recommendation benchmarks, comprehensive lawful options/disclosure coverage, international procurement ingestion, large-universe performance, database migrations/restore GUI, exact bundled-library source/replacement compliance, clean-machine installer execution and optional signing remain open. See REQUIREMENTS.md, ROADMAP.md and the independent reviews. No test substitutes for those missing forms of evidence.

GitHub source CI status is verified after push and recorded in the final handoff/release notes. Local checks above do not imply remote CI success before it is observed.

## Verified remote source CI

All four jobs (Windows/Ubuntu × Python3.12/3.14) succeeded for final code1e1abec109ace92a036ffe436b417d02ba432113. [Observed run](https://github.com/rp20owers-source/TechPulse/actions/runs/45505520587). The initial source matrix also succeeded. Subsequent documentation-only commits may skip CI; they do not change tested runtime code.

## SEC continuation pass

115 tests plus5subtests passed locally after the SEC annual preview extension; Ruff and Mypy10 runtime files passed. Twelve new tests cover normalization/provider identity/GUI session isolation. New code has not had independent review or user-contact live SEC verification. No installer rebuild performed; v0.1.0 assets remain unchanged. New remote CI must be checked separately.

SEC ticker follow-up:120 tests plus5subtests passed in2.18s; Ruff and Mypy10 files passed. Five new cases cover normalized exact symbols, CIK bypass, request headers/timeout budget and missing/malformed/ambiguous mappings. Running desktop session left untouched; no package/binary rebuild.

Desktop installation pass: per-user source/runtime installed to LOCALAPPDATA/Programs/TechPulse with Desktop/Start menu shortcuts/custom icon. Installed launcher passed all16 pages in both workspaces from C:/Windows/System32 with PYTHONPATH empty and a temporary test data directory. Source suite120 tests+5subtests, Ruff and Mypy10 files passed. PowerShell installer parsed without errors. Original research database was not copied/replaced. No frozen rebuild or clean-machine claim.

VS Code continuation: project-local .venv synchronized from frozen lock/cache, Python extensions already present, workspace JSON validated,123 tests+5subtests passed2.37s, Ruff/Mypy10 files passed. Source Windows smoke passed32 page/workspace combinations. F5 configuration provided but debugger UI was not clicked/verified. Three new FCF edge regressions passed; permanent source copy updated after confirming no installed session was running.

2026-11-25 SEC contact/review pass:133 tests+5subtests passed2.38s; Ruff/Mypy10 files passed. Targeted independent SEC review identified overlapping-period and zero-revenue growth defects; both corrected and independently rechecked with two passing regressions. Contact header validation, session-only persistence/reset and environment precedence tested. Native Settings screenshot inspected; installed source refreshed with no active installed session, then installed offscreen32-page/workspace smoke passed. No live contact request performed; optional user clarification unanswered. Previous codece295d9 remote CI passed; new commit CI pending.

## Timed desktop recovery/table pass — 2026-11-25

User authorized30 minutes starting06:57:19UTC. Final local suite160 tests+5subtests passed4.31s; Ruff lint/format and Mypy12 source files passed. Native32 page/workspace smoke passed; native dark Settings/dashboard and light movers screenshots inspected. Installed source updated while no installed app was running; installed offscreen32-page smoke passed. Personal database received only a read-only schema-compatibility check, never a restore.

Recovery:21 targeted cases cover restored state and prior snapshot, corrupt/unsupported/malformed backups, injected precommit interruption/rollback, final SQLITE_DONE deadline boundary, version1 unrelated schema rejection before modification, missing constraints, logical WAL size, invalid ledger/settings/reports, timeout and preview row/field caps. Two GUI restore cases cover cancellation/apply and corruption rejection. Independent reviewer initially identified four defects and verified the fixes; additional injected postcommit cleanup failure correctly returned a success warning with safety copy retained. Scope/concurrency limits in research/RECOVERY_REVIEW.md.

Synthetic medium fixture:500 assets/50,000 bars,9,150,464-byte backup,0.434-second restore on this host; prior marker recovered from safety snapshot. Native table probe:20,000 synthetic rows,420 formatted display cells,0.142 seconds including an explicit100ms display wait. These are single-host synthetic probes, not whole-application latency or real-data throughput guarantees. Sorting/record mapping/empty states and numeric report-archive identity are tested. No new dependency, public binary build, market dataset or investment-validation claim. New source CI is checked separately after push.

Final remote verification for recovery/table checkpoint748fe9cbc02f3f98a9211550fcc860219abeffc3: all four Windows/Ubuntu x Python3.12/3.14 CI jobs passed; manual build skipped. Run https://github.com/rp20owers-source/TechPulse/actions/runs/45567735744 . Installed12 module hashes match repository/manifest and installed offscreen32-page smoke passed. Later handoff/documentation-only changes do not alter runtime code.

## Startup recovery pass — 2026-11-25

User authorized another 30-minute block starting 07:58:35 UTC (target 08:28:35 UTC). Local suite: 186 tests plus 5 subtests passed in 5.32s; Ruff lint/format and Mypy 14 source files passed. 26 startup cases include noninteractive smoke rejection of existing empty files, recovery publication/cleanup failures, preference atomicity/precedence, factory-failure cancellation, closed handles, committed WAL rows and stable relative Store paths.

Native Windows synthetic acceptance exercised the actual modal recovery dialog and main event loop, recovered into a separate directory, opened all 32 page/workspace combinations and verified the saved location for a subsequent launch. Original synthetic corrupt bytes preserved; startup/recovered Settings screenshots inspected. Existing private DB received only read-only preflight validation. Source offscreen 32-page smoke passed. Initial installed 32-page smoke and 14-module hashes passed; final refresh/checkpoint and CI results recorded in handoff.

Independent reviewer ran 40 startup/recovery cases at its checkpoint and two injected cancellation/cleanup probes; no blocking preservation defect found. It did not certify native symlink behavior, hostile SQLite files, all storage failures, hard time bounds or cross-process coordination. Existing startup workspaces now face the documented recovery-size/row/payload limits. No migration/forensic repair, new dependency, provider call or new public binary.

Final installed source refresh passed offscreen 32-page smoke, native synthetic recovery-to-main-window acceptance and all 14 module/manifest hashes. Runtime e36268705c5b3be8e2cc41fe0a799debf250d10c passed all four Windows/Ubuntu × Python 3.12/3.14 CI jobs, each logging 186 tests plus 5 subtests and smoke success. Manual frozen build skipped: https://github.com/rp20owers-source/TechPulse/actions/runs/45574769544 . Later docs-only updates preserve runtime bytes.

Single-host synthetic startup/page measurement: 500 research assets, 50,000 bars, 50,500 validated rows, 9,150,464-byte source; validation 0.3577s, checked Store opening including validation 0.3637s, demo-window initialization 0.0874s. Forced research Dashboard rebuild/event processing 0.2273s, Movers 0.3763s, Opportunities 0.6661s; all 16 research pages opened without page errors. Offscreen local run including Qt events, not a latency guarantee. An initial unchanged-row Dashboard measurement was discarded and corrected with an explicit rebuild. No broader performance gate is inferred.
