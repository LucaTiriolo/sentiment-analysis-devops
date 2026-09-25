import pytest

from model_service import predict_sentiment, PredictionError


class FakeModel:
    """
    Modello fittizio utilizzato per isolare il servizio
    dal modello reale durante il test unitario.
    """

    classes_ = ["negative", "neutral", "positive"]

    def predict(self, reviews):
        return ["positive"]

    def predict_proba(self, reviews):
        return [[0.10, 0.20, 0.70]]


def test_predict_sentiment():
    """
    Verifica che il servizio restituisca correttamente
    sentimento e confidence senza utilizzare il modello reale.
    """
    sentiment, confidence = predict_sentiment(
        "This is a test review.",
        sentiment_model=FakeModel()
    )

    assert sentiment == "positive"
    assert confidence == pytest.approx(0.70)

class FailingModel:
    """
    Modello fittizio che simula un errore interno
    durante l'inferenza.
    """

    def predict(self, reviews):
        raise RuntimeError("Errore simulato del modello")

def test_predict_sentiment_wraps_model_error():
    """
    Verifica che qualsiasi errore generato dal modello
    venga convertito nell'eccezione applicativa PredictionError.
    """

    with pytest.raises(PredictionError):
        predict_sentiment(
            "This review causes an error.",
            sentiment_model=FailingModel()
        )