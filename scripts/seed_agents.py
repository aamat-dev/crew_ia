import asyncio
import json
from pathlib import Path
import sys
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import select

from backend.api.fastapi_app.models.agent import AgentTemplate, AgentModelsMatrix
from backend.api.fastapi_app.deps import get_sessionmaker


def _load_data(path: str) -> list[dict[str, Any]]:
    """Charge un fichier JSON ou YAML en liste de dicts.

    - JSON: extension .json
    - YAML: extensions .yaml/.yml (si PyYAML dispo)
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    suffix = p.suffix.lower()
    if suffix == ".json":
        return json.load(open(p, "r", encoding="utf-8"))
    if suffix in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore
        except Exception as e:  # pragma: no cover — dépendance optionnelle
            raise RuntimeError("PyYAML requis pour charger des seeds YAML") from e
        return yaml.safe_load(open(p, "r", encoding="utf-8")) or []
    raise ValueError(f"Format non supporté: {suffix}")


async def seed_templates(path: str = "seeds/agent_templates.json") -> None:
    SessionLocal = get_sessionmaker()
    async with SessionLocal() as s:
        data = _load_data(path)
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
        data = _load_data(path)
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
