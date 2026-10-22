from __future__ import annotations

import math

import numpy as np
import pandas as pd

from app.features.engine import engineer_features
from app.strategies.engine import get_strategy


def run_backtest(
    candles: pd.DataFrame,
    strategy_name: str,
    starting_capital: float = 10_000,
    position_size: float = 0.8,
    commission: float = 1,
    slippage: float = 0.0005,
) -> dict:
    if candles.empty:
        raise ValueError("Backtest requires market data")
    data = engineer_features(candles)
    signals = get_strategy(strategy_name).generate_signals(data)
    cash, shares, entry_cost = float(starting_capital), 0.0, 0.0
    equity_curve, trades, returns = [], [], []
    previous_equity = starting_capital
    for timestamp, row in data.iterrows():
        price = float(row["close"])
        signal = int(signals.loc[timestamp])
        if signal == 1 and shares == 0:
            fill = price * (1 + slippage)
            shares = max(0.0, math.floor((cash * position_size - commission) / fill))
            if shares:
                cost = shares * fill + commission
                cash -= cost
                entry_cost = cost
                trades.append(
                    {
                        "timestamp": timestamp.isoformat(),
                        "side": "BUY",
                        "price": round(fill, 4),
                        "quantity": shares,
                        "pnl": 0.0,
                    }
                )
        elif signal == 0 and shares > 0:
            fill = price * (1 - slippage)
            proceeds = shares * fill - commission
            pnl = proceeds - entry_cost
            trades.append(
                {
                    "timestamp": timestamp.isoformat(),
                    "side": "SELL",
                    "price": round(fill, 4),
                    "quantity": shares,
                    "pnl": round(pnl, 2),
                }
            )
            cash += proceeds
            shares, entry_cost = 0.0, 0.0
        equity = cash + shares * price
        returns.append(equity / previous_equity - 1 if previous_equity else 0)
        previous_equity = equity
        equity_curve.append({"date": timestamp.date().isoformat(), "value": round(equity, 2)})
    final_equity = equity_curve[-1]["value"]
    series = pd.Series([point["value"] for point in equity_curve], dtype=float)
    daily = pd.Series(returns[1:], dtype=float)
    drawdown = series / series.cummax() - 1
    closed = [trade["pnl"] for trade in trades if trade["side"] == "SELL"]
    wins, losses = [p for p in closed if p > 0], [p for p in closed if p <= 0]
    years = max(len(series) / 252, 1 / 252)
    downside = daily[daily < 0].std()
    benchmark = starting_capital * data["close"] / float(data["close"].iloc[0])
    metrics = {
        "total_return": round((final_equity / starting_capital - 1) * 100, 2),
        "annualized_return": round(((final_equity / starting_capital) ** (1 / years) - 1) * 100, 2),
        "sharpe_ratio": round(float(daily.mean() / daily.std() * np.sqrt(252)), 2) if daily.std() else 0,
        "sortino_ratio": round(float(daily.mean() / downside * np.sqrt(252)), 2) if downside else 0,
        "max_drawdown": round(float(drawdown.min() * 100), 2),
        "win_rate": round(len(wins) / len(closed) * 100, 2) if closed else 0,
        "profit_factor": round(sum(wins) / abs(sum(losses)), 2)
        if losses
        else (float(len(wins)) if wins else 0),
        "average_win": round(float(np.mean(wins)), 2) if wins else 0,
        "average_loss": round(float(np.mean(losses)), 2) if losses else 0,
        "trade_count": len(trades),
        "exposure": round(float(signals.mean() * 100), 2),
        "volatility": round(float(daily.std() * np.sqrt(252) * 100), 2) if len(daily) else 0,
        "benchmark_return": round(float((benchmark.iloc[-1] / starting_capital - 1) * 100), 2),
    }
    return {
        "metrics": metrics,
        "equity_curve": equity_curve,
        "benchmark_curve": [
            {"date": timestamp.date().isoformat(), "value": round(float(value), 2)}
            for timestamp, value in benchmark.items()
        ],
        "trades": trades,
    }
