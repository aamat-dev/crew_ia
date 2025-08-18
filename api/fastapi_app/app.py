# api/fastapi_app/app.py
from __future__ import annotations
import os
import time
import uuid
import logging
import json

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Charger .env le plus tôt possible
from dotenv import load_dotenv
load_dotenv()

from .deps import settings
from .routes import health, runs, nodes, artifacts, events, tasks

TAGS_METADATA = [
    {"name": "health", "description": "Healthcheck et disponibilité DB."},
    {"name": "runs", "description": "Lecture des exécutions (runs) et résumé agrégé."},
    {"name": "nodes", "description": "Lecture des nœuds d'un run (DAG)."},
    {"name": "artifacts", "description": "Lecture des artifacts produits par les nœuds."},
    {"name": "events", "description": "Lecture des événements/logs d'un run."},
    {"name": "tasks", "description": "Déclenchement d’un run ad-hoc et suivi de statut."},
]

app = FastAPI(
    title="Crew Orchestrator – Read-only API",
    version="0.1.0",
    openapi_tags=TAGS_METADATA,
)

# -------- Middlewares --------
logger = logging.getLogger("api.requests") 

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = time.perf_counter()
        response = await call_next(request)
        dur_ms = int((time.perf_counter() - start) * 1000)
        response.headers["X-Request-ID"] = rid
        logger.info(json.dumps({
            "request_id": rid,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": dur_ms,
        }))
        return response

# Garde l’ID de requête le plus tôt possible
app.add_middleware(RequestIDMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1024)

# CORS (une seule source de vérité : settings.cors_origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# -------- Routes --------

app.include_router(health.router)
app.include_router(runs.router)
app.include_router(nodes.router)
app.include_router(artifacts.router)
app.include_router(events.router)
app.include_router(tasks.router)

# Redirection vers Swagger
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")
