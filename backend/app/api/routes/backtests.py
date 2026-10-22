from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.backtesting.engine import run_backtest
from app.database.models import Backtest, BacktestTrade, MarketCandle, Stock, User
from app.database.session import get_db
from app.schemas.platform import BacktestRequest

router = APIRouter(prefix="/backtests", tags=["backtesting"])


def _payload(item: Backtest, include_curves: bool = False) -> dict:
    result = {
        "id": item.id,
        "symbol": item.symbol,
        "strategy": item.strategy,
        "status": item.status,
        "start_date": item.start_date.isoformat(),
        "end_date": item.end_date.isoformat(),
        "config": item.config,
        "metrics": item.metrics,
        "created_at": item.created_at.isoformat(),
    }
    if include_curves:
        result.update({"equity_curve": item.equity_curve, "benchmark_curve": item.benchmark_curve})
    return result


@router.get("")
def list_backtests(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict]:
    return [
        _payload(item)
        for item in db.scalars(
            select(Backtest).where(Backtest.user_id == user.id).order_by(Backtest.created_at.desc())
        ).all()
    ]


@router.post("", status_code=201)
def create_backtest(
    payload: BacktestRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    symbol = payload.symbol.upper()
    if db.get(Stock, symbol) is None:
        raise HTTPException(status_code=404, detail="Unknown ticker")
    query = select(MarketCandle).where(MarketCandle.symbol == symbol)
    if payload.start_date:
        query = query.where(MarketCandle.timestamp >= payload.start_date)
    if payload.end_date:
        query = query.where(MarketCandle.timestamp <= payload.end_date)
    rows = db.scalars(query.order_by(MarketCandle.timestamp)).all()
    frame = pd.DataFrame(
        [{"open": r.open, "high": r.high, "low": r.low, "close": r.close, "volume": r.volume} for r in rows],
        index=pd.DatetimeIndex([r.timestamp for r in rows]),
    )
    try:
        result = run_backtest(
            frame,
            payload.strategy,
            payload.starting_capital,
            payload.position_size,
            payload.commission,
            payload.slippage,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    item = Backtest(
        user_id=user.id,
        symbol=symbol,
        strategy=payload.strategy,
        start_date=rows[0].timestamp.date(),
        end_date=rows[-1].timestamp.date(),
        config=payload.model_dump(mode="json"),
        metrics=result["metrics"],
        equity_curve=result["equity_curve"],
        benchmark_curve=result["benchmark_curve"],
    )
    db.add(item)
    db.flush()
    for trade in result["trades"]:
        db.add(
            BacktestTrade(
                backtest_id=item.id,
                symbol=symbol,
                side=trade["side"],
                quantity=trade["quantity"],
                price=trade["price"],
                timestamp=pd.Timestamp(trade["timestamp"]).to_pydatetime(),
                pnl=trade["pnl"],
                signal_confidence=0,
            )
        )
    db.commit()
    db.refresh(item)
    return _payload(item, include_curves=True)


@router.get("/{backtest_id}")
def get_backtest(
    backtest_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    item = db.scalar(select(Backtest).where(Backtest.id == backtest_id, Backtest.user_id == user.id))
    if item is None:
        raise HTTPException(status_code=404, detail="Backtest not found")
    result = _payload(item, include_curves=True)
    result["trades"] = [
        {
            "timestamp": trade.timestamp.isoformat(),
            "side": trade.side,
            "quantity": trade.quantity,
            "price": trade.price,
            "pnl": trade.pnl,
        }
        for trade in db.scalars(select(BacktestTrade).where(BacktestTrade.backtest_id == item.id)).all()
    ]
    return result
