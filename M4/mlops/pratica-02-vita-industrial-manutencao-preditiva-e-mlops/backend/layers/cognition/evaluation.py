"""Avaliacao e interpretacao dos modelos candidatos."""

import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline

from backend.config import DECISION_THRESHOLD


def evaluate_candidate(
    model: Pipeline, x_test: pd.DataFrame, y_test: pd.Series
) -> dict:
    """Avalia desempenho e custo operacional de falsos resultados."""
    probability = model.predict_proba(x_test)[:, 1]
    prediction = (probability >= DECISION_THRESHOLD).astype(int)
    actual = y_test.to_numpy()
    false_positive = int(((prediction == 1) & (actual == 0)).sum())
    false_negative = int(((prediction == 0) & (actual == 1)).sum())
    return {
        "roc_auc": round(float(roc_auc_score(y_test, probability)), 6),
        "f1": round(float(f1_score(y_test, prediction, zero_division=0)), 6),
        "precision_failure": round(
            float(precision_score(y_test, prediction, zero_division=0)), 6
        ),
        "recall_failure": round(
            float(recall_score(y_test, prediction, zero_division=0)), 6
        ),
        "expected_cost": round(
            (false_negative * 10 + false_positive) / len(y_test), 6
        ),
        "false_negative": false_negative,
        "false_positive": false_positive,
    }


def select_candidate(runs: list[dict]) -> dict:
    """Seleciona por custo esperado e, no desempate, recall de falhas."""
    return min(
        runs,
        key=lambda item: (item["expected_cost"], -item["recall_failure"]),
    )
