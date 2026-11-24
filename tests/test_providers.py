"""Synthetic protocol fixtures only, not downloaded/restricted market data."""

import json

import httpx
import pytest

from techpulse.providers import (
    AlpacaProvider,
    CoinGeckoProvider,
    ProviderError,
    USAspendingProvider,
    _RateGate,
)


@pytest.fixture(autouse=True)
def no_network_or_waits(monkeypatch):
    monkeypatch.setattr(_RateGate, "wait", lambda *args: None)
    monkeypatch.setattr("techpulse.providers.time.sleep", lambda _: None)


def client_for(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_crypto_snapshot_nulls_provenance_and_key_header():
    def handler(request):
        assert request.url.host == "api.coingecko.com"
        assert request.headers["x-cg-demo-api-key"] == "fake-test-key"
        assert "fake-test-key" not in str(request.url)
        assert request.url.params["page"] == "1"
        assert request.url.params["per_page"] == "100"
        return httpx.Response(200, json=[{"id": "fictional-token", "symbol": "fct", "name": "Fictional Token",
                                       "current_price": 10.0, "market_cap": 1000,
                                       "price_change_percentage_24h": -2.5}])
    with client_for(handler) as client:
        record = CoinGeckoProvider("fake-test-key", client=client).markets()[0]
    assert record["price"] == 10
    assert record["day_pct"] == -2.5
    assert record["week_pct"] is None
    assert record["category"] == "Unclassified"
    assert record["volume"] is None
    assert record["redistributable"] is False
    assert "Top 100" in record["coverage"]
    assert record["fetched_at"]


@pytest.mark.parametrize("payload", [{"error": "denied"}, [{"id": "f", "current_price": "NaN"}],
                                     [{"id": "f", "current_price": -1}], [{"id": "f"}, {"id": "f"}],
                                     [{"symbol": "NO_ID"}]])
def test_invalid_crypto_response_rejected(payload):
    with client_for(lambda _: httpx.Response(200, json=payload)) as client:
        with pytest.raises(ProviderError):
            CoinGeckoProvider("fake", client=client).markets()


def test_no_credentials_no_network():
    with pytest.raises(ProviderError):
        CoinGeckoProvider("")
    with pytest.raises(ProviderError):
        AlpacaProvider("", "")


def bar(day="2026-01-02"):
    return {"t": day + "T05:00:00Z", "o": 10, "h": 12, "l": 9, "c": 11, "v": 1200}


def test_alpaca_multiple_symbols_are_paginated_and_feed_explicit():
    requests = []
    def handler(request):
        requests.append(request)
        assert request.headers["APCA-API-KEY-ID"] == "fake-key"
        assert request.url.params["feed"] == "iex"
        assert request.url.params["adjustment"] == "all"
        assert request.url.params["end"] == "2026-01-05T23:59:59Z"
        if "page_token" not in request.url.params:
            return httpx.Response(200, json={"bars": {"FICT": [bar()]}, "next_page_token": "second"})
        assert request.url.params["page_token"] == "second"
        return httpx.Response(200, json={"bars": {"SYNTH": [bar("2026-01-05")]}, "next_page_token": None})
    with client_for(handler) as client:
        data = AlpacaProvider("fake-key", "fake-secret", client=client).daily_bars(
            ["FICT", "SYNTH"], "2026-01-01", "2026-01-05")
    assert len(requests) == 2
    assert data["FICT"][0]["close"] == 11
    assert data["SYNTH"][0]["date"] == "2026-01-05"
    assert data["FICT"][0]["redistributable"] is False
    assert "not consolidated" in data["FICT"][0]["coverage"]


@pytest.mark.parametrize("symbols,start,end", [([], "2026-01-01", "2026-02-01"),
    (["FICT", "FICT"], "2026-01-01", "2026-02-01"), (["bad/url"], "2026-01-01", "2026-02-01"),
    (["FICT"], "20260101", "2026-02-01"), (["FICT"], "2026-02-01", "2026-01-01")])
def test_alpaca_input_validation(symbols, start, end):
    with client_for(lambda _: pytest.fail("No network expected")) as client:
        with pytest.raises(ValueError):
            AlpacaProvider("fake", "fake", client=client).daily_bars(symbols, start, end)


def test_alpaca_page_budget_never_returns_silently_partial_history():
    with client_for(lambda _: httpx.Response(200, json={"bars": {"FICT": [bar()]}, "next_page_token": "more"})) as client:
        with pytest.raises(ProviderError, match="No partial history"):
            AlpacaProvider("fake", "fake", client=client, max_pages=1).daily_bars(
                ["FICT"], "2026-01-01", "2026-01-10")


@pytest.mark.parametrize("rows", [[bar(), bar()], [{**bar(), "h": 8}], [{**bar(), "v": -5}],
                                [{**bar(), "c": None}], [bar("2025-01-01")],
                                [{**bar(), "t": "2026-01-02T05:00:00"}]])
def test_alpaca_bad_bars_rejected(rows):
    with client_for(lambda _: httpx.Response(200, json={"bars": {"FICT": rows}})) as client:
        with pytest.raises(ProviderError):
            AlpacaProvider("fake", "fake", client=client).daily_bars(["FICT"], "2026-01-01", "2026-01-10")


def test_usaspending_cumulative_obligations_no_ceiling_no_ticker_guess():
    def handler(request):
        assert request.method == "POST"
        payload = json.loads(request.content)
        assert payload["filters"]["award_type_codes"] == ["A", "B", "C", "D"]
        assert payload["filters"]["keywords"] == ["synthetic"]
        assert payload["limit"] == 100
        assert payload["subawards"] is False
        row = {"generated_internal_id": "SYNTH_AWARD", "Award ID": "TEST-001", "Award Amount": 500000,
               "Recipient Name": "Fictional Supplier", "Description": "Synthetic test only",
               "Start Date": "2026-01-01", "End Date": "2027-01-01", "Base Obligation Date": "2026-01-01"}
        return httpx.Response(200, json={"results": [row, row], "page_metadata": {"hasNext": True}})
    with client_for(handler) as client:
        records = USAspendingProvider(client=client).search("synthetic")
    assert len(records) == 1
    row = records[0]
    assert row["obligated"] == 500000
    assert row["ceiling"] is None
    assert row["ticker"] is None
    assert row["announcement_date"] is None
    assert "not global" in row["coverage"]
    assert row["source_url"] == "https://www.usaspending.gov/award/SYNTH_AWARD"


def test_usaspending_missing_amount_not_zero_and_negative_correction_allowed():
    with client_for(lambda _: httpx.Response(200, json={"results": [
        {"Award ID": "SYNTH1"}, {"Award ID": "SYNTH2", "Award Amount": -25}]})) as client:
        records = USAspendingProvider(client=client).search("fictional")
    assert records[0]["obligated"] is None
    assert records[1]["obligated"] == -25


def test_server_retry_bounded_then_success():
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(503, headers={"Retry-After": "0"}) if len(calls) < 3 else httpx.Response(200, json=[])
    with client_for(handler) as client:
        assert CoinGeckoProvider("fake", client=client).markets() == []
    assert len(calls) == 3


def test_long_cooldown_does_not_block_or_retry():
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(429, headers={"Retry-After": "3600"})
    with client_for(handler) as client:
        with pytest.raises(ProviderError, match="cooldown"):
            CoinGeckoProvider("fake", client=client).markets()
    assert len(calls) == 1


@pytest.mark.parametrize("status", [301, 400, 401, 403, 404, 429, 500, 503])
def test_http_errors_are_safe_and_never_leak_response_or_credential(status):
    with client_for(lambda _: httpx.Response(status, text="fake-secret-key", headers={"location": "https://example.com"})) as client:
        with pytest.raises(ProviderError) as caught:
            CoinGeckoProvider("fake-secret-key", client=client).markets()
    assert "fake-secret-key" not in str(caught.value)


def test_invalid_json_and_oversize_are_safe():
    with client_for(lambda _: httpx.Response(200, text="<html>not JSON</html>")) as client:
        with pytest.raises(ProviderError, match="invalid JSON"):
            CoinGeckoProvider("fake", client=client).markets()
    with client_for(lambda _: httpx.Response(200, content=b" " * 100)) as client:
        provider = CoinGeckoProvider("fake", client=client)
        provider.max_bytes = 50
        with pytest.raises(ProviderError, match="size limit"):
            provider.markets()


def test_network_errors_bounded_and_sanitized():
    calls = []
    def handler(request):
        calls.append(request)
        raise httpx.ConnectError("fake-secret-key", request=request)
    with client_for(handler) as client:
        with pytest.raises(ProviderError) as caught:
            CoinGeckoProvider("fake-secret-key", client=client).markets()
    assert len(calls) == 3
    assert "fake-secret-key" not in str(caught.value)
