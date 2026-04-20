import warnings
import os
import sys
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.rag_controller import router as rag_router
import time
import logging
from fastapi import Request
import uvicorn

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

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*XMLParsedAsHTMLWarning.*")
warnings.filterwarnings("ignore", message=".*resume_download.*")
warnings.filterwarnings("ignore", message=".*shadows an attribute.*")

request_logger = logging.getLogger("request")

app = FastAPI(
    title="RAG API",
    description="Retrieval-Augmented Generation API",
    version="2.0.0",
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    request_logger.info("→ %s %s", request.method, request.url.path)
    response = await call_next(request)
    duration = (time.perf_counter() - start) * 1000
    request_logger.info(
        "← %s %s | status=%d | total=%.1fms",
        request.method, request.url.path, response.status_code, duration
    )
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rag_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)



