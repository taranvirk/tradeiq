from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.database.models import MarketCandle, Stock
from app.database.session import SessionLocal

router = APIRouter(tags=["realtime"])


@router.websocket("/ws/market")
async def market_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            with SessionLocal() as db:
                symbols = db.scalars(select(Stock.symbol).order_by(Stock.symbol)).all()
                quotes = []
                for symbol in symbols:
                    latest = db.scalar(
                        select(MarketCandle)
                        .where(MarketCandle.symbol == symbol)
                        .order_by(MarketCandle.timestamp.desc())
                    )
                    if latest:
                        quotes.append(
                            {
                                "symbol": symbol,
                                "price": round(latest.close, 2),
                                "timestamp": latest.timestamp.isoformat(),
                            }
                        )
            await websocket.send_json({"type": "quotes", "data": quotes})
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        return
