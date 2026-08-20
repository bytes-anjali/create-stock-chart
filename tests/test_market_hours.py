from datetime import time

from stock_chart.market_hours import session_window


def test_nse_equity_and_index_use_ist_session():
    for ticker in ["RELIANCE.NS", "TCS.NS", "^NSEI", "^BSESN"]:
        open_time, close_time, tz = session_window(ticker)
        assert (open_time, close_time) == (time(9, 15), time(15, 30))
        assert tz.key == "Asia/Kolkata"


def test_non_nse_ticker_defaults_to_us_session():
    open_time, close_time, tz = session_window("AAPL")
    assert (open_time, close_time) == (time(9, 30), time(16, 0))
    assert tz.key == "America/New_York"
