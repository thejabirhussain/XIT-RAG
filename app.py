import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*XMLParsedAsHTMLWarning.*")
warnings.filterwarnings("ignore", message=".*resume_download.*")
warnings.filterwarnings("ignore", message=".*shadows an attribute.*")

from dotenv import load_dotenv
load_dotenv()

import os
from logger_config import setup_logging
setup_logging()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from controllers.rag_controller import router as rag_router

app = FastAPI(
    title="RAG API",
    description="Retrieval-Augmented Generation API",
    version="1.0.0",
)

import time
import logging
from fastapi import Request

request_logger = logging.getLogger("request")

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



