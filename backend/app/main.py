from fastapi import FastAPI

# Ensure NLTK data is present before importing modules that rely on it
from .utils.nltk_download import ensure_nltk_stopwords
ensure_nltk_stopwords()

from . import models
from .database import engine
from .routes import router as api_router


# Create DB tables if missing
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="HireSight Backend")
app.include_router(api_router, prefix="/api")


@app.get("/healthz")
def health():
    return {"status": "ok"}
