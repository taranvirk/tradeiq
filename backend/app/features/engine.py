from __future__ import annotations

import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "return_1d",
    "return_3d",
    "return_5d",
    "return_10d",
    "return_20d",
    "sma_10",
    "sma_20",
    "sma_50",
    "ema_12",
    "ema_26",
    "rsi",
    "macd",
    "macd_signal",
    "momentum",
    "roc",
    "atr",
    "volatility",
    "price_range",
    "relative_volume",
    "volume_change",
    "distance_sma20",
    "distance_sma50",
    "distance_52w_high",
    "distance_52w_low",
]


def engineer_features(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"open", "high", "low", "close", "volume"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Missing market columns: {sorted(required - set(frame.columns))}")
    data = frame.copy().sort_index()
    close = data["close"].astype(float)
    for days in (1, 3, 5, 10, 20):
        data[f"return_{days}d"] = close.pct_change(days)
    for days in (10, 20, 50, 200):
        data[f"sma_{days}"] = close.rolling(days, min_periods=min(days, 10)).mean()
    data["ema_12"] = close.ewm(span=12, adjust=False).mean()
    data["ema_26"] = close.ewm(span=26, adjust=False).mean()
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    loss = -delta.clip(upper=0).ewm(alpha=1 / 14, adjust=False).mean()
    data["rsi"] = 100 - 100 / (1 + gain / loss.replace(0, np.nan))
    data["macd"] = data["ema_12"] - data["ema_26"]
    data["macd_signal"] = data["macd"].ewm(span=9, adjust=False).mean()
    data["momentum"] = close - close.shift(10)
    data["roc"] = close.pct_change(10) * 100
    previous_close = close.shift(1)
    true_range = pd.concat(
        [
            (data["high"] - data["low"]),
            (data["high"] - previous_close).abs(),
            (data["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    data["atr"] = true_range.rolling(14, min_periods=5).mean()
    data["volatility"] = data["return_1d"].rolling(20, min_periods=5).std() * np.sqrt(252)
    data["price_range"] = (data["high"] - data["low"]) / close
    volume_mean = data["volume"].rolling(20, min_periods=5).mean()
    data["relative_volume"] = data["volume"] / volume_mean
    data["volume_change"] = data["volume"].pct_change()
    data["distance_sma20"] = close / data["sma_20"] - 1
    data["distance_sma50"] = close / data["sma_50"] - 1
    data["distance_52w_high"] = close / close.rolling(252, min_periods=20).max() - 1
    data["distance_52w_low"] = close / close.rolling(252, min_periods=20).min() - 1
    data.replace([np.inf, -np.inf], np.nan, inplace=True)
    return data
