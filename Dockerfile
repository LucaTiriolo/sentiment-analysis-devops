FROM python:3.14-slim

WORKDIR /app

# Copiamo prima le dipendenze per sfruttare la cache dei layer Docker.
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copiamo il codice dell'applicazione.
COPY main.py .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]