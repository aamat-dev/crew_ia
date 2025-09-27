# api/fastapi_app/routes/tasks.py
from __future__ import annotations

import json
import logging
import os
import time
from typing import Optional, Any, Dict
from uuid import UUID, uuid4
from datetime import datetime, UTC
import asyncio
import anyio

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Query
from pydantic import BaseModel
from fastapi import Header
from pydantic import ValidationError

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import strict_api_key_auth, get_session, read_timezone, to_tz, get_sessionmaker
from ..schemas_base import TaskRequest, TaskAcceptedResponse, Page

from backend.core.models import Task, TaskStatus
from backend.api.schemas.task import TaskCreate, TaskOut

from backend.core.models import Plan, PlanStatus
from backend.api.schemas.plan import PlanCreateResponse
from backend.core.services.supervisor import generate_plan
import orchestrator.api_runner as api_runner
from core.planning.task_graph import TaskGraph
from core.storage.db_models import Run, RunStatus, Event
from ..utils.run_flow import utcnow, make_callbacks, finalize_run
from backend.api.utils.pagination import (
    PaginationParams,
    pagination_params,
    set_pagination_headers,
)
from ..ordering import apply_order

# --- Planificateur de run (surchargé par les tests au besoin) ---
async def schedule_run(
    *,
    request: Request,
    run_id: UUID,
    title: str,
    task_spec: Dict[str, Any],
    options: Any,
    request_id: str | None,
):
    """Planifie l'exécution d'un run en tâche de fond et retourne immédiatement.

    Les tests peuvent monkeypatcher cette fonction pour court-circuiter l'exécution.
    """

    async def _runner() -> None:
        # Évite toute exécution si l'application est en cours d'arrêt
        if getattr(request.app.state, "shutting_down", False):
            return
        # Marque le run comme 'running' au démarrage pour refléter rapidement l'état
        # Respecte l'override FastAPI pour get_sessionmaker() si défini
        try:
            override_get_sm = request.app.dependency_overrides.get(get_sessionmaker)  # type: ignore[attr-defined]
        except Exception:
            override_get_sm = None
        SessionLocal = (override_get_sm() if callable(override_get_sm) else get_sessionmaker())
        async with SessionLocal() as session:
            run = await session.get(Run, run_id)
            # Compat: statut initial peut être 'pending' (app) ou 'queued' (DB)
            initial = getattr(run, "status", None)
            # Considère 'queued' sous toutes ses formes (Enum ou str)
            is_pending = (
                initial in {RunStatus.pending, RunStatus.queued} or str(initial) in {"queued", "RunStatus.queued"}
            )
            if run and is_pending:
                run.status = RunStatus.running
                run.started_at = utcnow()
                session.add(run)
                await session.commit()

        # Lance l'orchestrateur (événements/nœuds/artifacts via storage)
        storage = request.app.state.storage
        event_publisher = request.app.state.event_publisher
        try:
            await api_runner.run_task(
                run_id=str(run_id),
                task_spec=task_spec,
                options=options,
                storage=storage,
                event_publisher=event_publisher,
                title=title,
                request_id=request_id,
            )
        except (asyncio.CancelledError, anyio.get_cancelled_exc_class()):
            # Pendant le shutdown, on sort immédiatement sans effectuer d’IO DB/FS
            return
        finally:
            # Laisse l'event loop scheduler flusher les I/O avant la sortie du worker
            try:
                await anyio.sleep(0)
            except Exception:
                pass

    # En mode tests rapides, exécute le runner en mode synchrone pour fiabiliser le polling
    import os as _os
    if _os.getenv("FAST_TEST_RUN") == "1":
        await _runner()
        await anyio.sleep(0)
        return run_id
    tg = request.app.state.task_group
    tg.start_soon(_runner)
    return run_id

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Depends(strict_api_key_auth)],  # 🔒 vérifie la valeur de la clé
)

log = logging.getLogger("api.tasks")

# ---------- Rate limit config ----------
RATE_LIMIT = 3
WINDOW_SEC = 60


def _check_rate_limit(request: Request) -> None:
    store: Dict[str, tuple[int, float]] = request.app.state.rate_limits
    ip = request.client.host if request.client else "?"
    api_key = request.headers.get("X-API-Key", "")
    key = f"{ip}:{api_key}"
    now = time.time()
    count, start = store.get(key, (0, now))
    if now - start > WINDOW_SEC:
        store[key] = (1, now)
        return
    if count >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too Many Requests")
    store[key] = (count + 1, start)

