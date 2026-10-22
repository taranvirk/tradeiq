from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.database.models import PaperAccount, Portfolio, PortfolioSnapshot, Position, User
from app.database.session import get_db
from app.schemas.platform import (
    PaperAccountRequest,
    ProfileUpdateRequest,
    ResetPaperAccountRequest,
    TradingSettingsRequest,
)

router = APIRouter(tags=["account and onboarding"])


def get_active_paper_account(db: Session, user_id: int) -> PaperAccount | None:
    return db.scalar(
        select(PaperAccount).where(
            PaperAccount.user_id == user_id, PaperAccount.is_active.is_(True)
        )
    )


def validate_balance(value: float) -> Decimal:
    settings = get_settings()
    if value < settings.min_paper_balance or value > settings.max_paper_balance:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Starting balance must be between ${settings.min_paper_balance:,.0f} "
                f"and ${settings.max_paper_balance:,.0f}"
            ),
        )
    return Decimal(str(value)).quantize(Decimal("0.01"))


def paper_account_payload(account: PaperAccount) -> dict:
    return {
        "id": account.id,
        "name": account.name,
        "initial_balance": float(account.initial_balance),
        "cash_balance": float(account.cash_balance),
        "realized_pnl": float(account.realized_pnl),
        "risk_per_trade": account.risk_per_trade,
        "max_position_size": account.max_position_size,
        "max_daily_loss": account.max_daily_loss,
        "default_order_amount": float(account.default_order_amount),
        "ai_auto_trade_enabled": account.ai_auto_trade_enabled,
        "created_at": account.created_at.isoformat(),
    }


@router.get("/paper-account")
def get_paper_account(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    account = get_active_paper_account(db, user.id)
    if account is None:
        raise HTTPException(status_code=404, detail="Paper portfolio setup is required")
    return paper_account_payload(account)


@router.post("/paper-account", status_code=status.HTTP_201_CREATED)
def create_paper_account(
    payload: PaperAccountRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    if get_active_paper_account(db, user.id):
        raise HTTPException(status_code=409, detail="An active paper portfolio already exists")
    balance = validate_balance(payload.starting_balance)
    account = PaperAccount(user_id=user.id, initial_balance=balance, cash_balance=balance)
    db.add(account)
    db.flush()
    portfolio = db.scalar(select(Portfolio).where(Portfolio.user_id == user.id))
    if portfolio is None:
        portfolio = Portfolio(
            user_id=user.id,
            paper_account_id=account.id,
            cash=float(balance),
            initial_cash=float(balance),
            realized_pnl=0,
        )
        db.add(portfolio)
        db.flush()
    else:
        portfolio.paper_account_id = account.id
        portfolio.cash = float(balance)
        portfolio.initial_cash = float(balance)
        portfolio.realized_pnl = 0
    db.add(
        PortfolioSnapshot(
            portfolio_id=portfolio.id,
            paper_account_id=account.id,
            timestamp=datetime.now(UTC),
            equity=float(balance),
            cash=float(balance),
            exposure=0,
            positions_value=0,
            daily_pnl=0,
            total_pnl=0,
        )
    )
    db.commit()
    db.refresh(account)
    return paper_account_payload(account)


@router.post("/paper-account/reset")
def reset_paper_account(
    payload: ResetPaperAccountRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    if payload.confirmation != "RESET":
        raise HTTPException(status_code=422, detail="Type RESET to confirm the portfolio reset")
    current = get_active_paper_account(db, user.id)
    portfolio = db.scalar(select(Portfolio).where(Portfolio.user_id == user.id))
    if current is None or portfolio is None:
        raise HTTPException(status_code=404, detail="Paper portfolio not found")
    balance = validate_balance(payload.starting_balance)
    current.is_active = False
    db.execute(delete(Position).where(Position.portfolio_id == portfolio.id))
    account = PaperAccount(user_id=user.id, initial_balance=balance, cash_balance=balance)
    db.add(account)
    db.flush()
    portfolio.paper_account_id = account.id
    portfolio.cash = float(balance)
    portfolio.initial_cash = float(balance)
    portfolio.realized_pnl = 0
    db.add(
        PortfolioSnapshot(
            portfolio_id=portfolio.id,
            paper_account_id=account.id,
            timestamp=datetime.now(UTC),
            equity=float(balance),
            cash=float(balance),
            exposure=0,
            positions_value=0,
            daily_pnl=0,
            total_pnl=0,
        )
    )
    db.commit()
    db.refresh(account)
    return paper_account_payload(account)


@router.get("/settings/profile")
def get_profile(user: User = Depends(get_current_user)) -> dict:
    return {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "created_at": user.created_at.isoformat(),
    }


@router.patch("/settings/profile")
def update_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    user.first_name = payload.first_name.strip()
    user.last_name = payload.last_name.strip()
    user.full_name = f"{user.first_name} {user.last_name}"
    db.commit()
    return get_profile(user)


@router.get("/settings/trading")
def get_trading_settings(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    account = get_active_paper_account(db, user.id)
    if account is None:
        raise HTTPException(status_code=404, detail="Paper portfolio setup is required")
    return paper_account_payload(account)


@router.patch("/settings/trading")
def update_trading_settings(
    payload: TradingSettingsRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    account = get_active_paper_account(db, user.id)
    if account is None:
        raise HTTPException(status_code=404, detail="Paper portfolio setup is required")
    for key, value in payload.model_dump().items():
        setattr(account, key, value)
    db.commit()
    db.refresh(account)
    return paper_account_payload(account)
