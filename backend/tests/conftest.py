from __future__ import annotations

import os
from datetime import UTC, datetime

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.pop("REDIS_URL", None)
os.environ["DEMO_MODE"] = "false"
os.environ["JWT_SECRET"] = "test-only-secret-that-is-longer-than-32-characters"

import pytest

from app.core.security import hash_password
from app.database.base import Base
from app.database.models import MarketCandle, PaperAccount, Portfolio, Stock, User
from app.database.session import SessionLocal, engine


@pytest.fixture(scope="session", autouse=True)
def database_schema():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        user = User(
            email="demo@tradeiq.dev",
            password_hash=hash_password("tradeiq-demo"),
            first_name="TradeIQ",
            last_name="Demo",
            full_name="TradeIQ Demo",
            is_demo=True,
        )
        db.add(user)
        db.flush()
        paper_account = PaperAccount(user_id=user.id, initial_balance=10_000, cash_balance=10_000)
        db.add(paper_account)
        db.flush()
        db.add(
            Portfolio(
                user_id=user.id,
                paper_account_id=paper_account.id,
                cash=10_000,
                initial_cash=10_000,
            )
        )
        db.add(Stock(symbol="AAPL", company_name="Apple Inc.", sector="Technology", exchange="NASDAQ"))
        db.add(Stock(symbol="JPM", company_name="JPMorgan Chase & Co.", sector="Financial Services", exchange="NYSE"))
        db.add(Stock(symbol="SHOP.TO", company_name="Shopify Inc.", sector="Technology", exchange="TSX"))
        db.add(Stock(symbol="PNG.V", company_name="Kraken Robotics Inc.", sector="Industrials", exchange="TSXV"))
        db.add(
            MarketCandle(
                symbol="AAPL",
                timestamp=datetime.now(UTC),
                interval="1d",
                open=100,
                high=102,
                low=99,
                close=100,
                adjusted_close=100,
                volume=1_000_000,
                source="test",
            )
        )
        db.commit()
    yield
    Base.metadata.drop_all(engine)
