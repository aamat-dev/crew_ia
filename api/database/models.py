"""Re-export database models for the API tests."""

from sqlmodel import SQLModel

from core.storage.db_models import Artifact, Event, Node, Run
from app.models.task import Task
from app.models.plan import Plan
from app.models.plan_review import PlanReview
from app.models.assignment import Assignment
from api.fastapi_app.models.agent import Agent, AgentTemplate, AgentModelsMatrix

# Les tests s’attendent à un objet ayant un attribut `metadata`.
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
    "PlanReview",
    "Agent",
    "AgentTemplate",
    "AgentModelsMatrix",
]
