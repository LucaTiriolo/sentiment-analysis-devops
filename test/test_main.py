from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_hello_world():
    """Verifica che l'endpoint principale risponda correttamente."""
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_health_check():
    """Verifica che l'health check segnali l'applicazione come attiva."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}