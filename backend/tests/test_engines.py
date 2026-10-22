from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest
from app.backtesting.engine import run_backtest
from app.features.engine import engineer_features
from app.market_data.provider import MarketDataError, validate_candles
from app.risk.engine import RiskManager


def market_frame(rows: int = 100) -> pd.DataFrame:
    index = pd.date_range("2025-01-01", periods=rows, freq="B")
    close = pd.Series([100 + index * 0.25 + (index % 7) for index in range(rows)], index=index)
    return pd.DataFrame(
        {"open": close - 0.2, "high": close + 1, "low": close - 1, "close": close, "volume": 1_000_000},
        index=index,
    )


def test_feature_engine_produces_momentum_and_risk_features() -> None:
    features = engineer_features(market_frame())
    assert {"rsi", "macd", "atr", "relative_volume", "distance_52w_high"}.issubset(features.columns)
    assert features["sma_20"].iloc[-1] > 0


def test_backtest_tracks_costs_and_benchmark() -> None:
    result = run_backtest(market_frame(), "moving_average", commission=1, slippage=0.001)
    assert result["equity_curve"]
    assert "benchmark_return" in result["metrics"]
    assert result["metrics"]["trade_count"] >= 1


def test_backtest_rejects_missing_market_data() -> None:
    with pytest.raises(ValueError, match="requires market data"):
        run_backtest(pd.DataFrame(), "rsi")


def test_risk_manager_blocks_disabled_trading_and_oversized_positions() -> None:
    manager = RiskManager(max_position=0.25)
    disabled = manager.validate_order(
        side="BUY", order_value=100, cash=1000, equity=1000, exposure=0, confidence=0.8, trading_enabled=False
    )
    oversized = manager.validate_order(
        side="BUY", order_value=300, cash=1000, equity=1000, exposure=0, confidence=0.8, trading_enabled=True
    )
    assert disabled.code == "TRADING_DISABLED"
    assert oversized.code == "POSITION_TOO_LARGE"


def test_market_validation_rejects_duplicates_and_negative_prices() -> None:
    timestamp = datetime.now(UTC)
    row = {
        "symbol": "AAPL",
        "timestamp": timestamp,
        "open": 100,
        "high": 101,
        "low": 99,
        "close": 100,
        "adjusted_close": 100,
        "volume": 1000,
    }
    with pytest.raises(MarketDataError, match="Duplicate"):
        validate_candles([row, row])
    with pytest.raises(MarketDataError, match="non-positive"):
        validate_candles([{**row, "timestamp": timestamp + timedelta(days=1), "close": -1}])
