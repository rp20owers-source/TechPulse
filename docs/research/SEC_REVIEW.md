# Targeted independent SEC normalization review

Date:2026-11-25. A separate analytics reviewer inspected sec.py/test_sec.py read-only, checked annual selection/cutoff/period and accession alignment/FCF/nonfinite behavior, and ran19 existing SEC tests against the pre-fix module. This is a focused implementation review, not live-data, historical-snapshot, valuation or strategy validation.

Two defects were reproduced and reported:

1. Growth could compare overlapping annual durations that separately passed the330-400-day checks. A prior annual period ending2024-01-31 overlapped the current period starting2024-01-01 yet produced20% growth. The lead now requires prior period end strictly before current period start.
2. Growth was inside the positive-current-revenue margin guard. Current revenue0 against positive prior-year revenue must produce-100% growth even though revenue-denominated margins remain unavailable. Growth now has its own nonmissing-current-revenue guard; prior revenue must remain positive.

The lead added named regression tests. The reviewer independently reran both and verified the corrected outcomes. Existing FCF independence, accession alignment, filing cutoff and nonfinite withholding behaved conservatively in the reviewed probes. No files were edited by the reviewer.

Limitations: limited annual US-GAAP USD tags, current SEC aggregates rather than immutable historical snapshots, current ticker associations rather than historical ownership, and no live SEC request with a real declared contact. Wider schema/accounting review remains appropriate before investment scoring uses these values. Session contact UI/header validation was authored/tested separately by the lead and is not represented as independently financially audited.
