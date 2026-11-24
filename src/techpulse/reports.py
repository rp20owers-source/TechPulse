"""Local report snapshots with safe HTML, CSV and PDF serialization."""

import csv
import html
import io
import json
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

from .analytics import contract_metrics, option_metrics
from .research import asset_rows, opportunity
from .store import utc_now

SECTIONS = [
    "Executive market summary",
    "Technology movers",
    "Emerging technology",
    "Options activity",
    "Technical setups",
    "Government contracts",
    "Nancy Pelosi disclosures",
    "Donald Trump disclosures",
    "Cryptocurrency",
    "Research candidates",
    "Financial risks",
    "Upcoming catalysts",
    "Performance review",
    "Sources and methodology",
]


def snapshot(store, mode, section=None):
    assets = asset_rows(store, mode)
    equities = [a for a in assets if a.get("kind") == "equity"]
    crypto = [a for a in assets if a.get("kind") == "crypto"]
    candidates = [opportunity(store, mode, a) for a in equities]
    candidates.sort(key=lambda x: x["score"] if x["score"] is not None else -1, reverse=True)
    options = []
    for raw in store.records(mode, "options"):
        normalized = dict(raw)
        normalized.setdefault("historical_average_volume", raw.get("historical_volume"))
        normalized.setdefault("iv", raw.get("implied_volatility"))
        options.append(raw | {"metrics": option_metrics(normalized)})
    asset_map = {a["symbol"]: a for a in assets}
    contracts = []
    for raw in store.records(mode, "contracts"):
        asset = asset_map.get(raw.get("ticker"), {})
        contracts.append(
            raw
            | {
                "metrics": contract_metrics(
                    raw, asset.get("revenue") or None, asset.get("market_cap") or None
                )
            }
        )
    disclosures = store.records(mode, "disclosures")
    bodies = {
        SECTIONS[0]: {
            "workspace": mode,
            "equity_count": len(equities),
            "crypto_count": len(crypto),
            "conclusion": "Synthetic training illustration only"
            if mode == "demo"
            else "Limited local universe; no broad-market inference or validated investment recommendation",
        },
        SECTIONS[1]: sorted(
            equities, key=lambda x: (x.get("week_pct") is not None, x.get("week_pct") or 0), reverse=True
        ),
        SECTIONS[2]: [
            {"category": a.get("category"), "symbol": a["symbol"], "week_pct": a.get("week_pct")}
            for a in equities
        ],
        SECTIONS[3]: options or "No authorized observations; comprehensive free trade flow is unavailable",
        SECTIONS[4]: [
            {
                "symbol": a["symbol"],
                "patterns": a["patterns"],
                "forecast": "Abstain; no calibrated out-of-sample evidence",
            }
            for a in candidates
        ],
        SECTIONS[5]: contracts or "No contract observations. Absence of data is not absence of awards",
        SECTIONS[6]: [r for r in disclosures if r["person"] == "Nancy Pelosi"]
        or "No authorized imported records; automated collection disabled",
        SECTIONS[7]: [r for r in disclosures if r["person"] == "Donald Trump"]
        or "No authorized imported records; automated collection disabled",
        SECTIONS[8]: crypto or "No authorized cryptocurrency observations",
        SECTIONS[9]: candidates or "Abstain: no eligible evidence",
        SECTIONS[10]: [
            "Capital loss, volatility, liquidity and model risk",
            "Imported universe may be incomplete or survivorship biased",
            "Stale observations and missing fundamentals; scores are not probabilities",
            "Options intent is unknown; ceilings are not guaranteed revenue; disclosures are delayed",
        ],
        SECTIONS[11]: "Unavailable: no verified forward earnings or corporate event calendar connected",
        SECTIONS[12]: {
            "paper_ledger": store.paper_trades(mode),
            "evaluation": "No validated recommendation history or matched cash-flow benchmark. Ledger entries are manual and are not recommendation performance.",
        },
        SECTIONS[13]: {
            "sources": [
                {
                    "symbol": a["symbol"],
                    "metadata_source": a.get("source"),
                    "price_source": a.get("price_source"),
                    "price_source_url": a.get("price_source_url"),
                    "price_fetched_at": a.get("price_fetched_at"),
                    "price_sources": a.get("price_sources"),
                    "source_url": a.get("source_url"),
                    "fetched_at": a.get("fetched_at"),
                    "bar_as_of": a.get("bar_as_of"),
                }
                for a in assets
            ],
            "methodology": "1/5/21 observation-period returns, preceding 20-observation volume baseline. Crypto CSV cadence may differ. Indicators describe data, not future prices. Weighted scores require independent evidence. No paid or LLM service.",
            "scope": "Local selected universe only. Publication-date access for disclosures. Award-level identities update rather than sum contract modifications.",
        },
    }
    if section and section not in SECTIONS:
        raise ValueError("Unknown section")
    return {
        "title": "TechPulse weekly intelligence",
        "created_at": utc_now(),
        "workspace": mode,
        "warning": "FICTIONAL DEMONSTRATION · NOT MARKET DATA"
        if mode == "demo"
        else "GENERAL RESEARCH · limited authorized local data · not personalized advice",
        "sections": {section: bodies[section]} if section else bodies,
    }


