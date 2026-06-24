"""Converte a predição em ação recomendada."""


def configure_action(probability: float, threshold: float, asset_state: dict) -> dict:
    high_risk = probability >= threshold
    physical_attention = asset_state["physical_state"] == "attention"

    if high_risk and physical_attention:
        priority = "critical"
        recommendation = "Inspecionar o equipamento nas próximas 24 horas."
    elif high_risk:
        priority = "high"
        recommendation = "Programar inspeção nas próximas 48 horas."
    elif physical_attention:
        priority = "medium"
        recommendation = "Revisar sensores e acompanhar a próxima leitura."
    else:
        priority = "normal"
        recommendation = "Manter monitoramento regular."

    return {
        "risk_class": "high" if high_risk else "low",
        "priority": priority,
        "recommendation": recommendation,
        "automatic_shutdown": False,
    }
