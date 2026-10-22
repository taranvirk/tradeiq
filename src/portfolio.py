from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from .metrics import calculate_metrics


def _price_column(frame: pd.DataFrame) -> pd.Series:
    return frame["Adj Close"] if "Adj Close" in frame.columns else frame["Close"]


def build_portfolio_equity(
    price_frames: Mapping[str, pd.DataFrame],
    initial_capital: float = 10_000,
    weights: dict[str, float] | None = None,
) -> tuple[pd.DataFrame, dict[str, float], dict[str, float]]:
    if not price_frames:
        raise ValueError("Portfolio requires at least one ticker.")

    prices = pd.concat(
        {ticker: _price_column(frame) for ticker, frame in price_frames.items()}, axis=1
    ).sort_index()
    prices = prices.ffill().dropna(how="any")
    returns = prices.pct_change().fillna(0.0)

    if weights is None:
        equal_weight = 1 / len(prices.columns)
        normalized_weights = {ticker: equal_weight for ticker in prices.columns}
    else:
        filtered = {ticker: float(weights.get(ticker, 0.0)) for ticker in prices.columns}
        total = sum(filtered.values())
        if total <= 0:
            raise ValueError("Portfolio weights must sum to more than 0.")
        normalized_weights = {ticker: value / total for ticker, value in filtered.items()}

    weight_series = pd.Series(normalized_weights)
    portfolio_returns = returns.mul(weight_series, axis=1).sum(axis=1)
    equity = initial_capital * (1 + portfolio_returns).cumprod()

    portfolio_frame = pd.DataFrame(
        {
            "Portfolio Return": portfolio_returns,
            "Equity": equity,
        },
        index=returns.index,
    )
    portfolio_frame["Drawdown"] = portfolio_frame["Equity"] / portfolio_frame["Equity"].cummax() - 1

    metrics = calculate_metrics(portfolio_frame["Equity"]).as_dict()
    return portfolio_frame, metrics, normalized_weights