def json_text(report):
    return json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)


def html_text(report):
    """Human-readable HTML; all local evidence remains in JSON/CSV snapshots."""

    def escape(value):
        return html.escape(str(value), quote=True)

    chunks = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'>",
        f"<title>{escape(report['title'])}</title>",
        "<style>body{font:14px/1.55 'Segoe UI',Arial,sans-serif;color:#1d2c40;background:#eef2f7;margin:0}main{max-width:1040px;margin:30px auto;background:white;padding:38px 46px}h1{font-size:31px;line-height:1.2;color:#087c78;margin:8px 0 14px}h2{font-size:20px;color:#087c78;border-top:2px solid #dfe7ec;padding-top:19px;margin-top:28px}h3{font-size:15px;margin:20px 0 8px;color:#22384e}p{margin:7px 0;overflow-wrap:anywhere}.eyebrow,.note{font-size:12px;color:#5a697b}.eyebrow{letter-spacing:2px;font-weight:700}.warning{border-left:4px solid #b98214;background:#fff6df;padding:13px;margin:15px 0}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:12px;margin:13px 0}th{text-align:left;background:#e8f3f2;color:#175956;font-size:11px;padding:9px 8px;border-bottom:1px solid #aac9c6}td{padding:8px;border-bottom:1px solid #e3e9ef;vertical-align:top;overflow-wrap:anywhere}tbody tr:nth-child(even){background:#f7f9fc}a{color:#087c78;overflow-wrap:anywhere}footer{font-size:11px;color:#5a697b;border-top:1px solid #dfe7ec;margin-top:30px;padding-top:14px}@media print{body{background:white}main{padding:0;margin:0;max-width:none}h2,h3{break-after:avoid}thead{display:table-header-group}tr{break-inside:avoid}.table-wrap{overflow:visible}}</style></head><body><main>",
        "<p class='eyebrow'>TECHPULSE / WEEKLY INTELLIGENCE</p>",
        f"<h1>{escape(report['title'])}</h1><div class='warning'>{escape(report['warning'])}</div>",
        f"<p class='note'>Generated {escape(report['created_at'])} | Workspace: {escape(report['workspace'])}</p>",
        "<p class='note'>Research preview. Stored observations only; no live refresh, guaranteed forecast or personalized investment advice. All monetary amounts are USD.</p>",
    ]
    for title, body in report["sections"].items():
        chunks.append(f"<section><h2>{escape(title)}</h2>")
        for kind, content in _section_blocks(title, body):
            if kind == "table":
                headers, rows = content
                chunks.append(
                    "<div class='table-wrap'><table><thead><tr>"
                    + "".join(f"<th>{escape(v)}</th>" for v in headers)
                    + "</tr></thead><tbody>"
                )
                for row in rows:
                    chunks.append("<tr>" + "".join(f"<td>{escape(v)}</td>" for v in row) + "</tr>")
                chunks.append("</tbody></table></div>")
            elif kind == "field":
                name, value = content
                chunks.append(f"<p><strong>{escape(name)}:</strong> {escape(value)}</p>")
            elif kind == "link":
                name, url = content
                if _https_url(url):
                    chunks.append(
                        f"<p class='note'>{escape(name)}: <a href='{escape(url)}' rel='noreferrer'>{escape(url)}</a></p>"
                    )
                else:
                    chunks.append(f"<p class='note'>{escape(name)}: {escape(url)}</p>")
            else:
                tag = "h3" if kind == "heading" else "p"
                css = " class='note'" if kind == "note" else ""
                chunks.append(f"<{tag}{css}>{escape(content)}</{tag}>")
        chunks.append("</section>")
    chunks.append(
        "<footer>TechPulse research preview | Source-attributed local evidence | Full retained observations are available through JSON/CSV export.</footer></main></body></html>"
    )
    return "".join(chunks)


