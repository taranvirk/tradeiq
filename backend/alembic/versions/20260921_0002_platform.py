"""Add complete TradeIQ platform schema.

Revision ID: 20260921_0002
Revises: 20260917_0001
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260921_0002"
down_revision: str | None = "20260917_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def created_at() -> sa.Column:
    return sa.Column("created_at", sa.DateTime(timezone=True), nullable=False)


def upgrade() -> None:
    op.add_column("system_events", sa.Column("details", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.create_table(
        "users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False), created_at(), sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table(
        "stocks", sa.Column("symbol", sa.String(12), primary_key=True), sa.Column("company_name", sa.String(160), nullable=False),
        sa.Column("sector", sa.String(100), nullable=False), sa.Column("exchange", sa.String(32), nullable=False),
    )
    op.create_table(
        "watchlist_items", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("symbol", sa.String(12), sa.ForeignKey("stocks.symbol"), nullable=False), created_at(),
        sa.UniqueConstraint("user_id", "symbol"),
    )
    op.create_index("ix_watchlist_items_user_id", "watchlist_items", ["user_id"])
    op.create_index("ix_watchlist_items_symbol", "watchlist_items", ["symbol"])
    op.create_table(
        "market_data", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symbol", sa.String(12), sa.ForeignKey("stocks.symbol"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False), sa.Column("interval", sa.String(12), nullable=False),
        sa.Column("open", sa.Float(), nullable=False), sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False), sa.Column("close", sa.Float(), nullable=False),
        sa.Column("adjusted_close", sa.Float(), nullable=False), sa.Column("volume", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(40), nullable=False), sa.UniqueConstraint("symbol", "timestamp", "interval"),
    )
    op.create_index("ix_market_data_symbol", "market_data", ["symbol"])
    op.create_index("ix_market_data_timestamp", "market_data", ["timestamp"])
    op.create_table(
        "ml_models", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("model_name", sa.String(80), nullable=False),
        sa.Column("version", sa.String(80), nullable=False, unique=True), sa.Column("algorithm", sa.String(80), nullable=False),
        sa.Column("training_start", sa.Date(), nullable=False), sa.Column("training_end", sa.Date(), nullable=False),
        sa.Column("features", sa.JSON(), nullable=False), sa.Column("hyperparameters", sa.JSON(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False), sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False), created_at(),
    )
    op.create_table(
        "ml_experiments", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("algorithm", sa.String(80), nullable=False),
        sa.Column("symbol", sa.String(12), nullable=False), sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("hyperparameters", sa.JSON(), nullable=False), sa.Column("training_window", sa.String(80), nullable=False),
        sa.Column("test_window", sa.String(80), nullable=False), sa.Column("metrics", sa.JSON(), nullable=False), created_at(),
    )
    op.create_table(
        "predictions", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("symbol", sa.String(12), sa.ForeignKey("stocks.symbol"), nullable=False),
        sa.Column("signal", sa.String(8), nullable=False), sa.Column("probability_up", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False), sa.Column("model_version", sa.String(80), nullable=False),
        sa.Column("explanation", sa.JSON(), nullable=False), created_at(),
    )
    op.create_index("ix_predictions_user_id", "predictions", ["user_id"])
    op.create_index("ix_predictions_symbol", "predictions", ["symbol"])
    op.create_table(
        "backtests", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("symbol", sa.String(12), nullable=False),
        sa.Column("strategy", sa.String(80), nullable=False), sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False), sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False), sa.Column("equity_curve", sa.JSON(), nullable=False),
        sa.Column("benchmark_curve", sa.JSON(), nullable=False), sa.Column("status", sa.String(20), nullable=False), created_at(),
    )
    op.create_index("ix_backtests_user_id", "backtests", ["user_id"])
    op.create_table(
        "backtest_trades", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("backtest_id", sa.Integer(), sa.ForeignKey("backtests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("symbol", sa.String(12), nullable=False), sa.Column("side", sa.String(8), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False), sa.Column("price", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False), sa.Column("pnl", sa.Float(), nullable=False),
        sa.Column("signal_confidence", sa.Float(), nullable=False),
    )
    op.create_index("ix_backtest_trades_backtest_id", "backtest_trades", ["backtest_id"])
    op.create_table(
        "portfolios", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("cash", sa.Float(), nullable=False), sa.Column("initial_cash", sa.Float(), nullable=False),
        sa.Column("realized_pnl", sa.Float(), nullable=False), created_at(),
    )
    op.create_table(
        "portfolio_snapshots", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("portfolio_id", sa.Integer(), sa.ForeignKey("portfolios.id"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False), sa.Column("equity", sa.Float(), nullable=False),
        sa.Column("cash", sa.Float(), nullable=False), sa.Column("exposure", sa.Float(), nullable=False),
    )
    op.create_index("ix_portfolio_snapshots_portfolio_id", "portfolio_snapshots", ["portfolio_id"])
    op.create_table(
        "positions", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("portfolio_id", sa.Integer(), sa.ForeignKey("portfolios.id"), nullable=False),
        sa.Column("symbol", sa.String(12), nullable=False), sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("average_entry", sa.Float(), nullable=False), sa.UniqueConstraint("portfolio_id", "symbol"),
    )
    op.create_index("ix_positions_portfolio_id", "positions", ["portfolio_id"])
    op.create_table(
        "orders", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("symbol", sa.String(12), nullable=False),
        sa.Column("side", sa.String(8), nullable=False), sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("order_type", sa.String(16), nullable=False), sa.Column("limit_price", sa.Float(), nullable=True),
        sa.Column("status", sa.String(24), nullable=False), sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("filled_at", sa.DateTime(timezone=True), nullable=True), sa.Column("average_fill_price", sa.Float(), nullable=True),
        sa.Column("broker_order_id", sa.String(100), nullable=True), sa.Column("strategy", sa.String(80), nullable=False),
        sa.Column("model_version", sa.String(80), nullable=True), sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("client_order_id", sa.String(100), nullable=False, unique=True), created_at(),
    )
    op.create_index("ix_orders_user_id", "orders", ["user_id"])
    op.create_table(
        "trades", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False, unique=True),
        sa.Column("symbol", sa.String(12), nullable=False), sa.Column("side", sa.String(8), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False), sa.Column("entry_price", sa.Float(), nullable=False),
        sa.Column("exit_price", sa.Float(), nullable=True), sa.Column("pnl", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True), sa.Column("strategy", sa.String(80), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False), created_at(),
    )
    op.create_index("ix_trades_user_id", "trades", ["user_id"])
    op.create_table(
        "risk_events", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False), sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("message", sa.String(500), nullable=False), sa.Column("details", sa.JSON(), nullable=False), created_at(),
    )
    op.create_index("ix_risk_events_user_id", "risk_events", ["user_id"])


def downgrade() -> None:
    for table in (
        "risk_events", "trades", "orders", "positions", "portfolio_snapshots", "portfolios",
        "backtest_trades", "backtests", "predictions", "ml_experiments", "ml_models", "market_data",
        "watchlist_items", "stocks", "users",
    ):
        op.drop_table(table)
    op.drop_column("system_events", "details")
