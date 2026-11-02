import os
import pytest
from fastapi.testclient import TestClient
from app.server import app, limiter

os.environ.setdefault("INTERNAL_API_KEY", "test-api-key")
os.environ.setdefault("BASE_URL", "https://fahrinfo.vbb.de/restproxy/latest")
os.environ.setdefault("ACCESS_ID", "test-access-id")
os.environ.setdefault("DATA_LAKE_PATH", "/tmp/test_data_lake")

from app.server import app  # noqa: E402


@pytest.fixture
def client():
    limiter.enabled = False  # Rate Limiting für Tests deaktivieren
    with TestClient(app) as c:
        yield c
    limiter.enabled = True


@pytest.fixture
def api_key_header():
    return {"X-Api-Key": os.environ["INTERNAL_API_KEY"]}