from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.database.models import (
    MarketCandle,
    Order,
    PaperAccount,
    Portfolio,
    PortfolioSnapshot,
    Position,
    Prediction,
    RiskEvent,
    Trade,
    User,
)
from app.database.session import get_db

router = APIRouter(tags=["portfolio and analytics"])


def portfolio_payload(db: Session, user_id: int) -> dict:
    portfolio = db.scalar(select(Portfolio).where(Portfolio.user_id == user_id))
    account = db.scalar(
        select(PaperAccount).where(
            PaperAccount.user_id == user_id, PaperAccount.is_active.is_(True)
        )
    )
    if portfolio is None or account is None:
        raise HTTPException(status_code=404, detail="Paper portfolio setup is required")
    positions = db.scalars(select(Position).where(Position.portfolio_id == portfolio.id)).all()
    items, market_value, unrealized = [], 0.0, 0.0
    for position in positions:
        latest = db.scalar(
            select(MarketCandle)
            .where(MarketCandle.symbol == position.symbol)
            .order_by(MarketCandle.timestamp.desc())
        )
        price = latest.close if latest else position.average_entry
        value = position.quantity * price
        pnl = (price - position.average_entry) * position.quantity
        market_value += value
        unrealized += pnl
        items.append(
            {
                "symbol": position.symbol,
                "quantity": position.quantity,
                "average_entry": round(position.average_entry, 2),
                "price": round(price, 2),
                "market_value": round(value, 2),
                "unrealized_pnl": round(pnl, 2),
                "return_percent": round((price / position.average_entry - 1) * 100, 2),
            }
        )
    cash = float(account.cash_balance)
    initial_balance = float(account.initial_balance)
    equity = cash + market_value
    snapshots = db.scalars(
        select(PortfolioSnapshot)
        .where(
            PortfolioSnapshot.portfolio_id == portfolio.id,
            PortfolioSnapshot.paper_account_id == account.id,
        )
        .order_by(PortfolioSnapshot.timestamp)
    ).all()
    prior_equity = snapshots[-2].equity if len(snapshots) > 1 else initial_balance
    return {
        "paper_account_id": account.id,
        "starting_balance": round(initial_balance, 2),
        "cash": round(cash, 2),
        "buying_power": round(cash, 2),
        "equity": round(equity, 2),
        "market_value": round(market_value, 2),
        "market_exposure": round(market_value / equity * 100, 2) if equity else 0,
        "realized_pnl": round(float(account.realized_pnl), 2),
        "unrealized_pnl": round(unrealized, 2),
        "today_pnl": round(equity - prior_equity, 2),
        "total_pnl": round(equity - initial_balance, 2),
        "total_return": round((equity / initial_balance - 1) * 100, 2),
        "positions": items,
        "performance": [
            {"date": row.timestamp.date().isoformat(), "value": round(row.equity, 2)} for row in snapshots
        ],
    }


