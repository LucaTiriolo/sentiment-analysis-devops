import time
import logging


from fastapi import FastAPI, HTTPException, Request
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field, field_validator
from starlette.responses import Response
from typing import Literal

from metrics import (
    HTTP_REQUEST_DURATION,
    PREDICTION_ERRORS,
    PREDICTIONS_TOTAL,
)
from model_service import (
    ModelLoadError,
    PredictionError,
    load_model,
    predict_sentiment,
)

logger = logging.getLogger(__name__)
app = FastAPI(
    title="Sentiment Analysis DevOps",
    description="API per il deploy e il monitoraggio di un modello di Sentiment Analysis",
    version="1.0.0"
)


class PredictionRequest(BaseModel):
    review: str = Field(
        ...,
        min_length=1,
        max_length=5000
    )

    @field_validator("review")
    @classmethod
    def validate_review(cls, value: str) -> str:
        """
        Impedisce l'invio di recensioni contenenti esclusivamente spazi.
        """
        value = value.strip()

        if not value:
            raise ValueError("La recensione non può essere vuota")

        return value


class PredictionResponse(BaseModel):
    sentiment: Literal["negative", "neutral", "positive"]
    confidence: float = Field(..., ge=0.0, le=1.0)


@app.middleware("http")
async def collect_request_metrics(request: Request, call_next):
    """
    Misura il tempo impiegato da ogni richiesta HTTP.

    La durata viene registrata anche nel caso in cui
    l'elaborazione della richiesta generi un'eccezione
    non gestita.
    """
    start_time = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code

        return response

    finally:
        duration = time.perf_counter() - start_time

        HTTP_REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=status_code
        ).observe(duration)


@app.get("/")
def application_info():
    """
    Restituisce le informazioni principali del servizio.
    """
    return {
        "service": "Sentiment Analysis API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health_check():
    """
    Verifica che l'API sia attiva e che il modello
    di Sentiment Analysis sia disponibile.
    """
    try:
        load_model()

        return {
            "status": "ok",
            "model": "loaded"
        }

    except ModelLoadError as exc:
        logger.exception(
            "Il modello di Sentiment Analysis non è disponibile"
        )

        raise HTTPException(
            status_code=503,
            detail="Modello non disponibile"
        ) from exc


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    try:
        sentiment, confidence = predict_sentiment(request.review)

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

@app.get("/metrics")
def metrics():
    """
    Espone le metriche nel formato richiesto da Prometheus.
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )