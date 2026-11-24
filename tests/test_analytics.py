"""Financial arithmetic and chronology tests; no market-performance claims."""

import importlib.util
import math
import unittest
from datetime import date, timedelta
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "analytics", Path(__file__).parents[1] / "src" / "techpulse" / "analytics.py"
)
an = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(an)


def bars(closes, volumes=None):
    origin = date(2024, 1, 1)
    return [
        {
            "date": (origin + timedelta(days=i)).isoformat(),
            "open": value,
            "close": value,
            "high": value + 1,
            "low": max(value - 1, value / 2),
            "volume": volumes[i] if volumes is not None else 100,
        }
        for i, value in enumerate(closes)
    ]


class IndicatorTests(unittest.TestCase):
    def test_empty_history_is_unavailable(self):
        self.assertIsNone(an.indicators([])["rsi14"])
        self.assertIsNone(an.summarize([])["price"])
        self.assertEqual(an.detect_patterns([]), [])

    def test_sma_population_bollinger_and_macd_linear_series(self):
        result = an.indicators(bars(list(range(1, 61))))
        self.assertAlmostEqual(result["sma20"], 50.5)
        self.assertAlmostEqual(result["sma50"], 35.5)
        self.assertAlmostEqual(result["bb_upper"], 50.5 + 2 * math.sqrt(33.25))
        self.assertAlmostEqual(result["bb_lower"], 50.5 - 2 * math.sqrt(33.25))
        self.assertAlmostEqual(result["macd"], 7)
        self.assertAlmostEqual(result["macd_signal"], 7)

    def test_rsi_wilder_known_example(self):
        prices = [
            44.34,
            44.09,
            44.15,
            43.61,
            44.33,
            44.83,
            45.10,
            45.42,
            45.84,
            46.08,
            45.89,
            46.03,
            45.61,
            46.28,
            46.28,
        ]
        self.assertAlmostEqual(an.indicators(bars(prices))["rsi14"], 70.464135021097, places=8)
        prices.append(46.00)
        self.assertAlmostEqual(an.indicators(bars(prices))["rsi14"], 66.249618553555, places=8)

    def test_rsi_flat_increasing_decreasing_and_warmup(self):
        self.assertEqual(an.indicators(bars([10] * 15))["rsi14"], 50)
        self.assertEqual(an.indicators(bars(list(range(1, 16))))["rsi14"], 100)
        self.assertEqual(an.indicators(bars(list(range(15, 0, -1))))["rsi14"], 0)
        self.assertIsNone(an.indicators(bars([10] * 14))["rsi14"])

    def test_macd_signal_warmup(self):
        self.assertIsNone(an.indicators(bars([10] * 25))["macd"])
        self.assertIsNone(an.indicators(bars([10] * 33))["macd_signal"])
        self.assertEqual(an.indicators(bars([10] * 34))["macd_signal"], 0)

    def test_atr_seed_and_gap_recursion(self):
        rows = bars([10] * 14 + [20])
        self.assertEqual(an.indicators(rows[:14])["atr14"], 2)
        self.assertAlmostEqual(an.indicators(rows)["atr14"], (13 * 2 + 11) / 14)

    def test_support_resistance_exclude_latest(self):
        rows = bars([10] * 20 + [100])
        self.assertEqual(an.indicators(rows)["resistance"], 11)
        self.assertEqual(an.indicators(rows)["support"], 9)

    def test_summary_returns_and_volume_exclude_latest_from_baseline(self):
        rows = bars(list(range(1, 23)), [100] * 21 + [300])
        result = an.summarize(rows)
        self.assertAlmostEqual(result["day_pct"], 100 * (22 / 21 - 1))
        self.assertAlmostEqual(result["week_pct"], 100 * (22 / 17 - 1))
        self.assertAlmostEqual(result["month_pct"], 2100)
        self.assertEqual(result["relative_volume"], 3)
        self.assertEqual(result["data_points"], 22)

    def test_zero_volume_baseline_is_unavailable(self):
        self.assertIsNone(an.summarize(bars([10] * 21, [0] * 20 + [1]))["relative_volume"])

    def test_bad_bars_rejected(self):
        for field, value in (
            ("open", 0),
            ("high", math.nan),
            ("low", math.inf),
            ("volume", -1),
            ("close", True),
        ):
            with self.subTest(field=field):
                row = bars([10])[0]
                row[field] = value
                with self.assertRaises(ValueError):
                    an.indicators([row])
        row = bars([10])[0]
        row["high"] = 9
        with self.assertRaises(ValueError):
            an.summarize([row])

    def test_duplicate_unsorted_and_noncanonical_dates_rejected(self):
        for rows in (bars([10]) * 2, list(reversed(bars([10, 11])))):
            with self.assertRaises(ValueError):
                an.validate_bars(rows)
        row = bars([10])[0]
        row["date"] = "20240101"
        with self.assertRaises(ValueError):
            an.validate_bars([row])


