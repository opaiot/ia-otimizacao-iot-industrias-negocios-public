"""Aquisição simulada de sensores industriais."""

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from backend.config import DATA_SCHEMA_VERSION, RUNTIME_ROOT, TARGET


REQUIRED_COLUMNS = {
    "machine_id",
    "timestamp",
    "plant",
    "motor_age_days",
    "temp_mean_24h",
    "vibration_rms_24h",
    "current_mean_24h",
    "load_mean_24h",
    "maintenance_last_30d",
}


def generate_sensor_snapshot(
    n_samples: int = 2000,
    seed: int = 42,
    snapshot_name: str = "sensors_train_v1",
    drift: bool = False,
) -> pd.DataFrame:
    """Simula leituras agregadas de bombas e motores monitorados por IoT."""
    rng = np.random.default_rng(seed)
    plants = rng.choice(["SP", "MG", "PR"], size=n_samples, p=[0.45, 0.35, 0.20])
    vibration_shift = 0.9 if drift else 0.0
    load_shift = 0.08 if drift else 0.0
    temperature_shift = 4.0 if drift else 0.0

    data = pd.DataFrame(
        {
            "snapshot": snapshot_name,
            "schema_version": DATA_SCHEMA_VERSION,
            "machine_id": rng.integers(1, 251, size=n_samples),
            "timestamp": pd.Timestamp("2026-01-01")
            + pd.to_timedelta(rng.integers(0, 120, size=n_samples), unit="D"),
            "plant": plants,
            "motor_age_days": rng.integers(30, 3500, size=n_samples),
            "temp_mean_24h": rng.normal(72 + temperature_shift, 9, size=n_samples),
            "vibration_rms_24h": rng.gamma(2.0, 1.0, size=n_samples) + vibration_shift,
            "current_mean_24h": rng.normal(18, 4, size=n_samples),
            "load_mean_24h": np.clip(
                rng.normal(0.72 + load_shift, 0.12, size=n_samples), 0.1, 1.2
            ),
            "maintenance_last_30d": rng.binomial(1, 0.18, size=n_samples),
        }
    )

    plant_risk = data["plant"].map({"SP": 0.05, "MG": 0.03, "PR": 0.04})
    score = (
        -5.0
        + 0.0010 * data["motor_age_days"]
        + 0.035 * (data["temp_mean_24h"] - 70)
        + 0.55 * data["vibration_rms_24h"]
        + 0.025 * (data["current_mean_24h"] - 18)
        + 2.2 * (data["load_mean_24h"] - 0.7)
        - 0.7 * data["maintenance_last_30d"]
        + plant_risk
    )
    probability = 1 / (1 + np.exp(-score))
    data[TARGET] = rng.binomial(1, probability)
    return data


def validate_sensor_data(data: pd.DataFrame) -> dict:
    missing = REQUIRED_COLUMNS - set(data.columns)
    if missing:
        raise ValueError(f"Colunas ausentes: {sorted(missing)}")

    checks = {
        "motor_age_days": data["motor_age_days"].between(0, 5000),
        "temp_mean_24h": data["temp_mean_24h"].between(0, 150),
        "vibration_rms_24h": data["vibration_rms_24h"].between(0, 30),
        "current_mean_24h": data["current_mean_24h"].between(0, 80),
        "load_mean_24h": data["load_mean_24h"].between(0, 1.5),
        "maintenance_last_30d": data["maintenance_last_30d"].isin([0, 1]),
        "plant": data["plant"].isin(["SP", "MG", "PR"]),
    }
    failed = [name for name, valid in checks.items() if not bool(valid.all())]
    if failed:
        raise ValueError(f"Valores fora da faixa plausível: {failed}")

    return {
        "status": "valid",
        "rows": int(len(data)),
        "columns": int(len(data.columns)),
        "null_values": int(data.isna().sum().sum()),
        "schema_version": DATA_SCHEMA_VERSION,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_snapshot(data: pd.DataFrame, path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(path, index=False)
    return {
        "name": data["snapshot"].iloc[0] if "snapshot" in data else path.stem,
        "path": str(path.resolve().relative_to(RUNTIME_ROOT.resolve())),
        "rows": int(len(data)),
        "sha256": sha256_file(path),
        "schema_version": DATA_SCHEMA_VERSION,
    }
