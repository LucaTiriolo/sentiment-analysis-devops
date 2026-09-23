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

def test_predict_sentiment():
    """Verifica una predizione reale del modello di Sentiment Analysis."""
    response = client.post(
        "/predict",
        json={"review": "This is terrible. I hate it."}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["sentiment"] == "negative"
    assert 0.0 <= data["confidence"] <= 1.0


def test_predict_empty_review():
    """Verifica che una recensione vuota venga rifiutata."""
    response = client.post(
        "/predict",
        json={"review": "   "}
    )

    assert response.status_code == 422