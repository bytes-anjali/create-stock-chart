"""Orchestrates the full pipeline: Ticker -> Yahoo -> Price Data -> Extract Pattern
-> Stylized Chart -> Pattern Validation -> Final Image.
"""

from .fetch import TickerSnapshot, fetch_intraday
from .pattern import smooth
from .render import render_card
from .validate import validate_pattern
from .video import render_video

# Smoothing windows to try, most-stylized first, falling back to less smoothing
# whenever a window distorts a peak/trough badly enough to fail validation.
# window=1 is the raw series itself, so this loop always terminates successfully.
_SMOOTHING_LEVELS = [7, 5, 3, 1]


def stylize_and_validate(raw_prices):
    """Return (styled_prices, window_used, validation_reasons_from_rejected_attempts)."""
    rejected = []
    for window in _SMOOTHING_LEVELS:
        styled = smooth(raw_prices, window)
        result = validate_pattern(raw_prices, styled)
        if result.ok:
            return styled, window, rejected
        rejected.append((window, result.reasons))
    # Unreachable: window=1 (the raw series compared to itself) always validates.
    raise RuntimeError("failed to produce a pattern-valid chart even at window=1")


def generate(ticker: str, out_path: str) -> TickerSnapshot:
    """Run the full pipeline for `ticker` and write the resulting card PNG to `out_path`.
    Returns the fetched TickerSnapshot for callers that want the underlying numbers.
    """
    snapshot = fetch_intraday(ticker)
    styled_prices, _window, _rejected = stylize_and_validate(snapshot.prices)
    render_card(snapshot, styled_prices, snapshot.times, out_path)
    return snapshot


def generate_video(ticker: str, out_path: str, **video_kwargs) -> TickerSnapshot:
    """Run the full pipeline for `ticker` and write an MP4 that traces the day's line
    from open to the last available price to `out_path`. Extra keyword args (fps,
    reveal_seconds, hold_seconds) are forwarded to render_video.
    """
    snapshot = fetch_intraday(ticker)
    styled_prices, _window, _rejected = stylize_and_validate(snapshot.prices)
    render_video(snapshot, styled_prices, snapshot.times, out_path, **video_kwargs)
    return snapshot
