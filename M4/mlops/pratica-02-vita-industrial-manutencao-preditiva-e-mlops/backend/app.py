"""Aplicação FastAPI da VITA para manutenção preditiva industrial."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import SERVICE_VERSION
from backend.layers.configuration.api.routes import router as industrial_router


app = FastAPI(
    title="VITA - Manutenção Preditiva Industrial",
    description=(
        "Case educacional de predição de risco de falha em bombas e motores, "
        "organizado pelas seis camadas da arquitetura VITA."
    ),
    version=SERVICE_VERSION,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(industrial_router)


@app.get("/", tags=["Operação"])
def root():
    return {
        "platform": "VITA",
        "case": "Predição de risco de falha em bombas e motores",
        "architecture": "/api/v1/architecture",
        "swagger": "/docs",
        "health": "/health",
        "documentation": "/html/docs/",
    }


@app.get("/health", tags=["Operação"])
def health():
    return {"status": "ok", "service_version": SERVICE_VERSION}


docs_dir = Path(__file__).resolve().parent / "docs" / "build" / "html"
app.mount(
    "/html/docs",
    StaticFiles(directory=str(docs_dir), html=True, check_dir=False),
    name="documentation",
)
