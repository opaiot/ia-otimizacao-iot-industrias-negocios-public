"""Feature engineering compartilhada entre treino e inferência."""

import pandas as pd

from backend.config import FEATURE_SET_VERSION


def build_features(data: pd.DataFrame) -> pd.DataFrame:
    features = data.copy()
    features["temp_load_interaction"] = (
        features["temp_mean_24h"] * features["load_mean_24h"]
    )
    features["vibration_per_age"] = features["vibration_rms_24h"] / (
        features["motor_age_days"] / 365 + 1
    )
    return features


def feature_definitions() -> dict:
    return {
        "version": FEATURE_SET_VERSION,
        "features": {
            "motor_age_days": "Idade do motor em dias.",
            "temp_mean_24h": "Temperatura média das últimas 24 horas.",
            "vibration_rms_24h": "Vibração RMS das últimas 24 horas.",
            "current_mean_24h": "Corrente elétrica média das últimas 24 horas.",
            "load_mean_24h": "Carga operacional média das últimas 24 horas.",
            "maintenance_last_30d": "Indicador de manutenção nos últimos 30 dias.",
            "plant": "Planta industrial de origem.",
            "temp_load_interaction": "Interação entre temperatura e carga.",
            "vibration_per_age": "Vibração ajustada pela idade do equipamento.",
        },
    }
