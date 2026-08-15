import json
import logging
import os
import socket
import time

from fastapi import FastAPI, HTTPException, Request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
                "level": record.levelname,
                "message": record.getMessage(),
                "service": "backend",
            }
        )


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger = logging.getLogger("challenge")
logger.handlers = [handler]
logger.setLevel(logging.INFO)
logger.propagate = False

REQUESTS = Counter(
    "challenge_http_requests_total",
    "HTTP requests handled by the backend",
    ["method", "path", "status"],
)
LATENCY = Histogram(
    "challenge_http_request_duration_seconds",
    "Backend request duration",
    ["method", "path"],
)

app = FastAPI(title="Kubernetes Infrastructure Challenge", version="1.0.0")


@app.middleware("http")
async def observe_requests(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - started
    path = request.url.path
    REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    LATENCY.labels(request.method, path).observe(elapsed)
    logger.info(
        "%s %s status=%s duration_ms=%.2f",
        request.method,
        path,
        response.status_code,
        elapsed * 1000,
    )
    return response


@app.get("/api/info")
def info():
    return {
        "message": os.getenv("APP_MESSAGE", "Hello from Kubernetes"),
        "backend": "python-fastapi",
        "pod": socket.gethostname(),
    }


@app.get("/healthz")
def health():
    return {"status": "healthy"}


@app.get("/readyz")
def ready():
    if not os.getenv("APP_TOKEN"):
        raise HTTPException(status_code=503, detail="APP_TOKEN is not configured")
    return {"status": "ready"}


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
