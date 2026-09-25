import time

from fastapi import FastAPI, Request

from metrics import HTTP_REQUEST_DURATION


def register_middlewares(app: FastAPI) -> None:

    @app.middleware("http")
    async def collect_request_metrics(request: Request, call_next):
        """
        Misura il tempo impiegato da ogni richiesta HTTP.

        La durata viene registrata anche nel caso in cui
        l'elaborazione generi un'eccezione non gestita.
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