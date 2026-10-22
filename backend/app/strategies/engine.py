from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class TradingStrategy(ABC):
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series: ...


class MovingAverageStrategy(TradingStrategy):
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        fast = data["close"].rolling(20, min_periods=5).mean()
        slow = data["close"].rolling(50, min_periods=10).mean()
        return (fast > slow).astype(int)


class RSIStrategy(TradingStrategy):
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        rsi = data["rsi"].fillna(50)
        state = 0
        values = []
        for value in rsi:
            if value < 35:
                state = 1
            elif value > 65:
                state = 0
            values.append(state)
        return pd.Series(values, index=data.index)


class MLStrategy(TradingStrategy):
    def __init__(self, buy_threshold: float = 0.65, sell_threshold: float = 0.35) -> None:
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        probability = data.get("probability_up", pd.Series(0.5, index=data.index))
        return (probability >= self.buy_threshold).astype(int).where(probability > self.sell_threshold, 0)


def get_strategy(name: str) -> TradingStrategy:
    strategies = {"moving_average": MovingAverageStrategy, "rsi": RSIStrategy, "ml": MLStrategy}
    try:
        return strategies[name]()
    except KeyError as exc:
        raise ValueError(f"Unknown strategy: {name}") from exc
