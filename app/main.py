from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routes import router as api_router
from .ui_routes import router as ui_router

app = FastAPI(title="Fraud Detection API")
app.include_router(api_router, prefix="/v1")
app.include_router(ui_router)
app.mount("/static", StaticFiles(directory="static"), name="static")
