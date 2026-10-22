from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class PerformanceMetrics:
    cumulative_return: float
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    max_drawdown: float

    def as_dict(self) -> dict[str, float]:
        return {
            "Cumulative Return": self.cumulative_return,
            "Annualized Return": self.annualized_return,
            "Annualized Volatility": self.annualized_volatility,
            "Sharpe Ratio": self.sharpe_ratio,
            "Max Drawdown": self.max_drawdown,
        }


def calculate_metrics(equity_curve: pd.Series) -> PerformanceMetrics:
    equity = equity_curve.dropna().astype(float)
    if equity.empty or len(equity) < 2:
        return PerformanceMetrics(0.0, 0.0, 0.0, 0.0, 0.0)

    returns = equity.pct_change().dropna()
    cumulative_return = (equity.iloc[-1] / equity.iloc[0]) - 1

    periods = len(returns)
    annualized_return = (equity.iloc[-1] / equity.iloc[0]) ** (252 / max(periods, 1)) - 1 if periods else 0.0
    annualized_volatility = returns.std(ddof=0) * np.sqrt(252) if not returns.empty else 0.0
    sharpe_ratio = (returns.mean() * 252 / annualized_volatility) if annualized_volatility else 0.0

    running_max = equity.cummax()
    drawdown = (equity / running_max) - 1
    max_drawdown = drawdown.min() if not drawdown.empty else 0.0

    return PerformanceMetrics(
        cumulative_return=float(cumulative_return),
        annualized_return=float(annualized_return),
        annualized_volatility=float(annualized_volatility),
        sharpe_ratio=float(sharpe_ratio),
        max_drawdown=float(max_drawdown),
    )
