def test_health_and_architecture(client):
    health = client.get("/health")
    architecture = client.get("/api/v1/architecture")

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert architecture.status_code == 200
    assert len(architecture.json()["layers"]) == 6
    assert "algoritmos" in architecture.json()["layers"][2]["implementation"]
    assert "assistente" in architecture.json()["layers"][5]["implementation"]


def test_training_tracks_candidates_and_registers_model(trained_client):
    experiments = trained_client.get("/api/v1/experiments")
    registry = trained_client.get("/api/v1/registry")

    assert experiments.status_code == 200
    assert len(experiments.json()["runs"]) == 3
    assert registry.status_code == 200
    assert registry.json()["production_version"] == "1.0.1"
    assert registry.json()["models"][0]["stage"] == "production"


def test_prediction_crosses_cyber_cognition_and_configuration(trained_client):
    response = trained_client.post(
        "/api/v1/predict",
        json={
            "machine_id": 42,
            "plant": "SP",
            "motor_age_days": 1200,
            "temp_mean_24h": 88.5,
            "vibration_rms_24h": 5.2,
            "current_mean_24h": 19.5,
            "load_mean_24h": 0.97,
            "maintenance_last_30d": 0,
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["asset"]["asset_id"] == "SP-M0042"
    assert body["asset"]["physical_state"] == "attention"
    assert 0 <= body["prediction"]["risk_probability"] <= 1
    assert body["prediction"]["model_version"] == "1.0.1"
    assert body["decision"]["priority"] in {"normal", "medium", "high", "critical"}


def test_monitoring_detects_simulated_drift(trained_client):
    response = trained_client.post(
        "/api/v1/monitor", json={"n_samples": 300, "seed": 99, "drift": True}
    )

    body = response.json()
    assert response.status_code == 200
    assert body["drift_enabled"] is True
    assert len(body["features"]) == 6
    assert body["alerts_count"] >= 1


def test_governance_documents_are_available(trained_client):
    model_card = trained_client.get("/api/v1/governance/model-card")
    datasheet = trained_client.get("/api/v1/governance/datasheet")

    assert model_card.status_code == 200
    assert "Usos não recomendados" in model_card.text
    assert datasheet.status_code == 200
    assert "Dados pessoais e sensíveis" in datasheet.text


def test_traceability_audit_and_controlled_assistant(trained_client):
    traceability = trained_client.get("/api/v1/governance/traceability")
    audit = trained_client.get("/api/v1/governance/audit")
    assistant = trained_client.post(
        "/api/v1/consciousness/assistant",
        json={"question": "Qual versão do modelo está em produção?"},
    )

    assert traceability.status_code == 200
    assert "Hash do modelo" in traceability.text
    assert audit.status_code == 200
    assert any(
        event["event"] == "model_promoted" for event in audit.json()["events"]
    )
    assert assistant.status_code == 200
    assert assistant.json()["grounded"] is True
    assert "1.0.1" in assistant.json()["answer"]
    assert "model_registry" in assistant.json()["sources"]
