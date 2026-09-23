from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator

from model_service import predict_sentiment


app = FastAPI(
    title="Sentiment Analysis DevOps",
    description="API per il deploy e il monitoraggio di un modello di Sentiment Analysis",
    version="0.2.0"
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


@app.get("/")
def hello_world():
    return {"message": "Hello World"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    sentiment, confidence = predict_sentiment(request.review)

    return PredictionResponse(
        sentiment=sentiment,
        confidence=confidence
    )