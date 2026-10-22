from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .indicators import add_indicators, compute_rsi
from .metrics import calculate_metrics


@dataclass
class BacktestResult:
    strategy_name: str
    frame: pd.DataFrame
    metrics: dict[str, float]
    trades: pd.DataFrame


def _price_series(df: pd.DataFrame) -> pd.Series:
    return df["Adj Close"] if "Adj Close" in df.columns else df["Close"]


def _format_trades(trades: list[dict]) -> pd.DataFrame:
    if not trades:
        return pd.DataFrame(columns=["Date", "Action", "Price", "Reason"])

    trade_df = pd.DataFrame(trades)
    trade_df["Date"] = pd.to_datetime(trade_df["Date"])
    return trade_df


def _finalize_strategy_frame(
    base: pd.DataFrame, strategy_returns: pd.Series, initial_capital: float
) -> tuple[pd.DataFrame, dict[str, float]]:
    out = base.copy()
    out["Strategy Return"] = strategy_returns.fillna(0.0)
    out["Equity"] = initial_capital * (1 + out["Strategy Return"]).cumprod()
    metrics = calculate_metrics(out["Equity"]).as_dict()
    return out, metrics


def buy_and_hold_backtest(df: pd.DataFrame, initial_capital: float = 10_000) -> BacktestResult:
    frame = add_indicators(df)
    frame["Signal"] = 1
    frame["Position"] = 1
    frame["Market Return"] = frame["Price"].pct_change().fillna(0.0)

    result_frame, metrics = _finalize_strategy_frame(frame, frame["Market Return"], initial_capital)
    trades = _format_trades(
        [
            {
                "Date": result_frame.index[0],
                "Action": "BUY",
                "Price": float(result_frame["Price"].iloc[0]),
                "Reason": "Initial allocation",
            }
        ]
    )

    return BacktestResult("Buy and Hold", result_frame, metrics, trades)


def sma_crossover_backtest(
    df: pd.DataFrame,
    short_window: int = 20,
    long_window: int = 50,
    initial_capital: float = 10_000,
) -> BacktestResult:
    if short_window >= long_window:
        raise ValueError("Short SMA window must be smaller than the long SMA window.")

    frame = add_indicators(df)
    price = frame["Price"]
    frame["SMA Short"] = price.rolling(short_window).mean()
    frame["SMA Long"] = price.rolling(long_window).mean()
    frame["Signal"] = (frame["SMA Short"] > frame["SMA Long"]).astype(int)
    frame["Position"] = frame["Signal"].shift(1).fillna(0)
    frame["Market Return"] = price.pct_change().fillna(0.0)
    strategy_returns = frame["Position"] * frame["Market Return"]

    trades: list[dict] = []
    signal_changes = frame["Signal"].diff().fillna(frame["Signal"])
    for date, change in signal_changes.items():
        if change == 1:
            trades.append(
                {
                    "Date": date,
                    "Action": "BUY",
                    "Price": float(price.loc[date]),
                    "Reason": f"SMA{short_window} crossed above SMA{long_window}",
                }
            )
        elif change == -1:
            trades.append(
                {
                    "Date": date,
                    "Action": "SELL",
                    "Price": float(price.loc[date]),
                    "Reason": f"SMA{short_window} crossed below SMA{long_window}",
                }
            )

    result_frame, metrics = _finalize_strategy_frame(frame, strategy_returns, initial_capital)
    return BacktestResult(
        f"SMA {short_window}/{long_window} Crossover", result_frame, metrics, _format_trades(trades)
    )


def rsi_mean_reversion_backtest(
    df: pd.DataFrame,
    window: int = 14,
    lower: float = 30.0,
    upper: float = 55.0,
    initial_capital: float = 10_000,
) -> BacktestResult:
    if lower >= upper:
        raise ValueError("RSI lower threshold must be smaller than the upper threshold.")

    frame = add_indicators(df)
    price = frame["Price"]
    frame["RSI Strategy"] = frame["RSI14"] if window == 14 else compute_rsi(price, window)
    frame["Signal"] = 0
    frame["Position"] = 0
    position = 0
    trades: list[dict] = []

    for date, row in frame.iterrows():
        rsi = float(row["RSI Strategy"])
        current_price = float(row["Price"])

        if position == 0 and rsi < lower:
            position = 1
            frame.loc[date, "Signal"] = 1
            trades.append(
                {
                    "Date": date,
                    "Action": "BUY",
                    "Price": current_price,
                    "Reason": f"RSI dropped below {lower}",
                }
            )
        elif position == 1 and rsi > upper:
            position = 0
            frame.loc[date, "Signal"] = -1
            trades.append(
                {"Date": date, "Action": "SELL", "Price": current_price, "Reason": f"RSI rose above {upper}"}
            )

        frame.loc[date, "Position"] = position

    frame["Position"] = frame["Position"].shift(1).fillna(0)
    frame["Market Return"] = price.pct_change().fillna(0.0)
    strategy_returns = frame["Position"] * frame["Market Return"]

    result_frame, metrics = _finalize_strategy_frame(frame, strategy_returns, initial_capital)
    return BacktestResult("RSI Mean Reversion", result_frame, metrics, _format_trades(trades))
