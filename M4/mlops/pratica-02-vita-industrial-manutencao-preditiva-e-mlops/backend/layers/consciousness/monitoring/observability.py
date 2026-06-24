"""Logs de previsao e feedback humano para observabilidade."""

import json
from datetime import datetime, timezone

from backend.config import FEEDBACK_LOG_PATH, PREDICTION_LOG_PATH


def _append(path, record: dict) -> None:
    payload = {"timestamp": datetime.now(timezone.utc).isoformat(), **record}
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False) + "\n")


def log_prediction(record: dict) -> None:
    _append(PREDICTION_LOG_PATH, record)


def log_feedback(record: dict) -> None:
    _append(FEEDBACK_LOG_PATH, record)
