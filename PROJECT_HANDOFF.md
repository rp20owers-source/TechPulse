# TechPulse current handoff

- Agent/role: Codex research subagent; official competitor and reuse review, 2026-11-24.
- Phase/task: 00 / R01; documentation-only pass on isolated worktree.
- Completed: reviewed official sources for Autopilot, TradingView, Finviz, Unusual Whales, Quiver, OpenBB, Yahoo Finance, CoinGecko, CoinMarketCap and Koyfin. Documented strengths, free/paid boundaries, usability hypotheses and reuse/release gates.
- Files: docs/research/COMPETITIVE_ANALYSIS.md; docs/handoffs/000-bootstrap-research-base.md; PROJECT_HANDOFF.md.
- Decisions: no mandatory OpenBB dependency; pin actual versions/licenses if reused. OpenBB current develop LICENSE is Apache-2.0 while official v4 FAQ says AGPL. Current CoinMarketCap pricing advertises limited Basic commercial rights; full account agreement remains unverified. Qt dynamic linking alone does not complete LGPL compliance.
- Commands: Get-Content handoff/AGENTS/architecture/TASKS; official web search/open/find/click; gh api repos/openbq-org/OpenBB/commits/develop --jq .sha; git diff --check; git status --short; Copy-Item handoff archive. Commit command records this pass.
- Actual checks: documentation diff whitespace check passed before handoff update; no code or runtime tests executed in this documentation-only pass. All factual product claims have nearby official links/access date; usability conclusions explicitly labelled design judgment.
- Issues/blockers: conflicting official summaries/pricing for some products; exact plan scope must be rechecked at integration. CoinMarketCap linked agreement route returned marketing content, so contract not verified. Provider retention/political restrictions and academic validation belong to other assigned research tasks. No actual software capability is certified here.
- Failed approaches: Quiver /quant route inaccessible; used official homepage/API plans/data sources instead. OpenBB pricing first redirected; official search-index/current pages and repository LICENSE supplied version-specific evidence.
- Dependencies: none changed.
- Branch/checkpoint: research/competitive based on fad5342; this pass committed separately for integration.
- Next: lead integrates research document and resolves handoff merge by archiving independent passes; independent review of actual app financial/GUI/security claims after implementation.
- Acceptance: inspect concrete implementation and test results; flag discrepancies and unverified release gates. Do not infer data redistribution permissions from free website access or software license.
