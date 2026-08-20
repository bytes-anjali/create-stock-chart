"""HTTP API: ticker in, chart PNG or open-to-last-price MP4 out.

Run locally with: uvicorn stock_chart.api:app --reload
Deployed on Railway via the repo-root Procfile.
"""

import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from .fetch import fetch_intraday
from .generate import stylize_and_validate
from .render import render_card
from .video import render_video
from .video_v2 import render_video as render_video_v2

app = FastAPI(title="Stock Chart Generator")

_STATIC_DIR = Path(__file__).parent / "static"


@app.get("/")
def root():
    return FileResponse(_STATIC_DIR / "index.html", media_type="text/html")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "usage": {
            "png": "/chart/{ticker}",
            "video": "/chart/{ticker}/video",
            "video_v2": "/v2/chart/{ticker}/video",
        },
    }


@app.get("/chart/{ticker}")
def chart_png(ticker: str):
    snapshot, styled_prices = _fetch_and_stylize(ticker)
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    render_card(snapshot, styled_prices, snapshot.times, path)
    return FileResponse(
        path,
        media_type="image/png",
        filename=f"{ticker}.png",
        background=BackgroundTask(os.remove, path),
    )


@app.get("/chart/{ticker}/video")
def chart_video(ticker: str):
    snapshot, styled_prices = _fetch_and_stylize(ticker)
    fd, path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)
    render_video(snapshot, styled_prices, snapshot.times, path)
    return FileResponse(
        path,
        media_type="video/mp4",
        filename=f"{ticker}.mp4",
        background=BackgroundTask(os.remove, path),
    )


@app.get("/v2/chart/{ticker}/video")
def chart_video_v2(ticker: str):
    snapshot, styled_prices = _fetch_and_stylize(ticker)
    fd, path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)
    render_video_v2(snapshot, styled_prices, snapshot.times, ticker, path)
    return FileResponse(
        path,
        media_type="video/mp4",
        filename=f"{ticker}_v2.mp4",
        background=BackgroundTask(os.remove, path),
    )


def _fetch_and_stylize(ticker: str):
    try:
        snapshot = fetch_intraday(ticker)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not fetch '{ticker}' from Yahoo Finance: {exc}") from None
    styled_prices, _window, _rejected = stylize_and_validate(snapshot.prices)
    return snapshot, styled_prices
