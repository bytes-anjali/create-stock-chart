from datetime import datetime, timedelta
from unittest.mock import patch

import numpy as np
from fastapi.testclient import TestClient

from stock_chart.api import app
from stock_chart.fetch import TickerSnapshot


def _fake_snapshot():
    n = 50
    times = [datetime(2026, 8, 17, 9, 15) + timedelta(minutes=i) for i in range(n)]
    prices = list(np.linspace(100, 95, n) + np.sin(np.linspace(0, 6, n)))
    return TickerSnapshot(
        ticker="TEST.NS",
        name="TEST CO",
        currency_symbol="₹",
        times=times,
        prices=prices,
        previous_close=100.0,
        latest_price=prices[-1],
    )


def test_root_serves_the_html_tool_page():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<form" in response.text


def test_health_lists_endpoints():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert "png" in response.json()["usage"]


@patch("stock_chart.api.fetch_intraday", return_value=_fake_snapshot())
def test_chart_png_endpoint_returns_image(mock_fetch):
    client = TestClient(app)
    response = client.get("/chart/TEST.NS")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 1000


@patch("stock_chart.api.fetch_intraday", return_value=_fake_snapshot())
def test_chart_video_endpoint_returns_mp4(mock_fetch):
    client = TestClient(app)
    response = client.get("/chart/TEST.NS/video")
    assert response.status_code == 200
    assert response.headers["content-type"] == "video/mp4"
    assert len(response.content) > 1000


@patch("stock_chart.api.fetch_intraday", return_value=_fake_snapshot())
def test_chart_video_v2_endpoint_returns_mp4(mock_fetch):
    client = TestClient(app)
    response = client.get("/v2/chart/TEST.NS/video")
    assert response.status_code == 200
    assert response.headers["content-type"] == "video/mp4"
    assert len(response.content) > 1000


@patch("stock_chart.api.fetch_intraday", side_effect=ValueError("No intraday data returned by Yahoo Finance for ticker 'BOGUS'"))
def test_chart_png_endpoint_reports_fetch_failure_as_502(mock_fetch):
    client = TestClient(app)
    response = client.get("/chart/BOGUS")
    assert response.status_code == 502
    assert "BOGUS" in response.json()["detail"]
