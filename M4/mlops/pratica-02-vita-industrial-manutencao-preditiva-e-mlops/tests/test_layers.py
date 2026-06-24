import pandas as pd
import pytest

from backend.layers.connection.data import generate_sensor_snapshot, validate_sensor_data
from backend.layers.conversion.features import build_features
from backend.layers.cyber_physical.algorithms import candidate_algorithms


def test_connection_and_conversion_share_valid_contract():
    data = generate_sensor_snapshot(n_samples=50, seed=7)
    validation = validate_sensor_data(data)
    features = build_features(data)

    assert validation["status"] == "valid"
    assert "temp_load_interaction" in features
    assert "vibration_per_age" in features


def test_connection_rejects_out_of_range_sensor():
    data = generate_sensor_snapshot(n_samples=20, seed=7)
    data.loc[0, "temp_mean_24h"] = 999

    with pytest.raises(ValueError, match="faixa plausível"):
        validate_sensor_data(data)


def test_cyber_physical_layer_owns_the_model_algorithms():
    candidates = candidate_algorithms(seed=42)

    assert set(candidates) == {
        "LogisticRegression",
        "RandomForest",
        "GradientBoosting",
    }
