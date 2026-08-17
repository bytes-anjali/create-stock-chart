from datetime import datetime

from stock_chart.fetch import TickerSnapshot


def test_snapshot_computed_fields_match_reference_card():
    # Numbers from the NIFTY IT reference card: 30,178.05, +51.25 (+0.17%)
    snapshot = TickerSnapshot(
        ticker="^CNXIT",
        name="NIFTY IT",
        currency_symbol="₹",
        times=[datetime(2026, 8, 17, 9, 15)],
        prices=[30178.05],
        previous_close=30126.80,
        latest_price=30178.05,
    )
    assert round(snapshot.change, 2) == 51.25
    assert round(snapshot.change_pct, 2) == 0.17
    assert snapshot.is_positive


def test_negative_change_flags_not_positive():
    snapshot = TickerSnapshot(
        ticker="TEST.NS",
        name="TEST",
        currency_symbol="₹",
        times=[datetime(2026, 8, 17, 9, 15)],
        prices=[95.0],
        previous_close=100.0,
        latest_price=95.0,
    )
    assert snapshot.change == -5.0
    assert round(snapshot.change_pct, 2) == -5.0
    assert not snapshot.is_positive
