"""Script de seed pour injecter quelques runs/nodes/feedbacks de demonstration."""

import argparse
import asyncio
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict

from sqlalchemy import delete, select

ROOT = Path(__file__).resolve().parents[1]
for extra in (ROOT, ROOT / "backend"):
    sys.path.insert(0, str(extra))

from backend.api.fastapi_app.deps import get_sessionmaker  # noqa: E402
from core.storage.db_models import (  # noqa: E402
    Artifact,
    Event,
    Feedback,
    Node,
    NodeStatus,
    Run,
    RunStatus,
)


class SeedError(Exception):
    """Exception dediee au script de seed."""


async def _purge_existing_demo_data(run_titles: list[str]) -> None:
    SessionLocal = get_sessionmaker()
    async with SessionLocal() as session:
        rows = await session.execute(select(Run).where(Run.title.in_(run_titles)))
        runs = rows.scalars().all()
        if not runs:
            return
        run_ids = [r.id for r in runs]
        node_rows = await session.execute(select(Node.id).where(Node.run_id.in_(run_ids)))
        node_ids = [row[0] for row in node_rows]

        if node_ids:
            await session.execute(delete(Feedback).where(Feedback.node_id.in_(node_ids)))
            await session.execute(delete(Artifact).where(Artifact.node_id.in_(node_ids)))
            await session.execute(delete(Event).where(Event.node_id.in_(node_ids)))
        await session.execute(delete(Event).where(Event.run_id.in_(run_ids)))
        await session.execute(delete(Node).where(Node.run_id.in_(run_ids)))
        await session.execute(delete(Feedback).where(Feedback.run_id.in_(run_ids)))
        await session.execute(delete(Run).where(Run.id.in_(run_ids)))
        await session.commit()


