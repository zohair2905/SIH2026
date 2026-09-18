from fastapi.testclient import TestClient


def test_echoes_incoming_request_id(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-ID": "req-123"})
    assert response.headers["X-Request-ID"] == "req-123"


def test_generates_request_id_when_absent(client: TestClient) -> None:
    response = client.get("/health")
    assert response.headers["X-Request-ID"]


def test_request_id_appears_in_error_envelope(client: TestClient) -> None:
    response = client.get("/does-not-exist")
    body = response.json()
    assert body["request_id"] == response.headers["X-Request-ID"]