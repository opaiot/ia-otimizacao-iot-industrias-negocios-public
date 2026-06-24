"""Constrói o estado digital de uma bomba ou motor."""


def build_asset_state(reading: dict) -> dict:
    alerts = []
    if reading["temp_mean_24h"] >= 85:
        alerts.append("temperatura_elevada")
    if reading["vibration_rms_24h"] >= 5:
        alerts.append("vibracao_elevada")
    if reading["load_mean_24h"] >= 0.95:
        alerts.append("carga_elevada")

    return {
        "asset_id": f"{reading['plant']}-M{int(reading['machine_id']):04d}",
        "machine_id": int(reading["machine_id"]),
        "plant": reading["plant"],
        "operational_alerts": alerts,
        "physical_state": "attention" if alerts else "normal",
        "sensor_snapshot": {
            "temperature": reading["temp_mean_24h"],
            "vibration": reading["vibration_rms_24h"],
            "current": reading["current_mean_24h"],
            "load": reading["load_mean_24h"],
        },
    }