async def seed_demo_data(*, reset: bool = False) -> Dict[str, int]:
    SessionLocal = get_sessionmaker()
    run_titles = ["Demo run #1", "Demo run #2"]

    if reset:
        await _purge_existing_demo_data(run_titles)

    async with SessionLocal() as session:
        existing = await session.execute(select(Run.id).where(Run.title.in_(run_titles)))
        if existing.scalars().first():
            raise SeedError(
                "Des donnees de demo existent deja. Relancez avec --reset si vous souhaitez les regenerer."
            )

        now = datetime.now(timezone.utc)
        counts = {"runs": 0, "nodes": 0, "artifacts": 0, "events": 0, "feedbacks": 0}

        scenarios = [
            {
                "title": "Demo run #1",
                "status": RunStatus.completed,
                "duration": timedelta(minutes=8),
                "meta": {"seed": "demo", "use_case": "brief client"},
                "nodes": [
                    {
                        "key": "n1",
                        "title": "Analyse du besoin",
                        "status": NodeStatus.completed,
                        "role": "manager",
                        "deps": [],
                        "checksum": "demo-n1",
                    },
                    {
                        "key": "n2",
                        "title": "Plan daction",
                        "status": NodeStatus.completed,
                        "role": "supervisor",
                        "deps": ["n1"],
                        "checksum": "demo-n2",
                    },
                    {
                        "key": "n3",
                        "title": "Livrable final",
                        "status": NodeStatus.completed,
                        "role": "executor",
                        "deps": ["n1", "n2"],
                        "checksum": "demo-n3",
                    },
                ],
                "artifacts": [
                    {
                        "node_key": "n3",
                        "type": "markdown",
                        "path": "/artifacts/brief_demo.md",
                        "content": "# Livrable de demonstration\nQuelques puces pour illustrer.",
                        "summary": "Livrable synthetique",
                    }
                ],
                "events": [
                    {
                        "node_key": "n1",
                        "level": "INFO",
                        "message": "Demarrage de l'analyse",
                        "request_id": "demo-1",
                    },
                    {
                        "node_key": "n2",
                        "level": "INFO",
                        "message": "Plan valide",
                        "request_id": "demo-2",
                    },
                    {
                        "node_key": None,
                        "level": "RUN_COMPLETED",
                        "message": "Livrable transmis",
                        "request_id": "demo-run-1",
                    },
                ],
                "feedbacks": [
                    {
                        "node_key": "n3",
                        "source": "client",
                        "reviewer": "Alexandre",
                        "score": 5,
                        "comment": "Tres clair, merci !",
                        "meta": {"seed": "demo"},
                    }
                ],
            },
            {
                "title": "Demo run #2",
                "status": RunStatus.failed,
                "duration": timedelta(minutes=12),
                "meta": {"seed": "demo", "use_case": "audit interne"},
                "nodes": [
                    {
                        "key": "n1",
                        "title": "Collecte de documents",
                        "status": NodeStatus.completed,
                        "role": "manager",
                        "deps": [],
                        "checksum": "demo2-n1",
                    },
                    {
                        "key": "n2",
                        "title": "Analyse de conformite",
                        "status": NodeStatus.failed,
                        "role": "executor",
                        "deps": ["n1"],
                        "checksum": "demo2-n2",
                    },
                    {
                        "key": "n3",
                        "title": "Synthese",
                        "status": NodeStatus.canceled,
                        "role": "reviewer",
                        "deps": ["n2"],
                        "checksum": "demo2-n3",
                    },
                ],
                "artifacts": [
                    {
                        "node_key": "n2",
                        "type": "sidecar",
                        "path": "/artifacts/audit_notes.json",
                        "content": '{"issues": 3, "severity": "medium"}',
                        "summary": "Notes brutes",
                    }
                ],
                "events": [
                    {
                        "node_key": "n1",
                        "level": "INFO",
                        "message": "Documents collectes",
                        "request_id": "demo2-1",
                    },
                    {
                        "node_key": "n2",
                        "level": "ERROR",
                        "message": "Blocage sur la conformite RGPD",
                        "request_id": "demo2-2",
                    },
                    {
                        "node_key": None,
                        "level": "RUN_FAILED",
                        "message": "Fin anticipee",
                        "request_id": "demo-run-2",
                    },
                ],
                "feedbacks": [
                    {
                        "node_key": "n2",
                        "source": "qa",
                        "reviewer": "Elisa",
                        "score": 2,
                        "comment": "Analyse interrompue, prevoir un second passage.",
                        "meta": {"seed": "demo"},
                    }
                ],
            },
        ]

        for scenario in scenarios:
            run_id = uuid.uuid4()
            run = Run(
                id=run_id,
                title=scenario["title"],
                status=scenario["status"],
                started_at=now - scenario["duration"],
                ended_at=now,
                meta=scenario["meta"],
            )
            session.add(run)
            counts["runs"] += 1
            await session.flush()

            node_objects: Dict[str, uuid.UUID] = {}
            for node_data in scenario["nodes"]:
                node_id = uuid.uuid4()
                node = Node(
                    id=node_id,
                    run_id=run_id,
                    key=node_data["key"],
                    title=node_data["title"],
                    status=node_data["status"],
                    role=node_data["role"],
                    deps=node_data["deps"],
                    checksum=node_data["checksum"],
                    created_at=now - scenario["duration"] + timedelta(minutes=1),
                    updated_at=now - timedelta(minutes=1),
                )
                session.add(node)
                node_objects[node_data["key"]] = node_id
                counts["nodes"] += 1

            await session.flush()

            for artifact in scenario["artifacts"]:
                node_id = node_objects[artifact["node_key"]]
                session.add(
                    Artifact(
                        node_id=node_id,
                        type=artifact["type"],
                        path=artifact["path"],
                        content=artifact["content"],
                        summary=artifact["summary"],
                        created_at=now,
                    )
                )
                counts["artifacts"] += 1

            for event in scenario["events"]:
                node_id = node_objects.get(event["node_key"]) if event["node_key"] else None
                session.add(
                    Event(
                        run_id=run_id,
                        node_id=node_id,
                        level=event["level"],
                        message=event["message"],
                        request_id=event["request_id"],
                        timestamp=now,
                        extra={"seed": "demo"},
                    )
                )
                counts["events"] += 1

            for feedback in scenario["feedbacks"]:
                node_id = node_objects[feedback["node_key"]]
                session.add(
                    Feedback(
                        run_id=run_id,
                        node_id=node_id,
                        source=feedback["source"],
                        reviewer=feedback["reviewer"],
                        score=feedback["score"],
                        comment=feedback["comment"],
                        meta=feedback["meta"],
                    )
                )
                counts["feedbacks"] += 1

        await session.commit()

    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed de donnees de demonstration pour Crew IA.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Purge les donnees de demo existantes avant de reinserer",
    )
    return parser.parse_args()


async def async_main(reset: bool) -> None:
    counts = await seed_demo_data(reset=reset)
    print(
        "Seed de demo termine - runs={runs}, nodes={nodes}, artifacts={artifacts}, events={events}, feedbacks={feedbacks}".format(
            **counts
        )
    )


def main() -> None:
    args = parse_args()
    try:
        asyncio.run(async_main(reset=args.reset))
    except SeedError as exc:
        print(f"Attention: {exc}")


if __name__ == "__main__":
    main()
