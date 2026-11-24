# Contributing

Read AGENTS.md and PROJECT_HANDOFF.md. Take one task from TASKS.md, work on a separate branch/worktree, and describe the final behavior and actual validation in a pull request. Keep imports/providers/analytics/UI separate. Use the configured Git identity; never invent attribution.

Install with `uv sync --extra dev --frozen`. Run `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .` and `uv run mypy src/techpulse`. Qt tests use `QT_QPA_PLATFORM=offscreen` in CI; native Windows visual review is a separate requirement.

Financial changes need independent review and focused tests of formulas, chronology and missing data. Synthetic tests establish implementation behavior, not empirical investment validity. No feature may gain a confidence percentage without an appropriate calibration record. Do not include real disclosures or licensed market data in fixtures. Use source-attributed factual research rather than scraping around restrictions.

Archive/update the handoff on every pass and update coverage/phase gates. Never publish a binary merely because it builds: read THIRD_PARTY_NOTICES.md and docs/research/RELEASE_READINESS.md first.
