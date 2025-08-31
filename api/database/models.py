"""Re-export database models for the API tests with limited metadata."""

from sqlalchemy import MetaData
from sqlmodel import SQLModel

from core.storage.db_models import Artifact, Event, Node, Run
from app.models.task import Task
from app.models.plan import Plan
from app.models.assignment import Assignment

# Limiter le schéma aux tables nécessaires pour les tests
_metadata = MetaData()
for tbl in [
    Run.__table__,
    Node.__table__,
    Artifact.__table__,
    Event.__table__,
    Task.__table__,
    Plan.__table__,
    Assignment.__table__,
]:
    tbl.tometadata(_metadata)

class Base:  # pragma: no cover - simple conteneur
    metadata = _metadata

__all__ = [
    "Base",
    "Run",
    "Node",
    "Artifact",
    "Event",
    "Task",
    "Plan",
    "Assignment",
]
