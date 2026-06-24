import os
import tempfile

import pytest
from fastapi.testclient import TestClient


TEST_RUNTIME = tempfile.mkdtemp(prefix="vita_test_")
os.environ["VITA_RUNTIME_ROOT"] = TEST_RUNTIME


@pytest.fixture(scope="session")
def client():
    from backend.app import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def trained_client(client):
    response = client.post("/api/v1/train", json={"n_samples": 350, "seed": 42})
    assert response.status_code == 200, response.text
    return client
