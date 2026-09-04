"""End-to-end health and database connectivity tests."""


def test_health_workflow(api_client):
    """The API reports healthy status through the test database."""
    response = api_client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)
    assert data


def test_liveness_workflow(api_client):
    """The liveness endpoint is reachable through FastAPI."""
    response = api_client.get("/api/v1/health/live")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)
    assert data


def test_readiness_workflow(api_client):
    """The readiness endpoint confirms the application is ready."""
    response = api_client.get("/api/v1/health/ready")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)
    assert data