"""Trilha de auditoria das decisoes e evidencias do ciclo de vida."""

import json
from datetime import datetime, timezone

from backend.config import AUDIT_LOG_PATH


def audit_event(event: str, actor: str, details: dict | None = None) -> dict:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "actor": actor,
        "details": details or {},
    }
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def list_audit_events(limit: int = 100) -> list[dict]:
    if not AUDIT_LOG_PATH.exists():
        return []
    lines = AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines[-limit:] if line.strip()][::-1]