# ---------- Routes ----------

# ----- Listing des tâches -----
ORDERABLE_FIELDS = {
    "created_at": Task.created_at,
    "updated_at": Task.updated_at,
    "title": Task.title,
    "status": Task.status,
}


@router.get("", response_model=Page[TaskOut])
async def list_tasks(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
    tz = Depends(read_timezone),
    pagination: PaginationParams = Depends(pagination_params),
    status: str | None = Query(None, description="Filtre par status"),
    title_contains: str | None = Query(None, description="Filtre par sous-chaîne du titre"),
    include_archived: bool = Query(False, description="Inclure les tâches archivées"),
):
    where = []
    if status:
        where.append(Task.status == status)
    if title_contains:
        like = f"%{title_contains}%"
        where.append(Task.title.ilike(like))
    if not include_archived:
        try:
            # filtre les archivées si la colonne existe
            where.append(Task.__table__.c.archived.is_(False))  # type: ignore[attr-defined]
        except Exception:
            pass

    base = select(Task)
    if where:
        base = base.where(and_(*where))

    total_q = select(func.count(Task.id))
    if where:
        total_q = total_q.where(and_(*where))
    total = (await session.execute(total_q)).scalar_one()

    stmt = apply_order(
        base,
        pagination.order_by,
        pagination.order_dir,
        ORDERABLE_FIELDS,
        "-created_at",
    ).limit(pagination.limit).offset(pagination.offset)

    rows = (await session.execute(stmt)).scalars().all()
    items = [
        TaskOut(
            id=t.id,
            title=t.title,
            description=t.description,
            status=t.status,
            created_at=to_tz(getattr(t, "created_at", None), tz) or t.created_at,
            updated_at=to_tz(getattr(t, "updated_at", None), tz) or t.updated_at,
        )
        for t in rows
    ]

    links = set_pagination_headers(
        response,
        request,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )

    return Page[TaskOut](
        items=items,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
        links=links or None,
    )


class TaskUpdatePayload(BaseModel):
    title: str | None = None
    description: str | None = None
    archived: bool | None = None


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: UUID,
    payload: TaskUpdatePayload,
    session: AsyncSession = Depends(get_session),
):
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="not found")
    data = payload.model_dump(exclude_unset=True)
    # Titre/description
    if "title" in data and data["title"] is not None:
        if not data["title"].strip():
            raise HTTPException(status_code=422, detail="title must not be empty")
        task.title = data["title"].strip()
    if "description" in data:
        task.description = (data["description"] or None)
    # Archive
    if data.get("archived") is True:
        if task.status == TaskStatus.running:
            raise HTTPException(status_code=409, detail="cannot archive a running task")
        try:
            setattr(task, "archived", True)
        except Exception:
            pass
    if data.get("archived") is False:
        try:
            setattr(task, "archived", False)
        except Exception:
            pass
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return TaskOut.model_validate(task)


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    task = await session.get(Task, task_id)
    if not task:
        return Response(status_code=204)
    if task.status == TaskStatus.running:
        raise HTTPException(status_code=409, detail="cannot delete a running task")
    await session.delete(task)
    await session.commit()
    return Response(status_code=204)

