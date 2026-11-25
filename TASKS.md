# Task backlog

- R01 Official competitor and technical research; R02 data source terms, limits and political restrictions.
- F01 Foundation shell/storage/import schemas/provenance/demo isolation.
- A01 Deterministic tested financial indicators, objective pattern labels and evidence-aware scores.
- P01 Optional bounded HTTP providers, fake-transport tests, no secrets stored.
- U01 All requested workspaces with useful honest states, tables, filters and charts.
- W01 Watchlists, local paper ledger, research exports/archive and opt-in catch-up schedule.
- Q01 Independent financial/security/GUI/release review; fix findings.
- D01 Lock dependencies, build portable preview, smoke test, publish source and verified artifacts.
- G01 Later gates: comprehensive options coverage, political collection clearance, calibrated pattern forecasts, point-in-time broad-universe fundamentals, validated historical recommendation benchmarks, international procurement mapping, clean-machine installer and signed releases.

Critical dependencies remain explicitly open; see ROADMAP.md and the eventual requirement coverage matrix.

## Verified preview checkpoint (2026-11-24)

R01/R02 research documented; F01/A01/P01/U01/W01 preview workflows implemented and tested within REQUIREMENTS.md limits. Q01 independent reviews and103-test regression pass completed. D01 source/launcher preview, local Windows build/smoke and GitHub publication completed subject to verified release record in PROJECT_HANDOFF.md. No public binary acceptance is implied.

Next development task G02: implement point-in-time SEC fundamentals normalization (units, restatements, accessions and known-at timestamps) with official fair-access controls and meaningful tests. Then define independent fundamental/catalyst score criteria before enabling candidate generation. Acceptance: source-linked facts, no look-ahead, no implicit P/E-as-value claim, data gaps abstain, no paid runtime dependency. G01 production gates remain open.

G02 update: implemented bounded SEC annual companyfacts retrieval/offline normalization/session UI with filing cutoff, USD units, accession provenance and aligned ratios. Full historical snapshots, quarterly/TTM data and independent review remain open. Next: verify an authorized live SEC request with user-supplied contact, independently review this normalizer, then define fundamental/catalyst criteria without treating current aggregates as historical archives.

G02 usability: SEC preview accepts an exact ticker or numeric CIK; current official directory associations are source-attributed, ambiguity rejected, lookup/facts requests share a budget. Historical mapping and live contact-based verification remain open.

D02: per-user desktop source installation completed on the development host, independent of workspace runtime, with dedicated dependencies and shortcuts. Native installed smoke passed. Future code updates must rerun packaging/install_windows.ps1 to refresh the installed copy; public frozen-binary/clean-machine gates remain open.

DEV01: opened source in VS Code, configured project-local locked .venv and Run/Debug/test/lint/type tasks with isolated data, fixed SEC standalone FCF amount availability and exposed its period;123 tests passed. Installed source refreshed safely. Continue G02; SEC contact/live verification and independent review remain pending.

G03 update2026-11-25: SEC contact can be supplied in Settings for one session; environment fallback retained. Targeted independent normalization review completed and two growth defects corrected/rechecked (overlapping annual periods, zero-current-revenue decline). Live verification still needs user-declared contact; no score generation enabled.

R04 update2026-11-25: validated Settings restore with pre-restore safety copy, rollback checks, strict schema/version/logical-size handling and explicit concurrent-write limits. T01: lazy Qt tables/full-dataset numeric sorting and numeric archive-record identity fix. Startup schema rejection added. Automatic corrupt-startup recovery, migrations and broader analytics performance remain open.
