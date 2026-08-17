"""CLI entry point: `python -m stock_chart.cli RELIANCE.NS`"""

import argparse
import sys

from .generate import generate, generate_video


def _default_output_path(ticker: str, video: bool) -> str:
    safe = ticker.replace("^", "").replace(".", "_")
    return f"{safe}.mp4" if video else f"{safe}.png"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a stock/index intraday chart card from a Yahoo Finance ticker."
    )
    parser.add_argument("ticker", help="Yahoo Finance ticker, e.g. RELIANCE.NS, TCS.NS, ^NSEI")
    parser.add_argument("-o", "--output", default=None, help="Output path (default: <ticker>.png/.mp4)")
    parser.add_argument(
        "--video",
        action="store_true",
        help="Render an MP4 tracing the line from the day's open to the last available price, instead of a static PNG",
    )
    args = parser.parse_args()

    out_path = args.output or _default_output_path(args.ticker, args.video)
    try:
        if args.video:
            generate_video(args.ticker, out_path)
        else:
            generate(args.ticker, out_path)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