class PatternTests(unittest.TestCase):
    def test_double_bottom_and_top_geometry_are_uncalibrated(self):
        values = [
            120,
            118,
            116,
            114,
            110,
            105,
            100,
            104,
            110,
            115,
            110,
            106,
            102,
            100.5,
            104,
            108,
            112,
            118,
            120,
            121,
            122,
            123,
            124,
            125,
            126,
        ]
        results = an.detect_patterns(bars(values))
        bottom = next(r for r in results if r["name"] == "Double bottom")
        self.assertEqual(bottom["status"], "Confirmed geometry")
        self.assertIsNone(bottom["confidence"])
        self.assertFalse(bottom["validated"])
        self.assertEqual(bottom["sample_size"], 0)
        top_values = [250 - v for v in values]
        self.assertIn("Double top", [r["name"] for r in an.detect_patterns(bars(top_values))])

    def test_head_shoulders_geometry(self):
        values = [
            100,
            102,
            104,
            108,
            112,
            110,
            106,
            100,
            105,
            110,
            116,
            120,
            116,
            110,
            105,
            100,
            105,
            110,
            112,
            110,
            106,
            100,
            98,
            96,
            95,
        ]
        names = [r["name"] for r in an.detect_patterns(bars(values))]
        self.assertIn("Head and shoulders", names)
        inverse = [250 - v for v in values]
        self.assertIn(
            "Inverse head and shoulders",
            [r["name"] for r in an.detect_patterns(bars(inverse))],
        )

    def test_breakout_and_no_unconfirmed_recent_pivot(self):
        rows = bars([10] * 24 + [15], [100] * 24 + [200])
        results = an.detect_patterns(rows)
        breakout = next(r for r in results if r["name"] == "20-bar breakout")
        self.assertIn("Volume >=1.5x", breakout["evidence"])
        self.assertNotIn("Double top", [r["name"] for r in results])


class ScoreTests(unittest.TestCase):
    def test_complete_score_and_missing_inputs_not_renormalized(self):
        result = an.score_candidate(dict.fromkeys(an.DEFAULT_WEIGHTS, 80))
        self.assertAlmostEqual(result["score"], 80)
        self.assertAlmostEqual(result["coverage"], 1)
        self.assertEqual(result["decision"], "Research candidate")
        partial = an.score_candidate({"technical": 100, "reliability": 100})
        self.assertAlmostEqual(partial["score"], 35)
        self.assertAlmostEqual(partial["coverage"], 0.35)
        self.assertEqual(partial["decision"], "Abstain")

    def test_political_and_options_cannot_determine_candidate(self):
        result = an.score_candidate({"options": 100, "political": 100, "reliability": 100})
        self.assertEqual(result["decision"], "Abstain")
        self.assertIn(
            "Fundamentals or a verified corporate catalyst is required.",
            result["reasons"],
        )

    def test_custom_weights_normalize_and_zero_disabled_inputs_do_not_count(self):
        weights = dict.fromkeys(an.DEFAULT_WEIGHTS, 0)
        weights["technical"] = 1
        result = an.score_candidate(dict.fromkeys(an.DEFAULT_WEIGHTS, 100), weights)
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["decision"], "Abstain")

    def test_invalid_weights_components_and_low_reliability(self):
        for values in ({"technical": -1}, {"technical": 101}, {"technical": math.nan}):
            with self.assertRaises(ValueError):
                an.score_candidate(values)
        with self.assertRaises(ValueError):
            an.score_candidate({}, {"technical": 100})
        with self.assertRaises(ValueError):
            an.score_candidate({}, dict.fromkeys(an.DEFAULT_WEIGHTS, 0))
        values = dict.fromkeys(an.DEFAULT_WEIGHTS, 100)
        values["reliability"] = 59
        self.assertEqual(an.score_candidate(values)["decision"], "Abstain")


