# logger_config.py
import logging
import sys
import os
from datetime import datetime

def setup_logging():
    log_format = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    os.makedirs("logs", exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        force=True,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f"logs/rag_{datetime.now().strftime('%Y%m%d')}.log", encoding="utf-8"),
        ],
    )

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("qdrant_client").setLevel(logging.WARNING)
