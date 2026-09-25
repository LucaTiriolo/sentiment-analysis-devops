import pickle
from functools import lru_cache
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model" / "sentiment_analysis_model.pkl"

class PredictionError(RuntimeError):
    """
    Errore applicativo sollevato quando non è possibile
    completare una predizione.
    """

class ModelLoadError(RuntimeError):
    """
    Errore applicativo sollevato quando il modello
    non può essere caricato correttamente.
    """

@lru_cache(maxsize=1)
def load_model() -> Any:
    """
    Carica il modello di Sentiment Analysis dal file pickle.

    Il modello viene caricato una sola volta e successivamente
    recuperato dalla cache.
    """
    try:
        with MODEL_PATH.open("rb") as file:
            return pickle.load(file)

    except Exception as exc:
        raise ModelLoadError(
            "Impossibile caricare il modello di Sentiment Analysis"
        ) from exc


def predict_sentiment(
    review: str,
    sentiment_model: Any | None = None
) -> tuple[str, float]:
    """
    Esegue la predizione del sentimento di una recensione.

    Se non viene fornito esplicitamente un modello, utilizza
    quello configurato per l'applicazione.

    Restituisce:
    - sentimento previsto;
    - confidence associata alla classe prevista.

    Solleva:
    - PredictionError se il modello non riesce a completare
      correttamente la predizione.
    """
    model = sentiment_model if sentiment_model is not None else load_model()

    try:
        prediction = str(model.predict([review])[0])
        probabilities = model.predict_proba([review])[0]

        class_index = list(model.classes_).index(prediction)
        confidence = float(probabilities[class_index])

        return prediction, confidence


    except Exception as exc:
        raise PredictionError(
            "Errore durante l'esecuzione della predizione"
        ) from exc