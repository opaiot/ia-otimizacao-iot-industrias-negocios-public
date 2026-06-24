"""Consolida somente fontes controladas e rastreaveis do projeto."""

import json
from datetime import datetime, timezone
from pathlib import Path

from backend.config import (
    DATASHEET_PATH,
    FEEDBACK_LOG_PATH,
    MANIFEST_DIR,
    MODEL_CARD_PATH,
    PREDICTION_LOG_PATH,
    REPORT_DIR,
    TRACEABILITY_PATH,
)
from backend.layers.consciousness.audit import list_audit_events
from backend.layers.cyber_physical.registry import load_registry
from backend.layers.cyber_physical.training import list_runs


def _json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _text(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line)


def knowledge_snapshot() -> dict:
    """Monta o contexto verificavel usado pelo dashboard e pelo assistente."""
    registry = load_registry()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": [
            "model_registry",
            "experiment_tracking",
            "training_manifest",
            "feature_definitions",
            "drift_report",
            "model_card",
            "datasheet",
            "traceability_report",
            "audit_log",
        ],
        "model_registry": registry,
        "production_model": next(
            (
                model
                for model in registry.get("models", [])
                if model["version"] == registry.get("production_version")
            ),
            None,
        ),
        "recent_experiments": list_runs()[-10:],
        "training_manifest": _json(MANIFEST_DIR / "training_manifest.json", None),
        "feature_definitions": _json(
            MANIFEST_DIR / "feature_definitions.json", None
        ),
        "drift_report": _json(REPORT_DIR / "drift_report.json", None),
        "documents": {
            "model_card": _text(MODEL_CARD_PATH),
            "datasheet": _text(DATASHEET_PATH),
            "traceability_report": _text(TRACEABILITY_PATH),
        },
        "operational_evidence": {
            "prediction_records": _line_count(PREDICTION_LOG_PATH),
            "feedback_records": _line_count(FEEDBACK_LOG_PATH),
            "recent_audit_events": list_audit_events(limit=20),
        },
    }
