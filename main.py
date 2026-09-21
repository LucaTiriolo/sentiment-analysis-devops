from fastapi import FastAPI

# Istanza principale dell'applicazione FastAPI.
app = FastAPI(
    title="Sentiment Analysis DevOps",
    description="API per il deploy e il monitoraggio di un modello di Sentiment Analysis",
    version="0.1.0"
)


@app.get("/")
def hello_world():
    """Endpoint di prova dell'applicazione."""
    return {"message": "Hello World"}


@app.get("/health")
def health_check():
    """
    Endpoint utilizzato per verificare che l'applicazione sia attiva.

    In seguito verrà utilizzato anche dalla pipeline di deploy
    per controllare che il container sia partito correttamente.
    """
    return {"status": "ok"}