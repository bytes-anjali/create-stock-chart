"""Render the fixed stock-chart card template (matching the reference design) as a PNG."""

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.patches import FancyBboxPatch, PathPatch
from matplotlib.path import Path

POSITIVE_COLOR = "#1DA57A"
NEGATIVE_COLOR = "#E24C4B"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#E7EEEA"
OUTER_BG = "#E9F5EF"
GRID_COLOR = "#ECEFED"
TEXT_DARK = "#14161A"
TEXT_MUTED = "#6B7280"

FIG_W, FIG_H = 11.2, 8.12  # inches; matches the reference card's aspect ratio


def render_card(snapshot, styled_prices, times, out_path, dpi: int = 100) -> None:
    """Draw the card for `snapshot` using `styled_prices` (already pattern-validated
    against the raw Yahoo series) sampled at `times`, and save it to `out_path`.
    """
    styled_prices = np.asarray(styled_prices, dtype=float)
    accent = POSITIVE_COLOR if snapshot.is_positive else NEGATIVE_COLOR
    arrow = "▲" if snapshot.is_positive else "▼"

    fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=dpi)
    fig.patch.set_facecolor(OUTER_BG)

    draw_card_background(fig)
    draw_header(fig, snapshot, accent, arrow)
    _draw_chart(fig, styled_prices, times, accent)

    fig.savefig(out_path, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)


def draw_card_background(fig) -> None:
    margin = 0.03
    card = FancyBboxPatch(
        (margin, margin),
        1 - 2 * margin,
        1 - 2 * margin,
        boxstyle="round,pad=0,rounding_size=0.045",
        linewidth=1.2,
        edgecolor=CARD_BORDER,
        facecolor=CARD_BG,
        transform=fig.transFigure,
        zorder=0,
    )
    fig.add_artist(card)


def draw_header(fig, snapshot, accent, arrow) -> None:
    fig.text(0.085, 0.905, snapshot.name, fontsize=27, fontweight="bold", color=TEXT_DARK, va="top")

    price_str = f"{snapshot.currency_symbol}{snapshot.latest_price:,.2f}"
    price_text = fig.text(0.085, 0.815, price_str, fontsize=31, fontweight="bold", color=TEXT_DARK, va="top")

    # Measure the actual rendered width of the price text so the change text starts
    # right after it without overlapping, regardless of currency/digit count.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    price_bbox = price_text.get_window_extent(renderer=renderer).transformed(fig.transFigure.inverted())

    change_str = f"{snapshot.change:+,.2f} ({snapshot.change_pct:+.2f}%) {arrow}"
    fig.text(price_bbox.x1 + 0.018, 0.818, change_str, fontsize=21, fontweight="bold", color=accent, va="top")


def prepare_axis(fig, styled_prices, times):
    """Add the chart axes with gridlines/tick labels fixed to the FULL series' range,
    so a partial (in-progress animation) reveal never rescales the axis mid-video.
    Returns (ax, x, y_min, y_max) for callers to plot the line/fill/dot into.
    """
    ax = fig.add_axes((0.075, 0.10, 0.80, 0.56))
    ax.set_facecolor(CARD_BG)
    for spine in ax.spines.values():
        spine.set_visible(False)

    x = np.arange(len(styled_prices))
    y_min, y_max = float(styled_prices.min()), float(styled_prices.max())
    y_span = max(y_max - y_min, 1e-9)

    y_ticks = np.linspace(y_min, y_max, 4)
    ax.set_yticks(y_ticks)
    ax.yaxis.tick_right()
    ax.set_yticklabels([f"{v:,.0f}" for v in y_ticks], fontsize=13, color=TEXT_MUTED)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="y", color=GRID_COLOR, linewidth=1)
    ax.set_ylim(y_min - y_span * 0.06, y_max + y_span * 0.06)

    n_ticks = min(4, len(times))
    tick_pos = np.linspace(0, len(times) - 1, n_ticks).astype(int)
    ax.set_xticks(tick_pos)
    ax.set_xticklabels([times[i].strftime("%H:%M") for i in tick_pos], fontsize=13, color=TEXT_MUTED)
    ax.tick_params(axis="x", length=0)
    ax.set_xlim(0, len(styled_prices) - 1)

    return ax, x, y_min, y_max


def _draw_chart(fig, styled_prices, times, accent) -> None:
    ax, x, y_min, _y_max = prepare_axis(fig, styled_prices, times)
    ax.plot(x, styled_prices, color=accent, linewidth=2.6, solid_capstyle="round", zorder=3)
    _fill_gradient_area(ax, x, styled_prices, y_min, accent)
    _draw_latest_dot(ax, x[-1], styled_prices[-1], accent)


def _fill_gradient_area(ax, x, y, floor, accent) -> None:
    verts = np.column_stack(
        [np.concatenate([x, x[::-1]]), np.concatenate([y, np.full_like(x, floor, dtype=float)])]
    )
    clip_patch = PathPatch(Path(verts), facecolor="none", edgecolor="none")
    ax.add_patch(clip_patch)

    r, g, b = to_rgb(accent)
    gradient = np.zeros((256, 1, 4))
    gradient[..., 0] = r
    gradient[..., 1] = g
    gradient[..., 2] = b
    gradient[..., 3] = np.linspace(0.30, 0.0, 256).reshape(-1, 1)

    image = ax.imshow(
        gradient,
        extent=(x.min(), x.max(), floor, y.max()),
        origin="upper",
        aspect="auto",
        zorder=2,
    )
    image.set_clip_path(clip_patch)


def _draw_latest_dot(ax, lx, ly, accent) -> None:
    ax.scatter([lx], [ly], s=950, color=accent, alpha=0.16, zorder=4, linewidths=0)
    ax.scatter([lx], [ly], s=170, color=accent, alpha=0.35, zorder=4, linewidths=0)
    ax.scatter([lx], [ly], s=55, color=accent, zorder=5, linewidths=0)
