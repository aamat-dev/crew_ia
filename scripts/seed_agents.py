import asyncio
import json
from sqlalchemy import select

from api.fastapi_app.models.agent import AgentTemplate, AgentModelsMatrix
from api.fastapi_app.deps import get_sessionmaker


async def seed_templates(path: str = "seeds/agent_templates.json") -> None:
    SessionLocal = get_sessionmaker()
    async with SessionLocal() as s:
        data = json.load(open(path, "r", encoding="utf-8"))
        for row in data:
            exists = (
                await s.execute(
                    select(AgentTemplate).where(AgentTemplate.name == row["name"])
                )
            ).scalar_one_or_none()
            if not exists:
                s.add(AgentTemplate(**row))
        await s.commit()


async def seed_matrix(path: str = "seeds/agent_models_matrix.json") -> None:
    SessionLocal = get_sessionmaker()
    async with SessionLocal() as s:
        data = json.load(open(path, "r", encoding="utf-8"))
        for row in data:
            exists = (
                await s.execute(
                    select(AgentModelsMatrix).where(
                        AgentModelsMatrix.role == row["role"],
                        AgentModelsMatrix.domain == row["domain"],
                    )
                )
            ).scalar_one_or_none()
            if not exists:
                s.add(AgentModelsMatrix(**row))
        await s.commit()


async def main() -> None:
    await seed_matrix()
    await seed_templates()


if __name__ == "__main__":
    asyncio.run(main())
