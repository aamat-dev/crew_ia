from __future__ import annotations

import asyncio
import datetime as dt
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from ..deps import get_session, require_auth
from core.storage.db_models import Run, Node, Event, Artifact

router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(require_auth)])


# --------- Schemas ---------
class TaskCreateIn(BaseModel):
    title: str = Field(..., min_length=1, examples=["Adhoc run"])
    params: dict[str, Any] = Field(default_factory=dict, examples=[{"foo": "bar"}])

    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {"title": "Adhoc run", "params": {"foo": "bar"}}
        ]
    })


class TaskAcceptedOut(BaseModel):
    run_id: uuid.UUID
    status: str = "accepted"

    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {"run_id": "9a5a0d83-90b6-4d2a-81d5-9a3d3f99a7f3", "status": "accepted"}
        ]
    })


class TaskStatusOut(BaseModel):
    run_id: uuid.UUID
    title: str | None = None
    status: str
    started_at: dt.datetime | None = None
    ended_at: dt.datetime | None = None

    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "run_id": "9a5a0d83-90b6-4d2a-81d5-9a3d3f99a7f3",
                "title": "Adhoc run",
                "status": "completed",
                "started_at": "2025-08-17T12:18:41.591278Z",
                "ended_at": "2025-08-17T12:20:41.591278Z",
            }
        ]
    })


# --------- Orchestration (wrapper minimal) ---------
async def _run_orchestration(run_id: uuid.UUID, params: dict[str, Any], db_url: str) -> None:
    """Simple background orchestration used for tests."""
    engine = create_async_engine(db_url, future=True)
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as s:  # type: AsyncSession
        try:
            start = dt.datetime.now(dt.timezone.utc)
            # passe à running
            await s.execute(
                update(Run)
                .where(Run.id == run_id)
                .values(status="running", started_at=start)
            )
            await s.commit()

            # Simule un node + event + artifact
            node_id = uuid.uuid4()
            await s.execute(
                insert(Node).values(
                    {
                        "id": node_id,
                        "run_id": run_id,
                        "key": "n1",
                        "title": "auto",
                        "status": "completed",
                        "created_at": start,
                        "updated_at": start,
                        "checksum": None,
                    }
                )
            )
            await s.execute(
                insert(Event).values(
                    {
                        "id": uuid.uuid4(),
                        "run_id": run_id,
                        "node_id": node_id,
                        "level": "INFO",
                        "message": "run",
                        "timestamp": start,
                    }
                )
            )
            await s.execute(
                insert(Artifact).values(
                    {
                        "id": uuid.uuid4(),
                        "node_id": node_id,
                        "type": "result",
                        "path": None,
                        "content": "ok",
                        "summary": "ok",
                        "created_at": start,
                    }
                )
            )
            await s.commit()

            # completed
            await s.execute(
                update(Run)
                .where(Run.id == run_id)
                .values(status="completed", ended_at=dt.datetime.now(dt.timezone.utc))
            )
            await s.commit()
        except Exception:
            await s.execute(
                update(Run)
                .where(Run.id == run_id)
                .values(status="failed", ended_at=dt.datetime.now(dt.timezone.utc))
            )
            await s.commit()


# --------- Routes ---------
@router.post("", response_model=TaskAcceptedOut, status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(require_auth)])
async def create_task(payload: TaskCreateIn, session: AsyncSession = Depends(get_session)) -> TaskAcceptedOut:
    """
    Crée un Run en DB (status=pending) puis lance l'orchestration en tâche de fond.
    """
    run_id = uuid.uuid4()
    session.add(
        Run(
            id=run_id,
            title=payload.title,
            status="pending",
            started_at=None,
            ended_at=None,
        )
    )
    await session.commit()

    # Lancer la tâche de fond (hors cycle requête)
    bind = session.get_bind()
    db_url = str(bind.url)
    asyncio.create_task(_run_orchestration(run_id, payload.params, db_url))

    return TaskAcceptedOut(run_id=run_id)


@router.get("/{run_id}", response_model=TaskStatusOut, dependencies=[Depends(require_auth)])
async def get_task(run_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> TaskStatusOut:
    """
    Retourne l'état courant du Run.
    """
    res = await session.execute(select(Run).where(Run.id == run_id))
    run: Run | None = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return TaskStatusOut(
        run_id=run.id,
        title=run.title,
        status=run.status,
        started_at=run.started_at,
        ended_at=run.ended_at,
    )
