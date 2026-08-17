"""Fetch intraday price data and metadata for a ticker from Yahoo Finance."""

from dataclasses import dataclass, field
from datetime import datetime

import yfinance as yf

CURRENCY_SYMBOLS = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
}

# Interval/period pairs to try in order until one returns usable intraday bars.
# Thinly-traded tickers or a just-closed session can come back empty at 1m/1d.
_FETCH_ATTEMPTS = [
    ("1m", "1d"),
    ("5m", "1d"),
    ("5m", "2d"),
    ("15m", "5d"),
]


@dataclass
class TickerSnapshot:
    ticker: str
    name: str
    currency_symbol: str
    times: list[datetime]
    prices: list[float]
    previous_close: float
    latest_price: float

    @property
    def change(self) -> float:
        return self.latest_price - self.previous_close

    @property
    def change_pct(self) -> float:
        if not self.previous_close:
            return 0.0
        return (self.change / self.previous_close) * 100

    @property
    def is_positive(self) -> bool:
        return self.change >= 0


def fetch_intraday(ticker: str) -> TickerSnapshot:
    """Fetch the latest session's intraday bars and identity/price metadata for `ticker`."""
    tk = yf.Ticker(ticker)

    hist = None
    for interval, period in _FETCH_ATTEMPTS:
        candidate = tk.history(period=period, interval=interval, prepost=False)
        if not candidate.empty and candidate["Close"].dropna().shape[0] >= 2:
            hist = candidate
            break

    if hist is None:
        raise ValueError(f"No intraday data returned by Yahoo Finance for ticker '{ticker}'")

    last_session = hist.index.normalize().max()
    hist = hist[hist.index.normalize() == last_session]
    closes = hist["Close"].dropna()
    if closes.shape[0] < 2:
        raise ValueError(f"Not enough intraday points for ticker '{ticker}' to plot a chart")

    previous_close, currency = _resolve_previous_close_and_currency(tk, closes)
    name = _resolve_name(tk, ticker)

    return TickerSnapshot(
        ticker=ticker,
        name=name,
        currency_symbol=CURRENCY_SYMBOLS.get(currency, f"{currency} "),
        times=[t.to_pydatetime() for t in closes.index],
        prices=[float(p) for p in closes.values],
        previous_close=float(previous_close),
        latest_price=float(closes.iloc[-1]),
    )


def _resolve_previous_close_and_currency(tk, closes):
    try:
        fast = tk.fast_info
        previous_close = fast.get("previous_close") or fast.get("regularMarketPreviousClose")
        currency = fast.get("currency") or "USD"
        if previous_close:
            return float(previous_close), currency
    except Exception:
        pass
    # Fall back to the first bar of the session if Yahoo's metadata is unavailable.
    return float(closes.iloc[0]), "USD"


def _resolve_name(tk, ticker: str) -> str:
    try:
        info = tk.get_info()
        return info.get("shortName") or info.get("longName") or ticker
    except Exception:
        return ticker
