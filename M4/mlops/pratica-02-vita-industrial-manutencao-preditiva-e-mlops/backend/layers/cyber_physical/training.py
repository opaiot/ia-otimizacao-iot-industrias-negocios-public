"""Treinamento, tracking e registro da representacao ciberfisica."""

import json
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from backend.config import (
    CATEGORICAL_FEATURES,
    DECISION_THRESHOLD,
    FEATURES,
    FEATURE_SET_VERSION,
    MANIFEST_DIR,
    MLFLOW_DB_PATH,
    MODEL_DIR,
    NUMERIC_FEATURES,
    PROCESSED_DATA_DIR,
    PROJECT_ROOT,
    RAW_DATA_DIR,
    RUNTIME_ROOT,
    RUNS_PATH,
    TARGET,
)
from backend.layers.cognition.evaluation import evaluate_candidate, select_candidate
from backend.layers.connection.data import (
    generate_sensor_snapshot,
    save_snapshot,
    sha256_file,
    validate_sensor_data,
)
from backend.layers.conversion.features import build_features, feature_definitions
from backend.layers.cyber_physical.algorithms import candidate_algorithms
from backend.layers.cyber_physical.registry import load_registry, register_model


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "uncommitted"


def _requirements_hash() -> str:
    path = PROJECT_ROOT / "requirements.txt"
    return sha256_file(path) if path.exists() else "unavailable"


def _preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        [
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                CATEGORICAL_FEATURES,
            ),
        ]
    )


def _append_run(row: dict) -> None:
    frame = pd.DataFrame([row])
    frame.to_csv(RUNS_PATH, mode="a", header=not RUNS_PATH.exists(), index=False)


def _log_mlflow(
    run_name: str,
    parameters: dict,
    metrics: dict,
    artifacts: list[Path],
    model,
) -> str | None:
    try:
        import mlflow
        import mlflow.sklearn

        mlflow.set_tracking_uri(f"sqlite:///{MLFLOW_DB_PATH.resolve()}")
        mlflow.set_experiment("vita_pump_failure_risk")
        with mlflow.start_run(run_name=run_name) as run:
            mlflow.log_params(parameters)
            mlflow.log_metrics(
                {
                    key: float(value)
                    for key, value in metrics.items()
                    if isinstance(value, (int, float))
                }
            )
            for artifact in artifacts:
                mlflow.log_artifact(str(artifact))
            mlflow.sklearn.log_model(model, name="model")
            return run.info.run_id
    except Exception:
        # runs.csv mantem a pratica funcional mesmo sem a interface do MLflow.
        return None


def train_and_register(n_samples: int = 1200, seed: int = 42) -> dict:
    raw_data = generate_sensor_snapshot(n_samples=n_samples, seed=seed)
    validation = validate_sensor_data(raw_data)
    raw_path = RAW_DATA_DIR / "sensors_train_v1.csv"
    data_version = save_snapshot(raw_data, raw_path)

    processed = build_features(raw_data)
    processed_path = PROCESSED_DATA_DIR / "train_features_v1.csv"
    processed.to_csv(processed_path, index=False)

    feature_path = MANIFEST_DIR / "feature_definitions.json"
    feature_path.write_text(
        json.dumps(feature_definitions(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    base_manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "data_version": data_version,
        "feature_set_version": FEATURE_SET_VERSION,
        "code_commit": _git_commit(),
        "requirements_sha256": _requirements_hash(),
        "random_seed": seed,
        "decision_threshold": DECISION_THRESHOLD,
        "split": {"test_size": 0.25, "strategy": "stratified", "seed": seed},
        "validation": validation,
    }
    manifest_path = MANIFEST_DIR / "training_manifest.json"
    manifest_path.write_text(
        json.dumps(base_manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    x = processed[FEATURES]
    y = processed[TARGET]
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.25, random_state=seed, stratify=y
    )

    runs = []
    candidate_dir = MODEL_DIR / "candidates"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    for algorithm, estimator in candidate_algorithms(seed).items():
        pipeline = Pipeline([("preprocessor", _preprocessor()), ("model", estimator)])
        pipeline.fit(x_train, y_train)
        metrics = evaluate_candidate(pipeline, x_test, y_test)
        local_run_id = uuid.uuid4().hex
        model_path = candidate_dir / f"{local_run_id}_{algorithm}.joblib"
        joblib.dump(pipeline, model_path)
        parameters = {
            "algorithm": algorithm,
            "seed": seed,
            "threshold": DECISION_THRESHOLD,
            "data_sha256": data_version["sha256"],
            "feature_set_version": FEATURE_SET_VERSION,
            "code_commit": base_manifest["code_commit"],
        }
        mlflow_run_id = _log_mlflow(
            algorithm, parameters, metrics, [manifest_path, feature_path], pipeline
        )
        run = {
            "run_id": mlflow_run_id or local_run_id,
            "algorithm": algorithm,
            "model_path": str(model_path.relative_to(RUNTIME_ROOT)),
            **metrics,
            **parameters,
        }
        _append_run(run)
        runs.append(run)

    selected = select_candidate(runs)
    next_version = len(load_registry()["models"]) + 1
    production_path = MODEL_DIR / f"PumpFailureRisk_v1.0.{next_version}.joblib"
    shutil.copy2(RUNTIME_ROOT / selected["model_path"], production_path)
    registered = register_model(
        {
            "registered_model_name": "PumpFailureRisk",
            "algorithm": selected["algorithm"],
            "source_run_id": selected["run_id"],
            "model_path": str(production_path.relative_to(RUNTIME_ROOT)),
            "model_sha256": sha256_file(production_path),
            "metrics": {
                key: selected[key]
                for key in [
                    "roc_auc",
                    "f1",
                    "precision_failure",
                    "recall_failure",
                    "expected_cost",
                ]
            },
            "data_version": data_version,
            "feature_set_version": FEATURE_SET_VERSION,
            "code_commit": base_manifest["code_commit"],
            "decision_threshold": DECISION_THRESHOLD,
            "owner": "Equipe de IA e Manutencao",
            "intended_use": "Priorizar inspecoes de bombas e motores industriais.",
            "validation_status": "approved",
        }
    )
    return {"selected_model": registered, "runs": runs, "manifest": base_manifest}


def list_runs() -> list[dict]:
    if not RUNS_PATH.exists():
        return []
    return pd.read_csv(RUNS_PATH).fillna("").to_dict(orient="records")
