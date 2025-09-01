"""Re-export database models for the API tests.

The core application stores its SQLModel models in
``core.storage.db_models``.  The API tests expect them to be available
under ``api.database.models`` so we re-export them here.
"""

from sqlmodel import SQLModel

from core.storage.db_models import Artifact, Event, Node, Run
from app.models.task import Task
from app.models.plan import Plan
from app.models.assignment import Assignment

# FastAPI tests expect a ``Base`` object with a ``metadata`` attribute
# similar to the SQLAlchemy declarative base. ``SQLModel`` already
# exposes the metadata via ``SQLModel.metadata`` so we simply alias it.
Base = SQLModel

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
