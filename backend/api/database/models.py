"""Re-export database models for the API tests."""

from sqlmodel import SQLModel

from core.storage.db_models import Artifact, Event, Node, Run, Feedback, AuditLog, AuditSource
from backend.core.models import Task, Plan, PlanReview, Assignment
from backend.api.fastapi_app.models.agent import Agent, AgentTemplate, AgentModelsMatrix

# Les tests s’attendent à un objet ayant un attribut `metadata`.
Base = SQLModel

__all__ = [
    "Base",
    "Run",
    "Node",
    "Artifact",
    "Event",
    "Feedback",
    "AuditLog",
    "AuditSource",
    "Task",
    "Plan",
    "Assignment",
    "PlanReview",
    "Agent",
    "AgentTemplate",
    "AgentModelsMatrix",
]
