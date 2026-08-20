"""V2 variant of the reveal video: the line grows across the exchange's full
market-hours timeline (not just the fetched data's own range), and once
generation stops at the latest available price the cursor blinks there
instead of holding steady — marking exactly where the chart ends.
"""

from datetime import datetime, timedelta

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import imageio.v2 as imageio

from .market_hours import session_window
from .render import CARD_BG, FIG_H, FIG_W, GRID_COLOR, POSITIVE_COLOR, NEGATIVE_COLOR, TEXT_MUTED, draw_card_background, draw_header

DEFAULT_FPS = 20
DEFAULT_REVEAL_SECONDS = 2.5
DEFAULT_BLINK_SECONDS = 2.0
DEFAULT_BLINK_HZ = 1.4


def _localize(dt, tz):
    return dt.replace(tzinfo=tz) if dt.tzinfo is None else dt.astimezone(tz)


def _session_bounds(ticker, times):
    open_time, close_time, tz = session_window(ticker)
    last = _localize(times[-1], tz)
    open_dt = datetime.combine(last.date(), open_time, tzinfo=tz)
    close_dt = datetime.combine(last.date(), close_time, tzinfo=tz)
    return open_dt, close_dt


def _hourly_ticks(open_dt, close_dt):
    """Hour-boundary marks between `open_dt` and `close_dt`, both endpoints included."""
    ticks = [open_dt]
    cursor = open_dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    while cursor < close_dt:
        ticks.append(cursor)
        cursor += timedelta(hours=1)
    ticks.append(close_dt)
    return ticks


def render_video(
    snapshot,
    styled_prices,
    times,
    ticker,
    out_path,
    fps: int = DEFAULT_FPS,
    reveal_seconds: float = DEFAULT_REVEAL_SECONDS,
    blink_seconds: float = DEFAULT_BLINK_SECONDS,
    blink_hz: float = DEFAULT_BLINK_HZ,
    dpi: int = 100,
) -> None:
    """Animate the line growing from the day's open towards the last available
    price, positioned along a fixed full-session x-axis (open to close) rather
    than the fetched range, so the timeline reads as real market timings and
    the untraded remainder of the session stays visibly blank. Once the reveal
    reaches the last point it blinks there for `blink_seconds` instead of
    holding steady. Axis range and header are fixed to their final values
    throughout, exactly as in the V1 video — only the line, fill, and cursor
    visibility animate.
    """
    styled_prices = np.asarray(styled_prices, dtype=float)
    n = len(styled_prices)
    if n < 2:
        raise ValueError("need at least 2 points to animate a chart")

    open_dt, close_dt = _session_bounds(ticker, times)
    tz = open_dt.tzinfo
    localized_times = [_localize(t, tz) for t in times]
    session_minutes = (close_dt - open_dt).total_seconds() / 60.0
    x = np.array([(t - open_dt).total_seconds() / 60.0 for t in localized_times])

    accent = POSITIVE_COLOR if snapshot.is_positive else NEGATIVE_COLOR
    arrow = "▲" if snapshot.is_positive else "▼"

    fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=dpi)
    fig.patch.set_facecolor(CARD_BG)
    draw_card_background(fig)
    draw_header(fig, snapshot, accent, arrow)

    ax = fig.add_axes((0.075, 0.10, 0.80, 0.56))
    ax.set_facecolor(CARD_BG)
    for spine in ax.spines.values():
        spine.set_visible(False)

    y_min, y_max = float(styled_prices.min()), float(styled_prices.max())
    y_span = max(y_max - y_min, 1e-9)
    y_ticks = np.linspace(y_min, y_max, 4)
    ax.set_yticks(y_ticks)
    ax.yaxis.tick_right()
    ax.set_yticklabels([f"{v:,.0f}" for v in y_ticks], fontsize=13, color=TEXT_MUTED)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="y", color=GRID_COLOR, linewidth=1)
    ax.set_ylim(y_min - y_span * 0.06, y_max + y_span * 0.06)

    ticks = _hourly_ticks(open_dt, close_dt)
    ax.set_xticks([(t - open_dt).total_seconds() / 60.0 for t in ticks])
    ax.set_xticklabels([t.strftime("%H:%M") for t in ticks], fontsize=13, color=TEXT_MUTED)
    ax.tick_params(axis="x", length=0)
    ax.set_xlim(0, session_minutes)

    (line,) = ax.plot([], [], color=accent, linewidth=2.6, solid_capstyle="round", zorder=3)
    halo = ax.scatter([], [], s=950, color=accent, alpha=0.16, zorder=4, linewidths=0)
    mid = ax.scatter([], [], s=170, color=accent, alpha=0.35, zorder=4, linewidths=0)
    core = ax.scatter([], [], s=55, color=accent, zorder=5, linewidths=0)
    fill_artist = [None]

    reveal_frames = max(2, min(int(round(reveal_seconds * fps)), n))
    reveal_counts = np.unique(np.linspace(2, n, reveal_frames, dtype=int))

    frames = [
        _render_frame(fig, ax, line, halo, mid, core, fill_artist, x, styled_prices, count, accent, y_min, blink_on=True)
        for count in reveal_counts
    ]

    blink_total_frames = max(1, int(round(blink_seconds * fps)))
    half_period = max(1, int(round(fps / blink_hz / 2)))
    for i in range(blink_total_frames):
        blink_on = (i // half_period) % 2 == 0
        frames.append(
            _render_frame(fig, ax, line, halo, mid, core, fill_artist, x, styled_prices, n, accent, y_min, blink_on=blink_on)
        )

    plt.close(fig)

    # Figure dimensions (in pixels) are already even, satisfying yuv420p's chroma
    # subsampling requirement, so macro_block_size=1 skips ffmpeg's default 16px-grid
    # padding/resize without any real player-compatibility risk.
    imageio.mimwrite(out_path, frames, fps=fps, codec="libx264", pixelformat="yuv420p", quality=8, macro_block_size=1)


def _render_frame(fig, ax, line, halo, mid, core, fill_artist, x, y, count, accent, floor, blink_on):
    xs = x[:count]
    ys = y[:count]
    line.set_data(xs, ys)

    if fill_artist[0] is not None:
        fill_artist[0].remove()
    fill_artist[0] = ax.fill_between(xs, ys, floor, color=accent, alpha=0.18, zorder=2)

    last_x, last_y = xs[-1], ys[-1]
    offset = [[last_x, last_y]]
    for artist in (halo, mid, core):
        artist.set_offsets(offset)
        artist.set_visible(blink_on)

    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())
    return buf[..., :3].copy()
