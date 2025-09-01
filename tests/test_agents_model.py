import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from api.fastapi_app.models.agent import Agent


@pytest.mark.asyncio
async def test_create_read_agent(db_session):
    agent = Agent(
        name="manager-frontend-general",
        role="manager",
        domain="frontend",
        default_model="openai:gpt-4o-mini",
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)

    stmt = select(Agent).where(Agent.id == agent.id)
    res = await db_session.execute(stmt)
    fetched = res.scalar_one()
    assert fetched.name == "manager-frontend-general"
    assert fetched.role == "manager"
    assert fetched.domain == "frontend"


@pytest.mark.asyncio
async def test_unique_agent_name(db_session):
    a1 = Agent(name="dup", role="manager", domain="frontend")
    a2 = Agent(name="dup", role="manager", domain="backend")
    db_session.add(a1)
    await db_session.commit()
    db_session.add(a2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
