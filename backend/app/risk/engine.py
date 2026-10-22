from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    code: str
    message: str


class RiskManager:
    def __init__(
        self, max_position: float = 0.25, max_exposure: float = 0.85, minimum_confidence: float = 0.55
    ):
        self.max_position = max_position
        self.max_exposure = max_exposure
        self.minimum_confidence = minimum_confidence

    def validate_order(
        self,
        *,
        side: str,
        order_value: float,
        cash: float,
        equity: float,
        exposure: float,
        confidence: float | None,
        trading_enabled: bool,
    ) -> RiskDecision:
        if not trading_enabled:
            return RiskDecision(False, "TRADING_DISABLED", "The trading kill switch is disabled.")
        if order_value <= 0:
            return RiskDecision(False, "INVALID_ORDER_VALUE", "Order value must be positive.")
        if side == "BUY" and order_value > cash:
            return RiskDecision(False, "INSUFFICIENT_BUYING_POWER", "Order exceeds available buying power.")
        if side == "BUY" and equity and order_value / equity > self.max_position:
            return RiskDecision(False, "POSITION_TOO_LARGE", "Order exceeds the maximum position size.")
        if side == "BUY" and equity and (exposure + order_value) / equity > self.max_exposure:
            return RiskDecision(False, "EXPOSURE_LIMIT", "Order exceeds maximum portfolio exposure.")
        if confidence is not None and confidence < self.minimum_confidence:
            return RiskDecision(False, "LOW_CONFIDENCE", "Signal confidence is below the configured minimum.")
        return RiskDecision(True, "APPROVED", "Order passed all risk controls.")

    @staticmethod
    def position_size(
        equity: float, price: float, method: str, value: float, stop_loss_percent: float = 0.05
    ) -> float:
        if price <= 0 or equity <= 0 or value <= 0:
            raise ValueError("Equity, price, and sizing value must be positive")
        if method == "fixed":
            dollars = value
        elif method == "percent":
            dollars = equity * value
        elif method == "risk":
            dollars = equity * value / stop_loss_percent
        else:
            raise ValueError("Method must be fixed, percent, or risk")
        return max(0, int(dollars / price))
