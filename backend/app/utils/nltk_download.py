import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def ensure_nltk_stopwords():
    """Ensure NLTK 'stopwords' corpus is available locally.

    Downloads to a project-local `nltk_data` directory if missing.
    """
    try:
        import nltk
    except Exception:
        logger.warning("nltk not installed; skipping stopwords check")
        return

    data_dir = Path(__file__).resolve().parents[2] / "nltk_data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Ensure NLTK looks in our local directory first
    os.environ.setdefault("NLTK_DATA", str(data_dir))

    try:
        nltk.data.find("corpora/stopwords")
        logger.info("NLTK stopwords corpus found")
    except LookupError:
        logger.info("NLTK stopwords not found; downloading to %s", data_dir)
        nltk.download("stopwords", download_dir=str(data_dir), quiet=True)
        logger.info("NLTK stopwords download complete")
