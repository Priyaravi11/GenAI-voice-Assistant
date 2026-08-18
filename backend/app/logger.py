import logging
import os


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger for the given module.
    """
    # Silence verbose 3rd party loggers
    for verbose_logger in (
        "httpcore",
        "httpx",
        "huggingface_hub",
        "sentence_transformers",
        "urllib3",
        "pymongo",
        "google_genai",
        "google_genai.models",
    ):
        logging.getLogger(verbose_logger).setLevel(logging.WARNING)

    return logging.getLogger(name)
