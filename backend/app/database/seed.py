from __future__ import annotations

from datetime import UTC, datetime, timedelta

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.backtesting.engine import run_backtest
from app.core.security import hash_password
from app.database.models import (
    Backtest,
    BacktestTrade,
    MarketCandle,
    MLExperiment,
    MLModel,
    Order,
    PaperAccount,
    Portfolio,
    PortfolioSnapshot,
    Position,
    Prediction,
    Stock,
    Trade,
    User,
    WatchlistItem,
)
from app.features.engine import FEATURE_COLUMNS, engineer_features
from app.machine_learning.service import train_and_compare
from app.market_data.catalog import CORE_DEMO_SYMBOLS, STOCK_CATALOG

DEMO_EMAIL = "demo@tradeiq.dev"
DEMO_PASSWORD = "tradeiq-demo"


def _candles(symbol: str, target_price: float) -> pd.DataFrame:
    seed = sum(ord(char) for char in symbol)
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=datetime.now(UTC).date(), periods=360, tz="UTC")
    daily = rng.normal(0.0007, 0.018, len(dates))
    raw = 100 * np.exp(np.cumsum(daily))
    close = raw * (target_price / raw[-1])
    opening = close * (1 + rng.normal(0, 0.004, len(close)))
    high = np.maximum(opening, close) * (1 + rng.uniform(0.001, 0.015, len(close)))
    low = np.minimum(opening, close) * (1 - rng.uniform(0.001, 0.015, len(close)))
    return pd.DataFrame(
        {
            "open": opening,
            "high": high,
            "low": low,
            "close": close,
            "volume": rng.integers(15_000_000, 95_000_000, len(close)),
        },
        index=dates,
    )


def _market_frame(db: Session, symbol: str) -> pd.DataFrame:
    rows = db.scalars(
        select(MarketCandle).where(MarketCandle.symbol == symbol).order_by(MarketCandle.timestamp)
    ).all()
    return pd.DataFrame(
        [{"open": row.open, "high": row.high, "low": row.low, "close": row.close, "volume": row.volume} for row in rows],
        index=pd.DatetimeIndex([row.timestamp for row in rows]),
    )


def seed_market_catalog(db: Session, include_demo_history: bool = True) -> None:
    """Upsert the supported universe and add fallback history only when a symbol has none."""
    existing = {stock.symbol: stock for stock in db.scalars(select(Stock)).all()}
    for symbol, definition in STOCK_CATALOG.items():
        stock = existing.get(symbol)
        if stock is None:
            stock = Stock(symbol=symbol)
            db.add(stock)
        stock.company_name = definition.company_name
        stock.sector = definition.sector
        stock.exchange = definition.exchange
    db.flush()

    if include_demo_history:
        symbols_with_history = set(db.scalars(select(MarketCandle.symbol).distinct()).all())
        candles: list[MarketCandle] = []
        for symbol, definition in STOCK_CATALOG.items():
            if symbol in symbols_with_history:
                continue
            for timestamp, row in _candles(symbol, definition.demo_price).iterrows():
                candles.append(
                    MarketCandle(
                        symbol=symbol,
                        timestamp=timestamp.to_pydatetime(),
                        interval="1d",
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        adjusted_close=float(row["close"]),
                        volume=int(row["volume"]),
                        source="demo-simulation",
                    )
                )
        db.add_all(candles)
    db.flush()


