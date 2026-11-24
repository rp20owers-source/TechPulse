"""Conservative annual SEC facts: filing-date cutoff, explicit units and provenance.

Companyfacts is a current aggregate, not a guaranteed historical database.
Date-only filed metadata is usable only strictly before the chosen cutoff.
No scoring, valuation or ticker mapping is inferred from this module.
"""

from __future__ import annotations

import math
import re
from datetime import date
from typing import Any

import httpx

from .providers import ProviderError, _HTTPProvider, _now

CONCEPTS = {
    "revenue": (
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ),
    "net_income": ("NetIncomeLoss",),
    "operating_cash_flow": ("NetCashProvidedByUsedInOperatingActivities",),
    "capital_expenditure": ("PaymentsToAcquirePropertyPlantAndEquipment",),
}


def cik_value(raw) -> str:
    text = str(raw).strip()
    if not re.fullmatch(r"[0-9]{1,10}", text) or int(text) == 0:
        raise ValueError("CIK must be a positive 1–10 digit SEC identifier")
    return text.zfill(10)


def normalize_company_facts(payload: dict, as_of: str | None = None) -> dict:
    if not isinstance(payload, dict) or not isinstance(payload.get("facts"), dict):
        raise ValueError("Expected an SEC companyfacts JSON object")
    cik = cik_value(payload.get("cik", ""))
    cutoff = date.fromisoformat(as_of) if as_of else date.today()
    if cutoff > date.today():
        raise ValueError("Filing cutoff cannot be in the future")
    gaap = payload["facts"].get("us-gaap", {})
    if not isinstance(gaap, dict):
        raise ValueError("Invalid us-gaap facts object")
    metrics: dict[str, Any] = {}
    histories: dict[str, list[dict]] = {}
    warnings: list[str] = []
    for metric, tags in CONCEPTS.items():
        candidates = []
        for priority, tag in enumerate(tags):
            concept = gaap.get(tag, {})
            if not isinstance(concept, dict):
                continue
            units = concept.get("units", {})
            if not isinstance(units, dict) or not isinstance(units.get("USD", []), list):
                continue
            for row in units.get("USD", []):
                if not isinstance(row, dict) or row.get("form") not in {"10-K", "10-K/A"}:
                    continue
                try:
                    start, end, filed = (date.fromisoformat(row[k]) for k in ("start", "end", "filed"))
                    value = float(row["val"])
                    accession = row["accn"]
                    if isinstance(row["val"], bool) or not math.isfinite(value):
                        continue
                    if not isinstance(accession, str) or not re.fullmatch(r"\d{10}-\d{2}-\d{6}", accession):
                        continue
                    if not 330 <= (end - start).days <= 400 or not end <= filed < cutoff:
                        continue
                    if metric in {"revenue", "capital_expenditure"} and value < 0:
                        continue
                except (ValueError, KeyError, TypeError, OverflowError):
                    continue
                candidates.append(
                    {
                        "value": value,
                        "unit": "USD",
                        "concept": tag,
                        "period_start": start.isoformat(),
                        "period_end": end.isoformat(),
                        "filed": filed.isoformat(),
                        "accession": accession,
                        "form": row["form"],
                        "source_url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/",
                        "priority": priority,
                    }
                )
        histories[metric] = candidates
        if not candidates:
            metrics[metric] = None
            warnings.append(f"{metric}: no eligible annual USD fact before cutoff")
            continue
        # Latest period, then latest eligible filing, then declared tag preference.
        best = max(candidates, key=lambda r: (r["period_end"], r["filed"], -r["priority"]))
        peers = [
            r
            for r in candidates
            if (r["period_end"], r["filed"], r["priority"])
            == (best["period_end"], best["filed"], best["priority"])
        ]
        if len({(r["value"], r["accession"], r["period_start"]) for r in peers}) != 1:
            metrics[metric] = None
            warnings.append(f"{metric}: conflicting facts; value withheld")
        else:
            metrics[metric] = {k: v for k, v in best.items() if k != "priority"}

    def aligned(*names):
        selected = [metrics[n] for n in names]
        return (
            all(selected)
            and len({(r["period_start"], r["period_end"], r["accession"]) for r in selected}) == 1
        )

    revenue = metrics["revenue"]
    margin = fcf = fcf_margin = growth = None
    if revenue and revenue["value"] > 0:
        if aligned("revenue", "net_income"):
            margin = 100 * metrics["net_income"]["value"] / revenue["value"]
        if aligned("revenue", "operating_cash_flow", "capital_expenditure"):
            fcf = metrics["operating_cash_flow"]["value"] - metrics["capital_expenditure"]["value"]
            fcf_margin = 100 * fcf / revenue["value"]
        prior = [
            r
            for r in histories["revenue"]
            if r["accession"] == revenue["accession"]
            and r["concept"] == revenue["concept"]
            and 330
            <= (date.fromisoformat(revenue["period_end"]) - date.fromisoformat(r["period_end"])).days
            <= 400
            and 330
            <= (date.fromisoformat(revenue["period_start"]) - date.fromisoformat(r["period_start"])).days
            <= 400
        ]
        # Multiple distinct comparable periods/values are ambiguous, not averaged.
        comparable = {(r["period_start"], r["period_end"], r["value"]) for r in prior}
        if len(comparable) == 1 and prior[0]["value"] > 0:
            growth = 100 * (revenue["value"] / prior[0]["value"] - 1)
    if any(metrics.values()) and (margin is None or fcf is None):
        warnings.append("Some ratios withheld: missing facts, zero revenue or unmatched period/accession")
    derived = [margin, fcf, fcf_margin, growth]
    if any(v is not None and not math.isfinite(v) for v in derived):
        warnings.append("Nonfinite derived ratios withheld")
    margin, fcf, fcf_margin, growth = [v if v is None or math.isfinite(v) else None for v in derived]
    return {
        "symbol": "CIK" + cik,
        "cik": cik,
        "name": str(payload.get("entityName", "Unknown filer"))[:500],
        "as_of": cutoff.isoformat(),
        "source": "SEC EDGAR companyfacts",
        "source_url": f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
        "fetched_at": _now(),
        "coverage": "Annual US-GAAP USD facts only; filing-date-filtered current aggregate; not a historical archive",
        "metrics": metrics,
        "net_margin_pct": margin,
        "free_cash_flow_usd": fcf,
        "fcf_margin_pct": fcf_margin,
        "revenue_growth_pct": growth,
        "warnings": warnings,
        "methodology": "Filed dates strictly precede cutoff. Ratios require identical periods/accession. Free cash flow = operating cash flow minus reported PP&E acquisition payments; excludes other capitalized investment. No valuation or investment score inferred.",
    }


class SECProvider(_HTTPProvider):
    name = "SEC EDGAR"
    base_url = "https://data.sec.gov"
    interval = 1.0  # conservative process-local 1/sec, below SEC fair-access ceiling

    def __init__(self, user_agent: str, *, client: httpx.Client | None = None):
        if (
            not isinstance(user_agent, str)
            or not re.search(r"[^\s@]+@[^\s@]+\.[^\s@]+", user_agent)
            or any(c in user_agent for c in "\r\n")
        ):
            raise ProviderError("Set SEC_USER_AGENT to your application name and real contact email")
        super().__init__(client=client)
        self._headers = {"User-Agent": user_agent.strip()}

    def annual_fundamentals(self, cik, as_of=None):
        expected = cik_value(cik)
        payload = self._request("GET", f"/api/xbrl/companyfacts/CIK{expected}.json", headers=self._headers)
        try:
            result = normalize_company_facts(payload, as_of)
        except (ValueError, TypeError) as exc:
            raise ProviderError("SEC response could not be normalized; no data substituted") from exc
        if result["cik"] != expected:
            raise ProviderError("SEC response CIK does not match the requested company")
        return [result]
