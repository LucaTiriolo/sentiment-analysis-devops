FROM python:3.14-slim

WORKDIR /app

# Copiamo prima le dipendenze per sfruttare la cache Docker.
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copiamo il codice applicativo.
COPY main.py .
COPY model_service.py .

# Copiamo il modello di Sentiment Analysis.
COPY model ./model

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]