from __future__ import annotations

from fastapi import FastAPI, Depends

# Configuration du logger structuré dès le démarrage de l'application
import core.log  # noqa: F401
from fastapi.responses import RedirectResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging
from uuid import UUID
from anyio import create_task_group
import os

# Charger .env le plus tôt possible (sauf si CONFIG_SKIP_DOTENV=1)
from dotenv import load_dotenv
if os.getenv("CONFIG_SKIP_DOTENV", "").strip().lower() not in {"1", "true", "yes", "on"}:
    load_dotenv()

import core.log  # configure root logger

from .deps import settings, strict_api_key_auth
from .routes import (
    health,
    runs,
    nodes,
    artifacts,
    events,
    tasks,
    agents,
    feedbacks,
    node_actions,
    plans,
)
from .routes.qa_report import router as qa_router
from .middleware.request_id import RequestIdMiddleware
from .middleware.access import AccessLogMiddleware
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
    {"name": "agents", "description": "Gestion des agents, recrutement et matrice modèles."},
    {
        "name": "feedbacks",
        "description": "Gestion des feedbacks auto ou humains: création et listing par nœud ou run.",
    },
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
            # N'active l'adaptateur PG que si l'URL cible bien PostgreSQL
            try:
                from sqlalchemy.engine import make_url
                if make_url(settings.database_url).get_backend_name() == "postgresql":
                    adapters.append(PostgresAdapter(settings.database_url))
                else:
                    # ignore silencieusement en env de test (ex: sqlite)
                    pass
            except Exception:
                # En cas d'URL invalide, on ignore pour ne pas bloquer le démarrage
                pass
        elif item:
            raise RuntimeError(f"Unknown adapter in STORAGE_ORDER: {item}")
    if not adapters:
        # filet de sécurité
        adapters.append(FileAdapter(base_dir=runs_root))
    return CompositeAdapter(adapters)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configure 'api.access' logger so it's capturable by tests and present in prod
    try:
        lg = logging.getLogger("api.access")
        if not lg.handlers:
            # Attach a simple stream handler once; caplog will still intercept
            handler = logging.StreamHandler()
            lg.addHandler(handler)
        lg.setLevel(logging.INFO)
        lg.propagate = True
        lg.disabled = False
    except Exception:
        pass
    async with create_task_group() as tg:
        storage = _build_storage()
        def _safe_uuid(val: str):
            try:
                return UUID(val)
            except Exception:
                return None
        storage.set_resolvers(run_resolver=_safe_uuid, node_resolver=_safe_uuid)
        app.state.task_group = tg
        app.state.storage = storage
        app.state.event_publisher = EventPublisher(storage)
        app.state.rate_limits = {}
        # --- application running ---
        yield
        # Désactive l'édition d'événements pendant l'extinction pour éviter
        # les écritures concurrentes pendant le teardown des tests.
        try:
            app.state.event_publisher.disabled = True
            app.state.shutting_down = True
        except Exception:
            pass
        # task group exits cancelling background tasks

app = FastAPI(
    title="Crew Orchestrator – Read-only API",
    version="0.1.0",
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
)

# -------- Middlewares --------
app.add_middleware(RequestIdMiddleware)                # X-Request-ID propagation
app.add_middleware(AccessLogMiddleware)                # access logs
if init_sentry():
    app.add_middleware(SentryContextMiddleware)        # Sentry annotations
app.add_middleware(MetricsMiddleware)                  # Prometheus metrics
app.add_middleware(GZipMiddleware, minimum_size=1024)  # gzip

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Link", "X-Total-Count"],
)

# -------- Routes --------
# Auth: toutes les routes sensibles exigent une clé API, /health reste public
protected = [Depends(strict_api_key_auth)]
app.include_router(health.router)
app.include_router(runs.router, dependencies=protected)
app.include_router(nodes.router, dependencies=protected)
app.include_router(artifacts.router_nodes, dependencies=protected)
app.include_router(artifacts.router_artifacts, dependencies=protected)
app.include_router(events.router, dependencies=protected)
app.include_router(tasks.router, dependencies=protected)
app.include_router(node_actions.router, dependencies=protected)
app.include_router(plans.router, dependencies=protected)
app.include_router(agents.router, dependencies=protected)
app.include_router(feedbacks.router, dependencies=protected)
app.include_router(qa_router, dependencies=protected)

# Redirection vers Swagger
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")