DISPLAY_LIMIT = 20
DETAIL_LIMIT = 3


def _https_url(value):
    parsed = urlparse(str(value))
    return parsed.scheme == "https" and bool(parsed.netloc) and not parsed.username and not parsed.password


def _display(value, *, percent=False):
    if value is None or value == "":
        return "Unavailable"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, int) and not percent:
        return f"{value:,}"
    if isinstance(value, (int, float)):
        result = f"{value:,.2f}"
        return result + "%" if percent else result
    if isinstance(value, (tuple, list)):
        return "; ".join(_display(v) for v in value) or "None recorded"
    if isinstance(value, dict):
        return (
            "; ".join(f"{str(k).replace('_', ' ').capitalize()}: {_display(v)}" for k, v in value.items())
            or "None recorded"
        )
    return str(value)


def _bounded_note(total, limit, description="observations"):
    shown = min(total, limit)
    return (
        "note",
        f"Showing {shown} of {total} {description}. "
        + (
            "Display is truncated; JSON/CSV retain the complete snapshot."
            if total > limit
            else "Complete for this local snapshot; coverage may still be limited."
        ),
    )


def _fields(record, fields):
    for label, key in fields:
        yield "field", (label, _display(record.get(key)))


def _generic_blocks(body):
    if isinstance(body, dict):
        for key, value in body.items():
            if isinstance(value, (dict, list)):
                yield "heading", str(key).replace("_", " ").capitalize()
                yield from _generic_blocks(value)
            else:
                yield "field", (str(key).replace("_", " ").capitalize(), _display(value))
    elif isinstance(body, list):
        yield _bounded_note(len(body), DISPLAY_LIMIT)
        for row in body[:DISPLAY_LIMIT]:
            yield from _generic_blocks(row)
    else:
        yield "paragraph", _display(body)


