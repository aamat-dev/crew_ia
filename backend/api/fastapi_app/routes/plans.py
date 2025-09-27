from __future__ import annotations

from uuid import UUID
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import Plan, PlanStatus
from backend.core.models import PlanReview
from backend.core.models import Assignment
from backend.api.schemas.assignment import AssignmentsPayload, AssignmentsResponse
from backend.api.fastapi_app.deps import get_db, strict_api_key_auth, require_role, require_request_id
from backend.api.schemas.plan import PlanGraph, PlanCreateResponse
from backend.app.models.plan_version import PlanVersion
from ..schemas.prompting import RecruitRequest
from ..services.recruit_service import RecruitService
import os

router = APIRouter(
    prefix="/plans",
    tags=["plans"],
    dependencies=[Depends(strict_api_key_auth)],
)


class FieldDelta(BaseModel):
    previous: Any
    current: Any


class PlanNodeChange(BaseModel):
    id: str
    changes: dict[str, FieldDelta]


class PlanVersionDiffOut(BaseModel):
    plan_id: str
    current_version: int
    previous_version: int
    added_nodes: list[dict[str, Any]]
    removed_nodes: list[dict[str, Any]]
    changed_nodes: list[PlanNodeChange]
    added_edges: list[dict[str, str]]
    removed_edges: list[dict[str, str]]


