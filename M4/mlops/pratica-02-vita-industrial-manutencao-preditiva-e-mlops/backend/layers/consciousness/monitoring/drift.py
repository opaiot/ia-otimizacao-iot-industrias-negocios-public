"""Deteccao de mudanca na distribuicao dos dados de sensores."""

import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from backend.config import RAW_DATA_DIR, RAW_NUMERIC_FEATURES, REPORT_DIR
from backend.layers.connection.data import (
    generate_sensor_snapshot,
    save_snapshot,
    validate_sensor_data,
)


def population_stability_index(expected, actual, bins: int = 10) -> float:
    expected = pd.Series(expected).dropna().astype(float)
    actual = pd.Series(actual).dropna().astype(float)
    breakpoints = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)))
    if len(breakpoints) < 3:
        return 0.0
    expected_counts = np.histogram(expected, bins=breakpoints)[0] / len(expected)
    actual_counts = np.histogram(actual, bins=breakpoints)[0] / len(actual)
    expected_counts = np.where(expected_counts == 0, 0.0001, expected_counts)
    actual_counts = np.where(actual_counts == 0, 0.0001, actual_counts)
    return float(
        np.sum(
            (actual_counts - expected_counts)
            * np.log(actual_counts / expected_counts)
        )
    )


def monitor_drift(n_samples: int = 1000, seed: int = 99, drift: bool = True) -> dict:
    reference_path = RAW_DATA_DIR / "sensors_train_v1.csv"
    if not reference_path.exists():
        raise FileNotFoundError("Execute o treinamento antes do monitoramento.")
    reference = pd.read_csv(reference_path)
    production = generate_sensor_snapshot(
        n_samples=n_samples,
        seed=seed,
        snapshot_name="sensors_production_v2",
        drift=drift,
    )
    validate_sensor_data(production)
    production_version = save_snapshot(
        production, RAW_DATA_DIR / "sensors_production_v2.csv"
    )

    report = {}
    for feature in RAW_NUMERIC_FEATURES:
        psi = population_stability_index(reference[feature], production[feature])
        report[feature] = {
            "psi": round(psi, 4),
            "status": "alert" if psi >= 0.2 else "ok",
        }
    alerts = [name for name, result in report.items() if result["status"] == "alert"]
    output = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "production_data_version": production_version,
        "drift_enabled": drift,
        "alerts": alerts,
        "alerts_count": len(alerts),
        "recommended_action": (
            "Investigar as mudancas antes de retreinar ou promover outro modelo."
            if alerts
            else "Manter o modelo e o monitoramento regular."
        ),
        "automatic_retraining": False,
        "features": report,
    }
    (REPORT_DIR / "drift_report.json").write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return output
