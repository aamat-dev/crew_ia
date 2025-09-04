from sqlmodel import SQLModel

# Import des modèles pour qu'ils soient enregistrés auprès de SQLModel
# Import minimal models so SQLModel.metadata is populated
from backend.core.models import Plan  # noqa: F401
from backend.core.models import Task  # noqa: F401
from backend.api.fastapi_app.models.agent import Agent, AgentTemplate, AgentModelsMatrix  # noqa: F401

Base = SQLModel
