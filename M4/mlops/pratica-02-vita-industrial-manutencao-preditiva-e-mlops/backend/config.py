"""Configuração central do case industrial VITA."""

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = Path(os.getenv("VITA_RUNTIME_ROOT", str(PROJECT_ROOT))).resolve()
DATA_DIR = RUNTIME_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
ARTIFACT_DIR = RUNTIME_ROOT / "artifacts"
MODEL_DIR = ARTIFACT_DIR / "models"
MANIFEST_DIR = ARTIFACT_DIR / "manifests"
REPORT_DIR = ARTIFACT_DIR / "reports"
TRACKING_DIR = ARTIFACT_DIR / "tracking"
REGISTRY_PATH = ARTIFACT_DIR / "registry.json"
RUNS_PATH = TRACKING_DIR / "runs.csv"
MLFLOW_DB_PATH = TRACKING_DIR / "mlflow.db"
PREDICTION_LOG_PATH = TRACKING_DIR / "predictions.jsonl"
FEEDBACK_LOG_PATH = TRACKING_DIR / "feedback.jsonl"
AUDIT_LOG_PATH = TRACKING_DIR / "audit.jsonl"
MODEL_CARD_PATH = RUNTIME_ROOT / "docs" / "governance" / "model_card.md"
DATASHEET_PATH = RUNTIME_ROOT / "docs" / "governance" / "datasheet.md"
TRACEABILITY_PATH = RUNTIME_ROOT / "docs" / "governance" / "traceability_report.md"
GOVERNANCE_DIR = RUNTIME_ROOT / "docs" / "governance"

TARGET = "failure_next_7d"
RAW_NUMERIC_FEATURES = [
    "motor_age_days",
    "temp_mean_24h",
    "vibration_rms_24h",
    "current_mean_24h",
    "load_mean_24h",
    "maintenance_last_30d",
]
DERIVED_FEATURES = ["temp_load_interaction", "vibration_per_age"]
NUMERIC_FEATURES = RAW_NUMERIC_FEATURES + DERIVED_FEATURES
CATEGORICAL_FEATURES = ["plant"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
REQUEST_FEATURES = RAW_NUMERIC_FEATURES + CATEGORICAL_FEATURES

DECISION_THRESHOLD = 0.35
FEATURE_SET_VERSION = "industrial_sensor_features:v1"
DATA_SCHEMA_VERSION = "sensor_snapshot:v1"
SERVICE_VERSION = "2.1.0"
OPENAI_MODEL = os.getenv("VITA_OPENAI_MODEL", "gpt-5.4-mini")


def ensure_directories() -> None:
    for directory in [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        MODEL_DIR,
        MANIFEST_DIR,
        REPORT_DIR,
        TRACKING_DIR,
        MODEL_CARD_PATH.parent,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


ensure_directories()
