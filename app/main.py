from fastapi import FastAPI

from .routes import router as api_router

app = FastAPI(title="Fraud Detection API")
app.include_router(api_router, prefix="/v1")

