import model_service


class FakeModel:
    """
    Modello fittizio utilizzato per isolare il servizio
    dal modello reale durante il test unitario.
    """

    def predict(self, reviews):
        return ["positive"]

    def predict_proba(self, reviews):
        return [[0.10, 0.20, 0.70]]


def test_predict_sentiment(monkeypatch):
    """
    Verifica che il servizio restituisca correttamente
    sentimento e confidence.
    """

    monkeypatch.setattr(model_service, "model", FakeModel())

    sentiment, confidence = model_service.predict_sentiment(
        "This is a test review."
    )

    assert sentiment == "positive"
    assert confidence == 0.70