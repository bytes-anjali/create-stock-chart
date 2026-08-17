# stock_chart

Ticker in, pattern-faithful chart card out.

```
Ticker → Yahoo → Price Data → Extract Pattern → Stylized Chart → Pattern Validation → Final Image
```

## Usage

```bash
pip install -r requirements.txt
python -m stock_chart.cli RELIANCE.NS                # static PNG card
python -m stock_chart.cli ^NSEI -o nifty.png
python -m stock_chart.cli TCS.NS --video             # MP4 tracing open -> last price
```

Or from Python:

```python
from stock_chart import generate, generate_video

snapshot = generate("TCS.NS", "tcs.png")
generate_video("TCS.NS", "tcs.mp4")
print(snapshot.latest_price, snapshot.change_pct)
```

### HTTP API

```bash
uvicorn stock_chart.api:app --reload
curl http://localhost:8000/chart/RELIANCE.NS -o reliance.png
curl http://localhost:8000/chart/RELIANCE.NS/video -o reliance.mp4
```

### Deploying on Railway

The repo root has a `Procfile` (`web: uvicorn stock_chart.api:app --host 0.0.0.0
--port $PORT`) and a `requirements.txt` that includes `stock_chart/requirements.txt`
plus `fastapi`/`uvicorn`. Railway's Nixpacks builder picks both up automatically —
just point a new Railway service at this repo/branch and deploy. No Dockerfile or
system `ffmpeg` install is needed: `imageio-ffmpeg` bundles a static ffmpeg binary.

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
6. **`video.py`** — animates the same card: the line/fill/dot grow from the
   day's open to the last available price, then hold on the finished chart.
   The axis range and header numbers are fixed to their final values before
   the first frame is drawn, so the animation can only ever reveal more of
   the real, already-validated line — it can't imply a price or extremum
   that isn't in the data.
7. **`api.py`** — a FastAPI app exposing `GET /chart/{ticker}` (PNG) and
   `GET /chart/{ticker}/video` (MP4), for deploying as an HTTP service.

## Notes

- Yahoo Finance access needs outbound HTTPS to `query1.finance.yahoo.com` /
  `query2.finance.yahoo.com`. If that's blocked by your network/egress
  policy, `fetch_intraday()` will raise — the rest of the pipeline
  (pattern extraction, validation, rendering) has no other external
  dependency and is covered by the test suite using synthetic data.
- Indices (e.g. `^NSEI`, `^CNXIT`) and equities (e.g. `RELIANCE.NS`,
  `AAPL`) both work — `fetch_intraday` doesn't special-case either.
