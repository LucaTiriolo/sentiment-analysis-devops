import time

from fastapi import FastAPI, HTTPException, Request
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field, field_validator
from starlette.responses import Response

from metrics import (
    HTTP_REQUEST_DURATION,
    PREDICTION_ERRORS,
    PREDICTIONS_TOTAL,
)
from model_service import predict_sentiment


app = FastAPI(
    title="Sentiment Analysis DevOps",
    description="API per il deploy e il monitoraggio di un modello di Sentiment Analysis",
    version="0.3.0"
)


class PredictionRequest(BaseModel):
    review: str = Field(..., min_length=1)

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
    sentiment: str
    confidence: float


@app.middleware("http")
async def collect_request_metrics(request: Request, call_next):
    """
    Misura il tempo impiegato da ogni richiesta HTTP.
    """
    start_time = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start_time

    HTTP_REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).observe(duration)

    return response


@app.get("/")
def hello_world():
    return {"message": "Hello World"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


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

    except Exception as exc:
        PREDICTION_ERRORS.inc()

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