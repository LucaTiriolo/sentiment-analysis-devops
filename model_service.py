import pickle
from pathlib import Path


# Percorso del modello rispetto alla root del progetto.
MODEL_PATH = Path("model/sentiment_analysis_model.pkl")


# Il modello viene caricato una sola volta all'avvio del modulo.
with MODEL_PATH.open("rb") as file:
    model = pickle.load(file)


def predict_sentiment(review: str) -> tuple[str, float]:
    """
    Esegue la predizione del sentimento di una recensione.

    Restituisce:
    - sentimento previsto;
    - confidence associata alla classe prevista.
    """

    prediction = model.predict([review])[0]

    probabilities = model.predict_proba([review])[0]

    confidence = float(max(probabilities))

    return prediction, confidence