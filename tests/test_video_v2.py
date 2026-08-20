from datetime import datetime, timedelta
from types import SimpleNamespace

import imageio.v2 as imageio
import numpy as np

from stock_chart.video_v2 import render_video


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


def test_render_video_v2_produces_playable_mp4(tmp_path):
    n = 40
    times = [datetime(2026, 8, 17, 9, 15) + timedelta(minutes=i) for i in range(n)]
    prices = list(np.linspace(100, 95, n) + np.sin(np.linspace(0, 6, n)))
    snapshot = _fake_snapshot(latest_price=prices[-1], previous_close=prices[0])

    out_path = tmp_path / "chart.mp4"
    render_video(snapshot, prices, times, "TEST.NS", str(out_path), fps=10, reveal_seconds=0.5, blink_seconds=0.2)

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


def test_render_video_v2_blinks_after_reaching_the_last_point(tmp_path):
    # fps/blink_hz chosen so the blink toggles a couple of times within blink_seconds,
    # with a clean boundary between an "on" and an "off" frame to sample.
    n = 40
    times = [datetime(2026, 8, 17, 9, 15) + timedelta(minutes=i) for i in range(n)]
    prices = list(np.linspace(100, 95, n) + np.sin(np.linspace(0, 6, n)))
    snapshot = _fake_snapshot(latest_price=prices[-1], previous_close=prices[0])

    out_path = tmp_path / "chart.mp4"
    render_video(
        snapshot, prices, times, "TEST.NS", str(out_path),
        fps=10, reveal_seconds=0.5, blink_seconds=1.0, blink_hz=2.5,
    )

    reader = imageio.get_reader(str(out_path))
    frame_count = reader.count_frames()

    # reveal_frames = min(round(0.5*10), n) = 5 -> blink phase starts at frame index 5.
    # half_period = round(10/2.5/2) = 2, so frames 5-6 are "on" and 7-8 are "off".
    on_frame = reader.get_data(min(5, frame_count - 1))
    off_frame = reader.get_data(min(7, frame_count - 1))
    assert not np.array_equal(on_frame, off_frame)


def test_render_video_v2_rejects_single_point_series(tmp_path):
    import pytest

    snapshot = _fake_snapshot(latest_price=100, previous_close=100)
    with pytest.raises(ValueError):
        render_video(
            snapshot, [100.0], [datetime(2026, 8, 17, 9, 15)], "TEST.NS", str(tmp_path / "chart.mp4")
        )
