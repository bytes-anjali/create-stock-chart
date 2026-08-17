import numpy as np

from stock_chart.pattern import find_extrema, smooth


def test_find_extrema_detects_single_peak():
    prices = [1, 2, 3, 2, 1]
    assert find_extrema(prices, prominence_frac=0.1) == [(2, "peak")]


def test_find_extrema_ignores_noise_below_prominence():
    prices = [10, 10.01, 10, 15, 10, 10.02, 10]
    extrema = find_extrema(prices, prominence_frac=0.3)
    assert extrema == [(3, "peak")]


def test_find_extrema_preserves_chronological_order():
    prices = [1, 5, 1, 6, 1, 7, 1]
    extrema = find_extrema(prices, prominence_frac=0.1)
    indices = [i for i, _ in extrema]
    assert indices == sorted(indices)
    assert [kind for _, kind in extrema] == ["peak", "trough", "peak", "trough", "peak"]


def test_smooth_window_one_is_identity():
    prices = [1.0, 5.0, 2.0, 8.0, 3.0]
    assert list(smooth(prices, 1)) == prices


def test_smooth_preserves_length():
    prices = np.linspace(0, 10, 50) + np.sin(np.linspace(0, 20, 50))
    assert len(smooth(prices, 5)) == len(prices)
