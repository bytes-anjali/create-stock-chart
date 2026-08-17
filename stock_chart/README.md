# stock_chart

Ticker in, pattern-faithful chart card out.

```
Ticker → Yahoo → Price Data → Extract Pattern → Stylized Chart → Pattern Validation → Final Image
```

## Usage

```bash
pip install -r requirements.txt
python -m stock_chart.cli RELIANCE.NS
python -m stock_chart.cli ^NSEI -o nifty.png
```

Or from Python:

```python
from stock_chart import generate

snapshot = generate("TCS.NS", "tcs.png")
print(snapshot.latest_price, snapshot.change_pct)
```

## How it works

1. **`fetch.py`** — pulls the current session's intraday bars (1-minute where
   Yahoo has them, falling back to coarser intervals for thin/closed sessions)
   plus the instrument's name, previous close, and currency via `yfinance`.
2. **`pattern.py`** — finds the series' significant peaks/troughs
   (`find_extrema`, prominence-filtered so minor noise doesn't count) and
   offers a rolling-mean `smooth()` for visual polish.
3. **`validate.py`** — compares a stylized series against the raw one: same
   number of peaks/troughs, same order, each within a position and value
   tolerance, and the overall start-to-end direction unchanged.
4. **`generate.py`** — tries progressively lighter smoothing windows
   (7 → 5 → 3 → 1) until one passes validation. Window 1 is the raw series
   itself, so this always terminates with a pattern-valid chart — smoothing
   is stylistic, never a source of drift from the real Yahoo data.
5. **`render.py`** — draws the fixed card template: rounded white card, name
   + price + change header, right-aligned price gridlines, bottom time
   labels, gradient area fill, and a haloed dot at the latest price. Color
   (teal-green vs red) follows the sign of the overall change, matching the
   reference design.

## Notes

- Yahoo Finance access needs outbound HTTPS to `query1.finance.yahoo.com` /
  `query2.finance.yahoo.com`. If that's blocked by your network/egress
  policy, `fetch_intraday()` will raise — the rest of the pipeline
  (pattern extraction, validation, rendering) has no other external
  dependency and is covered by the test suite using synthetic data.
- Indices (e.g. `^NSEI`, `^CNXIT`) and equities (e.g. `RELIANCE.NS`,
  `AAPL`) both work — `fetch_intraday` doesn't special-case either.