def seed_demo_database(db: Session) -> None:
    seed_market_catalog(db)
    if db.scalar(select(User).where(User.email == DEMO_EMAIL)):
        db.commit()
        return
    user = User(
        email=DEMO_EMAIL,
        password_hash=hash_password(DEMO_PASSWORD),
        first_name="TradeIQ",
        last_name="Demo",
        full_name="TradeIQ Demo",
        is_demo=True,
        last_login_at=datetime.now(UTC),
    )
    db.add(user)
    db.flush()
    frames = {symbol: _market_frame(db, symbol) for symbol in CORE_DEMO_SYMBOLS}
    for symbol in CORE_DEMO_SYMBOLS:
        db.add(WatchlistItem(user_id=user.id, symbol=symbol))
    paper_account = PaperAccount(
        user_id=user.id,
        name="Demo Portfolio",
        initial_balance=10000,
        cash_balance=4200,
        realized_pnl=342.18,
    )
    db.add(paper_account)
    db.flush()
    portfolio = Portfolio(
        user_id=user.id,
        paper_account_id=paper_account.id,
        cash=4200,
        initial_cash=10000,
        realized_pnl=342.18,
    )
    db.add(portfolio)
    db.flush()
    quantities = {"AAPL": 12.0, "MSFT": 5.0, "NVDA": 16.0}
    entries = {"AAPL": 198.4, "MSFT": 389.2, "NVDA": 166.5}
    for symbol, quantity in quantities.items():
        db.add(
            Position(
                portfolio_id=portfolio.id, symbol=symbol, quantity=quantity, average_entry=entries[symbol]
            )
        )
    base = datetime.now(UTC) - timedelta(days=89)
    for day in range(90):
        progress = day / 89
        equity = 10000 + 2543.18 * progress + 230 * np.sin(progress * np.pi * 5)
        db.add(
            PortfolioSnapshot(
                portfolio_id=portfolio.id,
                paper_account_id=paper_account.id,
                timestamp=base + timedelta(days=day),
                equity=float(equity),
                cash=4200,
                exposure=float(equity - 4200),
                positions_value=float(equity - 4200),
                daily_pnl=0,
                total_pnl=float(equity - 10000),
            )
        )
    # Keep first boot fast. Full on-demand training also evaluates XGBoost.
    training = train_and_compare(frames["AAPL"], "AAPL", include_xgboost=False)
    best_metrics = next(
        item["metrics"] for item in training["results"] if item["algorithm"] == training["algorithm"]
    )
    model = MLModel(
        model_name="Directional Classifier",
        version=training["version"],
        algorithm=training["algorithm"],
        training_start=training["training_start"],
        training_end=training["training_end"],
        features=FEATURE_COLUMNS,
        hyperparameters={"chronological_split": 0.8},
        metrics={**best_metrics, "walk_forward": training["walk_forward"]},
        file_path=training["file_path"],
        is_active=True,
    )
    db.add(model)
    for result in training["results"]:
        db.add(
            MLExperiment(
                algorithm=result["algorithm"],
                symbol="AAPL",
                features=FEATURE_COLUMNS,
                hyperparameters={"chronological_split": 0.8},
                training_window=f"{training['training_start']}:{training['training_end']}",
                test_window=f"{training['test_start']}:{training['test_end']}",
                metrics=result["metrics"],
            )
        )
    artifact = joblib.load(training["file_path"])
    for symbol, frame in frames.items():
        latest = engineer_features(frame)[FEATURE_COLUMNS].iloc[[-1]]
        probability = float(artifact["model"].predict_proba(latest)[:, 1][0])
        signal = "BUY" if probability >= 0.6 else "SELL" if probability <= 0.4 else "HOLD"
        momentum = float(latest.iloc[0]["return_20d"])
        db.add(
            Prediction(
                user_id=user.id,
                symbol=symbol,
                signal=signal,
                probability_up=probability,
                confidence=abs(probability - 0.5) * 2,
                model_version=training["version"],
                explanation={
                    "positive_factors": ["price above SMA 20", "relative volume"]
                    if momentum > 0
                    else ["mean reversion setup"],
                    "negative_factors": ["elevated volatility"]
                    if float(latest.iloc[0]["volatility"]) > 0.25
                    else [],
                },
            )
        )
    result = run_backtest(frames["NVDA"], "moving_average", 10_000)
    backtest = Backtest(
        user_id=user.id,
        symbol="NVDA",
        strategy="moving_average",
        start_date=frames["NVDA"].index[0].date(),
        end_date=frames["NVDA"].index[-1].date(),
        config={"starting_capital": 10000, "position_size": 0.8},
        metrics=result["metrics"],
        equity_curve=result["equity_curve"],
        benchmark_curve=result["benchmark_curve"],
    )
    db.add(backtest)
    db.flush()
    for item in result["trades"]:
        db.add(
            BacktestTrade(
                backtest_id=backtest.id,
                symbol="NVDA",
                side=item["side"],
                quantity=item["quantity"],
                price=item["price"],
                timestamp=datetime.fromisoformat(item["timestamp"]),
                pnl=item["pnl"],
                signal_confidence=0.68,
            )
        )
    for index, (symbol, side, quantity) in enumerate(
        (("NVDA", "BUY", 4.0), ("AAPL", "BUY", 3.0), ("MSFT", "SELL", 1.0))
    ):
        price = float(frames[symbol]["close"].iloc[-1])
        created = datetime.now(UTC) - timedelta(days=3 - index)
        order = Order(
            user_id=user.id,
            paper_account_id=paper_account.id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            notional_amount=quantity * price,
            requested_price=price,
            status="FILLED",
            submitted_at=created,
            filled_at=created,
            average_fill_price=price,
            broker_order_id=f"SIM-{index + 1}",
            strategy="ml_signal",
            model_version=training["version"],
            mode="simulation",
            client_order_id=f"demo-{index + 1}",
        )
        db.add(order)
        db.flush()
        db.add(
            Trade(
                user_id=user.id,
                paper_account_id=paper_account.id,
                order_id=order.id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=price,
                pnl=float((index - 1) * 42.5),
                value=quantity * price,
                realized_pnl=float((index - 1) * 42.5),
                confidence=0.62 + index * 0.04,
                strategy="ml_signal",
                context={"exit_reason": "signal", "source": "seeded demo simulation"},
            )
        )
    db.commit()
