from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import ClassifierMixin
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.features.engine import FEATURE_COLUMNS, engineer_features

MODEL_DIR = Path(__file__).resolve().parents[3] / "artifacts" / "models"


def _models(include_xgboost: bool = True) -> dict[str, ClassifierMixin]:
    models: dict[str, ClassifierMixin] = {
        "logistic_regression": Pipeline(
            [
                ("imputer", SimpleImputer()),
                ("scaler", StandardScaler()),
                ("model", LogisticRegression(max_iter=1000)),
            ]
        ),
        "random_forest": Pipeline(
            [
                ("imputer", SimpleImputer()),
                ("model", RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)),
            ]
        ),
        "gradient_boosting": Pipeline(
            [
                ("imputer", SimpleImputer()),
                ("model", GradientBoostingClassifier(n_estimators=80, random_state=42)),
            ]
        ),
    }
    if not include_xgboost:
        return models
    try:
        from xgboost import XGBClassifier

        models["xgboost"] = Pipeline(
            [
                ("imputer", SimpleImputer()),
                (
                    "model",
                    XGBClassifier(
                        n_estimators=40,
                        max_depth=4,
                        learning_rate=0.05,
                        random_state=42,
                        n_jobs=1,
                        tree_method="hist",
                    ),
                ),
            ]
        )
    except ImportError:
        pass
    return models


def prepare_training_data(candles: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    features = engineer_features(candles)
    features["target"] = (features["close"].shift(-1) > features["close"]).astype(int)
    clean = features.iloc[:-1].dropna(subset=["return_20d", "sma_50"]).copy()
    if len(clean) < 80:
        raise ValueError("At least 80 usable candles are required to train a model")
    return clean[FEATURE_COLUMNS], clean["target"], features


def train_and_compare(candles: pd.DataFrame, symbol: str, include_xgboost: bool = True) -> dict:
    x, y, enriched = prepare_training_data(candles)
    split = max(int(len(x) * 0.8), 60)
    x_train, x_test = x.iloc[:split], x.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    if y_train.nunique() < 2 or y_test.nunique() < 2:
        raise ValueError("Training window must contain both positive and negative returns")
    results: list[dict] = []
    best: tuple[float, str, ClassifierMixin] | None = None
    for name, model in _models(include_xgboost).items():
        model.fit(x_train, y_train)
        probability = model.predict_proba(x_test)[:, 1]
        predicted = (probability >= 0.5).astype(int)
        metrics = {
            "accuracy": round(float(accuracy_score(y_test, predicted)), 4),
            "precision": round(float(precision_score(y_test, predicted, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, predicted, zero_division=0)), 4),
            "f1": round(float(f1_score(y_test, predicted, zero_division=0)), 4),
            "roc_auc": round(float(roc_auc_score(y_test, probability)), 4),
            "trading_return": round(
                float(
                    (
                        (1 + candles["close"].pct_change().reindex(x_test.index).fillna(0) * predicted).prod()
                        - 1
                    )
                    * 100
                ),
                2,
            ),
        }
        results.append({"algorithm": name, "metrics": metrics})
        if best is None or metrics["roc_auc"] > best[0]:
            best = (metrics["roc_auc"], name, model)
    assert best is not None
    version = f"{best[1]}-{symbol.lower()}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    file_path = MODEL_DIR / f"{version}.joblib"
    joblib.dump({"model": best[2], "features": FEATURE_COLUMNS}, file_path)
    latest = enriched[FEATURE_COLUMNS].iloc[[-1]]
    probability_up = float(best[2].predict_proba(latest)[:, 1][0])
    importance = _feature_importance(best[2], latest)
    return {
        "version": version,
        "algorithm": best[1],
        "file_path": str(file_path),
        "training_start": x.index[0].date(),
        "training_end": x_train.index[-1].date(),
        "test_start": x_test.index[0].date(),
        "test_end": x_test.index[-1].date(),
        "results": results,
        "probability_up": probability_up,
        "explanation": importance,
        "walk_forward": walk_forward_validate(x, y),
    }


def walk_forward_validate(x: pd.DataFrame, y: pd.Series) -> dict:
    scores = []
    for train_index, test_index in TimeSeriesSplit(n_splits=3).split(x):
        if y.iloc[train_index].nunique() < 2 or y.iloc[test_index].nunique() < 2:
            continue
        model = _models()["logistic_regression"]
        model.fit(x.iloc[train_index], y.iloc[train_index])
        scores.append(roc_auc_score(y.iloc[test_index], model.predict_proba(x.iloc[test_index])[:, 1]))
    return {"windows": len(scores), "average_roc_auc": round(float(np.mean(scores)), 4) if scores else 0}


def _feature_importance(model: ClassifierMixin, latest: pd.DataFrame) -> dict:
    estimator = model.named_steps["model"] if isinstance(model, Pipeline) else model
    weights = getattr(estimator, "feature_importances_", None)
    if weights is None:
        weights = np.abs(getattr(estimator, "coef_", np.ones((1, len(FEATURE_COLUMNS))))[0])
    ranked = sorted(
        zip(FEATURE_COLUMNS, weights, strict=True), key=lambda item: float(item[1]), reverse=True
    )[:6]
    positive, negative = [], []
    for feature, weight in ranked:
        value = float(latest.iloc[0][feature])
        item = {"feature": feature, "impact": round(float(weight), 4), "value": round(value, 4)}
        (positive if value >= 0 else negative).append(item)
    return {"positive_factors": positive[:4], "negative_factors": negative[:3]}
