from __future__ import annotations
from typing import Optional
from uuid import UUID
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import get_session, settings, strict_api_key_auth
from ..schemas_base import Page, ArtifactOut
from app.utils.pagination import (
    PaginationParams,
    pagination_params,
    set_pagination_headers,
)
from ..ordering import apply_order
from core.storage.db_models import Artifact  # type: ignore

router_nodes = APIRouter(prefix="/nodes", tags=["artifacts"], dependencies=[Depends(strict_api_key_auth)])
router_artifacts = APIRouter(prefix="/artifacts", tags=["artifacts"], dependencies=[Depends(strict_api_key_auth)])

ORDERABLE = {"created_at": Artifact.created_at, "type": Artifact.type}

@router_nodes.get("/{node_id}/artifacts", response_model=Page[ArtifactOut])
async def list_artifacts(
    node_id: UUID,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
    pagination: PaginationParams = Depends(pagination_params),
    type: Optional[str] = Query(None, description="Filtre par type d'artifact"),
    name_contains: Optional[str] = Query(None, description="Filtre nom (path ILIKE)"),
):
    base = select(Artifact).where(Artifact.node_id == node_id)
    if type:
        base = base.where(Artifact.type == type)
    if name_contains:
        base = base.where(Artifact.path.ilike(f"%{name_contains}%"))

    total_stmt = select(func.count(Artifact.id)).where(Artifact.node_id == node_id)
    if type:
        total_stmt = total_stmt.where(Artifact.type == type)
    if name_contains:
        total_stmt = total_stmt.where(Artifact.path.ilike(f"%{name_contains}%"))

    total = (await session.execute(total_stmt)).scalar_one()
    stmt = apply_order(
        base, pagination.order_by, pagination.order_dir, ORDERABLE, "-created_at"
    ).limit(pagination.limit).offset(pagination.offset)

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
    set_pagination_headers(
        response, request, total, pagination.limit, pagination.offset
    )
    return Page[ArtifactOut](
        items=items,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )

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
