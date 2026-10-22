"""Add multi-user onboarding and dedicated paper accounts.

Revision ID: 20260922_0003
Revises: 20260921_0002
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260922_0003"
down_revision: str | None = "20260921_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("first_name", sa.String(60), nullable=False, server_default=""))
    op.add_column("users", sa.Column("last_name", sa.String(60), nullable=False, server_default=""))
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("users", sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))
    op.add_column(
        "users",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.execute(
        "UPDATE users SET first_name = split_part(full_name, ' ', 1), "
        "last_name = CASE WHEN position(' ' in full_name) > 0 "
        "THEN substring(full_name from position(' ' in full_name) + 1) ELSE '' END"
    )

    op.create_table(
        "paper_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False, server_default="Paper Portfolio"),
        sa.Column("initial_balance", sa.Numeric(18, 2), nullable=False),
        sa.Column("cash_balance", sa.Numeric(18, 2), nullable=False),
        sa.Column("realized_pnl", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("risk_per_trade", sa.Float(), nullable=False, server_default="0.01"),
        sa.Column("max_position_size", sa.Float(), nullable=False, server_default="0.25"),
        sa.Column("max_daily_loss", sa.Float(), nullable=False, server_default="0.05"),
        sa.Column("default_order_amount", sa.Numeric(18, 2), nullable=False, server_default="500"),
        sa.Column("ai_auto_trade_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_paper_accounts_user_id", "paper_accounts", ["user_id"])
    op.create_index("ix_paper_accounts_is_active", "paper_accounts", ["is_active"])
    op.execute(
        "INSERT INTO paper_accounts (user_id, name, initial_balance, cash_balance, realized_pnl) "
        "SELECT user_id, CASE WHEN user_id = (SELECT id FROM users WHERE is_demo = true LIMIT 1) "
        "THEN 'Demo Portfolio' ELSE 'Paper Portfolio' END, initial_cash, cash, realized_pnl FROM portfolios"
    )

    op.add_column("portfolios", sa.Column("paper_account_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_portfolios_paper_account", "portfolios", "paper_accounts", ["paper_account_id"], ["id"]
    )
    op.create_unique_constraint("uq_portfolios_paper_account_id", "portfolios", ["paper_account_id"])
    op.execute(
        "UPDATE portfolios p SET paper_account_id = pa.id FROM paper_accounts pa "
        "WHERE pa.user_id = p.user_id AND pa.is_active = true"
    )

    op.add_column("portfolio_snapshots", sa.Column("paper_account_id", sa.Integer(), nullable=True))
    op.add_column(
        "portfolio_snapshots",
        sa.Column("positions_value", sa.Numeric(18, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "portfolio_snapshots",
        sa.Column("daily_pnl", sa.Numeric(18, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "portfolio_snapshots",
        sa.Column("total_pnl", sa.Numeric(18, 2), nullable=False, server_default="0"),
    )
    op.create_foreign_key(
        "fk_snapshots_paper_account",
        "portfolio_snapshots",
        "paper_accounts",
        ["paper_account_id"],
        ["id"],
    )
    op.create_index("ix_portfolio_snapshots_paper_account_id", "portfolio_snapshots", ["paper_account_id"])
    op.execute(
        "UPDATE portfolio_snapshots s SET paper_account_id = p.paper_account_id, "
        "positions_value = s.exposure, total_pnl = s.equity - p.initial_cash "
        "FROM portfolios p WHERE p.id = s.portfolio_id"
    )

    for table in ("orders", "trades"):
        op.add_column(table, sa.Column("paper_account_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            f"fk_{table}_paper_account", table, "paper_accounts", ["paper_account_id"], ["id"]
        )
        op.create_index(f"ix_{table}_paper_account_id", table, ["paper_account_id"])
        op.execute(
            f"UPDATE {table} t SET paper_account_id = pa.id FROM paper_accounts pa "
            "WHERE pa.user_id = t.user_id AND pa.is_active = true"
        )
    op.add_column("orders", sa.Column("notional_amount", sa.Numeric(18, 2), nullable=True))
    op.add_column("orders", sa.Column("requested_price", sa.Numeric(18, 4), nullable=True))
    op.execute("UPDATE orders SET notional_amount = quantity * average_fill_price, requested_price = average_fill_price")
    op.drop_constraint("orders_client_order_id_key", "orders", type_="unique")
    op.create_unique_constraint("uq_orders_user_client_order", "orders", ["user_id", "client_order_id"])

    op.add_column("trades", sa.Column("value", sa.Numeric(18, 2), nullable=False, server_default="0"))
    op.add_column(
        "trades", sa.Column("realized_pnl", sa.Numeric(18, 2), nullable=False, server_default="0")
    )
    op.execute("UPDATE trades SET value = quantity * entry_price, realized_pnl = pnl")


def downgrade() -> None:
    op.drop_column("trades", "realized_pnl")
    op.drop_column("trades", "value")
    op.drop_index("ix_trades_paper_account_id", table_name="trades")
    op.drop_constraint("fk_trades_paper_account", "trades", type_="foreignkey")
    op.drop_column("trades", "paper_account_id")
    op.drop_constraint("uq_orders_user_client_order", "orders", type_="unique")
    op.create_unique_constraint("orders_client_order_id_key", "orders", ["client_order_id"])
    op.drop_column("orders", "requested_price")
    op.drop_column("orders", "notional_amount")
    op.drop_index("ix_orders_paper_account_id", table_name="orders")
    op.drop_constraint("fk_orders_paper_account", "orders", type_="foreignkey")
    op.drop_column("orders", "paper_account_id")
    op.drop_index("ix_portfolio_snapshots_paper_account_id", table_name="portfolio_snapshots")
    op.drop_constraint("fk_snapshots_paper_account", "portfolio_snapshots", type_="foreignkey")
    for column in ("total_pnl", "daily_pnl", "positions_value", "paper_account_id"):
        op.drop_column("portfolio_snapshots", column)
    op.drop_constraint("uq_portfolios_paper_account_id", "portfolios", type_="unique")
    op.drop_constraint("fk_portfolios_paper_account", "portfolios", type_="foreignkey")
    op.drop_column("portfolios", "paper_account_id")
    op.drop_index("ix_paper_accounts_is_active", table_name="paper_accounts")
    op.drop_index("ix_paper_accounts_user_id", table_name="paper_accounts")
    op.drop_table("paper_accounts")
    for column in (
        "last_login_at",
        "updated_at",
        "token_version",
        "is_active",
        "last_name",
        "first_name",
    ):
        op.drop_column("users", column)
