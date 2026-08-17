"""Extract and stylize the shape (peaks/troughs) of an intraday price series."""

import numpy as np
from scipy.signal import find_peaks


def find_extrema(prices, prominence_frac: float = 0.06):
    """Return the significant peaks/troughs of `prices` as [(index, "peak"|"trough"), ...],
    in chronological order. `prominence_frac` is a fraction of the series' full range,
    so minor wiggles are ignored and only movements a viewer would actually notice count.
    """
    prices = np.asarray(prices, dtype=float)
    span = prices.max() - prices.min()
    prominence = max(span * prominence_frac, 1e-9)

    peak_idx, _ = find_peaks(prices, prominence=prominence)
    trough_idx, _ = find_peaks(-prices, prominence=prominence)

    extrema = [(int(i), "peak") for i in peak_idx] + [(int(i), "trough") for i in trough_idx]
    extrema.sort(key=lambda item: item[0])
    return extrema


def smooth(prices, window: int):
    """Centered rolling-mean smoothing for visual polish. window=1 returns the raw series
    unchanged, which trivially preserves every peak/trough — the safety net a validation
    retry loop can always fall back to.
    """
    prices = np.asarray(prices, dtype=float)
    if window <= 1:
        return prices.copy()
    kernel = np.ones(window) / window
    pad_left = window // 2
    pad_right = window - 1 - pad_left
    padded = np.pad(prices, (pad_left, pad_right), mode="edge")
    return np.convolve(padded, kernel, mode="valid")
