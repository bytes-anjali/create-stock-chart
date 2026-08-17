import numpy as np

from stock_chart.generate import stylize_and_validate
from stock_chart.validate import validate_pattern


def test_identity_series_validates():
    prices = [100, 102, 99, 105, 101, 98, 103]
    assert validate_pattern(prices, prices).ok


def test_stylize_and_validate_falls_back_until_pattern_is_preserved():
    rng = np.random.default_rng(0)
    trend = np.linspace(100, 90, 200)
    noise = rng.normal(0, 0.15, 200)
    prices = trend + noise
    prices[50] += 3  # a clear spike/peak
    prices[120] -= 3  # a clear trough

    styled, window, rejected = stylize_and_validate(list(prices))

    assert validate_pattern(prices, styled).ok
    if window != 1:
        assert rejected == [] or all(w > window for w, _ in rejected)


def test_flattening_a_real_peak_fails_validation():
    prices = [100, 100, 100, 130, 100, 100, 100]
    styled = [100, 100, 100, 100, 100, 100, 100]
    result = validate_pattern(prices, styled)
    assert not result.ok
    assert "extrema count mismatch" in result.reasons[0]


def test_reversed_direction_fails_validation():
    prices = [100, 101, 102, 103, 104]
    styled = [104, 103, 102, 101, 100]
    result = validate_pattern(prices, styled)
    assert not result.ok