@router.post(
    "",
    response_model=TaskOut | TaskAcceptedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    payload: Dict[str, Any],
    response: Response,
    request: Request,
    session: AsyncSession = Depends(get_session),
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-ID"),
):
    """Crée une tâche brouillon ou lance l'orchestrateur suivant le corps de requête.

    Exemple cURL (création simple)::

        curl -X POST http://localhost:8000/tasks \
             -H 'X-API-Key: <API_KEY>' \
             -H 'X-Request-ID: <UUIDv4>' \
             -H 'Content-Type: application/json' \
             -d '{"title": "T1", "description": "desc"}'
    """

    rid = x_request_id or str(uuid4())
    response.headers["X-Request-ID"] = rid

    # Branche simple: création d'une tâche brouillon (+ options rapides)
    # Ajout: auto_plan/auto_start pour un démarrage en 1 clic
    allowed_keys = {"title", "description", "auto_plan", "auto_start"}
    if set(payload.keys()) <= allowed_keys:
        try:
            data = TaskCreate.model_validate(payload)
        except ValidationError as e:
            errs = [{"loc": err["loc"], "msg": err["msg"], "type": err["type"]} for err in e.errors()]
            raise HTTPException(status_code=422, detail=errs)

        title = data.title

        exists = await session.execute(
            select(func.count())
            .select_from(Task)
            .where(func.lower(Task.title) == title.lower())
        )
        if exists.scalar_one() > 0:
            raise HTTPException(status_code=409, detail="task exists")

        now = datetime.now(UTC)
        task = Task(
            title=title,
            description=data.description,
            status=TaskStatus.draft,
            created_at=now,
            updated_at=now,
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)

        # Gestion 1‑clic: auto_plan / auto_start
        auto_plan = bool(payload.get("auto_plan", False))
        auto_start = bool(payload.get("auto_start", False))

        if not auto_plan and not auto_start:
            response.headers["Location"] = f"/tasks/{task.id}"
            return TaskOut.model_validate(task)

        # 1) Génération du plan (si demandée)
        plan = None
        if auto_plan:
            try:
                result = await generate_plan(task)
            except Exception as e:
                # Considère l'opération comme une création de tâche réussie, mais plan KO
                log.warning("auto_plan failed for task_id=%s err=%r", task.id, e)
                response.headers["Location"] = f"/tasks/{task.id}"
                return TaskOut.model_validate(task)

            if task.plan_id:
                plan = await session.get(Plan, task.plan_id)
            if plan:
                plan.graph = result.graph.model_dump()
                plan.status = result.status
                plan.version += 1
            else:
                plan = Plan(task_id=task.id, status=result.status, graph=result.graph.model_dump())
                session.add(plan)
                await session.flush()
                if result.status != PlanStatus.invalid:
                    task.plan_id = plan.id

            # Versioning optionnel
            try:
                from backend.app.models.plan_version import PlanVersion  # type: ignore
                session.add(
                    PlanVersion(
                        plan_id=plan.id,
                        numero_version=plan.version,
                        graph=plan.graph,
                    )
                )
            except Exception:
                pass
            await session.commit()

            # Si le plan n'est pas prêt et qu'on veut auto_start, on renvoie 409
            if auto_start and (not plan or plan.status != PlanStatus.ready):
                raise HTTPException(status_code=409, detail="Plan not ready")

        # 2) Démarrage (si demandé)
        if auto_start:
            _check_rate_limit(request)

            # Si aucun plan n'a été généré, on vérifie qu'il existe
            if task.plan_id is None:
                raise HTTPException(status_code=409, detail="Plan missing")
            plan_row = await session.get(Plan, task.plan_id)
            if not plan_row or plan_row.status != PlanStatus.ready:
                raise HTTPException(status_code=409, detail="Plan not ready")

            # Persiste spec dans plans.graph (pour l'orchestrateur)
            try:
                import json as _json
                from pathlib import Path as _Path
                graph = plan_row.graph or {}
                nodes = graph.get("plan") or graph.get("nodes") or []
                spec = {"title": task.title or str(task.id), "plan": nodes}
                path = _Path("plans.graph")
                if path.exists():
                    root = _json.loads(path.read_text(encoding="utf-8"))
                else:
                    root = {"version": "1.0", "plans": {}}
                if root.get("version") != "1.0":
                    root["version"] = "1.0"
                root.setdefault("plans", {})[str(plan_row.id)] = spec
                path.write_text(_json.dumps(root, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to persist plan spec: {e}")

            try:
                from backend.orchestrator import orchestrator_adapter as _orch
                run_uuid = await _orch.start(plan_row.id, dry_run=False)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Orchestrator start failed: {e}")

            try:
                task.run_id = run_uuid
                task.status = TaskStatus.running
                session.add(task)
                await session.commit()
            except Exception:
                await session.rollback()

            response.status_code = status.HTTP_201_CREATED
            response.headers["Location"] = f"/runs/{run_uuid}"
            return TaskAcceptedResponse(run_id=run_uuid, location=f"/runs/{run_uuid}")

        # Retour défaut si auto_plan seul
        response.headers["Location"] = f"/tasks/{task.id}"
        return TaskOut.model_validate(task)

    # Sinon: déclenchement orchestrateur (asynchrone)
    _check_rate_limit(request)

    try:
        body = TaskRequest.model_validate(payload)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())

    # Source du plan prioritaire: task_spec > task ; sinon task_file
    task_spec: Optional[Dict[str, Any]] = None
    if body.task_spec is not None:
        task_spec = body.task_spec.model_dump(exclude_unset=True)
    elif body.task is not None:
        task_spec = body.task.model_dump(exclude_unset=True)

    # Validation rapide côté API si on passe par un fichier
    if task_spec is None and body.task_file:
        if not os.path.isfile(body.task_file):
            raise HTTPException(status_code=400, detail=f"task_file not found: {body.task_file}")
        if not body.task_file.lower().endswith(".json"):
            raise HTTPException(status_code=400, detail="task_file must be a .json file")

    request_id = x_request_id or body.request_id or getattr(request.state, "request_id", None)

    if task_spec is None and body.task_file:
        try:
            with open(body.task_file, "r", encoding="utf-8") as f:
                task_spec = json.load(f)
        except FileNotFoundError:
            raise HTTPException(status_code=400, detail=f"task_file not found: {body.task_file}")
        except ValueError:
            raise HTTPException(status_code=400, detail="task_file must be a .json file")

    if task_spec is None:
        raise HTTPException(status_code=400, detail="Missing task spec")

    # Chemin démo géré côté orchestrateur: ne pas matérialiser un plan ici
    # afin de permettre la voie "légère" (sans run_graph) pour les runs ad-hoc.

    # Idempotence basique via X-Request-ID: si un run existe déjà pour ce request_id
    # on renvoie la même Location (pending/running)
    if request_id:
        try:
            existing = (
                await session.execute(
                    select(Run)
                    .where((Run.meta["request_id"].astext == request_id))
                    .order_by(Run.created_at.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
            if existing and (
                str(existing.status) in {"RunStatus.pending", "RunStatus.running", "queued"}
                or getattr(existing, "status", None)
                in {RunStatus.pending, RunStatus.running}
            ):
                response.status_code = status.HTTP_202_ACCEPTED
                response.headers["Location"] = f"/runs/{existing.id}"
                return TaskAcceptedResponse(run_id=existing.id, location=f"/runs/{existing.id}")
        except Exception:
            # En cas de backend non-JSONB, ignore la déduplication
            pass

    # Matérialise immédiatement le run en DB et déclenche l'exécution async
    # Utiliser 'queued' pour correspondre à l'ENUM PostgreSQL; garder la compat en lecture ailleurs.
    run = Run(title=body.title, status=RunStatus.queued, meta={"request_id": request_id})
    session.add(run)
    await session.commit()
    await session.refresh(run)

    # Lancement arrière-plan (tests peuvent monkeypatcher schedule_run)
    await schedule_run(
        request=request,
        run_id=run.id,
        title=body.title,
        task_spec=task_spec,
        options=body.options,
        request_id=request_id,
    )

    response.status_code = status.HTTP_202_ACCEPTED
    response.headers["Location"] = f"/runs/{run.id}"
    return TaskAcceptedResponse(run_id=run.id, location=f"/runs/{run.id}")


@router.post("/{task_id}/plan", response_model=PlanCreateResponse, status_code=status.HTTP_201_CREATED)
async def generate_task_plan(
    task_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
):
    """Génère et persiste un plan pour une tâche donnée."""

    task = await session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    result = await generate_plan(task)

    plan = None
    if task.plan_id:
        plan = await session.get(Plan, task.plan_id)
    if plan:
        plan.graph = result.graph.model_dump()
        plan.status = result.status
        plan.version += 1
    else:
        plan = Plan(task_id=task.id, status=result.status, graph=result.graph.model_dump())
        session.add(plan)
        await session.flush()
        if result.status != PlanStatus.invalid:
            task.plan_id = plan.id

    # Enregistre un snapshot de version (PlanVersion)
    try:
        from backend.app.models.plan_version import PlanVersion  # import local pour éviter cycles
        session.add(
            PlanVersion(
                plan_id=plan.id,
                numero_version=plan.version,
                graph=plan.graph,
            )
        )
    except Exception:
        # Tolère l’absence de table en environnements anciens
        pass

    await session.commit()

    req_id = x_request_id or getattr(request.state, "request_id", None)
    log.info(
        "plan generated",
        extra={"request_id": req_id, "task_id": str(task.id), "plan_id": str(plan.id), "status": result.status.value},
    )

    return PlanCreateResponse(plan_id=plan.id, status=plan.status, graph=result.graph)


@router.post("/{task_id}/start", status_code=status.HTTP_202_ACCEPTED)
async def start_task_run(
    task_id: UUID,
    request: Request,
    dry_run: bool = False,
    session: AsyncSession = Depends(get_session),
):
    """Démarre un run pour un ``task_id`` donné."""
    task = await session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.plan_id is None:
        raise HTTPException(status_code=409, detail="Plan missing")

    plan = (
        await session.execute(select(Plan).where(Plan.id == task.plan_id))
    ).scalar_one_or_none()
    if plan is None or plan.status != PlanStatus.ready:
        raise HTTPException(status_code=409, detail="Plan not ready")

    # Chemin exécution réelle via orchestrateur (activable par env)
    import os as _os
    if (_os.getenv("PLAN_EXECUTE_ON_START", "true").strip().lower() in {"1", "true", "yes", "on"}):
        # 1) écrire/mettre à jour plans.graph (best-effort)
        try:
            import json as _json
            from pathlib import Path as _Path
            plan_row = await session.get(Plan, task.plan_id)
            if not plan_row:
                raise HTTPException(status_code=409, detail="Plan not found")
            graph = plan_row.graph or {}
            nodes = graph.get("plan") or graph.get("nodes") or []
            spec = {"title": task.title or str(task_id), "plan": nodes}
            path = _Path("plans.graph")
            if path.exists():
                root = _json.loads(path.read_text(encoding="utf-8"))
            else:
                root = {"version": "1.0", "plans": {}}
            if root.get("version") != "1.0":
                root["version"] = "1.0"
            root.setdefault("plans", {})[str(plan_row.id)] = spec
            path.write_text(_json.dumps(root, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            # Plutôt que 500, on log et on passera en fallback DB-only
            logging.getLogger("api.tasks").warning("persist plans.graph failed: %s", e, exc_info=True)
            plan_row = None  # force fallback orchestrateur

        # 2) lancer orchestrateur
        try:
            from backend.orchestrator import orchestrator_adapter as _orch
            if plan_row is not None:
                run_uuid = await _orch.start(plan_row.id, dry_run=dry_run)
            else:
                raise RuntimeError("plans.graph not persisted")
        except HTTPException:
            raise
        except Exception as e:
            # Fallback robuste: crée un run DB-only plutôt que 500
            logging.getLogger("api.tasks").warning("orchestrator start failed: %s -- falling back to DB-only run", e, exc_info=True)
            request_id = getattr(request.state, "request_id", None)
            run = Run(title=task.title, status=RunStatus.running, started_at=utcnow(), meta={"request_id": request_id})
            session.add(run)
            await session.commit()
            await session.refresh(run)
            if not dry_run:
                try:
                    task.run_id = run.id
                    task.status = TaskStatus.running
                    session.add(task)
                    await session.commit()
                except Exception:
                    await session.rollback()
            session.add(
                Event(
                    run_id=run.id,
                    level="RUN_STARTED",
                    message=json.dumps({"request_id": request_id} if request_id else {}),
                    request_id=request_id,
                )
            )
            await session.commit()
            return {"run_id": str(run.id), "dry_run": dry_run}

        # 3) Mettre à jour la tâche (liaison run)
        if not dry_run:
            try:
                task.run_id = run_uuid
                task.status = TaskStatus.running
                session.add(task)
                await session.commit()
            except Exception:
                await session.rollback()
        return {"run_id": str(run_uuid), "dry_run": dry_run}

    # Chemin historique (tests) : ne lance pas l'exécution, crée un run "running" minimal
    request_id = getattr(request.state, "request_id", None)
    run = Run(title=task.title, status=RunStatus.running, started_at=utcnow(), meta={"request_id": request_id})
    session.add(run)
    await session.commit()
    await session.refresh(run)
    if not dry_run:
        task.run_id = run.id
        task.status = TaskStatus.running
        session.add(task)
        await session.commit()
    session.add(
        Event(
            run_id=run.id,
            level="RUN_STARTED",
            message=json.dumps({"request_id": request_id} if request_id else {}),
            request_id=request_id,
        )
    )
    await session.commit()
    return {"run_id": str(run.id), "dry_run": dry_run}
