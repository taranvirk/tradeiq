from __future__ import annotations

from datetime import date

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class SignupRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not any(char.isupper() for char in value):
            raise ValueError("Password must include an uppercase letter")
        if not any(char.islower() for char in value):
            raise ValueError("Password must include a lowercase letter")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must include a number")
        return value

    @model_validator(mode="after")
    def passwords_match(self) -> SignupRequest:
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
    onboarding_required: bool = False


class PaperAccountRequest(BaseModel):
    starting_balance: float


class ResetPaperAccountRequest(PaperAccountRequest):
    confirmation: str


class ProfileUpdateRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)


class TradingSettingsRequest(BaseModel):
    risk_per_trade: float = Field(ge=0.001, le=0.05)
    max_position_size: float = Field(ge=0.01, le=0.25)
    max_daily_loss: float = Field(ge=0.005, le=0.05)
    default_order_amount: float = Field(ge=1, le=1_000_000)
    ai_auto_trade_enabled: bool = False


class BacktestRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=12)
    strategy: str = Field(pattern="^(moving_average|rsi|ml)$")
    start_date: date | None = None
    end_date: date | None = None
    starting_capital: float = Field(default=10_000, gt=0)
    position_size: float = Field(default=0.8, gt=0, le=1)
    commission: float = Field(default=1, ge=0)
    slippage: float = Field(default=0.0005, ge=0, le=0.05)


class OrderRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=12)
    side: str = Field(pattern="^(BUY|SELL)$")
    quantity: float | None = Field(default=None, gt=0)
    notional_amount: float | None = Field(default=None, gt=0)
    order_type: str = Field(default="market", pattern="^(market|limit)$")
    limit_price: float | None = Field(default=None, gt=0)
    strategy: str = Field(default="manual", max_length=80)
    confidence: float | None = Field(default=None, ge=0, le=1)
    model_version: str | None = None
    client_order_id: str = Field(min_length=4, max_length=100)

    @model_validator(mode="after")
    def exactly_one_amount(self) -> OrderRequest:
        if (self.quantity is None) == (self.notional_amount is None):
            raise ValueError("Provide either quantity or notional_amount")
        return self


class PositionSizeRequest(BaseModel):
    equity: float = Field(gt=0)
    price: float = Field(gt=0)
    method: str = Field(pattern="^(fixed|percent|risk)$")
    value: float = Field(gt=0)
    stop_loss_percent: float = Field(default=0.05, gt=0, le=1)
