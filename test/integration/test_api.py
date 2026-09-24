from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_hello_world():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_sentiment():
    """
    Verifica l'integrazione completa tra API FastAPI
    e modello reale di Sentiment Analysis.
    """

    response = client.post(
        "/predict",
        json={"review": "This is terrible. I hate it."}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["sentiment"] == "negative"
    assert 0.0 <= data["confidence"] <= 1.0


def test_predict_empty_review():
    """
    Verifica che una recensione vuota venga rifiutata.
    """

    response = client.post(
        "/predict",
        json={"review": "   "}
    )

    assert response.status_code == 422


def test_metrics_endpoint():
    """
    Verifica che l'endpoint Prometheus sia raggiungibile
    e restituisca le metriche applicative.
    """

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "http_request_duration_seconds" in response.text
    assert "prediction_errors_total" in response.text