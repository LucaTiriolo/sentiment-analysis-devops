import pytest
from fastapi.testclient import TestClient

from main import app
from model_service import ModelLoadError, PredictionError


client = TestClient(app)


def test_application_info():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": "Sentiment Analysis API",
        "version": "1.0.0",
        "status": "running"
    }


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "model": "loaded"
    }

def test_health_check_model_unavailable(monkeypatch):
    """
    Verifica che l'health check restituisca HTTP 503
    quando il modello non è disponibile.
    """

    def raise_model_load_error():
        raise ModelLoadError("Errore simulato nel caricamento del modello")

    monkeypatch.setattr(
        "routers.system.load_model",
        raise_model_load_error
    )

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Modello non disponibile"
    }

@pytest.mark.parametrize(
    ("review", "expected_sentiment"),
    [
        ("This product is amazing! I love it.", "positive"),
        ("The product is okay, nothing special.", "neutral"),
        ("This is terrible. I hate it.", "negative"),
    ],
)
def test_predict_sentiment(review, expected_sentiment):
    """
    Verifica l'integrazione completa tra API FastAPI
    e modello reale per tutte le classi di sentimento previste.
    """
    response = client.post(
        "/predict",
        json={"review": review}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["sentiment"] == expected_sentiment
    assert isinstance(data["confidence"], float)
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
    Verifica che l'endpoint Prometheus:
    - sia raggiungibile;
    - restituisca il formato testuale previsto;
    - esponga tutte le metriche applicative personalizzate.
    """
    response = client.get("/metrics")

    assert response.status_code == 200

    assert response.headers["content-type"].startswith(
        "text/plain"
    )

    assert "http_request_duration_seconds" in response.text
    assert "prediction_errors_total" in response.text
    assert "predictions_total" in response.text

def get_prediction_errors_total() -> float:
    """
    Recupera il valore corrente del contatore degli errori
    direttamente dall'endpoint Prometheus.
    """
    response = client.get("/metrics")

    assert response.status_code == 200

    for line in response.text.splitlines():
        if line.startswith("prediction_errors_total "):
            return float(line.split()[1])

    raise AssertionError(
        "La metrica prediction_errors_total non è stata trovata"
    )


def test_prediction_error_increments_metric(monkeypatch):
    """
    Verifica che un errore durante la predizione incrementi
    la metrica prediction_errors_total.
    """

    initial_errors = get_prediction_errors_total()

    def raise_prediction_error(review: str):
        raise PredictionError(
            "Errore simulato durante la predizione"
        )

    monkeypatch.setattr(
        "routers.prediction.predict_sentiment",
        raise_prediction_error
    )

    response = client.post(
        "/predict",
        json={"review": "This is a valid review."}
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Errore durante la predizione"
    }

    final_errors = get_prediction_errors_total()

    assert final_errors == initial_errors + 1

def test_predict_review_too_long():
    """
    Verifica che una recensione superiore al limite massimo
    consentito venga rifiutata.
    """
    response = client.post(
        "/predict",
        json={"review": "a" * 5001}
    )

    assert response.status_code == 422

def test_predict_model_unavailable(monkeypatch):
    """
    Verifica che l'endpoint /predict restituisca HTTP 503
    quando il modello non può essere caricato.
    """

    def raise_model_load_error(review: str):
        raise ModelLoadError(
            "Errore simulato nel caricamento del modello"
        )

    monkeypatch.setattr(
        "routers.prediction.predict_sentiment",
        raise_model_load_error
    )

    response = client.post(
        "/predict",
        json={"review": "This is a valid review."}
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Modello non disponibile"
    }