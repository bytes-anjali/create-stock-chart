from datetime import datetime, timedelta
from types import SimpleNamespace

import imageio.v2 as imageio
import numpy as np

from stock_chart.video import render_video


def _fake_snapshot(latest_price, previous_close, name="TEST INDEX"):
    change = latest_price - previous_close
    return SimpleNamespace(
        name=name,
        currency_symbol="₹",
        latest_price=latest_price,
        change=change,
        change_pct=(change / previous_close) * 100,
        is_positive=change >= 0,
    )


def test_render_video_produces_playable_mp4(tmp_path):
    n = 40
    times = [datetime(2026, 8, 17, 9, 15) + timedelta(minutes=i) for i in range(n)]
    prices = list(np.linspace(100, 95, n) + np.sin(np.linspace(0, 6, n)))
    snapshot = _fake_snapshot(latest_price=prices[-1], previous_close=prices[0])

    out_path = tmp_path / "chart.mp4"
    render_video(snapshot, prices, times, str(out_path), fps=10, reveal_seconds=0.5, hold_seconds=0.2)

    assert out_path.exists()
    assert out_path.stat().st_size > 1000

    reader = imageio.get_reader(str(out_path))
    frame_count = reader.count_frames()
    assert frame_count > 1

    first = reader.get_data(0)
    last = reader.get_data(frame_count - 1)
    assert first.shape == last.shape
    # The line should have grown by the final frame: more non-background pixels revealed.
    assert not np.array_equal(first, last)


def test_render_video_rejects_single_point_series(tmp_path):
    import pytest

    snapshot = _fake_snapshot(latest_price=100, previous_close=100)
    with pytest.raises(ValueError):
        render_video(snapshot, [100.0], [datetime(2026, 8, 17, 9, 15)], str(tmp_path / "chart.mp4"))
