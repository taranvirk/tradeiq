from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("")
def application_metadata() -> dict[str, str | bool]:
    settings = get_settings()
    return {
        "name": "TradeIQ",
        "environment": settings.app_env,
        "trading_mode": settings.trading_mode,
        "trading_enabled": settings.trading_enabled,
        "version": "0.1.0",
    }
