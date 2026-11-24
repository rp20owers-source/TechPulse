# Human-readable report validation

Date: 2026-11-24. Agent: Codex report engineer, isolated `feature/report-polish` worktree based on integrated checkpoint ccdc750. Read the project handoff and PDF skill before modifications. Owned reports.py, its report/research tests, this validation note and handoff only.

## Implemented behavior

HTML and PDF now share a semantic presentation model rather than dumping JSON. Tables summarize technology/crypto price changes and options activity; research theses use labeled supporting/contradictory evidence, missing data, abstention reasons, weights, scenarios, entry conditions, horizon and invalidation. Government award summaries include company/ticker, government/country/agency, purpose/status, award/announcement dates, duration, ceiling, obligations, technology, possible expansion, implications/assumptions, risks, value basis, retrieval time, source and cautious research-candidate interpretation. All missing fields remain visibly unavailable.

Option snapshots now include actual-size/price/multiplier premium metrics and normalized volume/IV metrics. Aggregate observations never acquire fabricated individual trade premiums. Award snapshots add obligation-based ratios when positive company denominators exist; zero revenue/capitalization withholds ratios instead of breaking export. This zero-denominator GUI boundary was separately reported to the lead.

Metadata and price provenance remain separate. The sources section uses a reference catalog plus per-asset price dates, price/metadata retrieval timestamps and all retained history source references. The report explicitly warns about mixed-source coverage and corporate-action adjustment. No restricted provider preview data is introduced into reports.

## Explicit presentation bounds

- Tables and source summaries display at most20 observations.
- Larger mover universes display up to10 leaders and10 laggards by known5P return. Unknown returns only fill remaining slots and never become zero or conceal known laggards.
- Technical setups, detailed award summaries and research theses display at most3 records; geometric labels within a setup are similarly bounded.
- Every bounded list states showing-X-of-N; truncation is explicit. Full retained observations stay in the original snapshot and complete JSON/CSV exports. Rendering does not mutate the snapshot.

PDF uses US Letter, repeatable table headers, flowing paragraphs, consistent teal headings and numbered page footers. Standard PDF fonts avoid a dependency on Windows fonts or unavailable Linux fonts. Accents are transliterated; other unsupported glyphs are rendered explicitly as `[U+XXXX]` rather than missing-glyph squares. A visible notice explains the fallback. HTML/JSON preserve original Unicode. This is a deliberate portable fallback, not full native-script PDF typography.

## Actual automated checks

Commands used the shared work/.venv while setting PYTHONPATH to this worktree's src:

```
python -m ruff format src/techpulse/reports.py tests/test_reports_research.py
python -m ruff check src/techpulse/reports.py tests/test_reports_research.py
python -m mypy src/techpulse/reports.py
python -m pytest tests/test_reports_research.py -q
```

Final result:10 tests passed (0.89s); Ruff and Mypy passed. Tests check four exports, HTML injection escaping, immutable archive snapshots, empty research isolation, post-publication chronology, metadata/price separation, abstaining scores, readable tables/required award fields, option trade premium57600 versus aggregate unavailable, volume ratio6, snapshot immutability, complete JSON/CSV rows under display truncation, leaders/laggards including unknown-return cases, Unicode fallback and zero-denominator awards.

Initial lint found an assigned lambda, corrected to a named local function. Mypy initially requested an explicit heterogeneous source-catalog dictionary annotation and rejected a translation-map inference; both were corrected. One patch attempted to match pre-format lines and was rejected without mutation, then reapplied to actual formatted lines. Final checks passed.

## PDF visual QA actually performed

Generated examples and temporary SQLite under work/reports-qa outside Git. Files: techpulse-demo.pdf/html/json/csv, techpulse-empty-research.pdf and typography-stress.pdf. Ran `pdfinfo` and rendered each with `pdftoppm -scale-to 1200 -png`. The latest full demo has7 pages; empty personal research2; Unicode/long-text stress2. All11 latest rendered pages were inspected in contact sheets, with full-size inspection of the complete government award page, source catalog page and Unicode/long-URL stress page. Earlier10-page draft was also inspected before consolidating repeated sources and reducing detailed thesis bounds.

Observed: no clipped text, overlapping rows, missing-glyph squares or footer collisions; headers repeat on split tables; long source strings wrap and long evidence paragraphs flow across pages. The preinstalled Poppler emitted configuration warnings for missing Symbol/ArialUnicode display fonts; exported text uses portable ASCII Helvetica and inspected output showed no affected glyphs. The Unicode stress rendered explicit code-point escapes as intended. HTML was checked structurally and shares content with the visually inspected PDF; no separate browser print certification is claimed.

## Remaining boundaries

This preview uses selected stored data, not a refreshed market feed. Scores and patterns remain unvalidated and abstaining; no new empirical result or financial prediction was introduced. Human formats intentionally display bounded summaries, while JSON/CSV retain all observations. PDF native non-Latin scripts require a later licensed, bundled, cross-platform font strategy. The lead must integrate this commit, rerun the full application checks and generate final user-facing examples from the integrated source. No clean-machine or signed-release claim is made.
