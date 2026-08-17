from datetime import datetime, timedelta
from types import SimpleNamespace

import numpy as np

from stock_chart.render import render_card


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


def test_render_card_produces_a_png_file(tmp_path):
    n = 60
    times = [datetime(2026, 8, 17, 9, 15) + timedelta(minutes=i) for i in range(n)]
    prices = list(np.linspace(30500, 30150, n) + np.sin(np.linspace(0, 6, n)) * 20)
    snapshot = _fake_snapshot(latest_price=prices[-1] + 5, previous_close=prices[0] - 5)

    out_path = tmp_path / "chart.png"
    render_card(snapshot, prices, times, str(out_path))

    assert out_path.exists()
    assert out_path.stat().st_size > 2000


def test_render_card_handles_negative_change(tmp_path):
    n = 30
    times = [datetime(2026, 8, 17, 9, 15) + timedelta(minutes=i) for i in range(n)]
    prices = list(np.linspace(100, 110, n))
    snapshot = _fake_snapshot(latest_price=95, previous_close=100, name="DOWN CO")

    out_path = tmp_path / "chart_down.png"
    render_card(snapshot, prices, times, str(out_path))

    assert out_path.exists()
