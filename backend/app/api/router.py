from fastapi import APIRouter

from app.api.routes.account import router as account_router
from app.api.routes.auth import router as auth_router
from app.api.routes.backtests import router as backtests_router
from app.api.routes.market import router as market_router
from app.api.routes.meta import router as meta_router
from app.api.routes.orders import router as orders_router
from app.api.routes.portfolio import router as portfolio_router
from app.api.routes.research import router as research_router
from app.api.routes.stream import router as stream_router

api_router = APIRouter()
api_router.include_router(meta_router)
api_router.include_router(auth_router)
api_router.include_router(account_router)
api_router.include_router(market_router)
api_router.include_router(research_router)
api_router.include_router(backtests_router)
api_router.include_router(portfolio_router)
api_router.include_router(orders_router)
api_router.include_router(stream_router)
