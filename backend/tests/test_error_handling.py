from fastapi.testclient import TestClient


def test_unknown_route_uniform_404(client: TestClient) -> None:
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "http_404"
    assert body["detail"] == "Not Found"
    assert body["request_id"]


def test_validation_error_keeps_detail(client: TestClient) -> None:
    response = client.post("/cases", json={"malformed": True})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert isinstance(body["detail"], list)
    assert body["error"]["message"] == body["detail"]


def test_existing_404_detail_is_preserved(client: TestClient) -> None:
    response = client.get("/cases/CASE-00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["detail"]