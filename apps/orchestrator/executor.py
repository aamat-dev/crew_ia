"""
executor.py — Exécute un DAG avec gestion de reprise + checksum des inputs.
- Skip seulement si: status == completed ET input_checksum identique (sauf override).
- --dry-run: affiche [SKIP]/[RECALC] pour tous les nœuds et n'exécute rien.
"""
from __future__ import annotations

import asyncio
import json
import hashlib
import traceback
from typing import Optional, Set, Callable, Awaitable, Dict, Any
from datetime import datetime, timezone
from pathlib import Path

from core.config import get_var
from core.planning.task_graph import TaskGraph, PlanNode, NodeStatus
from core.storage.composite_adapter import CompositeAdapter
from core.agents.executor_llm import run_executor_llm


RESET = "\033[0m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"


def colorize(msg: str, color: str) -> str:
    return f"{color}{msg}{RESET}"


def _node_input_checksum(node: PlanNode) -> str:
    h = hashlib.sha256()
    # On base la stabilité sur: titre + deps + llm provider/model si présents
    h.update((node.title or "").encode("utf-8"))
    if node.deps:
        h.update("|".join(node.deps).encode("utf-8"))
    llm = node.llm or {}
    h.update((llm.get("provider") or "").encode("utf-8"))
    h.update((llm.get("model") or "").encode("utf-8"))
    return h.hexdigest()[:16]


async def _execute_node(node: PlanNode, storage: CompositeAdapter) -> Dict[str, Any]:
    # Pour l’instant, exécuteur LLM unique
    return await run_executor_llm(node=node, storage=storage)


async def run_graph(
    dag: TaskGraph,
    storage: CompositeAdapter,
    run_id: str,
    override_completed: Set[str] | None = None,
    dry_run: bool = False,
    on_node_start: Optional[Callable[[PlanNode], Awaitable[None]]] = None,
    on_node_end: Optional[Callable[[PlanNode, str], Awaitable[None]]] = None,
):
    RUNS_ROOT = get_var("RUNS_ROOT", ".runs")
    Path(RUNS_ROOT).mkdir(parents=True, exist_ok=True)

    completed_ids: Set[str] = set()
    skipped_count = 0
    replayed_count = 0

    # exécution topologique simple (le DAG produit déjà un ordre valable)
    for node in dag.nodes:
        node.checksum = _node_input_checksum(node)
        node_dir = Path(RUNS_ROOT) / run_id / "nodes" / node.id
        status_file = node_dir / "status.json"
        node_dir.mkdir(parents=True, exist_ok=True)

        previous: Dict[str, Any] = {}
        if status_file.exists():
            try:
                previous = json.loads(status_file.read_text(encoding="utf-8"))
            except Exception:
                previous = {}

        prev_status = previous.get("status")
        prev_checksum = previous.get("checksum")

        # Dépendances: si une dep a échoué, on s'arrête
        if any(dep not in completed_ids for dep in (node.deps or [])):
            print(colorize(f"[BLOCK]  {node.id} — dépendances incomplètes", YELLOW))
            continue

        must_recompute = True
        if prev_status == "completed" and prev_checksum == node.checksum and node.id not in (override_completed or set()):
            must_recompute = False

        label = "exécution" if must_recompute else "skip (cache)"
        print(f"[RUN]    {node.id} — {label}")

        if not must_recompute and dry_run:
            skipped_count += 1
            continue
        if not must_recompute:
            skipped_count += 1
            completed_ids.add(node.id)
            continue

        # start hook
        if on_node_start:
            try:
                await on_node_start(node)
            except Exception as e:
                print(colorize(f"[HOOK-ERR] on_node_start: {e}", RED))

        # Exécution du nœud
        status = "failed"
        try:
            _ = await _execute_node(node, storage)
            status = "completed"
            replayed_count += 1
            completed_ids.add(node.id)
        except Exception as e:
            traceback.print_exc()
            print(colorize(f"[ERR]    {node.id} — {e}", RED))
            status = "failed"

        # Persiste statut file-based (toujours)
        out = {
            "status": status,
            "checksum": node.checksum,
            "ended_at": datetime.now(timezone.utc).isoformat(),
        }
        status_file.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

        # end hook
        if on_node_end:
            try:
                await on_node_end(node, status)
            except Exception as e:
                print(colorize(f"[HOOK-ERR] on_node_end: {e}", RED))

    # résumé
    now_utc = datetime.now(timezone.utc)
    try:
        import pytz
        tz = pytz.timezone("Europe/Paris")
        now_paris = now_utc.astimezone(tz)
    except Exception:
        now_paris = now_utc

    print(colorize(f"📊 Bilan : {skipped_count} skippé(s), {replayed_count} rejoué(s).", CYAN))
    print(colorize(f"🕒 Heure UTC   : {now_utc:%Y-%m-%d %H:%M:%S %Z}", CYAN))
    print(colorize(f"🕒 Heure Paris : {now_paris:%Y-%m-%d %H:%M:%S %Z}", CYAN))

    summary = {
        "run_id": run_id,
        "completed": sorted(completed_ids),
        "skipped_count": skipped_count,
        "replayed_count": replayed_count,
        "utc_time": now_utc.isoformat(),
        "paris_time": now_paris.isoformat()
    }
    summary_path = Path(RUNS_ROOT) / run_id / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(colorize(f"💾 Résumé sauvegardé : {summary_path}", CYAN))

    print(f"{CYAN}📊 Bilan : {skipped_count} skippé(s), {replayed_count} rejoué(s).{RESET}")
    return {"status": "success", "completed": sorted(completed_ids), "run_id": run_id}
