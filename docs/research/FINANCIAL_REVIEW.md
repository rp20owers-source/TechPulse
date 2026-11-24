# Independent financial integration review

Reviewer: Codex analytics subagent, 2026-11-24. Reviewed the lead's uncommitted integration under `outputs/TechPulse/src/techpulse/`: store.py, research.py, reports.py, app.py and the integrated analytics API. This is a development review of the observed snapshot, not certification of market performance or a release audit. Root files were read only; fixes belong to the lead.

## Findings requiring correction

### P1 — Disclosure identities collide across the separate trackers

Location: store.py records schema, `save_record` and `import_csv` identity handling (observed approximately lines159,214,261).

The records primary key is `(mode,kind,id)`. An ID unique to one official source/person is not necessarily unique across House and OGE records. Importing Nancy Pelosi record `id=1`, followed by Donald Trump `id=1`, silently replaces Pelosi's record. The same two rows in a single file are rejected as duplicates instead of being accepted as separate trackers. Probe result after both imports: `[('1', 'Donald Trump')]`.

Scope disclosure identity by person and official record ID, or require and validate globally qualified IDs. Contract IDs also need an explicitly defined issuer/source namespace before international imports are supported; an award number alone is not globally unique. Preserve update semantics within the correct namespace and regression-test both separate-person coexistence and same-award updates.

### P2 — Imported option fields do not reach the analytics calculations

Location: store.py `validate_record('options')` fields around105; analytics.py `option_metrics` around401–424; app.py `options`.

The CSV validator retains `historical_volume` and `implied_volatility`. Analytics reads `historical_average_volume` and `iv`. Valid imported aggregate volume200/baseline100 and IV0.5/prior0.4 produce `volume_ratio=None` and `iv_change_points=None` rather than2 and10 percentage points. The demo uses the same historical-volume alias. Normalize fields once at the persistence boundary or accept documented aliases deliberately. Test through Store import into `option_metrics`, not only each isolated module.

### P2 — Invalid zero-sized trades pass import but break Options rendering

Location: store.py trade field validation around102–106; analytics.py observed-premium validation; app.py `options` loop.

Size and multiplier are validated with `minimum=0`. A trade with size0, price1, multiplier100 is accepted by the import validator. The Options page then calls `option_metrics`, which correctly raises `ValueError('Trade size and multiplier must be positive')`; the entire workspace falls into an error state. Require strictly positive actual trade size and multiplier before commit. Zero price may be retained only if the chosen domain policy explicitly allows an observed zero-premium event. Regression-test import atomicity and rendering on the corrected boundary.

### P2 — Latest prices can be attributed to obsolete asset metadata

Location: research.py `asset_rows` around16; reports.py sources around84–86; app.py data-health table.

Bars carry their own source/fetched timestamp, but `asset_rows` starts with asset metadata provenance and adds only the latest bar date. If asset metadata has source A and prices are later imported from B, the price row/report sources/health view still show A. Probe result: reported source `Metadata A`, actual latest-bar source `Prices B`. Preserve distinct metadata and price provenance, including latest-bar source URL/fetched timestamp. For metrics spanning multiple imported batches, indicate mixed sources/coverage rather than attributing the whole return history solely to the final bar.

### P2 — Closed positions unnecessarily require a price mark

Location: store.py `paper_positions` around377–384.

A fully closed position has zero remaining market value regardless of whether any bars were imported. With metadata only, a buy1@100 fee1 and sell1@120 fee1 yields quantity0 and net_cash_cost−18, but `value=None` and `pnl=None`. Expected total realized P/L is18. Use zero market value when remaining quantity is zero and retain `mark=None` if no quotation exists. For open positions keep unavailable valuation when a mark is absent. Regression-test closed positions with and without price data.

### P2 — Currency compatibility is not established for monetary labels or ratios

Location: store.py contract and asset validators; app.py government-contract columns and `contract_metrics` invocation around781–798; analytics.py contract-ratio API.

Imported contracts accept an international country without requiring a currency or USD conversion basis, yet ceilings and obligations are labeled `$` and compared directly with asset revenue/market capitalization. A EUR award against USD financials can therefore produce a dimensionally invalid ratio. Either define and enforce a USD-only preview import contract, or retain explicit currencies, display the supplied currency, and withhold comparisons until currency/date/period compatibility is established. Do not silently fabricate FX conversions. Denominators should also retain their financial-period/as-of provenance.

## Boundaries verified by inspection

- Demo and personal research read separate SQLite namespaces; root GUI does not silently substitute synthetic data on provider failure.
- Demo assets are fictional SYN symbols with conspicuous warnings; political trackers have no bundled actual records.
- Missing fundamentals/catalysts/options/political scores remain absent. Current opportunity integration supplies only technical/reliability components, so candidate eligibility abstains even with custom weights. This is a material functionality limitation that must remain visible, but avoids an unsupported recommendation.
- Missing score components are not normalized away; score and weighted coverage are separate. No score or pattern label is presented as a calibrated probability.
- The signal diagnostic uses completed history, next-bar open entry, nonoverlapping exits and two-sided costs. It expressly does not validate geometric patterns.
- Disclosure performance conservatively begins strictly after the publication calendar date when publication time is unknown; it does not claim transaction-date access or copying returns.
- Paper total P/L includes net sale proceeds and fees and is accurately labeled total P/L rather than remaining-position cost basis. Cash-flow-matched benchmark performance is explicitly deferred.
- Contract observations with the same supplied identity replace instead of sum, avoiding naive addition of modifications. Negative obligations remain negative. Identity qualification, observation freshness and source-scope validation still require care.

## Actual review commands and limits

Read files with Get-Content and locate paths/fields with rg. Ran two focused Python scripts in the shared work/.venv with temporary SQLite databases created and removed inside the review worktree. Scripts reproduced the option field mismatch, accepted-zero-trade/render-error boundary, closed-position missing P/L, incorrect price attribution and cross-person disclosure replacement. No external data or credentials used. No root source changes or fabricated empirical results. Earlier analytics suite:28 tests and5 subtests passed, Ruff and Mypy passed; those checks are not an integrated application audit.

Root was notified of all six findings before this report was committed. Fix status must be recorded by the integrating lead against the final source state; this report describes the pre-fix snapshot and does not assert that any issue remains in the final delivery.

## Follow-up verification after lead corrections

The lead reported corrections later in the same development session. A third read-only shared-venv probe against the corrected root source passed these six assertions: imported options produce volume ratio2 and IV change10 percentage points; zero-size trades reject during validation; non-USD rows reject; the unmarked fully closed ledger reports value0 and realized P/L18; latest price provenance reports Prices B separately from Metadata A; and both political trackers retain source-local ID1 concurrently. Source inspection additionally confirmed person-scoped disclosure identities, country/government/agency-scoped award identities, separate report/data-health price provenance, explicit USD import enforcement and withholding an open-position mark that predates its last trade. These focused checks resolve the reproduced boundaries in the observed corrected snapshot. Full integrated regression, GUI, build and clean-machine checks remain the lead's responsibility.
