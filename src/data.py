from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
import yfinance as yf

REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]


def parse_tickers(raw: str | Iterable[str]) -> list[str]:
    if isinstance(raw, str):
        values = raw.replace("\n", ",").split(",")
    else:
        values = list(raw)

    tickers = []
    seen = set()
    for value in values:
        ticker = str(value).strip().upper()
        if ticker and ticker not in seen:
            seen.add(ticker)
            tickers.append(ticker)
    return tickers


def _clean_single_ticker_frame(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()

    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)

    for col in REQUIRED_COLUMNS:
        if col not in frame.columns:
            if col == "Adj Close" and "Close" in frame.columns:
                frame[col] = frame["Close"]
            elif col == "Volume":
                frame[col] = 0
            else:
                raise ValueError(f"Missing required market data column: {col}")

    frame = frame[REQUIRED_COLUMNS]
    frame.index = pd.to_datetime(frame.index)
    frame = frame.sort_index()
    frame = frame.dropna(subset=["Close"])
    return frame


def download_price_data(tickers: list[str], start: str, end: str) -> dict[str, pd.DataFrame]:
    if not tickers:
        raise ValueError("No tickers were provided.")

    raw = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        auto_adjust=False,
        group_by="ticker",
        progress=False,
        threads=True,
    )

    if raw.empty:
        raise ValueError("No price data returned. Try a different date range or ticker.")

    frames: dict[str, pd.DataFrame] = {}

    if len(tickers) == 1:
        frames[tickers[0]] = _clean_single_ticker_frame(raw)
        return frames

    for ticker in tickers:
        if ticker not in raw.columns.get_level_values(0):
            continue
        frame = raw[ticker].copy()
        frames[ticker] = _clean_single_ticker_frame(frame)

    if not frames:
        raise ValueError("No valid ticker data could be loaded.")

    return frames
