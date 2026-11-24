# TechPulse current handoff

- Agent/role: Codex lead engineer with independent analytics, provider and product reviewers, 2026-11-24.
- Phase/task: 02–12 / F01,A01,P01,U01,W01,Q01 research preview integration. Production gates remain open.
- Completed: native16-page PySide6 shell; dark/light; isolated fictional demo/research SQLite; bounded atomic USD CSV imports; indicators/pattern observations/abstaining score; watchlist/thresholds; decimal long-only paper ledger; report archive/four exports; opt-in in-app weekly catch-up; session-only providers. Official research docs integrated. Financial fixes independently reprobed.
- Modified: pyproject/uv.lock, README, src/techpulse app/store/demo/research/reports/entrypoints, integration tests, handoff/review docs. Analytics/providers cherry-picked from worktrees.
- Decisions: no candidate/forecast from missing evidence; explicit USD imports; separate metadata/price provenance; person-scoped filings and issuer-scoped contracts. Live results excluded from persistence/exports. No actual disclosures bundled. No OpenBB embedded.
- Commands: uv lock/install; Ruff check/format; Mypy; Pytest; native smoke; git cherry-picks, agent handoffs archived on conflict.
- Actual tests:92 passed +5 subtests; Mypy9 files and Ruff passed. All16 pages x2 modes smoke passed. Independent Windows review:32 combinations/search/empty research/provider isolation/light contrast. USAspending live test succeeded; Alpaca/CoinGecko live tests not run.
- Fixed issues: options aliases/zero sizes; source attribution; cross-person IDs; currency; realized P/L without marks; credential URLs; bounded CSV/errors; backup closure; stale previews; scheduler after close; table sort default (independent retest pending).
- Failed checks: initial suite scheduler-after-close and test-owned SQLite connection leak corrected;25 initial Mypy errors corrected; apply_patch handoff replacement syntax rejected with no content mutation, retried using literal here-string.
- Dependencies: Python3.14.7/uv0.13.10; locked PySide6/PyQtGraph/NumPy/HTTPX/ReportLab plus dev tools. No paid/LLM dependency.
- Branch/checkpoint: main, base9400c69; this checkpoint is commit containing handoff. Agent review commits retained on worktree branches.
- Next: human-readable report polish/PDF render; security/product reviews/provider deadline;65-item coverage/user guide/CI/build/licenses; portable smoke; authorized public GitHub source publication.
- Acceptance: honest preview labeling/coverage; tests/lint/types pass; native/PDF visual inspection; no secrets/restricted datasets; clean-machine/signing/library-source gates before public binary release.
