"""CLI entry point: `python -m stock_chart.cli RELIANCE.NS`"""

import argparse
import sys

from .generate import generate


def _default_output_path(ticker: str) -> str:
    safe = ticker.replace("^", "").replace(".", "_")
    return f"{safe}.png"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a stock/index intraday chart card from a Yahoo Finance ticker."
    )
    parser.add_argument("ticker", help="Yahoo Finance ticker, e.g. RELIANCE.NS, TCS.NS, ^NSEI")
    parser.add_argument("-o", "--output", default=None, help="Output PNG path (default: <ticker>.png)")
    args = parser.parse_args()

    out_path = args.output or _default_output_path(args.ticker)
    try:
        generate(args.ticker, out_path)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