def _extract_nodes(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    nodes = []
    if isinstance(graph, dict):
        if isinstance(graph.get("plan"), list):
            nodes = graph.get("plan") or []
        elif isinstance(graph.get("nodes"), list):
            nodes = graph.get("nodes") or []
    out: dict[str, dict[str, Any]] = {}
    for node in nodes:
        if isinstance(node, dict):
            node_id = node.get("id")
            if isinstance(node_id, str) and node_id:
                out[node_id] = node
    return out


def _extract_edges(graph: dict[str, Any]) -> list[dict[str, str]]:
    edges_raw = []
    if isinstance(graph, dict) and isinstance(graph.get("edges"), list):
        edges_raw = graph.get("edges") or []
    edges: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for edge in edges_raw:
        if not isinstance(edge, dict):
            continue
        source = edge.get("source") or edge.get("from")
        target = edge.get("target") or edge.get("to")
        if isinstance(source, str) and isinstance(target, str):
            key = (source, target)
            if key not in seen:
                seen.add(key)
                edges.append({"source": source, "target": target})
    return edges


def _plan_node_ids(plan: Plan) -> set[str]:
    # Tolère graph.plan (standard) et graph.nodes (legacy)
    nodes = plan.graph.get("plan") or plan.graph.get("nodes") or []
    return {n.get("id") for n in nodes if isinstance(n, dict) and n.get("id")}


class PlanCreatePayload(BaseModel):
    task_id: UUID
    graph: PlanGraph
    status: Optional[PlanStatus] = None


@router.post("", response_model=PlanCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    payload: PlanCreatePayload,
    db: AsyncSession = Depends(get_db),
) -> PlanCreateResponse:
    from backend.core.models import Task  # import local pour éviter cycles

    task = await db.get(Task, payload.task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    status_value = payload.status or PlanStatus.draft
    # Normalise la forme du graphe en sortie (clé 'plan')
    graph_payload = payload.graph.model_dump()
    plan = Plan(task_id=task.id, status=status_value, graph=graph_payload)
    db.add(plan)
    await db.flush()
    # Snapshot initial en plan_versions (V1)
    db.add(
        PlanVersion(
            plan_id=plan.id,
            numero_version=plan.version,
            graph=graph_payload,
        )
    )
    # Lier à la tâche si le plan est valide ou brouillon (non invalid)
    if status_value != PlanStatus.invalid:
        task.plan_id = plan.id
        db.add(task)
    await db.commit()

    return PlanCreateResponse(plan_id=plan.id, status=plan.status, graph=payload.graph)


@router.get("/{plan_id}")
async def get_plan(plan_id: UUID, db: AsyncSession = Depends(get_db)) -> Any:
    plan = await db.get(Plan, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return {
        "id": str(plan.id),
        "task_id": str(plan.task_id),
        "status": plan.status.value if hasattr(plan.status, "value") else str(plan.status),
        "graph": plan.graph,
        "version": plan.version,
        "created_at": getattr(plan, "created_at", None),
        "updated_at": getattr(plan, "updated_at", None),
    }


@router.get("/{plan_id}/versions")
async def list_plan_versions(plan_id: UUID, db: AsyncSession = Depends(get_db)) -> Any:
    plan = await db.get(Plan, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    rows = (
        await db.execute(
            select(PlanVersion).where(PlanVersion.plan_id == plan_id).order_by(PlanVersion.numero_version.asc())
        )
    ).scalars().all()
    return {
        "plan_id": str(plan_id),
        "versions": [
            {
                "numero_version": v.numero_version,
                "created_at": getattr(v, "created_at", None),
                "reason": getattr(v, "reason", None),
            }
            for v in rows
        ],
    }


@router.get("/{plan_id}/versions/{numero}")
async def get_plan_version(plan_id: UUID, numero: int, db: AsyncSession = Depends(get_db)) -> Any:
    plan = await db.get(Plan, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    row = (
        await db.execute(
            select(PlanVersion).where(PlanVersion.plan_id == plan_id, PlanVersion.numero_version == numero).limit(1)
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    return {
        "plan_id": str(plan_id),
        "numero_version": row.numero_version,
        "graph": row.graph,
        "created_at": getattr(row, "created_at", None),
        "reason": getattr(row, "reason", None),
    }


@router.get("/{plan_id}/versions/{numero}/diff", response_model=PlanVersionDiffOut)
async def get_plan_version_diff(
    plan_id: UUID,
    numero: int,
    previous: Optional[int] = Query(None, ge=1, description="Version précédente à comparer. Défaut: numero-1"),
    db: AsyncSession = Depends(get_db),
):
    plan = await db.get(Plan, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    if numero < 1:
        raise HTTPException(status_code=400, detail="numero must be >= 1")

    current_row = (
        await db.execute(
            select(PlanVersion)
            .where(PlanVersion.plan_id == plan_id, PlanVersion.numero_version == numero)
            .limit(1)
        )
    ).scalar_one_or_none()
    if current_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    previous_num = previous if previous is not None else numero - 1
    if previous_num < 1 or previous_num >= numero:
        raise HTTPException(status_code=400, detail="invalid previous version")

    previous_row = (
        await db.execute(
            select(PlanVersion)
            .where(PlanVersion.plan_id == plan_id, PlanVersion.numero_version == previous_num)
            .limit(1)
        )
    ).scalar_one_or_none()
    if previous_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Previous version not found")

    current_graph = current_row.graph or {}
    previous_graph = previous_row.graph or {}

    current_nodes = _extract_nodes(current_graph)
    previous_nodes = _extract_nodes(previous_graph)

    added_ids = set(current_nodes) - set(previous_nodes)
    removed_ids = set(previous_nodes) - set(current_nodes)
    shared_ids = set(current_nodes) & set(previous_nodes)

    added_nodes = [current_nodes[nid] for nid in sorted(added_ids)]
    removed_nodes = [previous_nodes[nid] for nid in sorted(removed_ids)]

    changed_nodes: list[PlanNodeChange] = []
    for nid in sorted(shared_ids):
        prev_node = previous_nodes[nid]
        curr_node = current_nodes[nid]
        changes: dict[str, FieldDelta] = {}
        keys = set(prev_node.keys()) | set(curr_node.keys())
        for key in keys:
            if prev_node.get(key) != curr_node.get(key):
                changes[key] = FieldDelta(
                    previous=prev_node.get(key),
                    current=curr_node.get(key),
                )
        if changes:
            changed_nodes.append(PlanNodeChange(id=nid, changes=changes))

    current_edges = _extract_edges(current_graph)
    previous_edges = _extract_edges(previous_graph)

    current_edge_keys = {(edge["source"], edge["target"]): edge for edge in current_edges}
    previous_edge_keys = {(edge["source"], edge["target"]): edge for edge in previous_edges}

    added_edge_keys = set(current_edge_keys) - set(previous_edge_keys)
    removed_edge_keys = set(previous_edge_keys) - set(current_edge_keys)

    added_edges = [current_edge_keys[key] for key in sorted(added_edge_keys)]
    removed_edges = [previous_edge_keys[key] for key in sorted(removed_edge_keys)]

    return PlanVersionDiffOut(
        plan_id=str(plan_id),
        current_version=numero,
        previous_version=previous_num,
        added_nodes=added_nodes,
        removed_nodes=removed_nodes,
        changed_nodes=changed_nodes,
        added_edges=added_edges,
        removed_edges=removed_edges,
    )


@router.post("/{plan_id}/assignments", response_model=AssignmentsResponse, status_code=status.HTTP_200_OK)
async def upsert_assignments(
    plan_id: UUID,
    payload: AssignmentsPayload,
    db: AsyncSession = Depends(get_db),
) -> AssignmentsResponse:
    plan = await db.get(Plan, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    valid_ids = _plan_node_ids(plan)
    updated = 0
    out_items = []
    for item in payload.items:
        if item.node_id not in valid_ids:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Unknown node_id: {item.node_id}")
        stmt = select(Assignment).where(
            Assignment.plan_id == plan_id, Assignment.node_id == item.node_id
        )
        result = await db.execute(stmt)
        assignment = result.scalar_one_or_none()
        data = item.model_dump()
        if assignment:
            assignment.role = data["role"]
            assignment.agent_id = data["agent_id"]
            assignment.llm_backend = data["llm_backend"]
            assignment.llm_model = data["llm_model"]
            assignment.params = data.get("params")
        else:
            assignment = Assignment(plan_id=plan_id, **data)
            db.add(assignment)
        updated += 1
        out_items.append(item)
    await db.commit()
    return AssignmentsResponse(updated=updated, items=out_items)


@router.post("/{plan_id}/submit_for_validation")
async def submit_for_validation(
    plan_id: UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
) -> dict:
    plan = await db.get(Plan, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    validated = bool(body.get("validated"))
    errors = body.get("errors") or []

    review = PlanReview(
        plan_id=plan_id,
        version=plan.version,
        validated=validated,
        errors=errors,
    )
    db.add(review)

    if validated and not errors:
        plan.status = PlanStatus.ready
    else:
        plan.status = PlanStatus.draft

    await db.commit()

    return {"plan_id": str(plan_id), "validated": validated, "errors": errors}


@router.post(
    "/{plan_id}/auto_assign",
    dependencies=[Depends(require_role("editor", "admin"))],
)
async def auto_recruit_and_assign(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    request_id: str = Depends(require_request_id),
) -> dict:
    """Recrute des agents pour chaque nœud du plan et crée/actualise les assignations.

    - Utilise RecruitService (sans HTTP sortant) pour persister les agents en DB.
    - Upsert des Assignment(plan_id, node_id, role, agent_id, llm_backend, llm_model).
    """
    plan = await db.get(Plan, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    graph = plan.graph or {}
    nodes = graph.get("plan") or graph.get("nodes") or []
    edges = graph.get("edges") or []
    if not isinstance(nodes, list) or not nodes:
        raise HTTPException(status_code=422, detail="Plan has no nodes")

    created = 0
    updated = 0
    items: list[dict] = []

    default_provider = os.getenv("LLM_DEFAULT_PROVIDER", "ollama")
    default_model = os.getenv("LLM_DEFAULT_MODEL", os.getenv("OLLAMA_MODEL", "llama3.1:8b"))

    # Construire un set des nœuds ayant des enfants (source d'au moins une arête)
    try:
      sources: set[str] = set()
      for e in edges:
          if isinstance(e, dict):
              s = e.get("source") or e.get("from")
              t = e.get("target") or e.get("to")
              if isinstance(s, str) and isinstance(t, str):
                  sources.add(s)
    except Exception:
      sources = set()

    for n in nodes:
        if not isinstance(n, dict):
            continue
        node_id = str(n.get("id")) if n.get("id") else None
        if not node_id:
            continue
        # Rôle: utilise d'abord la suggestion, sinon heuristique manager/executor
        role = str(n.get("suggested_agent_role") or ("manager" if node_id in sources else "executor"))
        # Recrutement
        req = RecruitRequest(
            role_description=f"Auto-recruit for node {node_id}: {n.get('title','')}",
            role=role,
            domain=None,
            language="fr",
            tone="professionnel",
            tools_required=[],
        )
        res = await RecruitService.recruit(db, req, request_id)
        agent_id = res.agent_id
        # Backend/modèle (provider:model) -> split
        provider_model = res.default_model or f"{default_provider}:{default_model}"
        if ":" in provider_model:
            backend_name, model_name = provider_model.split(":", 1)
        else:
            backend_name, model_name = default_provider, provider_model

        # Upsert Assignment
        stmt = select(Assignment).where(
            Assignment.plan_id == plan_id, Assignment.node_id == node_id
        )
        row = (await db.execute(stmt)).scalar_one_or_none()
        if row:
            row.role = role
            row.agent_id = agent_id
            row.llm_backend = backend_name
            row.llm_model = model_name
            row.params = row.params or None
            db.add(row)
            updated += 1
        else:
            row = Assignment(
                plan_id=plan_id,
                node_id=node_id,
                role=role,
                agent_id=agent_id,
                llm_backend=backend_name,
                llm_model=model_name,
                params=None,
            )
            db.add(row)
            created += 1
        items.append({
            "node_id": node_id,
            "role": role,
            "agent_id": agent_id,
            "llm_backend": backend_name,
            "llm_model": model_name,
        })

    await db.commit()
    return {"created": created, "updated": updated, "items": items}
