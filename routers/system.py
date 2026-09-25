import logging

from fastapi import APIRouter, HTTPException
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from config import APP_VERSION, SERVICE_NAME
from model_service import ModelLoadError, load_model


logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
def application_info():
    """
    Restituisce le informazioni principali del servizio.
    """
    return {
        "service": SERVICE_NAME,
        "version": APP_VERSION,
        "status": "running"
    }


@router.get("/health")
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


@router.get("/metrics")
def metrics():
    """
    Espone le metriche nel formato richiesto da Prometheus.
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )