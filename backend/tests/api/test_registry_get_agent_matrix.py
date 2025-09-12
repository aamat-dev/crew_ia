import uuid
import datetime as dt

import pytest
from sqlalchemy.dialects.postgresql import insert

from backend.api.fastapi_app.models.agent import AgentModelsMatrix
from core.agents.registry import get_agent_matrix


@pytest.mark.asyncio
async def test_get_agent_matrix_reads_from_db(db_session):
    now = dt.datetime.now(dt.timezone.utc)
    rows = [
        {
            "id": uuid.uuid4(),
            "role": "executor",
            "domain": "general",
            "models": {"preferred": [{"provider": "openai", "model": "gpt-4o-mini"}]},
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "role": "manager",
            "domain": "frontend",
            "models": {"fallbacks": [{"provider": "mistral", "model": "mistral-small"}]},
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
    ]
    await db_session.execute(insert(AgentModelsMatrix), rows)
    await db_session.commit()

    matrix = await get_agent_matrix(db_session)
    assert "executor:general" in matrix
    assert "manager:frontend" in matrix
    assert matrix["executor:general"]["preferred"][0]["provider"] == "openai"

