from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.models import MarketCandle, MLExperiment, MLModel, Prediction, Stock, User
from app.database.session import get_db
from app.features.engine import FEATURE_COLUMNS
from app.machine_learning.service import train_and_compare

router = APIRouter(tags=["machine learning"])


def _prediction_payload(item: Prediction) -> dict:
    return {
        "id": item.id,
        "symbol": item.symbol,
        "prediction": item.signal,
        "probability_up": round(item.probability_up, 4),
        "confidence": round(item.confidence, 4),
        "model_version": item.model_version,
        "timestamp": item.created_at.isoformat(),
        "explanation": item.explanation,
    }


@router.get("/predictions")
def predictions(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict]:
    rows = db.scalars(
        select(Prediction).where(Prediction.user_id == user.id).order_by(Prediction.created_at.desc())
    ).all()
    latest: dict[str, Prediction] = {}
    for item in rows:
        latest.setdefault(item.symbol, item)
    return [_prediction_payload(item) for item in latest.values()]


@router.get("/predictions/{symbol}")
def prediction(symbol: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    item = db.scalar(
        select(Prediction)
        .where(Prediction.user_id == user.id, Prediction.symbol == symbol.upper())
        .order_by(Prediction.created_at.desc())
    )
    if item is None:
        raise HTTPException(status_code=404, detail="No prediction available")
    return _prediction_payload(item)


@router.post("/models/train/{symbol}")
def train_model(symbol: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    symbol = symbol.upper()
    if db.get(Stock, symbol) is None:
        raise HTTPException(status_code=404, detail="Unknown ticker")
    rows = db.scalars(
        select(MarketCandle).where(MarketCandle.symbol == symbol).order_by(MarketCandle.timestamp)
    ).all()
    frame = pd.DataFrame(
        [{"open": r.open, "high": r.high, "low": r.low, "close": r.close, "volume": r.volume} for r in rows],
        index=pd.DatetimeIndex([r.timestamp for r in rows]),
    )
    try:
        result = train_and_compare(frame, symbol)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    db.execute(update(MLModel).values(is_active=False))
    chosen = next(item for item in result["results"] if item["algorithm"] == result["algorithm"])
    model = MLModel(
        model_name="Directional Classifier",
        version=result["version"],
        algorithm=result["algorithm"],
        training_start=result["training_start"],
        training_end=result["training_end"],
        features=FEATURE_COLUMNS,
        hyperparameters={"chronological_split": 0.8},
        metrics={**chosen["metrics"], "walk_forward": result["walk_forward"]},
        file_path=result["file_path"],
        is_active=True,
    )
    db.add(model)
    for experiment in result["results"]:
        db.add(
            MLExperiment(
                algorithm=experiment["algorithm"],
                symbol=symbol,
                features=FEATURE_COLUMNS,
                hyperparameters={"chronological_split": 0.8},
                training_window=f"{result['training_start']}:{result['training_end']}",
                test_window=f"{result['test_start']}:{result['test_end']}",
                metrics=experiment["metrics"],
            )
        )
    probability = result["probability_up"]
    prediction_row = Prediction(
        user_id=user.id,
        symbol=symbol,
        signal="BUY" if probability >= 0.65 else "SELL" if probability <= 0.35 else "HOLD",
        probability_up=probability,
        confidence=abs(probability - 0.5) * 2,
        model_version=result["version"],
        explanation=result["explanation"],
    )
    db.add(prediction_row)
    db.commit()
    db.refresh(prediction_row)
    return {
        "model": {
            "version": result["version"],
            "algorithm": result["algorithm"],
            "comparison": result["results"],
            "walk_forward": result["walk_forward"],
        },
        "prediction": _prediction_payload(prediction_row),
    }


@router.get("/models")
def models(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(MLModel).order_by(MLModel.created_at.desc())).all()
    return [
        {
            "id": item.id,
            "name": item.model_name,
            "version": item.version,
            "algorithm": item.algorithm,
            "training_start": item.training_start.isoformat(),
            "training_end": item.training_end.isoformat(),
            "metrics": item.metrics,
            "features": item.features,
            "is_active": item.is_active,
            "created_at": item.created_at.isoformat(),
        }
        for item in rows
    ]


@router.get("/experiments")
def experiments(db: Session = Depends(get_db)) -> list[dict]:
    return [
        {
            "id": item.id,
            "algorithm": item.algorithm,
            "symbol": item.symbol,
            "training_window": item.training_window,
            "test_window": item.test_window,
            "metrics": item.metrics,
        }
        for item in db.scalars(select(MLExperiment).order_by(MLExperiment.created_at.desc()).limit(50)).all()
    ]


@router.get("/scanner")
def scanner(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict]:
    rows = predictions(db, user)
    return sorted(rows, key=lambda item: item["probability_up"], reverse=True)
