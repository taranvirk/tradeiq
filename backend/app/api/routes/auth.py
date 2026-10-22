from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.database.models import PaperAccount, User
from app.database.seed import DEMO_EMAIL, DEMO_PASSWORD
from app.database.session import get_db
from app.schemas.platform import LoginRequest, SignupRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


def _user_payload(user: User, onboarding_required: bool) -> dict:
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": user.full_name,
        "email": user.email,
        "is_demo": user.is_demo,
        "created_at": user.created_at.isoformat(),
        "onboarding_required": onboarding_required,
    }


def _token(db: Session, user: User) -> TokenResponse:
    onboarding_required = db.scalar(
        select(PaperAccount.id).where(PaperAccount.user_id == user.id, PaperAccount.is_active.is_(True))
    ) is None
    return TokenResponse(
        access_token=create_access_token(user.id, user.token_version),
        user=_user_payload(user, onboarding_required),
        onboarding_required=onboarding_required,
    )


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if db.scalar(select(User).where(User.email == payload.email.lower())):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        full_name=f"{payload.first_name.strip()} {payload.last_name.strip()}",
        last_login_at=datetime.now(UTC),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists") from exc
    db.refresh(user)
    return _token(db, user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user.last_login_at = datetime.now(UTC)
    db.commit()
    return _token(db, user)


@router.post("/demo", response_model=TokenResponse)
def demo_login(db: Session = Depends(get_db)) -> TokenResponse:
    return login(LoginRequest(email=DEMO_EMAIL, password=DEMO_PASSWORD), db)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    user.token_version += 1
    db.commit()


@router.get("/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    onboarding_required = db.scalar(
        select(PaperAccount.id).where(
            PaperAccount.user_id == user.id, PaperAccount.is_active.is_(True)
        )
    ) is None
    return _user_payload(user, onboarding_required)
