"""Fetch 5-minute FX quotes using yfinance.

This script downloads 5-minute candle data for currency pairs using Yahoo! Finance
via the `yfinance` package. It is intended to provide a quick way to retrieve
recent intraday quotes (up to 60 days, subject to Yahoo! Finance limits).

Example usage:
    python scripts/fetch_fx_quotes.py EURUSD GBPJPY --period 5d --output fx_quotes.csv

The script saves the combined dataset to CSV if an output path is provided,
otherwise it prints the head of each dataframe to stdout.

Requirements:
    pip install yfinance pandas
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd
import yfinance as yf


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download 5-minute FX quotes for the requested currency pairs."
    )
    parser.add_argument(
        "pairs",
        nargs="+",
        help=(
            "List of currency pairs (e.g. EURUSD, USDJPY). "
            "These will be mapped to Yahoo! Finance tickers (PAIR=X)."
        ),
    )
    parser.add_argument(
        "--period",
        default="5d",
        help=(
            "Historical look-back period accepted by yfinance (default: 5d). "
            "Examples: 1d, 5d, 1mo, 3mo."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to save the combined results as CSV.",
    )
    return parser.parse_args()


def to_yahoo_ticker(pair: str) -> str:
    pair = pair.strip().upper()
    if len(pair) not in {6, 7}:  # Basic sanity check (supports e.g. XAUUSD)
        raise ValueError(
            f"Currency pair '{pair}' must have 6 or 7 characters (base+quote)."
        )
    if pair.endswith("=X"):
        return pair
    return f"{pair}=X"


def download_pair(pair: str, period: str) -> pd.DataFrame:
    ticker = to_yahoo_ticker(pair)
    df = yf.download(ticker, interval="5m", period=period, progress=False)
    if df.empty:
        raise ValueError(
            f"No data returned for {pair} (ticker {ticker}). "
            "Check the pair symbol or adjust the period."
        )
    df = df.reset_index().assign(pair=pair.upper())
    return df


def fetch_pairs(pairs: Iterable[str], period: str) -> pd.DataFrame:
    frames = []
    for pair in pairs:
        frames.append(download_pair(pair, period))
    combined = pd.concat(frames, ignore_index=True)
    combined = combined[["pair", "Datetime", "Open", "High", "Low", "Close", "Adj Close", "Volume"]]
    combined = combined.rename(columns={"Datetime": "timestamp"})
    return combined


def main() -> None:
    args = parse_args()
    try:
        data = fetch_pairs(args.pairs, args.period)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        data.to_csv(args.output, index=False)
        print(f"Saved {len(data)} rows to {args.output}")
    else:
        print(data.head())


if __name__ == "__main__":
    main()