@router.get("/portfolio")
def portfolio(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    return portfolio_payload(db, user.id)


@router.get("/positions")
def positions(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict]:
    return portfolio_payload(db, user.id)["positions"]


@router.get("/trades")
def trades(
    symbol: str | None = None,
    strategy: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[dict]:
    account = db.scalar(
        select(PaperAccount).where(
            PaperAccount.user_id == user.id, PaperAccount.is_active.is_(True)
        )
    )
    if account is None:
        raise HTTPException(status_code=404, detail="Paper portfolio setup is required")
    query = select(Trade).where(Trade.user_id == user.id, Trade.paper_account_id == account.id)
    if symbol:
        query = query.where(Trade.symbol == symbol.upper())
    if strategy:
        query = query.where(Trade.strategy == strategy)
    rows = db.scalars(query.order_by(Trade.created_at.desc())).all()
    return [
        {
            "id": row.id,
            "date": row.created_at.isoformat(),
            "symbol": row.symbol,
            "side": row.side,
            "quantity": row.quantity,
            "entry": row.entry_price,
            "exit": row.exit_price,
            "pnl": row.pnl,
            "confidence": row.confidence,
            "strategy": row.strategy,
            "context": row.context,
        }
        for row in rows
    ]


@router.get("/analytics")
def analytics(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    account = db.scalar(
        select(PaperAccount).where(
            PaperAccount.user_id == user.id, PaperAccount.is_active.is_(True)
        )
    )
    if account is None:
        raise HTTPException(status_code=404, detail="Paper portfolio setup is required")
    rows = db.scalars(
        select(Trade).where(Trade.user_id == user.id, Trade.paper_account_id == account.id)
    ).all()
    by_symbol: dict[str, float] = defaultdict(float)
    by_strategy: dict[str, float] = defaultdict(float)
    for row in rows:
        by_symbol[row.symbol] += row.pnl
        by_strategy[row.strategy] += row.pnl
    portfolio = db.scalar(select(Portfolio).where(Portfolio.user_id == user.id))
    snapshots = (
        db.scalars(
            select(PortfolioSnapshot)
            .where(
                PortfolioSnapshot.portfolio_id == portfolio.id,
                PortfolioSnapshot.paper_account_id == portfolio.paper_account_id,
            )
            .order_by(PortfolioSnapshot.timestamp)
        ).all()
        if portfolio
        else []
    )
    monthly: dict[str, list[float]] = defaultdict(list)
    for previous, current in zip(snapshots, snapshots[1:], strict=False):
        monthly[current.timestamp.strftime("%Y-%m")].append(current.equity / previous.equity - 1)
    monthly_returns = {month: round((sum(values)) * 100, 2) for month, values in monthly.items()}
    values = [row.equity for row in snapshots]
    peak, max_drawdown, current_drawdown = 0.0, 0.0, 0.0
    for value in values:
        peak = max(peak, value)
        current_drawdown = value / peak - 1 if peak else 0
        max_drawdown = min(max_drawdown, current_drawdown)
    return {
        "profit_by_symbol": dict(by_symbol),
        "profit_by_strategy": dict(by_strategy),
        "monthly_returns": monthly_returns,
        "best_stock": max(by_symbol, key=by_symbol.get) if by_symbol else None,
        "worst_stock": min(by_symbol, key=by_symbol.get) if by_symbol else None,
        "best_strategy": max(by_strategy, key=by_strategy.get) if by_strategy else None,
        "win_rate": round(sum(row.pnl > 0 for row in rows) / len(rows) * 100, 2) if rows else 0,
        "current_drawdown": round(current_drawdown * 100, 2),
        "maximum_drawdown": round(max_drawdown * 100, 2),
    }


@router.get("/risk")
def risk_dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    data = portfolio_payload(db, user.id)
    events = db.scalars(
        select(RiskEvent).where(RiskEvent.user_id == user.id).order_by(RiskEvent.created_at.desc()).limit(20)
    ).all()
    largest = max(data["positions"], key=lambda item: item["market_value"], default=None)
    settings = get_settings()
    return {
        "trading_enabled": settings.trading_enabled or settings.trading_mode in {"simulation", "paper"},
        "trading_mode": settings.trading_mode,
        "portfolio_exposure": data["market_exposure"],
        "daily_loss": 0,
        "risk_per_trade": 1,
        "largest_position": largest,
        "active_positions": len(data["positions"]),
        "limits": {
            "max_position_percent": settings.max_position_percent * 100,
            "max_exposure": settings.max_portfolio_exposure * 100,
            "max_daily_loss": settings.max_daily_loss_percent * 100,
        },
        "events": [
            {
                "type": item.event_type,
                "severity": item.severity,
                "message": item.message,
                "created_at": item.created_at.isoformat(),
            }
            for item in events
        ],
    }


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    data = portfolio_payload(db, user.id)
    predictions = db.scalars(
        select(Prediction)
        .where(Prediction.user_id == user.id)
        .order_by(Prediction.probability_up.desc())
        .limit(5)
    ).all()
    orders = db.scalars(
        select(Order)
        .where(Order.user_id == user.id, Order.paper_account_id == data["paper_account_id"])
        .order_by(Order.created_at.desc())
        .limit(5)
    ).all()
    return {
        "portfolio": data,
        "opportunities": [
            {
                "symbol": row.symbol,
                "signal": row.signal,
                "probability_up": row.probability_up,
                "confidence": row.confidence,
            }
            for row in predictions
        ],
        "recent_orders": [
            {
                "id": row.id,
                "symbol": row.symbol,
                "side": row.side,
                "quantity": row.quantity,
                "status": row.status,
                "price": row.average_fill_price,
                "created_at": row.created_at.isoformat(),
            }
            for row in orders
        ],
    }
