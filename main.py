from fastapi import FastAPI

from config import APP_DESCRIPTION, APP_NAME, APP_VERSION
from middleware import register_middlewares
from routers.prediction import router as prediction_router
from routers.system import router as system_router


app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION
)

register_middlewares(app)

app.include_router(system_router)
app.include_router(prediction_router)