from __future__ import annotations

import pandas as pd


def compute_rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Compute the Relative Strength Index (RSI)."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, float("nan"))
    rsi = 100 - (100 / (1 + rs))
    return rsi.astype(float).fillna(50.0)


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add common technical indicators used by the dashboard and strategies."""
    out = df.copy()
    price = out["Adj Close"] if "Adj Close" in out.columns else out["Close"]

    out["Price"] = price
    out["Daily Return"] = price.pct_change().fillna(0.0)
    out["SMA20"] = price.rolling(20).mean()
    out["SMA50"] = price.rolling(50).mean()
    out["SMA200"] = price.rolling(200).mean()
    out["RSI14"] = compute_rsi(price, 14)
    out["Volatility20"] = out["Daily Return"].rolling(20).std() * (252**0.5)
    out["High-Low %"] = ((out["High"] - out["Low"]) / out["Close"]).replace(
        [pd.NA, float("inf"), float("-inf")], 0.0
    )

    return out
