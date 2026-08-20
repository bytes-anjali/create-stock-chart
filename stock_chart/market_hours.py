"""Fixed exchange session windows used by the V2 (market-timeline) video variant."""

from datetime import time
from zoneinfo import ZoneInfo

_NSE_SUFFIXES = (".NS", ".BO")
_NSE_INDEX_PREFIXES = ("^NSE", "^BSE", "^CNX")

NSE_OPEN, NSE_CLOSE = time(9, 15), time(15, 30)
NSE_TZ = ZoneInfo("Asia/Kolkata")

US_OPEN, US_CLOSE = time(9, 30), time(16, 0)
US_TZ = ZoneInfo("America/New_York")


def session_window(ticker: str):
    """Return (open_time, close_time, tzinfo) for the exchange `ticker` trades on.

    Only NSE/BSE (India) and US-default hours are distinguished — matching the
    two markets stock_chart's own README calls out (RELIANCE.NS/^NSEI vs AAPL).
    """
    upper = ticker.upper()
    if upper.endswith(_NSE_SUFFIXES) or upper.startswith(_NSE_INDEX_PREFIXES):
        return NSE_OPEN, NSE_CLOSE, NSE_TZ
    return US_OPEN, US_CLOSE, US_TZ
