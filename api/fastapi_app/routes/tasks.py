from __future__ import annotations

import asyncio
import datetime as dt
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import insert, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..deps import api_key_auth, get_session, get_sessionmaker
from core.storage.db_models import Run, Node, Event, Artifact

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskIn(BaseModel):
    title: str | None = None
    params: dict | None = None


class TaskAccepted(BaseModel):
    run_id: UUID
    status: str = "accepted"


@router.post(
    "",
    response_model=TaskAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(api_key_auth)],
)
async def create_task(
    payload: TaskIn,
    session: AsyncSession = Depends(get_session),
    sessionmaker: async_sessionmaker[AsyncSession] = Depends(get_sessionmaker),
) -> TaskAccepted:
    run_id = uuid4()
    title = payload.title or "Adhoc run"

    await session.execute(
        insert(Run).values(
            id=run_id,
            title=title,
            status="pending",
            started_at=None,
            ended_at=None,
        )
    )
    await session.commit()

    asyncio.create_task(_execute_run(run_id, payload.params or {}, sessionmaker))

    return TaskAccepted(run_id=run_id)


@router.get("/{run_id}", dependencies=[Depends(api_key_auth)])
async def get_task(run_id: UUID, session: AsyncSession = Depends(get_session)):
    row = await session.get(Run, run_id)
    if not row:
        return {"status": "not_found"}
    return {
        "run_id": run_id,
        "status": row.status,
        "started_at": row.started_at,
        "ended_at": row.ended_at,
    }


async def _execute_run(
    run_id: UUID, params: dict, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    async with sessionmaker() as s:
        # -> running + started_at
        await s.execute(
            update(Run)
            .where(Run.id == run_id)
            .values(status="running", started_at=dt.datetime.now(dt.timezone.utc))
        )
        await s.execute(
            insert(Event).values(
                id=uuid4(),
                run_id=run_id,
                node_id=None,
                level="INFO",
                message=f"Run started with params={params}",
                timestamp=dt.datetime.now(dt.timezone.utc),
            )
        )
        await s.commit()

        try:
            node_id = uuid4()
            await s.execute(
                insert(Node).values(
                    id=node_id,
                    run_id=run_id,
                    key="n1",
                    title="Node 1",
                    status="completed",
                    created_at=dt.datetime.now(dt.timezone.utc),
                    updated_at=dt.datetime.now(dt.timezone.utc),
                    checksum=None,
                )
            )
            await s.execute(
                insert(Artifact).values(
                    id=uuid4(),
                    node_id=node_id,
                    type="markdown",
                    path="/tmp/demo.md",
                    content="# demo\nHello",
                    summary="demo",
                    created_at=dt.datetime.now(dt.timezone.utc),
                )
            )
            await s.execute(
                insert(Event).values(
                    id=uuid4(),
                    run_id=run_id,
                    node_id=node_id,
                    level="INFO",
                    message="Node 1 done",
                    timestamp=dt.datetime.now(dt.timezone.utc),
                )
            )
            await s.execute(
                update(Run)
                .where(Run.id == run_id)
                .values(status="completed", ended_at=dt.datetime.now(dt.timezone.utc))
            )
            await s.commit()
        except Exception as e:  # pragma: no cover - simple demo
            await s.execute(
                insert(Event).values(
                    id=uuid4(),
                    run_id=run_id,
                    node_id=None,
                    level="ERROR",
                    message=f"Run failed: {e}",
                    timestamp=dt.datetime.now(dt.timezone.utc),
                )
            )
            await s.execute(
                update(Run)
                .where(Run.id == run_id)
                .values(status="failed", ended_at=dt.datetime.now(dt.timezone.utc))
            )
            await s.commit()

