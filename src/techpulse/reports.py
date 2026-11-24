"""Local report snapshots with safe HTML, CSV and PDF serialization."""

import csv
import html
import io
import json
from pathlib import Path

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
    options = store.records(mode, "options")
    contracts = store.records(mode, "contracts")
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
        SECTIONS[1]: sorted(equities, key=lambda x: x.get("week_pct") or 0, reverse=True),
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
    chunks = [
        "<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>TechPulse intelligence</title><style>body{font:15px/1.6 system-ui;background:#f4f6fa;color:#16243a;max-width:1000px;margin:40px auto;padding:24px}h1{color:#087c78}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:white;padding:20px;border:1px solid #dce3ed;border-radius:8px}aside{border-left:4px solid #c48a21;padding:12px;background:#fff4d8}</style>",
        f"<h1>{html.escape(report['title'])}</h1><aside>{html.escape(report['warning'])}</aside><p>Generated {html.escape(report['created_at'])}</p>",
    ]
    for title, body in report["sections"].items():
        chunks.append(
            f"<h2>{html.escape(title)}</h2><pre>{html.escape(json.dumps(body, ensure_ascii=False, indent=2))}</pre>"
        )
    return "".join(chunks) + "</html>"


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
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

        styles = getSampleStyleSheet()
        styles.add(
            ParagraphStyle(
                name="Record",
                fontName="Helvetica",
                fontSize=8,
                leading=12,
                alignment=TA_LEFT,
                spaceAfter=8,
                wordWrap="CJK",
            )
        )
        doc = SimpleDocTemplate(
            str(path), rightMargin=48, leftMargin=48, topMargin=48, bottomMargin=48, title=report["title"]
        )
        story = [
            Paragraph(html.escape(report["title"]), styles["Title"]),
            Paragraph(html.escape(report["warning"]), styles["Normal"]),
            Paragraph(html.escape(report["created_at"]), styles["Normal"]),
            Spacer(1, 0.2 * inch),
        ]
        for section, body in report["sections"].items():
            story.append(Paragraph(html.escape(section), styles["Heading2"]))
            rows = body if isinstance(body, list) else [body]
            for row in rows:
                # Split records into bounded paragraphs so one oversized record can flow over pages.
                text = json.dumps(row, ensure_ascii=True, indent=2)
                for line in text.splitlines():
                    story.append(Paragraph(html.escape(line), styles["Record"]))

        def footer(canvas, document):
            canvas.setFillColor(colors.HexColor("#526277"))
            canvas.setFont("Helvetica", 8)
            canvas.drawString(48, 26, "TechPulse | General research | " + report["workspace"])
            canvas.drawRightString(document.pagesize[0] - 48, 26, str(document.page))

        doc.build(story, onFirstPage=footer, onLaterPages=footer)
    else:
        raise ValueError("Choose .pdf, .html, .csv or .json")