class OptionsAndContractTests(unittest.TestCase):
    def test_observed_trade_premium_actual_multiplier(self):
        result = an.option_metrics({"kind": "trade", "size": 7, "price": 2.5, "multiplier": 50})
        self.assertEqual(result["estimated_trade_premium"], 875)
        self.assertIn("Unknown", result["intent"])

    def test_aggregate_never_uses_volume_times_last(self):
        result = an.option_metrics(
            {
                "kind": "aggregate",
                "volume": 1000,
                "price": 10,
                "multiplier": 100,
                "size": 1000,
            }
        )
        self.assertIsNone(result["estimated_trade_premium"])
        self.assertIsNone(result["aggregate_premium"])

    def test_missing_multiplier_and_denominators_remain_unavailable(self):
        result = an.option_metrics(
            {
                "kind": "trade",
                "size": 10,
                "price": 2,
                "volume": 10,
                "open_interest": 0,
                "historical_average_volume": 0,
            }
        )
        self.assertIsNone(result["estimated_trade_premium"])
        self.assertIsNone(result["volume_ratio"])
        self.assertIsNone(result["volume_open_interest_ratio"])

    def test_options_ratios_iv_points_and_validation(self):
        result = an.option_metrics(
            {
                "volume": 200,
                "historical_average_volume": 100,
                "open_interest": 400,
                "iv": 0.5,
                "previous_iv": 0.4,
            }
        )
        self.assertEqual(result["volume_ratio"], 2)
        self.assertEqual(result["volume_open_interest_ratio"], 0.5)
        self.assertAlmostEqual(result["iv_change_points"], 10)
        for record in (
            {"kind": "sweep"},
            {"volume": -1},
            {"price": math.nan},
            {"kind": "trade", "size": 0, "price": 1, "multiplier": 100},
            {"kind": "trade", "size": 1e308, "price": 100, "multiplier": 100},
        ):
            with self.assertRaises(ValueError):
                an.option_metrics(record)

    def test_contract_obligations_not_ceiling_and_deobligation(self):
        result = an.contract_metrics({"obligated": 100, "ceiling": 1000}, revenue=500, market_cap=2000)
        self.assertEqual(result["funded_fraction"], 0.1)
        self.assertEqual(result["obligated_to_revenue_pct"], 20)
        self.assertEqual(result["obligated_to_market_cap_pct"], 5)
        negative = an.contract_metrics({"obligations": -100, "ceiling": 1000}, revenue=500)
        self.assertEqual(negative["obligated_to_revenue_pct"], -20)
        self.assertIn("Negative obligation", negative["warnings"][-1])

    def test_contract_missing_is_not_zero_and_invalid_denominators(self):
        self.assertIsNone(an.contract_metrics({"ceiling": 100})["obligated_to_revenue_pct"])
        for args in (({"obligated": math.inf}, None), ({"ceiling": -1}, None), ({}, 0)):
            with self.assertRaises(ValueError):
                an.contract_metrics(args[0], revenue=args[1])


class WalkForwardTests(unittest.TestCase):
    def test_signal_before_entry_costs_and_nonoverlap(self):
        rows = bars(list(range(100, 171)))
        result = an.walk_forward(rows, horizon=5, cost_bps=10)
        first = result["trades"][0]
        self.assertEqual(first["signal_date"], rows[49]["date"])
        self.assertEqual(first["entry_date"], rows[50]["date"])
        self.assertEqual(first["exit_date"], rows[54]["date"])
        expected = (154 * 0.999 / (150 * 1.001) - 1) * 100
        self.assertAlmostEqual(first["return_pct"], expected)
        self.assertEqual(result["sample_size"], 4)
        self.assertLess(first["exit_date"], result["trades"][1]["entry_date"])
        self.assertIsNone(result["confidence"])

    def test_future_change_does_not_change_earlier_trades(self):
        rows = bars(list(range(100, 181)))
        earlier = an.walk_forward(rows[:70])["trades"]
        changed = rows[:70] + bars([1000] * 11)
        # Preserve canonical chronology after replacing future price values.
        for i in range(70, len(changed)):
            changed[i]["date"] = rows[i]["date"]
        later = an.walk_forward(changed)["trades"]
        self.assertEqual(earlier, later[: len(earlier)])

    def test_no_signal_and_insufficient_history_abstain(self):
        self.assertEqual(an.walk_forward(bars([100] * 70))["sample_size"], 0)
        self.assertIsNone(an.walk_forward(bars([100] * 20))["mean_return_pct"])
        self.assertEqual(an.walk_forward(bars(list(range(100, 30, -1))))["sample_size"], 0)

    def test_invalid_horizon_and_cost(self):
        for value in (0, -1, 1.5, True):
            with self.assertRaises(ValueError):
                an.walk_forward([], horizon=value)
        for value in (-1, math.inf, 10000):
            with self.assertRaises(ValueError):
                an.walk_forward([], cost_bps=value)


if __name__ == "__main__":
    unittest.main()
