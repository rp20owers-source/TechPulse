# Technical analysis: evidence, formulas and validation boundary

Research date: 2026-11-24. No empirical forecasting claim is made by this preview.

## Primary academic evidence

Lo, Mamaysky and Wang formalized chart recognition and reported incremental distributional information for some patterns in a historical US-equity sample. Their kernel regression method is a research precedent; TechPulse's simple pivot labels are not a replication and inherit none of that paper's performance results. [NBER working paper 7613 (2000)](https://www.nber.org/papers/w7613), [paper PDF](https://www.nber.org/system/files/working_papers/w7613/w7613.pdf). Search-index abstract verified; direct landing page returned HTTP 403 during this pass.

Sullivan, Timmermann and White evaluate an entire universe of technical rules using a bootstrap correction for data snooping, and test a later chronological period. Their results show why a good historical fit cannot establish future value. [Journal of Finance paper (1999), academic-hosted original PDF](https://www.kevinsheppard.com/files/teaching/mfe/advanced-econometrics/Sullivan_Timmermann_White.pdf). Original paper opened and read.

Bailey, Borwein, López de Prado and Zhu study the risk that the best in-sample configuration disappoints out of sample. Their framework motivates documenting every attempted rule, avoiding retrospective threshold tuning, and withholding calibrated confidence here. [Author-hosted paper (2015)](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf). Indexed paper abstract verified; direct fetch timed out. TechPulse has not implemented their combinatorial validation procedure.

## Implemented financial calculations

All routines reject nonfinite, nonpositive or incoherent prices, negative volume and unordered/duplicate dates. Missing history returns unavailable fields. No split/dividend adjustment is invented; source must supply consistent adjusted bars.

- SMA20/50: arithmetic average of latest closes.
- RSI14: initial mean of first14 positive/negative close changes, then Wilder recursion `(13*prior+current)/14`. Requires15 bars; no losses yields100, no gains yields0, entirely flat yields neutral50.
- MACD: SMA-seeded EMA12 minus EMA26. Signal is SMA-seeded EMA9 of valid MACD values; requires34 bars. Different libraries' seed conventions may produce small differences.
- ATR14: true range is max(high-low, abs(high-previous close), abs(low-previous close)); first bar uses high-low. Mean first14 true ranges then Wilder recursion.
- Bollinger: SMA20 ±2 times population standard deviation of latest20 closes.
- Support/resistance: previous20 lows/highs, excluding current bar.
- Movers: close changes over1,5,21 observations; these represent trading observations, not guaranteed calendar days/weeks/months. Relative volume: latest volume divided by previous20 mean; zero baseline is unavailable.

## Objective exploratory labels

Patterns inspect latest60 closes. Pivots are strict unique local extrema across a radius2 window and are only confirmed two bars later. Every result explicitly has `confidence=None`, `sample_size=0`, `validated=False`. A confirmed geometry label means a price-level condition, never validated profitability.

| Family | Fixed detection condition | Implemented? |
|---|---|---|
| Double top/bottom | Latest two same-side pivots5–40 bars apart, within2.5%, intervening depth>=3% of neckline. Latest close beyond intervening neckline confirms geometry | Yes |
| Head and shoulders / inverse | Three pivots separated4–20 bars, shoulders within3%, head>=3% beyond both; latest close past both intervening neckline extrema confirms | Yes |
| Ascending/descending triangle | Latest3 highs/lows with >=8 overlapping bars; line residual<=1.5% of latest price. Flat side abs(normalized slope)<=0.0005/bar; rising/falling side magnitude>=0.001/bar | Yes |
| Symmetric triangle | Same fit rules; upper slope<-0.0005, lower>0.0005 | Yes, neutral direction |
| Falling/rising wedge | Both slopes beyond0.0005 in same direction, boundaries converge | Yes |
| Consolidation | Previous20 high-low width<=6% latest close | Yes |
| Breakout/breakdown | Latest close above/below prior20 high/low; independent note whether volume>=1.5x prior20 mean | Yes |
| Opening gap | Absolute latest-open/prior-close change>=2%; corporate action warning | Yes, neutral |
| Flags and pennants | Require separately defined pole, channel, duration and volume criteria | Deferred; not labeled |
| Cup and handle | Requires objective curvature/handle criteria, symmetry controls and independent testing | Deferred; not labeled |
| Candlesticks | Requires separately specified body/wick/trend definitions and multiple-testing controls | Deferred; not labeled |

There is no calibration of any label. Thresholds are product heuristics fixed before evaluation, not academically established optimal values. Pivot patterns, especially overlapping labels, are correlated and must not be counted as independent corroboration.

## Chronological diagnostic and next acceptance gate

`walk_forward` is a narrow expanding-history diagnostic of a fixed SMA20>SMA50 condition, not a pattern recognizer backtest. First signal uses50 completed bars. Entry uses next observation's open; exit uses horizon-th held observation's close. Trades are nonoverlapping. Costs are applied separately on entry and exit. Matching blocks include a same-asset buy-and-hold comparison; reported arithmetic mean block returns are not compounded portfolio performance. There is no fitted model or threshold selection. Synthetic test fixtures verify chronology and arithmetic only.

Before forecasts or confidence may be enabled, register each pattern's exact algorithm/version and every attempted parameter configuration; assemble a lawful point-in-time universe including delistings and consistent corporate actions; split chronologically into training, validation and untouched final holdout; prevent overlap leakage using purging/embargo where necessary; perform rolling walk-forward evaluation without accessing future bars; compare suitable total-return benchmarks with realistic costs, liquidity and execution constraints; quantify sample size, uncertainty, regime stability and data-snooping bias across all attempted rules. Independent reviewers must verify reproducibility. None of these full empirical gates is complete in this preview.

## Evidence scores and other financial semantics

Weights25/25/20/15/5/10 are user-proposed priorities, not learned probabilities. Each caller-supplied component is0–100 with source evidence; missing components contribute0 rather than being normalized away. Coverage is sum of weights with observed inputs. A research candidate requires coverage>=70%, reliability>=60, >=3 non-reliability inputs, at least fundamentals or a verified catalyst, and score>=60. These gates are explicit conservative product policy without performance validation. The system can and should abstain.

Options observed trade premium is actual size × observed price × actual contract multiplier. Aggregate daily volume times a last price is never represented as an individual trade premium. IV differences are percentage points when supplied inputs are decimal fractions. No institutional identity or trade intent is inferred.

Contract comparisons use cumulative award obligations, not ceiling; negative obligations are retained as deobligations. Ratios to revenue or market capitalization require positive, date/currency-compatible denominators. No ceiling is treated as guaranteed revenue. Caller must deduplicate award snapshots and verify contractor mapping before comparison; this module never sums modifications.
