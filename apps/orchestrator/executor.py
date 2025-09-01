# apps/orchestrator/executor.py
"""
Exécute un DAG avec gestion de reprise + checksum des inputs.
- Skip si: status == completed ET input_checksum identique (sauf override).
- --dry-run: affiche [SKIP]/[RECALC] pour tous les nœuds et n'exécute rien.
- Écrit les artifacts côté FS dans:
    .runs/<run_id>/nodes/<node_key>/artifact_<node_key>.md
    .runs/<run_id>/nodes/<node_key>/artifact_<node_key>.llm.json
"""
from __future__ import annotations

import json
import traceback
import logging
import inspect
import os
import asyncio
from typing import Optional, Set, Callable, Awaitable, Dict, Any
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID
from time import perf_counter

from core.config import get_var
from core.planning.task_graph import TaskGraph, PlanNode
from core.storage.db_models import NodeStatus
from core.storage.composite_adapter import CompositeAdapter
from core.agents.executor_llm import agent_runner
from core.agents.manager import run_manager
from core.agents.registry import resolve_agent
from core.agents.recruiter import recruit
from core.agents.schemas import PlanNodeModel
from core.telemetry.metrics import (
    metrics_enabled,
    get_orchestrator_node_duration_seconds,
)

# <<< AJOUT >>> helpers FS unifiés (option B)
from core.io.artifacts_fs import (
    write_llm_sidecar,
    write_md,
    node_dir as fs_node_dir,
)

log = logging.getLogger("crew.executor")

RESET = "\033[0m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"


def _is_pytest_tmp_cwd() -> bool:
    if not os.getenv("PYTEST_CURRENT_TEST"):
        return False
    # si on est dans le repo (dossier qui contient .git), on NE veut pas écrire à la racine
    return not (Path.cwd() / ".git").exists()

def colorize(msg: str, color: str) -> str:
    return f"{color}{msg}{RESET}"


def _get_attr(node, name, default=""):
    if isinstance(node, dict):
        val = node.get(name, default)
    else:
        val = getattr(node, name, default)
    return default if callable(val) else val


