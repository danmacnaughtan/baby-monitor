import logging.config
import os
from pathlib import Path


DATA_PATH = Path("data")

DATA_PATH.mkdir(parents=True, exist_ok=True)

USERS_FILE = DATA_PATH / "users.json"

SESSIONS_FILE = DATA_PATH / "sessions.json"

ACCESS_TOKENS_FILE = DATA_PATH / "access_tokens.json"

DEFAULT_SESSION_LENGTH = 7  # days

CERT_PEM_FILE = os.environ.get("CERT_PEM_FILE")
CERT_KEY_FILE = os.environ.get("CERT_KEY_FILE")

LOGGING_CONF = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "class": "logging.Formatter",
            "format": "%(asctime)s %(name)s %(levelname)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "server.log",
            "formatter": "default",
        },
    },
    "root": {"handlers": ["console", "file"], "level": "INFO"},
}

logging.config.dictConfig(LOGGING_CONF)
