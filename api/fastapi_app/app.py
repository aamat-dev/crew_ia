# api/fastapi_app/app.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from anyio import create_task_group

# Charger .env le plus tôt possible
from dotenv import load_dotenv
load_dotenv()

from .deps import settings
from .routes import health, runs, nodes, artifacts, events, tasks
from .middleware import RequestIDMiddleware
import os
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with create_task_group() as tg:
        pg = PostgresAdapter(settings.database_url)
        file = FileAdapter(settings.artifacts_dir)
        order_env = os.getenv("STORAGE_ORDER")
        order = [x.strip() for x in order_env.split(",") if x.strip()] if order_env else None
        storage = CompositeAdapter([file, pg], order=order)
        app.state.task_group = tg
        app.state.storage = storage
        app.state.event_publisher = EventPublisher(storage)
        yield
        # task group exits cancelling background tasks


app = FastAPI(
    title="Crew Orchestrator – Read-only API",
    version="0.1.0",
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
)

# -------- Middlewares --------
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
app.include_router(artifacts.router_nodes)
app.include_router(artifacts.router_artifacts)
app.include_router(events.router)
app.include_router(tasks.router)

# Redirection vers Swagger
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")
