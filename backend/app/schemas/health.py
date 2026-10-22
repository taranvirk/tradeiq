from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded"]
    database: Literal["connected", "unavailable"]
    redis: Literal["connected", "unavailable", "not_configured"]
    market_api: Literal["connected", "unavailable", "not_configured"]
    version: str
