# api/fastapi_app/app.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# Charger .env le plus tôt possible
from dotenv import load_dotenv
load_dotenv()

from .deps import settings
from .routes import health, runs, nodes, artifacts, events, tasks
from .middleware import RequestIDMiddleware

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
