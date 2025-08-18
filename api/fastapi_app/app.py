from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse

from .deps import settings
from .routes import health, runs, nodes, artifacts, events

TAGS_METADATA = [
    {"name": "health", "description": "Healthcheck et disponibilité DB."},
    {"name": "runs", "description": "Lecture des exécutions (runs) et résumé agrégé."},
    {"name": "nodes", "description": "Lecture des nœuds d'un run (DAG)."},
    {"name": "artifacts", "description": "Lecture des artifacts produits par les nœuds."},
    {"name": "events", "description": "Lecture des événements/logs d'un run."},
]

app = FastAPI(
    title="Crew Orchestrator – Read‑only API",
    version="0.1.0",
    openapi_tags=TAGS_METADATA,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"]
)

# Routes
app.include_router(health.router)
app.include_router(runs.router)
app.include_router(nodes.router)
app.include_router(artifacts.router)
app.include_router(events.router)

# Redirection vers Swagger
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")