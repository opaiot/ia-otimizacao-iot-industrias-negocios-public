"""Carregamento e inferencia do modelo ciberfisico em producao."""

import joblib
import pandas as pd

from backend.config import FEATURES, RUNTIME_ROOT
from backend.layers.conversion.features import build_features
from backend.layers.cyber_physical.registry import production_model


def predict_failure(reading: dict) -> dict:
    registered = production_model()
    model = joblib.load(RUNTIME_ROOT / registered["model_path"])
    row = build_features(pd.DataFrame([reading]))[FEATURES]
    probability = float(model.predict_proba(row)[:, 1][0])
    return {
        "risk_probability": round(probability, 4),
        "threshold": registered["decision_threshold"],
        "model_name": registered["registered_model_name"],
        "model_version": registered["version"],
        "run_id": registered["source_run_id"],
    }
