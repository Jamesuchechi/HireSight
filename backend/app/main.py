from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Make sure NLP dependencies can run
from .utils.nltk_download import ensure_nltk_stopwords
from .utils.spacy_download import ensure_spacy_model

ensure_nltk_stopwords()
ensure_spacy_model()

from . import models
from .config import settings
from .database import engine
from .routes import router as api_router


# Create DB tables if missing
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="HireSight Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api")


@app.get("/healthz")
def health():
    return {"status": "ok"}