def _section_blocks(title, body):
    """Presentation model shared by HTML/PDF. Never mutates/truncates snapshot."""
    if isinstance(body, str):
        yield "paragraph", body
        return
    if title in (SECTIONS[1], SECTIONS[8]) and isinstance(body, list):
        yield (
            "note",
            "1P / 5P / 21P are observation-period price changes, not total returns. Negative values identify losers. Source cadence and dates can differ; rows with unavailable returns are not gainers.",
        )
        known = sorted(
            (r for r in body if r.get("week_pct") is not None), key=lambda r: r["week_pct"], reverse=True
        )
        unknown = [r for r in body if r.get("week_pct") is None]
        displayed = (
            known + unknown[: max(0, DISPLAY_LIMIT - len(known))]
            if len(known) <= DISPLAY_LIMIT
            else known[: DISPLAY_LIMIT // 2] + known[-DISPLAY_LIMIT // 2 :]
        )
        yield _bounded_note(len(body), DISPLAY_LIMIT, "assets")
        yield (
            "note",
            "Larger universes show up to 10 leaders and 10 laggards ranked by known 5P returns. Unavailable returns fill remaining display slots and are never treated as zero.",
        )
        headers = ["Asset", "Close USD", "1P %", "5P %", "21P %", "Rel vol", "Price date"]
        rows = [
            [
                r.get("symbol"),
                _display(r.get("price")),
                _display(r.get("day_pct")),
                _display(r.get("week_pct")),
                _display(r.get("month_pct")),
                _display(r.get("relative_volume")),
                _display(r.get("bar_as_of")),
            ]
            for r in displayed
        ]
        yield "table", (headers, rows)
        pairs = {(r.get("price_source"), r.get("source")) for r in displayed}
        if len(pairs) == 1:
            price_source, metadata_source = next(iter(pairs))
            yield (
                "note",
                f"Displayed price source: {_display(price_source)}. Metadata source: {_display(metadata_source)}. URLs and retrieval times are listed in Sources and methodology.",
            )
        else:
            for r in displayed:
                yield (
                    "note",
                    f"{r['symbol']} | Price source: {_display(r.get('price_source'))}; metadata source: {_display(r.get('source'))}.",
                )
    elif title == SECTIONS[2] and isinstance(body, list):
        yield _bounded_note(len(body), DISPLAY_LIMIT, "category observations")
        yield (
            "table",
            (
                ["Technology category", "Asset", "5P change %"],
                [
                    [_display(r.get("category")), _display(r.get("symbol")), _display(r.get("week_pct"))]
                    for r in body[:DISPLAY_LIMIT]
                ],
            ),
        )
        yield (
            "note",
            "User-defined categories in a selected universe do not establish sector indices or sector outperformance.",
        )
    elif title == SECTIONS[3] and isinstance(body, list):
        yield (
            "paragraph",
            "Observed option activity does not establish trade intent, institutional identity or insider knowledge. Calls/puts may be hedges, spreads or closing transactions.",
        )
        yield _bounded_note(len(body), DISPLAY_LIMIT, "option observations")
        headers = [
            "Asset / type",
            "Observed",
            "Expiry / strike",
            "Record",
            "Trade premium USD",
            "Volume ratio",
        ]
        rows = []
        for r in body[:DISPLAY_LIMIT]:
            metrics = r.get("metrics", {})
            rows.append(
                [
                    f"{r.get('symbol', '')} / {r.get('option_type', '')}",
                    _display(r.get("date")),
                    f"{_display(r.get('expiry'))} / {_display(r.get('strike'))}",
                    _display(r.get("record_type")),
                    _display(metrics.get("estimated_trade_premium")),
                    _display(metrics.get("volume_ratio")),
                ]
            )
        yield "table", (headers, rows)
        for r in body[:DISPLAY_LIMIT]:
            metrics = r.get("metrics", {})
            yield (
                "field",
                (
                    f"{r.get('symbol')} evidence",
                    f"Size {_display(r.get('size'))}; observed price {_display(r.get('price'))}; multiplier {_display(r.get('multiplier'))}; volume {_display(r.get('volume'))}; open interest {_display(r.get('open_interest'))}; IV change {_display(metrics.get('iv_change_points'))} percentage points. Source: {_display(r.get('source'))}, retrieved {_display(r.get('fetched_at'))}.",
                ),
            )
            yield "link", ("Original option source", _display(r.get("source_url")))
        yield (
            "note",
            "Trade premium = actual observed size x price x multiplier. Aggregate volume x last price is never substituted. No comprehensive free trade-flow coverage or verified event-calendar linkage.",
        )
    elif title == SECTIONS[4] and isinstance(body, list):
        yield _bounded_note(len(body), DETAIL_LIMIT, "technical setup summaries")
        for r in body[:DETAIL_LIMIT]:
            yield "heading", r.get("symbol", "Asset")
            yield "paragraph", r.get("forecast", "Abstain: no validation evidence")
            patterns = r.get("patterns", [])
            yield _bounded_note(len(patterns), DETAIL_LIMIT, "exploratory geometric labels")
            for p in patterns[:DETAIL_LIMIT]:
                yield (
                    "field",
                    (
                        f"{p.get('name', 'Pattern')} / {p.get('direction', 'neutral')}",
                        _display(p.get("evidence")),
                    ),
                )
            yield (
                "note",
                "Validated forecast sample size: 0. Confidence unavailable. Geometry is not a guaranteed price direction.",
            )
    elif title == SECTIONS[5] and isinstance(body, list):
        yield (
            "paragraph",
            "Contract ceilings are potential limits, not guaranteed revenue. Obligations represent government commitments, not recognized company revenue. Award identities update instead of adding modifications; shared awards require separate verification.",
        )
        yield _bounded_note(len(body), DETAIL_LIMIT, "complete award summaries")
        fields = [
            ("Company", "company"),
            ("Stock ticker / research candidate", "ticker"),
            ("Award ID", "id"),
            ("Government", "government"),
            ("Country", "country"),
            ("Awarding agency", "agency"),
            ("Status", "status"),
            ("Purpose", "purpose"),
            ("Award date", "award_date"),
            ("Announcement date", "announcement_date"),
            ("Duration", "duration"),
            ("Potential ceiling USD", "ceiling"),
            ("Actually obligated USD", "obligated"),
            ("Technology", "technology"),
            ("Possible expansion (not funded unless stated)", "expansion"),
            ("Business implications / assumptions", "implications"),
            ("Risks", "risks"),
            ("Observation/value basis", "value_basis"),
            ("Source", "source"),
            ("Retrieved at", "fetched_at"),
        ]
        for r in body[:DETAIL_LIMIT]:
            yield "heading", f"{r.get('company', 'Company')} / {r.get('id', 'award')}"
            yield from _fields(r, fields)
            metrics = r.get("metrics", {})
            yield (
                "field",
                (
                    "Obligations / company revenue",
                    _display(metrics.get("obligated_to_revenue_pct"), percent=True),
                ),
            )
            yield (
                "field",
                (
                    "Obligations / market capitalization",
                    _display(metrics.get("obligated_to_market_cap_pct"), percent=True),
                ),
            )
            yield (
                "note",
                "Any mapped ticker is a candidate for further research only. Direct/subsidiary/subcontractor mapping and denominator dates/currency must be independently confirmed. No investment recommendation is established by an award alone.",
            )
            yield "link", ("Original award source", _display(r.get("source_url")))
    elif title in (SECTIONS[6], SECTIONS[7]) and isinstance(body, list):
        yield (
            "paragraph",
            "Authorized imported disclosures only. Statutory use restrictions apply; automated collection is disabled. Value ranges are not exact sizes. Ownership categories remain separate; no transaction-date copying is assumed.",
        )
        yield _bounded_note(len(body), DISPLAY_LIMIT, "disclosure observations")
        headers = ["Asset / owner", "Transaction", "Trade date", "Published", "Range USD"]
        yield (
            "table",
            (
                headers,
                [
                    [
                        f"{r.get('asset')} / {r.get('owner')}",
                        _display(r.get("transaction_type")),
                        _display(r.get("transaction_date")),
                        _display(r.get("publication_date")),
                        f"{_display(r.get('value_min'))} - {_display(r.get('value_max'))}",
                    ]
                    for r in body[:DISPLAY_LIMIT]
                ],
            ),
        )
        for r in body[:DISPLAY_LIMIT]:
            yield "link", (f"{r.get('id')} / {_display(r.get('source'))}", _display(r.get("source_url")))
    elif title == SECTIONS[9] and isinstance(body, list):
        yield (
            "paragraph",
            "Scores are configurable research priorities, not probabilities. Missing evidence earns no points; the system may recommend no investment. Current preview does not validate buy recommendations.",
        )
        yield _bounded_note(len(body), DETAIL_LIMIT, "ranked research theses")
        for r in body[:DETAIL_LIMIT]:
            yield "heading", f"{r.get('symbol')} / {_display(r.get('decision'))}"
            yield (
                "field",
                (
                    "Heuristic score /100; evidence coverage",
                    f"{_display(r.get('score'))}; {_display(100 * r.get('coverage', 0), percent=True)}",
                ),
            )
            for name, key in (
                ("Supporting evidence", "supporting"),
                ("Contradictory evidence", "contradictory"),
                ("Abstention reasons", "reasons"),
                ("Missing evidence", "missing"),
                ("Entry conditions", "entry_condition"),
                ("Investment horizon", "horizon"),
                ("Thesis invalidation", "invalidation"),
            ):
                yield "field", (name, _display(r.get(key)))
            for scenario, text in r.get("scenarios", {}).items():
                yield "field", (scenario.capitalize() + " scenario", _display(text))
            components, weights = r.get("components", {}), r.get("weights", {})
            yield (
                "table",
                (
                    ["Evidence component", "Observed /100", "Weight %"],
                    [
                        [key.capitalize(), _display(value), _display(weights.get(key))]
                        for key, value in components.items()
                    ],
                ),
            )
            yield "link", ("Asset metadata source", _display(r.get("source_url")))
    elif title == SECTIONS[12] and isinstance(body, dict):
        yield "paragraph", body.get("evaluation", "Recommendation performance unavailable")
        ledger = body.get("paper_ledger", [])
        yield _bounded_note(len(ledger), DISPLAY_LIMIT, "manual ledger entries")
        yield (
            "table",
            (
                ["Date", "Asset", "Side", "Quantity", "Price USD", "Fee USD"],
                [
                    [_display(r.get(k)) for k in ("date", "symbol", "side", "quantity", "price", "fee")]
                    for r in ledger[:DISPLAY_LIMIT]
                ],
            ),
        )
    elif title == SECTIONS[13] and isinstance(body, dict):
        yield "paragraph", body.get("methodology", "Methodology unavailable")
        yield "paragraph", body.get("scope", "Scope unavailable")
        sources = body.get("sources", [])
        yield _bounded_note(len(sources), DISPLAY_LIMIT, "asset source summaries")
        catalog: dict[tuple[str, str], str] = {}

        def source_id(name, url):
            key = (_display(name), _display(url))
            if key not in catalog:
                catalog[key] = f"S{len(catalog) + 1}"
            return catalog[key]

        rows = []
        for r in sources[:DISPLAY_LIMIT]:
            price = source_id(r.get("price_source"), r.get("price_source_url"))
            metadata = source_id(r.get("metadata_source"), r.get("source_url"))
            history = [source_id(pair[0], pair[1]) for pair in r.get("price_sources", []) if len(pair) == 2]
            rows.append(
                [
                    _display(r.get("symbol")),
                    _display(r.get("bar_as_of")),
                    price + (" / history " + ",".join(history) if history else ""),
                    metadata,
                    _display(r.get("price_fetched_at")),
                    _display(r.get("fetched_at")),
                ]
            )
        yield (
            "table",
            (
                [
                    "Asset",
                    "Price date",
                    "Price / history sources",
                    "Metadata source",
                    "Price retrieved UTC",
                    "Metadata retrieved UTC",
                ],
                rows,
            ),
        )
        yield (
            "note",
            "Price dates and retrieval timestamps are different. History references identify all sources represented across retained bars; a mixed-source history may not have consistent coverage or corporate-action adjustment.",
        )
        for (name, url), reference in catalog.items():
            yield "link", (f"{reference} / {name}", url)
    else:
        yield from _generic_blocks(body)


def csv_text(report):
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["workspace", "created_at", "section", "observation_json"])
    for section, body in report["sections"].items():
        rows = body if isinstance(body, list) else [body]
        for row in rows:
            fields = [report["workspace"], report["created_at"], section, json.dumps(row, ensure_ascii=False)]
            # Spreadsheet formula protection for user-controlled scalar fields.
            writer.writerow(["'" + s if s.lstrip().startswith(("=", "+", "-", "@")) else s for s in fields])
    return output.getvalue()


