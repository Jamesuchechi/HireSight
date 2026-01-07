import logging

logger = logging.getLogger(__name__)


def ensure_spacy_model(model_name: str = "en_core_web_sm"):
    """Make sure the requested spaCy model is available locally."""
    try:
        import spacy
    except ImportError:
        logger.warning("spaCy is not installed; skipping model check.")
        return

    try:
        spacy.load(model_name)
        logger.info("spaCy model %s already installed", model_name)
        return
    except OSError:
        logger.info("spaCy model %s missing; downloading...", model_name)
        try:
            from spacy.cli import download as spacy_download

            spacy_download(model_name)
            spacy.load(model_name)
            logger.info("spaCy model %s downloaded and ready", model_name)
        except Exception as exc:
            logger.warning("Failed to download spaCy model %s: %s", model_name, exc)
