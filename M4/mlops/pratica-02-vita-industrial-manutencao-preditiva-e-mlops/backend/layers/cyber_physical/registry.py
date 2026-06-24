"""Registry didatico e versionado dos modelos ciberfisicos."""

import json
from datetime import datetime, timezone

from backend.config import REGISTRY_PATH


def load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        return {
            "registered_model": "PumpFailureRisk",
            "production_version": None,
            "models": [],
        }
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def register_model(entry: dict) -> dict:
    registry = load_registry()
    for model in registry["models"]:
        if model["stage"] == "production":
            model["stage"] = "archived"

    version = f"1.0.{len(registry['models']) + 1}"
    registered = {
        **entry,
        "version": version,
        "stage": "production",
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "approval": {
            "status": "approved_for_educational_use",
            "approved_by": "Equipe de IA e Manutencao",
            "human_review_required": True,
        },
    }
    registry["models"].append(registered)
    registry["production_version"] = version
    REGISTRY_PATH.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return registered


def production_model() -> dict:
    registry = load_registry()
    version = registry.get("production_version")
    for model in registry["models"]:
        if model["version"] == version:
            return model
    raise FileNotFoundError("Nenhum modelo foi promovido para producao.")
