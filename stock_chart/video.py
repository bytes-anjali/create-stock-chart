"""Render an MP4 that traces the day's price line from the open to the last
available price, on the same fixed card template used for the static PNG.
"""

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import imageio.v2 as imageio

from .render import FIG_H, FIG_W, NEGATIVE_COLOR, OUTER_BG, POSITIVE_COLOR, draw_card_background, draw_header, prepare_axis

DEFAULT_FPS = 20
DEFAULT_REVEAL_SECONDS = 2.5
DEFAULT_HOLD_SECONDS = 1.0


def render_video(
    snapshot,
    styled_prices,
    times,
    out_path,
    fps: int = DEFAULT_FPS,
    reveal_seconds: float = DEFAULT_REVEAL_SECONDS,
    hold_seconds: float = DEFAULT_HOLD_SECONDS,
    dpi: int = 100,
) -> None:
    """Animate the line growing from the day's open (frame 0) to the last available
    price, then hold on the finished chart for `hold_seconds` so the ending reads
    clearly. The axis range and header (name/price/change) are fixed to their final
    values throughout — only the line, area fill, and latest-price dot animate — so
    the animation can never imply a peak/trough/price that isn't in the real data.
    """
    styled_prices = np.asarray(styled_prices, dtype=float)
    n = len(styled_prices)
    if n < 2:
        raise ValueError("need at least 2 points to animate a chart")

    accent = POSITIVE_COLOR if snapshot.is_positive else NEGATIVE_COLOR
    arrow = "▲" if snapshot.is_positive else "▼"

    fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=dpi)
    fig.patch.set_facecolor(OUTER_BG)
    draw_card_background(fig)
    draw_header(fig, snapshot, accent, arrow)
    ax, x, y_min, _y_max = prepare_axis(fig, styled_prices, times)

    (line,) = ax.plot([], [], color=accent, linewidth=2.6, solid_capstyle="round", zorder=3)
    halo = ax.scatter([], [], s=950, color=accent, alpha=0.16, zorder=4, linewidths=0)
    mid = ax.scatter([], [], s=170, color=accent, alpha=0.35, zorder=4, linewidths=0)
    core = ax.scatter([], [], s=55, color=accent, zorder=5, linewidths=0)
    fill_artist = [None]

    reveal_frames = max(2, min(int(round(reveal_seconds * fps)), n))
    reveal_counts = np.unique(np.linspace(2, n, reveal_frames, dtype=int))

    frames = [
        _render_frame(fig, ax, line, halo, mid, core, fill_artist, x, styled_prices, count, accent, y_min)
        for count in reveal_counts
    ]

    hold_frames = max(1, int(round(hold_seconds * fps)))
    frames.extend([frames[-1]] * hold_frames)

    plt.close(fig)

    # Figure dimensions (in pixels) are already even, satisfying yuv420p's chroma
    # subsampling requirement, so macro_block_size=1 skips ffmpeg's default 16px-grid
    # padding/resize without any real player-compatibility risk.
    imageio.mimwrite(out_path, frames, fps=fps, codec="libx264", pixelformat="yuv420p", quality=8, macro_block_size=1)


def _render_frame(fig, ax, line, halo, mid, core, fill_artist, x, y, count, accent, floor):
    xs = x[:count]
    ys = y[:count]
    line.set_data(xs, ys)

    if fill_artist[0] is not None:
        fill_artist[0].remove()
    fill_artist[0] = ax.fill_between(xs, ys, floor, color=accent, alpha=0.18, zorder=2)

    last_x, last_y = xs[-1], ys[-1]
    offset = [[last_x, last_y]]
    halo.set_offsets(offset)
    mid.set_offsets(offset)
    core.set_offsets(offset)

    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())
    return buf[..., :3].copy()
