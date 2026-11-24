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
