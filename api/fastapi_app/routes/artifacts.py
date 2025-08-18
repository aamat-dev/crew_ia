from __future__ import annotations
from typing import Optional
from uuid import UUID
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import get_session, require_api_key, settings, api_key_auth
from ..schemas import Page, ArtifactOut
from core.storage.db_models import Artifact  # type: ignore

router_nodes = APIRouter(prefix="/nodes", tags=["artifacts"], dependencies=[Depends(api_key_auth)])
router_artifacts = APIRouter(prefix="/artifacts", tags=["artifacts"], dependencies=[Depends(api_key_auth)])

ORDERABLE = {"created_at": Artifact.created_at, "type": Artifact.type}

def order(stmt, order_by: str | None):
    if not order_by:
        return stmt.order_by(desc(Artifact.created_at))
    key = order_by.lstrip("-")
    direction = desc if order_by.startswith("-") else asc
    col = ORDERABLE.get(key, Artifact.created_at)
    return stmt.order_by(direction(col))

@router_nodes.get("/{node_id}/artifacts", response_model=Page[ArtifactOut])
async def list_artifacts(
    node_id: UUID,
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    type: Optional[str] = Query(None, description="Filtre par type d'artifact"),
    order_by: Optional[str] = Query("-created_at"),
):
    base = select(Artifact).where(Artifact.node_id == node_id)
    if type:
        base = base.where(Artifact.type == type)

    total = (await session.execute(select(func.count(Artifact.id)).where(Artifact.node_id == node_id))).scalar_one()
    stmt = order(base, order_by).limit(limit).offset(offset)

    rows = (await session.execute(stmt)).scalars().all()

    def _preview(a: Artifact) -> str | None:
        if getattr(a, "summary", None):
            return a.summary
        if getattr(a, "content", None):
            return a.content[:280] + ("…" if len(a.content) > 280 else "")
        return None

    items = [
        ArtifactOut(
            id=a.id,
            node_id=a.node_id,
            type=a.type,
            path=a.path,
            content=a.content,
            summary=a.summary,
            created_at=a.created_at,
            preview=_preview(a),
        )
        for a in rows
    ]
    return Page[ArtifactOut](items=items, total=total, limit=limit, offset=offset)

# --- NEW: GET /artifacts/{artifact_id} ---
@router_artifacts.get("/{artifact_id}", response_model=ArtifactOut)
async def get_artifact(
    artifact_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    row = (await session.execute(select(Artifact).where(Artifact.id == artifact_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # preview (même logique que la liste)
    preview = row.summary or (row.content[:280] + ("…" if row.content and len(row.content) > 280 else "")) if row.content else None

    return ArtifactOut(
        id=row.id,
        node_id=row.node_id,
        type=row.type,
        path=row.path,
        content=row.content,
        summary=row.summary,
        created_at=row.created_at,
        preview=preview,
    )

# --- NEW (optionnel): GET /artifacts/{artifact_id}/download ---
@router_artifacts.get("/{artifact_id}/download")
async def download_artifact(
    artifact_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    row = (await session.execute(select(Artifact).where(Artifact.id == artifact_id))).scalar_one_or_none()
    if not row or not row.path:
        raise HTTPException(status_code=404, detail="Artifact not found or no path")

    # Sécurité : le fichier doit être sous ARTIFACTS_DIR (whitelist)
    root = Path(settings.artifacts_dir).resolve()
    target = (root / Path(row.path).name).resolve() if not Path(row.path).is_absolute() else Path(row.path).resolve()

    # Permettre les paths absolus, mais exige qu'ils restent dans root (si tu veux restreindre fortement)
    try:
        inside = root in target.parents or target == root or str(target).startswith(str(root))
    except Exception:
        inside = False
    if not inside:
        # fallback : autoriser strictement root/<basename>
        target = (root / Path(row.path).name).resolve()

    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found on disk")

    def file_iterator(p: Path, chunk_size: int = 64 * 1024):
        with p.open("rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    return StreamingResponse(
        file_iterator(target),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{target.name}"'},
    )