def export_report(report, path):
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".json":
        path.write_text(json_text(report), encoding="utf-8")
    elif suffix == ".html":
        path.write_text(html_text(report), encoding="utf-8")
    elif suffix == ".csv":
        path.write_text(csv_text(report), encoding="utf-8-sig", newline="")
    elif suffix == ".pdf":
        _export_pdf(report, path)
    else:
        raise ValueError("Choose .pdf, .html, .csv or .json")


def _pdf_text(value):
    """Portable ASCII fallback; exact Unicode remains in HTML/JSON exports.

    Standard PDF fonts do not cover arbitrary imported scripts. Transliterate
    accents and common punctuation; show unsupported code points explicitly
    rather than silently producing missing-glyph squares or dropping content.
    """
    mapped = str(value)
    for original, replacement in {
        "·": "|",
        "×": "x",
        "−": "-",
        "–": "-",
        "—": "-",
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "…": "...",
        "•": "-",
    }.items():
        mapped = mapped.replace(original, replacement)
    result = []
    for character in mapped:
        if ord(character) < 128:
            result.append(character)
            continue
        simple = unicodedata.normalize("NFKD", character).encode("ascii", "ignore").decode()
        result.append(simple if simple else f"[U+{ord(character):04X}]")
    return "".join(result)


def _export_pdf(report, path):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle

    ink, teal = colors.HexColor("#213348"), colors.HexColor("#087c78")
    styles = {
        "body": ParagraphStyle(
            "Body",
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=ink,
            spaceAfter=5,
            splitLongWords=True,
        ),
        "note": ParagraphStyle(
            "Note",
            fontName="Helvetica",
            fontSize=7.5,
            leading=10.5,
            textColor=colors.HexColor("#53677b"),
            spaceAfter=6,
            splitLongWords=True,
        ),
        "title": ParagraphStyle(
            "Title", fontName="Helvetica-Bold", fontSize=23, leading=28, textColor=teal, spaceAfter=10
        ),
        "section": ParagraphStyle(
            "Section",
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=18,
            textColor=teal,
            spaceBefore=16,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "heading": ParagraphStyle(
            "Record heading",
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=ink,
            spaceBefore=10,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "cell": ParagraphStyle(
            "Cell", fontName="Helvetica", fontSize=7.3, leading=10, textColor=ink, splitLongWords=True
        ),
        "headcell": ParagraphStyle(
            "Header cell",
            fontName="Helvetica-Bold",
            fontSize=7.2,
            leading=10,
            textColor=teal,
            splitLongWords=True,
        ),
    }

    def para(text, style="body", prefix=None):
        content = html.escape(_pdf_text(text))
        if prefix is not None:
            content = "<b>" + html.escape(_pdf_text(prefix)) + ":</b> " + content
        return Paragraph(content, styles[style])

    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        rightMargin=44,
        leftMargin=44,
        topMargin=48,
        bottomMargin=48,
        title=_pdf_text(report["title"]),
        author="TechPulse",
    )
    story = [
        para("TECHPULSE / WEEKLY INTELLIGENCE", "note"),
        para(report["title"], "title"),
        para(report["warning"], "heading"),
        para(f"Generated {report['created_at']} | Workspace: {report['workspace']}", "note"),
        para(
            "Research preview. Stored observations only; no live refresh, guaranteed forecast or personalized investment advice. Monetary amounts are USD.",
            "note",
        ),
        para(
            "Portable PDF typography transliterates accents and renders unsupported glyphs as [U+XXXX]. HTML/JSON preserve original Unicode text.",
            "note",
        ),
        Spacer(1, 4),
    ]
    for title, body in report["sections"].items():
        story.append(para(title, "section"))
        for kind, content in _section_blocks(title, body):
            if kind == "table":
                headers, rows = content
                if not rows:
                    story.append(para("No observations retained for this section.", "note"))
                    continue
                data = [[para(v, "headcell") for v in headers]]
                data.extend([[para(v, "cell") for v in row] for row in rows])
                grid = LongTable(
                    data,
                    colWidths=[doc.width / len(headers)] * len(headers),
                    repeatRows=1,
                    splitByRow=1,
                    splitInRow=1,
                    hAlign="LEFT",
                )
                grid.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f3f2")),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f8fb")]),
                            ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#acc9c6")),
                            ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.HexColor("#dfe7ee")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 6),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                            ("TOPPADDING", (0, 0), (-1, -1), 6),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ]
                    )
                )
                story.extend([grid, Spacer(1, 7)])
            elif kind == "field":
                name, value = content
                story.append(para(value, prefix=name))
            elif kind == "link":
                name, value = content
                story.append(para(value, "note", prefix=name))
            else:
                story.append(
                    para(content, "heading" if kind == "heading" else "note" if kind == "note" else "body")
                )

    def footer(canvas, document):
        width, height = document.pagesize
        canvas.setStrokeColor(colors.HexColor("#d9e2ea"))
        canvas.line(44, 37, width - 44, 37)
        canvas.setFillColor(colors.HexColor("#53677b"))
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(44, height - 28, "TECHPULSE | EVIDENCE BEFORE CONVICTION")
        canvas.drawString(44, 25, "General research | " + _pdf_text(report["workspace"]))
        canvas.drawRightString(width - 44, 25, "Page " + str(document.page))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
