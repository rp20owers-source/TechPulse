import copy

import httpx
import pytest

from techpulse.providers import ProviderError, _RateGate
from techpulse.sec import SECProvider, cik_value, normalize_company_facts


def fact(value, *, start="2024-01-01", end="2024-12-31", filed="2025-02-01", accn="0000000001-25-000001"):
    return {"val": value, "start": start, "end": end, "filed": filed, "accn": accn, "form": "10-K"}


def payload():
    return {
        "cik": 1,
        "entityName": "Fictional SEC fixture",
        "facts": {
            "us-gaap": {
                "Revenues": {"units": {"USD": [fact(120), fact(100, start="2023-01-01", end="2023-12-31")]}},
                "NetIncomeLoss": {"units": {"USD": [fact(12)]}},
                "NetCashProvidedByUsedInOperatingActivities": {"units": {"USD": [fact(30)]}},
                "PaymentsToAcquirePropertyPlantAndEquipment": {"units": {"USD": [fact(6)]}},
            }
        },
    }


def test_annual_metrics_formulas_and_accession_provenance():
    r = normalize_company_facts(payload(), "2025-03-01")
    assert r["net_margin_pct"] == 10
    assert r["free_cash_flow_usd"] == 24 and r["fcf_margin_pct"] == 20
    assert r["revenue_growth_pct"] == pytest.approx(20)
    assert "000000000125000001" in r["metrics"]["revenue"]["source_url"]
    assert r["metrics"]["revenue"]["unit"] == "USD"


def test_cutoff_excludes_same_day_and_later_restatement():
    data = payload()
    data["facts"]["us-gaap"]["Revenues"]["units"]["USD"].append(
        fact(500, filed="2025-04-01", accn="0000000001-25-000002")
    )
    assert normalize_company_facts(data, "2025-02-01")["metrics"]["revenue"] is None
    assert normalize_company_facts(data, "2025-03-01")["metrics"]["revenue"]["value"] == 120
    amended = normalize_company_facts(data, "2025-04-02")
    assert amended["metrics"]["revenue"]["value"] == 500
    assert amended["net_margin_pct"] is None  # Never combine unmatched accessions.


@pytest.mark.parametrize(
    "change",
    [
        {"val": float("nan")},
        {"val": True},
        {"val": float("inf")},
        {"start": "2024-10-01"},
        {"form": "10-Q"},
        {"accn": "bad"},
    ],
)
def test_invalid_or_nonannual_facts_unavailable(change):
    data = payload()
    row = fact(12) | change
    data["facts"]["us-gaap"]["NetIncomeLoss"]["units"]["USD"] = [row]
    assert normalize_company_facts(data, "2025-03-01")["net_margin_pct"] is None


def test_currency_zero_denominator_and_conflicts():
    data = payload()
    rev = data["facts"]["us-gaap"]["Revenues"]["units"]
    rev["EUR"] = rev.pop("USD")
    assert normalize_company_facts(data, "2025-03-01")["metrics"]["revenue"] is None
    rev["USD"] = [fact(0)]
    assert normalize_company_facts(data, "2025-03-01")["net_margin_pct"] is None
    rev["USD"] = [fact(120), fact(125)]
    assert normalize_company_facts(data, "2025-03-01")["metrics"]["revenue"] is None
    rev["USD"] = [fact(120), fact(120, start="2023-12-31")]
    assert normalize_company_facts(data, "2025-03-01")["metrics"]["revenue"] is None


def test_schema_and_cik_validation_without_mutating_inputs():
    for invalid in ("", "0", "../123", "1?x=1", "12345678901"):
        with pytest.raises(ValueError):
            cik_value(invalid)
    with pytest.raises(ValueError):
        normalize_company_facts({})
    data = payload()
    original = copy.deepcopy(data)
    normalize_company_facts(data, "2025-03-01")
    assert data == original


