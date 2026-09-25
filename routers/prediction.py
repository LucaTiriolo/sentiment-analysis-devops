import logging

from fastapi import APIRouter, HTTPException

from metrics import PREDICTION_ERRORS, PREDICTIONS_TOTAL
from model_service import (
    ModelLoadError,
    PredictionError,
    predict_sentiment,
)
from schemas import PredictionRequest, PredictionResponse


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/predict",
    response_model=PredictionResponse
)
def predict(request: PredictionRequest):
    """
    Esegue la Sentiment Analysis della recensione ricevuta.
    """
    try:
        sentiment, confidence = predict_sentiment(
            request.review
        )

        PREDICTIONS_TOTAL.labels(
            sentiment=sentiment
        ).inc()

        return PredictionResponse(
            sentiment=sentiment,
            confidence=confidence
        )

    except ModelLoadError as exc:
        PREDICTION_ERRORS.inc()

        logger.exception(
            "Il modello di Sentiment Analysis non è disponibile"
        )

        raise HTTPException(
            status_code=503,
            detail="Modello non disponibile"
        ) from exc

    except PredictionError as exc:
        PREDICTION_ERRORS.inc()

        logger.exception(
            "Errore durante la predizione della recensione"
        )

        raise HTTPException(
            status_code=500,
            detail="Errore durante la predizione"
        ) from exc