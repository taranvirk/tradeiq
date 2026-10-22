from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "TradeIQ API"
    app_env: Literal["development", "test", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "sqlite:///./tradeiq.db"
    redis_url: str | None = None
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ]
    )

    jwt_secret: str = Field(min_length=32)
    market_data_api_key: str | None = None
    alpaca_api_key: str | None = None
    alpaca_secret_key: str | None = None
    trading_mode: Literal["backtest", "simulation", "paper", "live"] = "simulation"
    trading_enabled: bool = False
    demo_mode: bool = True
    access_token_expire_minutes: int = 1440
    market_data_provider: str = "yahoo"
    alpaca_base_url: str = "https://paper-api.alpaca.markets"
    max_position_percent: float = 0.25
    max_portfolio_exposure: float = 0.85
    max_daily_loss_percent: float = 0.05
    minimum_order_confidence: float = 0.55
    min_paper_balance: float = 100
    max_paper_balance: float = 10_000_000
    default_paper_balance: float = 10_000


@lru_cache
def get_settings() -> Settings:
    return Settings()
