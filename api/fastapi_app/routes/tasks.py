from __future__ import annotations

import asyncio
import datetime as dt
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import get_session, api_key_auth, make_session_factory
from core.storage.db_models import Run

router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(api_key_auth)])


# --------- Schemas ---------
class TaskCreateIn(BaseModel):
    title: str = Field(..., min_length=1)
    params: dict[str, Any] = Field(default_factory=dict)


class TaskAcceptedOut(BaseModel):
    run_id: uuid.UUID
    status: str = "accepted"


class TaskStatusOut(BaseModel):
    run_id: uuid.UUID
    title: str | None = None
    status: str
    started_at: dt.datetime | None = None
    ended_at: dt.datetime | None = None


# --------- Orchestration (wrapper minimal) ---------
async def _run_orchestration(run_id: uuid.UUID, params: dict[str, Any]) -> None:
    """
    Tâche de fond : passe le run en 'running', exécute, puis 'completed' ou 'failed'.
    Ici on met un squelette : branche ton orchestrateur réel à l'endroit indiqué.
    """
    Session = make_session_factory()
    async with Session() as s:  # type: AsyncSession
        try:
            # <<< BRANCHEMENT ORCHESTRATEUR >>>
            # Exemple : await orchestrator.run(run_id=run_id, params=params)
            # Pour l’instant, on simule un petit temps de traitement :
            await asyncio.sleep(0.2)

            # -> completed
            await s.execute(
                update(Run)
                .where(Run.id == run_id)
                .values(status="completed", ended_at=dt.datetime.now(dt.timezone.utc))
            )
            await s.commit()
        except Exception:
            # -> failed
            await s.execute(
                update(Run)
                .where(Run.id == run_id)
                .values(status="failed", ended_at=dt.datetime.now(dt.timezone.utc))
            )
            await s.commit()


# --------- Routes ---------
@router.post("", response_model=TaskAcceptedOut, status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(api_key_auth)])
async def create_task(payload: TaskCreateIn, session: AsyncSession = Depends(get_session)) -> TaskAcceptedOut:
    """
    Crée un Run en DB (status=queued) puis lance l'orchestration en tâche de fond.
    """
    run_id = uuid.uuid4()
    now = dt.datetime.now(dt.timezone.utc)
    session.add(Run(id=run_id, title=payload.title, status="running", started_at=now, ended_at=None))
    await session.commit()

    # Lancer la tâche de fond (hors cycle requête)
    asyncio.create_task(_run_orchestration(run_id, payload.params))

    return TaskAcceptedOut(run_id=run_id)


@router.get("/{run_id}", response_model=TaskStatusOut, dependencies=[Depends(api_key_auth)])
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
