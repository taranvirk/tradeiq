from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.models import MarketCandle, Prediction, Stock, User, WatchlistItem
from app.database.session import get_db
from app.features.engine import engineer_features
from app.market_data.catalog import EXCHANGES, STOCK_CATALOG
from app.market_data.provider import MarketDataError, YahooMarketDataProvider

router = APIRouter(tags=["market data"])


def _latest(db: Session, symbol: str) -> MarketCandle | None:
    return db.scalar(
        select(MarketCandle).where(MarketCandle.symbol == symbol).order_by(MarketCandle.timestamp.desc())
    )


def _stock_payload(db: Session, stock: Stock) -> dict:
    candles = db.scalars(
        select(MarketCandle)
        .where(MarketCandle.symbol == stock.symbol)
        .order_by(MarketCandle.timestamp.desc())
        .limit(2)
    ).all()
    latest = candles[0] if candles else None
    previous = candles[1] if len(candles) > 1 else latest
    prediction = db.scalar(
        select(Prediction).where(Prediction.symbol == stock.symbol).order_by(Prediction.created_at.desc())
    )
    change = ((latest.close / previous.close - 1) * 100) if latest and previous else 0
    return {
        "symbol": stock.symbol,
        "company_name": stock.company_name,
        "sector": stock.sector,
        "exchange": stock.exchange,
        "quote_currency": "CAD" if stock.exchange in {"TSX", "TSXV"} else "USD",
        "price": round(latest.close, 2) if latest else None,
        "change_percent": round(change, 2),
        "volume": latest.volume if latest else None,
        "signal": prediction.signal if prediction else "N/A",
        "confidence": round(prediction.confidence, 4) if prediction else None,
    }


@router.get("/stocks")
def search_stocks(
    q: str = Query(default="", max_length=80),
    exchange: str | None = Query(default=None, max_length=32),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = select(Stock).where(Stock.symbol.in_(tuple(STOCK_CATALOG))).order_by(Stock.exchange, Stock.symbol)
    if q:
        cleaned = q.strip()
        query = query.where(
            (Stock.symbol.ilike(f"%{cleaned}%")) | (Stock.company_name.ilike(f"%{cleaned}%"))
        )
    if exchange:
        normalized_exchange = exchange.strip().upper()
        allowed = {item.upper(): item for item in EXCHANGES}
        if normalized_exchange == "NYSE":
            query = query.where(Stock.exchange.in_(("NYSE", "NYSE Arca")))
        elif normalized_exchange in allowed:
            query = query.where(Stock.exchange == allowed[normalized_exchange])
        else:
            raise HTTPException(status_code=422, detail="Unsupported exchange filter")
    return [_stock_payload(db, stock) for stock in db.scalars(query.limit(limit)).all()]


@router.get("/stocks/{symbol}")
def stock_detail(symbol: str, db: Session = Depends(get_db)) -> dict:
    stock = db.get(Stock, symbol.upper())
    if stock is None:
        raise HTTPException(status_code=404, detail="Unknown ticker")
    payload = _stock_payload(db, stock)
    year = db.scalars(
        select(MarketCandle)
        .where(MarketCandle.symbol == stock.symbol)
        .order_by(MarketCandle.timestamp.desc())
        .limit(252)
    ).all()
    if year:
        payload["range_52_week"] = {
            "low": round(min(row.low for row in year), 2),
            "high": round(max(row.high for row in year), 2),
        }
    return payload


@router.get("/stocks/{symbol}/history")
def stock_history(
    symbol: str,
    range: str = Query(default="1Y", pattern="^(1D|5D|1M|3M|6M|1Y|5Y|MAX)$"),
    db: Session = Depends(get_db),
) -> dict:  # noqa: A002
    if db.get(Stock, symbol.upper()) is None:
        raise HTTPException(status_code=404, detail="Unknown ticker")
    days = {"1D": 1, "5D": 5, "1M": 31, "3M": 93, "6M": 186, "1Y": 366, "5Y": 1827, "MAX": 36500}[range]
    rows = db.scalars(
        select(MarketCandle)
        .where(
            MarketCandle.symbol == symbol.upper(),
            MarketCandle.timestamp >= datetime.now(UTC) - timedelta(days=days),
        )
        .order_by(MarketCandle.timestamp)
    ).all()
    if not rows:
        raise HTTPException(status_code=404, detail="No market data available for this range")
    frame = pd.DataFrame(
        [{"open": r.open, "high": r.high, "low": r.low, "close": r.close, "volume": r.volume} for r in rows],
        index=pd.DatetimeIndex([r.timestamp for r in rows]),
    )
    enriched = engineer_features(frame)
    candles = []
    for row, (_, feature) in zip(rows, enriched.iterrows(), strict=True):
        candles.append(
            {
                "timestamp": row.timestamp.isoformat(),
                "open": round(row.open, 4),
                "high": round(row.high, 4),
                "low": round(row.low, 4),
                "close": round(row.close, 4),
                "volume": row.volume,
                "sma20": None if pd.isna(feature["sma_20"]) else round(float(feature["sma_20"]), 4),
                "sma50": None if pd.isna(feature["sma_50"]) else round(float(feature["sma_50"]), 4),
                "rsi": None if pd.isna(feature["rsi"]) else round(float(feature["rsi"]), 2),
                "macd": None if pd.isna(feature["macd"]) else round(float(feature["macd"]), 4),
            }
        )
    return {"symbol": symbol.upper(), "range": range, "candles": candles, "source": rows[-1].source}


@router.post("/stocks/{symbol}/refresh")
async def refresh_stock(
    symbol: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> dict:
    stock = db.get(Stock, symbol.upper())
    if stock is None:
        raise HTTPException(status_code=404, detail="Unknown ticker")
    try:
        candles = await YahooMarketDataProvider().get_historical_data(symbol.upper())
    except MarketDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    # Demo candles are a fallback dataset; replace them atomically once real data arrives.
    db.execute(
        delete(MarketCandle).where(
            MarketCandle.symbol == symbol.upper(),
            MarketCandle.source == "demo-simulation",
        )
    )
    db.flush()
    existing = set(
        db.scalars(select(MarketCandle.timestamp).where(MarketCandle.symbol == symbol.upper())).all()
    )
    added = 0
    for row in candles:
        if row["timestamp"] not in existing:
            db.add(MarketCandle(**row))
            added += 1
    db.commit()
    return {"symbol": symbol.upper(), "received": len(candles), "stored": added, "source": "yahoo"}


@router.get("/watchlist")
def watchlist(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict]:
    stocks = db.scalars(
        select(Stock)
        .join(WatchlistItem, WatchlistItem.symbol == Stock.symbol)
        .where(WatchlistItem.user_id == user.id)
        .order_by(Stock.symbol)
    ).all()
    return [_stock_payload(db, stock) for stock in stocks]


@router.post("/watchlist/{symbol}", status_code=status.HTTP_201_CREATED)
def add_watchlist(symbol: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    symbol = symbol.upper()
    if db.get(Stock, symbol) is None:
        raise HTTPException(status_code=404, detail="Unknown ticker")
    exists = db.scalar(
        select(WatchlistItem).where(WatchlistItem.user_id == user.id, WatchlistItem.symbol == symbol)
    )
    if not exists:
        db.add(WatchlistItem(user_id=user.id, symbol=symbol))
        db.commit()
    return {"symbol": symbol, "added": not bool(exists)}


@router.delete("/watchlist/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
def remove_watchlist(
    symbol: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> None:
    db.execute(
        delete(WatchlistItem).where(WatchlistItem.user_id == user.id, WatchlistItem.symbol == symbol.upper())
    )
    db.commit()
