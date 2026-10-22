from __future__ import annotations

import pandas as pd

from src.backtest import buy_and_hold_backtest, sma_crossover_backtest
from src.portfolio import build_portfolio_equity


def sample_frame() -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=120, freq="B")
    close = pd.Series(range(100, 220), index=index, dtype=float)
    return pd.DataFrame(
        {
            "Open": close - 1,
            "High": close + 1,
            "Low": close - 2,
            "Close": close,
            "Adj Close": close,
            "Volume": 1_000_000,
        },
        index=index,
    )


def test_buy_and_hold_generates_equity_curve() -> None:
    result = buy_and_hold_backtest(sample_frame(), initial_capital=10_000)
    assert not result.frame.empty
    assert result.frame["Equity"].iloc[-1] > 10_000


def test_sma_strategy_runs() -> None:
    result = sma_crossover_backtest(sample_frame(), short_window=10, long_window=20, initial_capital=10_000)
    assert "Equity" in result.frame.columns
    assert isinstance(result.metrics["Cumulative Return"], float)


def test_portfolio_builder_normalizes_weights() -> None:
    frame = sample_frame()
    portfolio_frame, _, weights = build_portfolio_equity(
        {"AAA": frame, "BBB": frame}, weights={"AAA": 70, "BBB": 30}
    )
    assert abs(sum(weights.values()) - 1.0) < 1e-9
    assert not portfolio_frame.empty
