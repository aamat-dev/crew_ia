# api/fastapi_app/app.py
from __future__ import annotations

from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from uuid import UUID
from anyio import create_task_group
import os

# Charger .env le plus tôt possible
from dotenv import load_dotenv
load_dotenv()

from .deps import settings, api_key_auth
from .routes import health, runs, nodes, artifacts, events, tasks
from .middleware import RequestIDMiddleware
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
app.add_middleware(GZipMiddleware, minimum_size=1024) # gzip

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
app.include_router(artifacts.router_nodes)
app.include_router(artifacts.router_artifacts)
app.include_router(events.router)
app.include_router(tasks.router, dependencies=[Depends(api_key_auth)])

# Redirection vers Swagger
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")