def test_provider_identity_headers_and_requested_cik(monkeypatch):
    monkeypatch.setattr(_RateGate, "wait", lambda *a: None)

    def handler(request):
        assert request.url.host == "data.sec.gov"
        assert request.url.path in {
            "/api/xbrl/companyfacts/CIK0000000001.json",
            "/api/xbrl/companyfacts/CIK0000000002.json",
        }
        assert request.headers["User-Agent"] == "Test test@example.invalid"
        return httpx.Response(200, json=payload())

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        r = SECProvider("Test test@example.invalid", client=client).annual_fundamentals("1", "2025-03-01")
        assert r[0]["cik"] == "0000000001"
        with pytest.raises(ProviderError, match="does not match"):
            SECProvider("Test test@example.invalid", client=client).annual_fundamentals("2")
    with pytest.raises(ProviderError):
        SECProvider("no contact provided")


def test_exact_ticker_resolution_shares_budget_and_retains_mapping(monkeypatch):
    monkeypatch.setattr(_RateGate, "wait", lambda *a: None)
    calls = []

    def handler(request):
        calls.append(request)
        if request.url.host == "www.sec.gov":
            assert request.url.path == "/files/company_tickers.json"
            return httpx.Response(
                200, json={"0": {"ticker": "TEST-A", "cik_str": 1, "title": "Fictional company"}}
            )
        assert request.url.host == "data.sec.gov"
        assert request.url.path.endswith("CIK0000000001.json")
        return httpx.Response(200, json=payload())

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        provider = SECProvider("Test test@example.invalid", client=client)
        rows = provider.fundamentals_for(" test-a ", "2025-03-01")
        assert rows[0]["symbol"] == "TEST-A" and rows[0]["cik"] == "0000000001"
        assert rows[0]["lookup_scope"].startswith("Current SEC directory")
        assert len(calls) == 2
        assert all(r.headers["user-agent"] == "Test test@example.invalid" for r in calls)
        assert calls[1].extensions["timeout"]["read"] <= calls[0].extensions["timeout"]["read"]
        calls.clear()
        provider.fundamentals_for("1", "2025-03-01")
        assert len(calls) == 1  # Numeric CIK avoids directory lookup.
        for bad in ("", "../TEST", "TEST?token=x"):
            with pytest.raises(ValueError):
                provider.fundamentals_for(bad)
        assert len(calls) == 1


@pytest.mark.parametrize(
    "directory",
    [
        [],
        {},
        {"0": {"ticker": "TEST", "cik_str": "bad"}},
        {"0": {"ticker": "TEST", "cik_str": 1}, "1": {"ticker": "TEST", "cik_str": 2}},
    ],
)
def test_bad_or_ambiguous_ticker_mapping_never_requests_facts(monkeypatch, directory):
    monkeypatch.setattr(_RateGate, "wait", lambda *a: None)
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=directory)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ProviderError):
            SECProvider("Test test@example.invalid", client=client).fundamentals_for("TEST")
    assert len(calls) == 1 and calls[0].url.host == "www.sec.gov"


@pytest.mark.parametrize("revenue", [None, 0])
def test_cash_flow_amount_does_not_require_revenue(revenue):
    data = payload()
    if revenue is None:
        del data["facts"]["us-gaap"]["Revenues"]
    else:
        data["facts"]["us-gaap"]["Revenues"]["units"]["USD"] = [fact(revenue)]
    result = normalize_company_facts(data, "2025-03-01")
    assert result["free_cash_flow_usd"] == 24
    assert result["free_cash_flow_period_end"] == "2024-12-31"
    assert result["fcf_margin_pct"] is None


def test_mismatched_cash_flow_accessions_withhold_amount():
    data = payload()
    data["facts"]["us-gaap"]["PaymentsToAcquirePropertyPlantAndEquipment"]["units"]["USD"] = [
        fact(6, accn="0000000001-25-000002")
    ]
    result = normalize_company_facts(data, "2025-03-01")
    assert result["free_cash_flow_usd"] is None and result["fcf_margin_pct"] is None
