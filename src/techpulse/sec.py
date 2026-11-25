"""Conservative annual SEC facts: filing-date cutoff, explicit units and provenance.

Companyfacts is a current aggregate, not a guaranteed historical database.
Date-only filed metadata is usable only strictly before the chosen cutoff.
No scoring, valuation or ticker mapping is inferred from this module.
"""

from __future__ import annotations

import math
import re
import time
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


def declared_user_agent(value: str) -> str:
    """Validate a header without opening a client, saving it or echoing its value."""
    if (
        not isinstance(value, str)
        or not value.isascii()
        or not value.isprintable()
        or len(value) > 256
        or not re.search(r"[^\s@]+@[^\s@]+\.[^\s@]+", value)
    ):
        raise ProviderError(
            "Enter an application name and real contact email using printable ASCII (maximum 256 characters)"
        )
    return value.strip()


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
    if aligned("operating_cash_flow", "capital_expenditure"):
        fcf = metrics["operating_cash_flow"]["value"] - metrics["capital_expenditure"]["value"]
    if revenue and revenue["value"] > 0:
        if aligned("revenue", "net_income"):
            margin = 100 * metrics["net_income"]["value"] / revenue["value"]
        if fcf is not None and aligned("revenue", "operating_cash_flow", "capital_expenditure"):
            fcf_margin = 100 * fcf / revenue["value"]
    if revenue:
        prior = [
            r
            for r in histories["revenue"]
            if r["accession"] == revenue["accession"]
            and r["concept"] == revenue["concept"]
            and r["period_end"] < revenue["period_start"]
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
        "free_cash_flow_period_end": metrics["operating_cash_flow"]["period_end"]
        if fcf is not None
        else None,
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
        contact = declared_user_agent(user_agent)
        super().__init__(client=client)
        self._headers = {"User-Agent": contact}

    def fundamentals_for(self, identifier, as_of=None):
        """Resolve an exact current ticker or numeric CIK, within one operation budget."""
        raw = str(identifier).strip().upper()
        if not raw:
            raise ValueError("Enter an exact ticker or numeric CIK")
        cutoff = date.fromisoformat(as_of) if as_of else date.today()
        if cutoff > date.today():
            raise ValueError("Filing cutoff cannot be in the future")
        deadline = time.monotonic() + self.operation_budget
        mapping = None
        if re.fullmatch(r"[0-9]+", raw):
            cik = cik_value(raw)
        else:
            if not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,14}", raw):
                raise ValueError("Use an exact ticker with letters, digits, dots or hyphens")
            directory = _SECCompanyDirectory(client=self._client)
            data = directory._request(
                "GET", "/files/company_tickers.json", headers=self._headers, deadline=deadline
            )
            if not isinstance(data, dict):
                raise ProviderError("SEC ticker directory has an unsupported format")
            matches = {}
            for row in data.values():
                if not isinstance(row, dict) or row.get("ticker") != raw:
                    continue
                try:
                    mapped_cik = cik_value(row.get("cik_str", ""))
                except ValueError as exc:
                    raise ProviderError("SEC ticker mapping has an invalid CIK") from exc
                matches[mapped_cik] = row
            if len(matches) != 1:
                raise ProviderError(
                    "SEC ticker mapping is missing or ambiguous; enter the verified numeric CIK instead"
                )
            cik, mapping = next(iter(matches.items()))
        result = self.annual_fundamentals(cik, cutoff.isoformat(), _deadline=deadline)
        if mapping is not None:
            result[0].update(
                symbol=raw,
                lookup_ticker=raw,
                lookup_company_name=str(mapping.get("title", ""))[:500],
                lookup_source_url="https://www.sec.gov/files/company_tickers.json",
                lookup_scope="Current SEC directory association, not a historical mapping; verify company identity",
            )
        return result

    def annual_fundamentals(self, cik, as_of=None, *, _deadline=None):
        expected = cik_value(cik)
        cutoff = date.fromisoformat(as_of) if as_of else date.today()
        if cutoff > date.today():
            raise ValueError("Filing cutoff cannot be in the future")
        payload = self._request(
            "GET", f"/api/xbrl/companyfacts/CIK{expected}.json", headers=self._headers, deadline=_deadline
        )
        try:
            result = normalize_company_facts(payload, cutoff.isoformat())
        except (ValueError, TypeError) as exc:
            raise ProviderError("SEC response could not be normalized; no data substituted") from exc
        if result["cik"] != expected:
            raise ProviderError("SEC response CIK does not match the requested company")
        return [result]


class _SECCompanyDirectory(_HTTPProvider):
    name = "SEC company directory"
    base_url = "https://www.sec.gov"
    interval = 1.0
