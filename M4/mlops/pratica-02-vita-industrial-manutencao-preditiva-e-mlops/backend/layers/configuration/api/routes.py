"""Endpoints que orquestram as seis camadas da VITA."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from backend.config import DATASHEET_PATH, MODEL_CARD_PATH, TRACEABILITY_PATH
from backend.layers.configuration.api.schemas import (
    AssistantRequest,
    FeedbackRequest,
    MonitorRequest,
    SensorReading,
    TrainRequest,
)
from backend.layers.configuration.decision import configure_action
from backend.layers.consciousness.assistant import answer_question
from backend.layers.consciousness.audit import audit_event, list_audit_events
from backend.layers.consciousness.governance.documents import (
    generate_governance_documents,
    read_document,
)
from backend.layers.consciousness.knowledge import knowledge_snapshot
from backend.layers.consciousness.monitoring import (
    log_feedback,
    log_prediction,
    monitor_drift,
)
from backend.layers.cyber_physical.assets import build_asset_state
from backend.layers.cyber_physical.inference import predict_failure
from backend.layers.cyber_physical.registry import load_registry, production_model
from backend.layers.cyber_physical.training import list_runs, train_and_register


router = APIRouter(prefix="/api/v1", tags=["VITA Industrial"])


@router.get("/architecture")
def architecture():
    return {
        "case": "Predição de risco de falha em bombas e motores",
        "organization": (
            "Instanciação pedagógica: o código foi organizado por camada para "
            "tornar responsabilidades, entradas, saídas e evidências observáveis."
        ),
        "layers": [
            {
                "name": "Conexão",
                "technology": "Data Technology",
                "implementation": "aquisição, identificação e validação de sensores IoT",
            },
            {
                "name": "Conversão",
                "technology": "Analytic Technology",
                "implementation": "curadoria, transformação e features versionadas",
            },
            {
                "name": "Ciberfísica",
                "technology": "Analytic Technology",
                "implementation": "estado digital, algoritmos, treinamento, inferência e registry",
            },
            {
                "name": "Cognição",
                "technology": "Analytic Technology",
                "implementation": "avaliação, diagnóstico, métricas e interpretação",
            },
            {
                "name": "Configuração",
                "technology": "Operation Technology",
                "implementation": "API, prioridade e recomendação operacional",
            },
            {
                "name": "Consciência",
                "technology": "Knowledge Technology",
                "implementation": (
                    "monitoramento, governança, auditoria, conhecimento e assistente"
                ),
            },
        ],
    }


@router.post("/train")
def train(request: TrainRequest):
    result = train_and_register(request.n_samples, request.seed)
    documents = generate_governance_documents(
        result["selected_model"], result["manifest"]
    )
    audit_event(
        "model_promoted",
        "training_pipeline",
        {
            "version": result["selected_model"]["version"],
            "run_id": result["selected_model"]["source_run_id"],
            "documents": list(documents),
        },
    )
    return {"status": "trained_and_registered", **result, "documents": documents}


@router.get("/experiments")
def experiments():
    return {"runs": list_runs()}


@router.get("/registry")
def registry():
    return load_registry()


@router.get("/registry/production")
def registry_production():
    try:
        return production_model()
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/predict")
def predict(reading: SensorReading):
    payload = reading.model_dump()
    asset_state = build_asset_state(payload)
    try:
        cognition = predict_failure(payload)
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=409,
            detail="Treine e registre um modelo antes da inferencia.",
        ) from error
    configuration = configure_action(
        cognition["risk_probability"], cognition["threshold"], asset_state
    )
    response = {
        "asset": asset_state,
        "prediction": cognition,
        "decision": configuration,
    }
    log_prediction(
        {
            "machine_id": reading.machine_id,
            "plant": reading.plant,
            "model_version": cognition["model_version"],
            "risk_probability": cognition["risk_probability"],
            "priority": configuration["priority"],
        }
    )
    audit_event(
        "prediction_generated",
        "api_user",
        {
            "machine_id": reading.machine_id,
            "model_version": cognition["model_version"],
            "priority": configuration["priority"],
        },
    )
    return response


@router.post("/monitor")
def monitor(request: MonitorRequest):
    try:
        report = monitor_drift(request.n_samples, request.seed, request.drift)
    except FileNotFoundError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    audit_event(
        "drift_monitoring_completed",
        "monitoring_pipeline",
        {"alerts": report["alerts"], "automatic_retraining": False},
    )
    return report


@router.post("/feedback")
def feedback(request: FeedbackRequest):
    log_feedback(request.model_dump())
    audit_event(
        "human_feedback_registered",
        "maintenance_operator",
        {
            "machine_id": request.machine_id,
            "model_version": request.model_version,
            "failure_confirmed": request.failure_confirmed,
        },
    )
    return {"status": "feedback_registered", "machine_id": request.machine_id}


def _document(path):
    try:
        return read_document(path)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/governance/model-card", response_class=PlainTextResponse)
def model_card():
    return _document(MODEL_CARD_PATH)


@router.get("/governance/datasheet", response_class=PlainTextResponse)
def datasheet():
    return _document(DATASHEET_PATH)


@router.get("/governance/traceability", response_class=PlainTextResponse)
def traceability():
    return _document(TRACEABILITY_PATH)


@router.get("/governance/audit")
def audit(limit: int = 100):
    return {"events": list_audit_events(limit=min(max(limit, 1), 500))}


@router.get("/consciousness/knowledge")
def knowledge():
    return knowledge_snapshot()


@router.post("/consciousness/assistant")
def assistant(request: AssistantRequest):
    result = answer_question(request.question)
    audit_event(
        "assistant_question_answered",
        "dashboard_user",
        {"provider": result["provider"], "sources": result["sources"]},
    )
    return result
