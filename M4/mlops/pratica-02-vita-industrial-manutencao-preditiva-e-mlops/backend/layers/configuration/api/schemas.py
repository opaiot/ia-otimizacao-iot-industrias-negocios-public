"""Contratos da API industrial."""

from pydantic import BaseModel, Field


class TrainRequest(BaseModel):
    n_samples: int = Field(default=1200, ge=300, le=20000)
    seed: int = Field(default=42, ge=0, le=1_000_000)


class SensorReading(BaseModel):
    machine_id: int = Field(ge=1, le=100000)
    plant: str = Field(pattern="^(SP|MG|PR)$")
    motor_age_days: int = Field(ge=0, le=5000)
    temp_mean_24h: float = Field(ge=0, le=150)
    vibration_rms_24h: float = Field(ge=0, le=30)
    current_mean_24h: float = Field(ge=0, le=80)
    load_mean_24h: float = Field(ge=0, le=1.5)
    maintenance_last_30d: int = Field(ge=0, le=1)


class MonitorRequest(BaseModel):
    n_samples: int = Field(default=1000, ge=100, le=20000)
    seed: int = Field(default=99, ge=0, le=1_000_000)
    drift: bool = True


class FeedbackRequest(BaseModel):
    machine_id: int = Field(ge=1)
    model_version: str
    failure_confirmed: bool
    notes: str = Field(default="", max_length=500)


class AssistantRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
