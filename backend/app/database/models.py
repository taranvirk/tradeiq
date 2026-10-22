from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    first_name: Mapped[str] = mapped_column(String(60), default="")
    last_name: Mapped[str] = mapped_column(String(60), default="")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    token_version: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PaperAccount(TimestampMixin, Base):
    __tablename__ = "paper_accounts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100), default="Paper Portfolio")
    initial_balance: Mapped[float] = mapped_column(Numeric(18, 2))
    cash_balance: Mapped[float] = mapped_column(Numeric(18, 2))
    realized_pnl: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    risk_per_trade: Mapped[float] = mapped_column(Float, default=0.01)
    max_position_size: Mapped[float] = mapped_column(Float, default=0.25)
    max_daily_loss: Mapped[float] = mapped_column(Float, default=0.05)
    default_order_amount: Mapped[float] = mapped_column(Numeric(18, 2), default=500)
    ai_auto_trade_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Stock(Base):
    __tablename__ = "stocks"
    symbol: Mapped[str] = mapped_column(String(12), primary_key=True)
    company_name: Mapped[str] = mapped_column(String(160))
    sector: Mapped[str] = mapped_column(String(100), default="Unknown")
    exchange: Mapped[str] = mapped_column(String(32), default="NASDAQ")


class WatchlistItem(TimestampMixin, Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (UniqueConstraint("user_id", "symbol"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    symbol: Mapped[str] = mapped_column(ForeignKey("stocks.symbol"), index=True)


class MarketCandle(Base):
    __tablename__ = "market_data"
    __table_args__ = (UniqueConstraint("symbol", "timestamp", "interval"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(ForeignKey("stocks.symbol"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    interval: Mapped[str] = mapped_column(String(12), default="1d")
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    adjusted_close: Mapped[float] = mapped_column(Float)
    volume: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(40))


class MLModel(TimestampMixin, Base):
    __tablename__ = "ml_models"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name: Mapped[str] = mapped_column(String(80))
    version: Mapped[str] = mapped_column(String(80), unique=True)
    algorithm: Mapped[str] = mapped_column(String(80))
    training_start: Mapped[date] = mapped_column(Date)
    training_end: Mapped[date] = mapped_column(Date)
    features: Mapped[list] = mapped_column(JSON)
    hyperparameters: Mapped[dict] = mapped_column(JSON)
    metrics: Mapped[dict] = mapped_column(JSON)
    file_path: Mapped[str] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)


class MLExperiment(TimestampMixin, Base):
    __tablename__ = "ml_experiments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    algorithm: Mapped[str] = mapped_column(String(80))
    symbol: Mapped[str] = mapped_column(String(12))
    features: Mapped[list] = mapped_column(JSON)
    hyperparameters: Mapped[dict] = mapped_column(JSON)
    training_window: Mapped[str] = mapped_column(String(80))
    test_window: Mapped[str] = mapped_column(String(80))
    metrics: Mapped[dict] = mapped_column(JSON)


class Prediction(TimestampMixin, Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    symbol: Mapped[str] = mapped_column(ForeignKey("stocks.symbol"), index=True)
    signal: Mapped[str] = mapped_column(String(8))
    probability_up: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(80))
    explanation: Mapped[dict] = mapped_column(JSON)


class Backtest(TimestampMixin, Base):
    __tablename__ = "backtests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(12))
    strategy: Mapped[str] = mapped_column(String(80))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    config: Mapped[dict] = mapped_column(JSON)
    metrics: Mapped[dict] = mapped_column(JSON)
    equity_curve: Mapped[list] = mapped_column(JSON)
    benchmark_curve: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="COMPLETED")


class BacktestTrade(Base):
    __tablename__ = "backtest_trades"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    backtest_id: Mapped[int] = mapped_column(ForeignKey("backtests.id", ondelete="CASCADE"), index=True)
    symbol: Mapped[str] = mapped_column(String(12))
    side: Mapped[str] = mapped_column(String(8))
    quantity: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    pnl: Mapped[float] = mapped_column(Float, default=0)
    signal_confidence: Mapped[float] = mapped_column(Float, default=0)


class Portfolio(TimestampMixin, Base):
    __tablename__ = "portfolios"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    paper_account_id: Mapped[int | None] = mapped_column(ForeignKey("paper_accounts.id"), unique=True, nullable=True)
    cash: Mapped[float] = mapped_column(Float, default=10000)
    initial_cash: Mapped[float] = mapped_column(Float, default=10000)
    realized_pnl: Mapped[float] = mapped_column(Float, default=0)


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    paper_account_id: Mapped[int | None] = mapped_column(ForeignKey("paper_accounts.id"), index=True, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    equity: Mapped[float] = mapped_column(Float)
    cash: Mapped[float] = mapped_column(Float)
    exposure: Mapped[float] = mapped_column(Float)
    positions_value: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    daily_pnl: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    total_pnl: Mapped[float] = mapped_column(Numeric(18, 2), default=0)


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (UniqueConstraint("portfolio_id", "symbol"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(12))
    quantity: Mapped[float] = mapped_column(Float)
    average_entry: Mapped[float] = mapped_column(Float)


class Order(TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (UniqueConstraint("user_id", "client_order_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    paper_account_id: Mapped[int | None] = mapped_column(ForeignKey("paper_accounts.id"), index=True, nullable=True)
    symbol: Mapped[str] = mapped_column(String(12))
    side: Mapped[str] = mapped_column(String(8))
    quantity: Mapped[float] = mapped_column(Float)
    notional_amount: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    requested_price: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    order_type: Mapped[str] = mapped_column(String(16), default="market")
    limit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="CREATED")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    filled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    average_fill_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    broker_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    strategy: Mapped[str] = mapped_column(String(80), default="manual")
    model_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    mode: Mapped[str] = mapped_column(String(20), default="simulation")
    client_order_id: Mapped[str] = mapped_column(String(100))


class Trade(TimestampMixin, Base):
    __tablename__ = "trades"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    paper_account_id: Mapped[int | None] = mapped_column(ForeignKey("paper_accounts.id"), index=True, nullable=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    symbol: Mapped[str] = mapped_column(String(12))
    side: Mapped[str] = mapped_column(String(8))
    quantity: Mapped[float] = mapped_column(Float)
    entry_price: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    pnl: Mapped[float] = mapped_column(Float, default=0)
    value: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    realized_pnl: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    strategy: Mapped[str] = mapped_column(String(80))
    context: Mapped[dict] = mapped_column(JSON, default=dict)


class RiskEvent(TimestampMixin, Base):
    __tablename__ = "risk_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(String(500))
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class SystemEvent(TimestampMixin, Base):
    __tablename__ = "system_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    message: Mapped[str] = mapped_column(String(500))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
