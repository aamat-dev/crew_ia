from sqlmodel import SQLModel

# Import des modèles pour qu'ils soient enregistrés auprès de SQLModel
from app.models import Assignment, Plan, Task  # noqa: F401

Base = SQLModel
