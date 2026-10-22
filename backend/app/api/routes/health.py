from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.database.session import engine
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


def database_status() -> Literal["connected", "unavailable"]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return "connected"
    except SQLAlchemyError:
        return "unavailable"


def redis_status() -> Literal["connected", "unavailable", "not_configured"]:
    redis_url = get_settings().redis_url
    if not redis_url:
        return "not_configured"

    client = Redis.from_url(redis_url, socket_connect_timeout=0.35, socket_timeout=0.35)
    try:
        client.ping()
        return "connected"
    except RedisError:
        return "unavailable"
    finally:
        client.close()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    settings = get_settings()
    database = database_status()
    redis = redis_status()
    required_services_available = database == "connected" and redis != "unavailable"

    return HealthResponse(
        status="healthy" if required_services_available else "degraded",
        database=database,
        redis=redis,
        market_api="connected" if settings.market_data_provider == "yahoo" else "not_configured",
        version="0.1.0",
    )
