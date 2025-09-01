# api/fastapi_app/app.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import RedirectResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from uuid import UUID
from anyio import create_task_group
import os

# Charger .env le plus tôt possible
from dotenv import load_dotenv
load_dotenv()

import core.log  # configure root logger

from .deps import settings
from .routes import health, runs, nodes, artifacts, events, tasks
from app.routers import nodes as node_actions
from app.routers import plans as plan_routes
from .middleware import RequestIDMiddleware
from .middleware.metrics import MetricsMiddleware
from .observability import (
    metrics_enabled,
    generate_latest,
    init_sentry,
    SentryContextMiddleware,
)
from core.storage.postgres_adapter import PostgresAdapter
from core.storage.file_adapter import FileAdapter
from core.storage.composite_adapter import CompositeAdapter
from core.events.publisher import EventPublisher

TAGS_METADATA = [
    {"name": "health", "description": "Healthcheck et disponibilité DB."},
    {"name": "runs", "description": "Lecture des exécutions (runs) et résumé agrégé."},
    {"name": "nodes", "description": "Lecture des nœuds d'un run (DAG)."},
    {"name": "artifacts", "description": "Lecture des artifacts produits par les nœuds."},
    {"name": "events", "description": "Lecture des événements/logs d'un run."},
    {"name": "tasks", "description": "Déclenchement d’un run ad-hoc et suivi de statut."},
]

def _build_storage():
    # Ordre: env STORAGE_ORDER="file,pg" (défaut) | "pg,file" | "file" | "pg"
    order = (os.getenv("STORAGE_ORDER") or "file,pg").replace(" ", "")
    runs_root = os.getenv("RUNS_ROOT") or ".runs"

    adapters = []
    for item in order.split(","):
        if item == "file":
            adapters.append(FileAdapter(base_dir=runs_root))
        elif item == "pg":
            adapters.append(PostgresAdapter(settings.database_url))
        elif item:
            raise RuntimeError(f"Unknown adapter in STORAGE_ORDER: {item}")
    if not adapters:
        # filet de sécurité
        adapters.append(FileAdapter(base_dir=runs_root))
    return CompositeAdapter(adapters)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with create_task_group() as tg:
        storage = _build_storage()
        storage.set_resolvers(run_resolver=lambda x: UUID(x), node_resolver=lambda x: UUID(x))
        app.state.task_group = tg
        app.state.storage = storage
        app.state.event_publisher = EventPublisher(storage)
        app.state.rate_limits = {}
        yield
        # task group exits cancelling background tasks

app = FastAPI(
    title="Crew Orchestrator – Read-only API",
    version="0.1.0",
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
)

# -------- Middlewares --------
app.add_middleware(RequestIDMiddleware)                # X-Request-ID propagation
if init_sentry():
    app.add_middleware(SentryContextMiddleware)        # Sentry annotations
app.add_middleware(MetricsMiddleware)                  # Prometheus metrics
app.add_middleware(GZipMiddleware, minimum_size=1024) # gzip

if metrics_enabled():
    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        payload = generate_latest()
        return Response(
            content=payload,
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

# CORS
# Origines autorisées via variable d'env ALLOWED_ORIGINS (CSV)
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
CORS_ALLOW_METHODS = ["GET", "POST", "PATCH", "OPTIONS"]
CORS_ALLOW_HEADERS = ["Content-Type", "Authorization", "X-API-Key", "X-Request-ID"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

# -------- Routes --------
# Auth: all routes require API key except /health
app.include_router(health.router)
app.include_router(runs.router)
app.include_router(nodes.router)
app.include_router(artifacts.router_nodes)
app.include_router(artifacts.router_artifacts)
app.include_router(events.router)
app.include_router(tasks.router)
app.include_router(node_actions.router)
app.include_router(plan_routes.router)

# Redirection vers Swagger
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")