def _node_input_checksum(node) -> str:
    import hashlib, json

    def _get(obj, attr, default=None):
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)

    title = _get(node, "title")
    if callable(title):
        title = None
    key = _get(node, "key")
    params = _get(node, "params", {}) or {}

    raw_deps = _get(node, "deps", []) or []
    if not isinstance(raw_deps, (list, tuple)):
        raw_deps = [raw_deps]
    norm_deps = []
    for d in raw_deps:
        if isinstance(d, str):
            norm_deps.append(d)
        elif isinstance(d, dict):
            norm_deps.append(d.get("key") or d.get("title") or "")
        else:
            nk = getattr(d, "key", None)
            nt = getattr(d, "title", None)
            if callable(nt):
                nt = None
            norm_deps.append(nk or nt or "")

    if title is None and isinstance(node, str):
        title = node

    payload = {
        "title": title or "",
        "key": key or "",
        "params": params,
        "deps": norm_deps,
    }

    h = hashlib.sha256()
    h.update(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    return h.hexdigest()


def _node_id_str(node, checksum: str) -> str:
    if isinstance(node, str) and node:
        return node
    nid = _get_attr(node, "id", None)
    if isinstance(nid, str) and nid:
        return nid
    if nid is not None:
        try:
            return str(nid)
        except Exception:
            pass
    return f"auto-{checksum[:8]}"


def _norm_dep_ids(node) -> list[str]:
    raw = _get_attr(node, "deps", []) or []
    if not isinstance(raw, (list, tuple)):
        raw = [raw]
    out: list[str] = []
    for d in raw:
        d_cs = _node_input_checksum(d)
        out.append(_node_id_str(d, d_cs))
    return out


# ---------- Extraction méta & markdown depuis le résultat agent_runner ---------

def _extract_llm_meta_from_result(artifact: Any) -> Dict[str, Any]:
    """
    Rend un dict normalisé pour le sidecar:
      {provider, model_used, latency_ms, usage, prompts?}
    On est tolérant: artifact peut être dict imbriqué, etc.
    """
    if not isinstance(artifact, dict):
        return {}

    # chemins possibles
    candidates = [artifact]
    for k in ("llm", "meta", "metrics"):
        v = artifact.get(k)
        if isinstance(v, dict):
            candidates.append(v)

    out: Dict[str, Any] = {}
    for obj in candidates:
        prov = obj.get("provider")
        model = obj.get("model_used") or obj.get("model")
        lat = obj.get("latency_ms") or obj.get("duration_ms") or obj.get("latency")
        usage = obj.get("usage")
        prompts = obj.get("prompts")
        markdown = obj.get("markdown")

        if prov or model or lat or usage or prompts:
            out = {
                "provider": prov,
                "model_used": model,
                "latency_ms": lat,
                "usage": usage,
            }
            if isinstance(prompts, dict):
                out["prompts"] = prompts
            if isinstance(markdown, str):
                out["markdown"] = markdown
            break

    if not out and isinstance(artifact.get("markdown"), str):
        out["markdown"] = artifact["markdown"]

    return out


def _extract_markdown_from_result(artifact: Any) -> str | None:
    """
    Essaie de récupérer un contenu markdown. Sinon None.
    On ne force pas: beaucoup d’agents renvoient du JSON structuré.
    """
    if isinstance(artifact, dict):
        # conventions possibles
        for key in ("markdown", "md", "content_md", "text_md", "content"):
            val = artifact.get(key)
            if isinstance(val, str) and val.strip():
                return val
    if isinstance(artifact, str) and artifact.strip():
        return artifact
    return None


async def _save_artifact_db(storage: CompositeAdapter, **kwargs) -> None:
    """Persiste l'artifact sur les adaptateurs DB (ext=.md/.llm.json) si node_id est un UUID."""
    node_id = kwargs.get("node_id")
    try:
        UUID(str(node_id))
    except Exception:
        log.debug("node_id non UUID, DB ignorée: %s", node_id)
        return

    adapters = getattr(storage, "adapters", None)
    if adapters:
        for ad in adapters:
            if getattr(ad, "expects_uuid_ids", False) and hasattr(ad, "save_artifact"):
                fn = getattr(ad, "save_artifact")
                if inspect.iscoroutinefunction(fn):
                    await fn(**kwargs)
                else:
                    fn(**kwargs)
    else:
        fn = getattr(storage, "save_artifact", None)
        if fn:
            if inspect.iscoroutinefunction(fn):
                await fn(**kwargs)
            else:
                fn(**kwargs)


# ---------- Exécution d'un nœud ----------------------------------------------

async def _execute_node(
    node: PlanNode,
    storage: CompositeAdapter,
    dag: TaskGraph,
    run_id: str,
    node_key: str,
    *,
    dry_run: bool = False,
    override: Dict[str, Any] | None = None,
) -> Dict[str, Any]:

    """Exécute un nœud du plan.

    Lorsque ``dry_run`` est à ``True`` on n'appelle pas réellement l'agent LLM
    mais on écrit quand même un sidecar minimimal contenant les informations
    d'exécution (backend, modèle, prompt, paramètres…).
    ``override`` permet de surcharger dynamiquement le prompt ou les paramètres
    du nœud.
    """

    node_log = logging.LoggerAdapter(log, {"run_id": run_id, "node_id": node_key})

    # Application éventuelle des overrides
    if override:
        node.llm = node.llm or {}
        if override.get("prompt") is not None:
            node.llm["prompt"] = override["prompt"]
        if override.get("params") is not None:
            node.llm["params"] = override["params"]

    role = node.suggested_agent_role if node.type != "manage" else "Manager_Generic"
    try:
        spec = resolve_agent(role)
    except KeyError:
        spec = recruit(role)
    node_log.debug(
        "node=%s role=%s provider=%s model=%s",
        node_key,
        role,
        spec.provider,
        spec.model,
    )

    # Assure le dossier FS du nœud
    ndir = fs_node_dir(run_id, node_key)
    ndir.mkdir(parents=True, exist_ok=True)

    if dry_run and node.type != "manage":
        # Construit un sidecar minimal sans appeler l'agent
        llm_conf = getattr(node, "llm", {}) or {}
        sidecar = {
            "backend": llm_conf.get("backend") or llm_conf.get("provider"),
            "model": llm_conf.get("model"),
            "prompt": llm_conf.get("prompt"),
            "params": llm_conf.get("params"),
            "inputs": llm_conf.get("inputs"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dry_run": True,
        }
        write_llm_sidecar(run_id, node_key, sidecar)
        return {}

    if node.type == "manage":
        nodes_iter = dag.nodes.values() if isinstance(dag.nodes, dict) else dag.nodes
        children = [n for n in nodes_iter if node.id in getattr(n, "deps", [])]
        if not children:
            minimal = {
                "assignments": [],
                "quality_checks": ["Aucun enfant à gérer pour ce nœud manage."],
                "integration_notes": "No-op manage node; no downstream tasks.",
            }
            (ndir / f"manager_{node_key}.json").write_text(
                json.dumps(minimal, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            return minimal
        subplan = [
            PlanNodeModel(
                id=n.id,
                title=n.title,
                type=n.type,
                suggested_agent_role=n.suggested_agent_role,
                acceptance=n.acceptance,
                deps=n.deps,
                risks=n.risks,
                assumptions=n.assumptions,
                notes=n.notes,
            )
            for n in children
        ]
        output = await run_manager(subplan)

        (ndir / f"manager_{node_key}.json").write_text(
            json.dumps(output.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return output.model_dump()

    # Sinon: agent "exécuteur" (LLM)
    if override:
        llm_conf = getattr(node, "llm", {}) or {}
        if override.get("prompt") is not None:
            llm_conf["prompt"] = override.get("prompt")
        if override.get("params") is not None:
            llm_conf["params"] = override.get("params")
        node.llm = llm_conf

    node_dbid = getattr(node, "db_id", None)

    if dry_run:
        meta = {
            "backend": (node.llm or {}).get("provider"),
            "model": (node.llm or {}).get("model"),
            "prompt": (node.llm or {}).get("prompt"),
            "params": (node.llm or {}).get("params", {}),
            "inputs": (node.llm or {}).get("inputs", {}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dry_run": True,
        }
        write_llm_sidecar(run_id, node_key, meta, node_id=str(node_dbid) if node_dbid else None)
        return {}

    artifact = await agent_runner(node)

    # Écrire éventuel markdown
    md = _extract_markdown_from_result(artifact)
    if md:
        write_md(run_id, node_key, md)
        if node_dbid:
            try:
                node_uuid = UUID(str(node_dbid))
                await _save_artifact_db(storage, node_id=node_uuid, content=md, ext=".md")
            except Exception:
                node_log.debug("node_db_id invalide, DB ignorée: %s", node_dbid)
        else:
            # Fallback legacy uniquement si les tests ont changé de CWD (tmpdir)
            if _is_pytest_tmp_cwd():
                Path(f"artifact_{node_key}.md").write_text(md, encoding="utf-8")

    # Écrire sidecar LLM systématique
    llm_conf = getattr(node, "llm", {}) or {}
    sidecar = {
        "backend": llm_conf.get("backend") or llm_conf.get("provider"),
        "model": llm_conf.get("model"),
        # priorité à l’override (llm_conf["prompt"]) ; sinon prompt final renvoyé par l’agent
        "prompt": llm_conf.get("prompt"),
        "params": llm_conf.get("params"),
        "inputs": llm_conf.get("inputs"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": False,
    }
    sidecar = {k: v for k, v in sidecar.items() if v is not None}
    meta = _extract_llm_meta_from_result(artifact)
    if meta:
        sidecar.update(meta)
    # si aucun override de prompt, on copie le prompt final de l’agent (s’il existe)
    if not sidecar.get("prompt"):
        sidecar["prompt"] = (sidecar.get("prompts", {}) or {}).get("final")
    if md:
        sidecar["markdown"] = md

    node_uuid_str = None
    if node_dbid:
        try:
            node_uuid_str = str(UUID(str(node_dbid)))
        except Exception:
            node_uuid_str = None
    sidecar = write_llm_sidecar(
        run_id, node_key, sidecar, node_id=node_uuid_str
    )

    if node_dbid and node_uuid_str:
        try:
            node_uuid = UUID(node_uuid_str)
            await _save_artifact_db(
                storage,
                node_id=node_uuid,
                content=json.dumps(sidecar, ensure_ascii=False, indent=2),
                ext=".llm.json",
            )
        except Exception:
            node_log.debug("node_db_id invalide, DB ignorée: %s", node_dbid)
    else:
        # Fallback legacy uniquement si les tests ont changé de CWD (tmpdir)
        if _is_pytest_tmp_cwd():
            Path(f"artifact_{node_key}.llm.json").write_text(
                json.dumps(sidecar, ensure_ascii=False, indent=2), encoding="utf-8"
            )

        if _is_pytest_tmp_cwd():
            Path(f"artifact_{node_key}.llm.json").write_text(
                json.dumps(sidecar, ensure_ascii=False, indent=2), encoding="utf-8"
            )

    node_log.info(
        "node=%s role=%s provider=%s model=%s latency_ms=%s",
        node_key,
        role,
        sidecar.get("provider") if sidecar else None,
        (sidecar.get("model") or sidecar.get("model_used")) if sidecar else None,
        sidecar.get("latency_ms") if sidecar else None,
    )

    return {"markdown": md, "llm": sidecar}


# ---------- Boucle d'exécution du DAG ----------------------------------------


async def _run_single_node(
    node: PlanNode,
    dag: TaskGraph,
    storage: CompositeAdapter,
    run_dir: Path,
    run_id: str,
    node_id_txt: str,
    *,
    dry_run: bool,
    on_node_start: Optional[Callable[..., Awaitable[None]]],
    on_node_end: Optional[Callable[..., Awaitable[None]]],
    skip_nodes: Set[str],
    overrides: Dict[str, Dict[str, Any]],
    override_completed: Set[str],
    max_retries: int,
    backoff_ms: int,
    pause_event: Optional[Any],
) -> Dict[str, Any]:
    node_log = logging.LoggerAdapter(log, {"run_id": run_id, "node_id": node_id_txt})
    if pause_event is not None:
        await pause_event.wait()
    _cs = _node_input_checksum(node)
    if hasattr(node, "checksum"):
        node.checksum = _cs
    node_dir = run_dir / "nodes" / node_id_txt
    node_dir.mkdir(parents=True, exist_ok=True)
    status_file = node_dir / "status.json"
    previous: Dict[str, Any] = {}
    if status_file.exists():
        try:
            previous = json.loads(status_file.read_text(encoding="utf-8"))
        except Exception:
            previous = {}
    prev_status = previous.get("status")
    prev_checksum = previous.get("input_checksum")

    must_recompute = True
    if prev_status == "completed" and prev_checksum == _cs and node_id_txt not in override_completed:
        must_recompute = False

    label = "exécution" if must_recompute else "skip (cache)"
    print(f"[RUN]    {node_id_txt} — {label}")

    if node_id_txt in skip_nodes:
        label = "skip (action)"
        print(f"[RUN]    {node_id_txt} — {label}")
        if on_node_start:
            try:
                await on_node_start(node, node_id_txt)
            except TypeError:
                await on_node_start(node)
        await _execute_node(
            node,
            storage,
            dag,
            run_id,
            node_id_txt,
            dry_run=True,
            override=overrides.get(node_id_txt),
        )
        status = "skipped"
        out = {
            "run_id": run_id,
            "node_id": node_id_txt,
            "status": status,
            "input_checksum": _cs,
            "ended_at": datetime.now(timezone.utc).isoformat(),
        }
        status_file.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        if on_node_end:
            try:
                await on_node_end(node, node_id_txt, status)
            except TypeError:
                await on_node_end(node, status)
        return {"status": status, "skipped": 1, "replayed": 0}

    if not must_recompute and dry_run:
        await _execute_node(
            node, storage, dag, run_id, node_id_txt, dry_run=True, override=overrides.get(node_id_txt)
        )
        if on_node_end:
            try:
                await on_node_end(node, node_id_txt, "skipped")
            except TypeError:
                await on_node_end(node, "skipped")
        return {"status": "skipped", "skipped": 1, "replayed": 0}

    if not must_recompute:
        return {"status": "skipped", "skipped": 1, "replayed": 0}

    if on_node_start:
        try:
            try:
                await on_node_start(node, node_id_txt)
            except TypeError:
                await on_node_start(node)
        except Exception as e:
            print(colorize(f"[HOOK-ERR] on_node_start: {e}", RED))

    status = "failed"
    replayed = 0
    attempt = 0
    result: Dict[str, Any] | None = None
    while True:
        attempt += 1
        t0 = perf_counter() if metrics_enabled() else None
        try:
            result = await _execute_node(
                node,
                storage,
                dag,
                run_id,
                node_id_txt,
                dry_run=dry_run,
                override=overrides.get(node_id_txt),
            )
            status = "completed"
            replayed = 1
            if node.type == "manage" and isinstance(result, dict):
                for assignment in result.get("assignments", []) or []:
                    node_id = assignment.get("node_id")
                    role = assignment.get("agent_role") or assignment.get("agent")
                    tooling = assignment.get("tooling") or []
                    if not node_id or node_id not in dag.nodes:
                        continue
                    target = dag.nodes[node_id]
                    if role:
                        target.suggested_agent_role = role
                    if tooling:
                        if getattr(target, "llm", None) is None:
                            target.llm = {}
                        target.llm["tooling"] = tooling
            break
        except Exception as e:
            traceback.print_exc()
            print(colorize(f"[ERR]    {node_id_txt} — {e}", RED))
            if os.getenv("SENTRY_DSN"):
                import sentry_sdk
                with sentry_sdk.push_scope() as scope:
                    if run_id:
                        scope.set_tag("run_id", run_id)
                    if node_id_txt:
                        scope.set_tag("node_id", node_id_txt)
                    llm_conf = getattr(node, "llm", {}) or {}
                    provider = llm_conf.get("provider")
                    model = llm_conf.get("model")
                    if provider:
                        scope.set_tag("provider", provider)
                    if model:
                        scope.set_tag("model", model)
                    sentry_sdk.capture_exception(e)
            if attempt <= max_retries:
                wait = (backoff_ms / 1000.0) * (2 ** (attempt - 1))
                node_log.warning("retrying in %.2f seconds (attempt %s/%s)", wait, attempt, max_retries)
                await asyncio.sleep(wait)
                continue
            else:
                status = "failed"
                break
        finally:
            if t0 is not None:
                dt = perf_counter() - t0
                role = node.suggested_agent_role or "unknown"
                provider = (
                    getattr(node, "provider", None)
                    or getattr(getattr(node, "meta", None), "provider", None)
                    or "na"
                )
                model = (
                    getattr(node, "model", None)
                    or getattr(getattr(node, "meta", None), "model", None)
                    or "na"
                )
                get_orchestrator_node_duration_seconds().labels(
                    role,
                    provider,
                    model,
                ).observe(dt)

    out = {
        "run_id": run_id,
        "node_id": node_id_txt,
        "status": status,
        "input_checksum": _cs,
        "ended_at": datetime.now(timezone.utc).isoformat(),
    }
    status_file.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    if on_node_end:
        try:
            try:
                await on_node_end(node, node_id_txt, status)
            except TypeError:
                await on_node_end(node, status)
        except Exception as e:
            print(colorize(f"[HOOK-ERR] on_node_end: {e}", RED))
    return {"status": status, "skipped": 0, "replayed": replayed}


async def run_graph(
    dag: TaskGraph,
    storage: CompositeAdapter,
    run_id: str,
    override_completed: Set[str] | None = None,
    dry_run: bool = False,
    on_node_start: Optional[Callable[..., Awaitable[None]]] = None,
    on_node_end: Optional[Callable[..., Awaitable[None]]] = None,
    pause_event: Optional[Any] = None,
    skip_nodes: Optional[Set[str]] = None,
    overrides: Optional[Dict[str, Dict[str, Any]]] = None,
):
    RUNS_ROOT = get_var("RUNS_ROOT", ".runs")
    Path(RUNS_ROOT).mkdir(parents=True, exist_ok=True)
    run_dir = Path(RUNS_ROOT) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    skip_nodes = skip_nodes or set()
    overrides = overrides or {}
    override_completed = override_completed or set()
    max_retries = int(get_var("NODE_MAX_RETRIES", 0))
    backoff_ms = int(get_var("NODE_BACKOFF_MS", 0))

    nodes_iter = dag.nodes.values() if isinstance(dag.nodes, dict) else dag.nodes
    pending = {n.id: n for n in nodes_iter}
    completed_ids: Set[str] = set()
    failed_ids: Set[str] = set()
    skipped_count = 0
    replayed_count = 0

    while pending:
        ready = [
            nid for nid, node in list(pending.items())
            if all(dep in completed_ids for dep in node.deps)
        ]
        if not ready:
            failed_ids.update(pending.keys())
            break
        tasks = [
            _run_single_node(
                pending[nid],
                dag,
                storage,
                run_dir,
                run_id,
                nid,
                dry_run=dry_run,
                on_node_start=on_node_start,
                on_node_end=on_node_end,
                skip_nodes=skip_nodes,
                overrides=overrides,
                override_completed=override_completed,
                max_retries=max_retries,
                backoff_ms=backoff_ms,
                pause_event=pause_event,
            )
            for nid in ready
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for nid, res in zip(ready, results):
            if isinstance(res, Exception):
                failed_ids.add(nid)
            else:
                skipped_count += res.get("skipped", 0)
                replayed_count += res.get("replayed", 0)
                if res.get("status") == "failed":
                    failed_ids.add(nid)
                else:
                    completed_ids.add(nid)
            pending.pop(nid, None)

    # Écrire un status "failed" pour les nœuds restants non exécutés
    for nid in failed_ids:
        node_dir = run_dir / "nodes" / nid
        node_dir.mkdir(parents=True, exist_ok=True)
        status_file = node_dir / "status.json"
        if not status_file.exists():
            _cs = _node_input_checksum(dag.nodes[nid])
            out = {
                "run_id": run_id,
                "node_id": nid,
                "status": "failed",
                "input_checksum": _cs,
                "ended_at": datetime.now(timezone.utc).isoformat(),
            }
            status_file.write_text(
                json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
            )

    now_utc = datetime.now(timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        now_paris = now_utc.astimezone(ZoneInfo("Europe/Paris"))
    except Exception:
        now_paris = now_utc

    summary = {
        "run_id": run_id,
        "completed": sorted(completed_ids),
        "failed": sorted(failed_ids),
        "skipped_count": skipped_count,
        "replayed_count": replayed_count,
        "utc_time": now_utc.isoformat(),
        "paris_time": now_paris.isoformat(),
    }
    summary_path = run_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    total = len(dag.nodes)
    if not failed_ids and len(completed_ids) == total:
        final_status = "succeeded"
    elif failed_ids and not completed_ids:
        final_status = "failed"
    else:
        final_status = "partial"

    return {
        "status": final_status,
        "completed": sorted(completed_ids),
        "failed": sorted(failed_ids),
        "run_id": run_id,
        "stats": {
            "succeeded": len(completed_ids),
            "failed": len(failed_ids),
            "skipped": skipped_count,
        },
    }
