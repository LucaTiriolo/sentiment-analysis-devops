from prometheus_client import Counter, Histogram


# Tempo impiegato dall'API per elaborare le richieste HTTP.
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Tempo di risposta delle richieste HTTP",
    ["method", "endpoint", "status_code"]
)


# Numero totale di errori avvenuti durante una predizione.
PREDICTION_ERRORS = Counter(
    "prediction_errors_total",
    "Numero totale di errori durante le predizioni"
)


# Numero totale di predizioni effettuate.
PREDICTIONS_TOTAL = Counter(
    "predictions_total",
    "Numero totale di predizioni effettuate",
    ["sentiment"]
)