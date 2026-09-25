from typing import Literal

from pydantic import BaseModel, Field, field_validator


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
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0
    )