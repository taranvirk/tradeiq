from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
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
    RiskEvent,
    Trade,
    User,
)
from app.database.session import get_db
from app.risk.engine import RiskManager
from app.schemas.platform import OrderRequest, PositionSizeRequest

router = APIRouter(tags=["orders and risk"])


def _order_payload(row: Order) -> dict:
    return {
        "id": row.id,
        "symbol": row.symbol,
        "side": row.side,
        "quantity": row.quantity,
        "notional_amount": float(row.notional_amount) if row.notional_amount is not None else None,
        "order_type": row.order_type,
        "limit_price": row.limit_price,
        "status": row.status,
        "submitted_at": row.submitted_at.isoformat() if row.submitted_at else None,
        "filled_at": row.filled_at.isoformat() if row.filled_at else None,
        "average_fill_price": row.average_fill_price,
        "broker_order_id": row.broker_order_id,
        "strategy": row.strategy,
        "model_version": row.model_version,
        "mode": row.mode,
    }


@router.get("/orders")
def list_orders(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict]:
    account = db.scalar(
        select(PaperAccount).where(
            PaperAccount.user_id == user.id, PaperAccount.is_active.is_(True)
        )
    )
    if account is None:
        raise HTTPException(status_code=404, detail="Paper portfolio setup is required")
    return [
        _order_payload(row)
        for row in db.scalars(
            select(Order)
            .where(Order.user_id == user.id, Order.paper_account_id == account.id)
            .order_by(Order.created_at.desc())
        ).all()
    ]


@router.post("/orders", status_code=201)
def submit_order(
    payload: OrderRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    settings = get_settings()
    symbol = payload.symbol.upper()
    latest = db.scalar(
        select(MarketCandle).where(MarketCandle.symbol == symbol).order_by(MarketCandle.timestamp.desc())
    )
    if latest is None:
        raise HTTPException(status_code=404, detail="No price available for ticker")
    portfolio = db.scalar(select(Portfolio).where(Portfolio.user_id == user.id))
    account = db.scalar(
        select(PaperAccount).where(
            PaperAccount.user_id == user.id, PaperAccount.is_active.is_(True)
        )
    )
    if portfolio is None or account is None:
        raise HTTPException(status_code=404, detail="Paper portfolio setup is required")
    positions = db.scalars(select(Position).where(Position.portfolio_id == portfolio.id)).all()
    market_value = sum(
        position.quantity
        * (
            db.scalar(
                select(MarketCandle.close)
                .where(MarketCandle.symbol == position.symbol)
                .order_by(MarketCandle.timestamp.desc())
            )
            or position.average_entry
        )
        for position in positions
    )
    cash = float(account.cash_balance)
    equity = cash + market_value
    price = payload.limit_price if payload.order_type == "limit" else latest.close
    quantity = payload.quantity if payload.quantity is not None else payload.notional_amount / price
    order_value = quantity * price
    decision = RiskManager(
        min(settings.max_position_percent, account.max_position_size),
        settings.max_portfolio_exposure,
        settings.minimum_order_confidence,
    ).validate_order(
        side=payload.side,
        order_value=order_value,
        cash=cash,
        equity=equity,
        exposure=market_value,
        confidence=payload.confidence,
        trading_enabled=settings.trading_enabled or settings.trading_mode in {"simulation", "paper"},
    )
    if not decision.allowed:
        db.add(
            RiskEvent(
                user_id=user.id,
                event_type=decision.code,
                severity="warning",
                message=decision.message,
                details=payload.model_dump(),
            )
        )
        db.commit()
        detail = decision.message
        if decision.code == "INSUFFICIENT_BUYING_POWER":
            detail = f"Insufficient buying power. Available: ${cash:,.2f}. Requested: ${order_value:,.2f}."
        raise HTTPException(status_code=403, detail=detail, headers={"X-TradeIQ-Error": decision.code})
    position = next((item for item in positions if item.symbol == symbol), None)
    if payload.side == "SELL" and (position is None or position.quantity + 1e-9 < quantity):
        raise HTTPException(status_code=422, detail="Sell quantity exceeds the current position")
    now = datetime.now(UTC)
    row = Order(
        user_id=user.id,
        paper_account_id=account.id,
        symbol=symbol,
        side=payload.side,
        quantity=quantity,
        notional_amount=payload.notional_amount,
        requested_price=price,
        order_type=payload.order_type,
        limit_price=payload.limit_price,
        status="FILLED",
        submitted_at=now,
        filled_at=now,
        average_fill_price=price,
        broker_order_id=f"SIM-{uuid4()}",
        strategy=payload.strategy,
        model_version=payload.model_version,
        mode=settings.trading_mode,
        client_order_id=payload.client_order_id,
    )
    db.add(row)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate client order ID") from exc
    if payload.side == "BUY":
        cash -= order_value
        if position:
            total = position.quantity + quantity
            position.average_entry = (
                position.quantity * position.average_entry + quantity * price
            ) / total
            position.quantity = total
        else:
            db.add(
                Position(
                    portfolio_id=portfolio.id, symbol=symbol, quantity=quantity, average_entry=price
                )
            )
        realized = 0.0
    else:
        cash += order_value
        realized = (price - position.average_entry) * quantity
        account.realized_pnl = float(account.realized_pnl) + realized
        position.quantity -= quantity
        if position.quantity <= 1e-9:
            db.delete(position)
    account.cash_balance = cash
    portfolio.cash = cash
    portfolio.realized_pnl = float(account.realized_pnl)
    db.add(
        Trade(
            user_id=user.id,
            paper_account_id=account.id,
            order_id=row.id,
            symbol=symbol,
            side=payload.side,
            quantity=quantity,
            entry_price=price,
            pnl=realized,
            value=order_value,
            realized_pnl=realized,
            confidence=payload.confidence,
            strategy=payload.strategy,
            context={"model_version": payload.model_version, "risk_decision": decision.code},
        )
    )
    new_market_value = market_value + order_value if payload.side == "BUY" else market_value - order_value
    new_equity = cash + new_market_value
    db.add(
        PortfolioSnapshot(
            portfolio_id=portfolio.id,
            paper_account_id=account.id,
            timestamp=now,
            equity=new_equity,
            cash=cash,
            exposure=new_market_value,
            positions_value=new_market_value,
            daily_pnl=0,
            total_pnl=new_equity - float(account.initial_balance),
        )
    )
    db.commit()
    db.refresh(row)
    return _order_payload(row)


@router.post("/orders/{order_id}/cancel")
def cancel_order(
    order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    account = db.scalar(
        select(PaperAccount).where(
            PaperAccount.user_id == user.id, PaperAccount.is_active.is_(True)
        )
    )
    row = db.scalar(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == user.id,
            Order.paper_account_id == (account.id if account else -1),
        )
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if row.status in {"FILLED", "CANCELLED", "REJECTED"}:
        raise HTTPException(status_code=409, detail=f"A {row.status.lower()} order cannot be cancelled")
    row.status = "CANCELLED"
    db.commit()
    return _order_payload(row)


@router.post("/risk/position-size")
def calculate_position_size(payload: PositionSizeRequest, _: User = Depends(get_current_user)) -> dict:
    quantity = RiskManager.position_size(
        payload.equity, payload.price, payload.method, payload.value, payload.stop_loss_percent
    )
    return {
        "quantity": quantity,
        "position_value": round(quantity * payload.price, 2),
        "method": payload.method,
    }
