from sqlmodel import SQLModel

# Import des modèles pour qu'ils soient enregistrés auprès de SQLModel
# Import minimal models so SQLModel.metadata is populated
from app.models.plan import Plan  # noqa: F401
from app.models.task import Task  # noqa: F401
from api.fastapi_app.models.agent import Agent, AgentTemplate, AgentModelsMatrix  # noqa: F401

Base = SQLModel
