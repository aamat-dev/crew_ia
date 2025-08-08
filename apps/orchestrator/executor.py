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
import argparse

from typing import Optional, Set
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from core.config import get_var
from core.storage.file_adapter import FileStatusStore
from core.agents.executor_llm import run_executor_llm

# --- ANSI couleurs pour la console ---
RESET = "\033[0m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"

def colorize(text, color):
    if get_var("NO_COLOR", "").lower() in ("1", "true", "yes"):
        return text
    return f"{color}{text}{RESET}"

def _node_input_checksum(node) -> str:
    payload = {
        "id": node.id,
        "title": getattr(node, "title", ""),
        "description": getattr(node, "description", ""),
        "type": getattr(node, "type", ""),
        "deps": list(getattr(node, "deps", [])),
        "acceptance": getattr(node, "acceptance", ""),
        "suggested_agent_role": getattr(node, "suggested_agent_role", ""),
    }
    s = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return "sha256:" + hashlib.sha256(s.encode("utf-8")).hexdigest()

async def run_graph(
    dag,
    storage,
    run_id: str,
    override_completed: Optional[Set[str]] = None,
    dry_run: bool = False,
):
    # Config lue à l'exécution
    RETRIES = int(get_var("NODE_RETRIES", 2))
    BASE_DELAY = float(get_var("RETRY_BASE_DELAY", 1.0))
    MAX_CONCURRENCY = int(get_var("MAX_CONCURRENCY", 3))
    RUNS_ROOT = get_var("RUNS_ROOT", ".runs")

    override_completed = override_completed or set()
    status = FileStatusStore(runs_root=RUNS_ROOT)

    skipped_count = 0
    replayed_count = 0

    # 🔎 PRE-SCAN en mode dry-run (affiche la décision pour TOUS les nœuds) puis sort
    if dry_run:
        print("🔎 Pré-scan dry-run (comparaison checksum / cache) :")
        for nid, node in dag.nodes.items():
            st = status.read(run_id, nid)
            checksum = _node_input_checksum(node)
            if st and st.status == "completed" and st.input_checksum == checksum and nid not in override_completed:
                print(f"{GREEN}[SKIP]{RESET}   {nid} — checksum identique")
                skipped_count += 1
            else:
                raisons = []
                if not st or st.status != "completed":
                    raisons.append("pas encore terminé")
                if st and st.input_checksum != checksum:
                    raisons.append("checksum différent")
                if nid in override_completed:
                    raisons.append("forcé par override")
                raison_txt = " / ".join(raisons) or "recalcul"
                print(f"{YELLOW}[RECALC]{RESET} {nid} — {raison_txt}")
                replayed_count += 1
        print(f"{CYAN}📊 Bilan : {skipped_count} skippé(s), {replayed_count} rejoué(s).{RESET}")
        return {"status": "success", "completed": list(dag.nodes.keys()), "run_id": run_id}
    
    # Pré-calculs pour l'exécution réelle
    completed_ids: Set[str] = set()
    for nid, node in dag.nodes.items():
        st = status.read(run_id, nid)
        if (
            st and st.status == "completed"
            and st.input_checksum == _node_input_checksum(node)
            and nid not in override_completed
        ):
            completed_ids.add(nid)

    pending_ids: Set[str] = set(dag.nodes.keys())  # enfile tout, l’éligibilité dépendra des deps
    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    async def run_one(node):
        nonlocal skipped_count, replayed_count
        node_id = node.id
        checksum = _node_input_checksum(node)
        st = status.read(run_id, node_id)

        must_skip = (
            st and st.status == "completed"
            and node_id not in override_completed
            and st.input_checksum == checksum
        )

        if must_skip:
            print(f"{GREEN}[SKIP]{RESET}   {node_id} — checksum identique")
            skipped_count += 1
            return True, "skipped"
        
        print(f"{YELLOW}[RUN]{RESET}    {node_id} — exécution (checksum différent ou pas encore terminé)")
        replayed_count += 1

        attempt = 0
        
        while attempt <= RETRIES:
            status.mark_in_progress(run_id, node_id, input_checksum=checksum)
            try:
                async with sem:
                    ok = await run_executor_llm(node, storage=storage)
                if ok is True:
                    status.mark_completed(run_id, node_id)
                    return True, "executed"
                else:
                    raise RuntimeError("Worker returned False")
            except Exception as e:
                attempt += 1
                tb = traceback.format_exc(limit=3)
                status.mark_failed(run_id, node_id, f"{type(e).__name__}: {e}\n{tb}")
                if attempt > RETRIES:
                    return False, "failed"
                await asyncio.sleep(BASE_DELAY * (2 ** (attempt - 1)))

    # Boucle de scheduling
    while pending_ids:
        ready_ids = []
        for nid in list(pending_ids):
            deps_ok = True
            for dep_id in dag.nodes[nid].deps:
                if dep_id in completed_ids:
                    continue
                st_dep = status.read(run_id, dep_id)
                same_checksum = False
                if st_dep and st_dep.status == "completed":
                    # la dépendance est "vraiment" complétée seulement si son checksum n'a pas changé et pas d'override
                    same_checksum = (st_dep.input_checksum == _node_input_checksum(dag.nodes[dep_id])) and (dep_id not in override_completed)
                if not same_checksum:
                    deps_ok = False
                    break
            if deps_ok:
                ready_ids.append(nid)
        if not ready_ids:
            return {"status": "failed", "reason": "deadlock_or_blocked", "run_id": run_id}

        results = await asyncio.gather(*(run_one(dag.nodes[nid]) for nid in ready_ids))
        for nid, (ok, _how) in zip(ready_ids, results):
            pending_ids.remove(nid)
            if ok:
                completed_ids.add(nid)
            else:
                return {"status": "failed", "failed_nodes": [nid], "run_id": run_id}

    now_utc = datetime.now(tz=ZoneInfo("UTC"))
    now_paris = now_utc.astimezone(ZoneInfo("Europe/Paris"))

    print(colorize(f"📊 Bilan : {skipped_count} skippé(s), {replayed_count} rejoué(s).", CYAN))
    print(colorize(f"🕒 Heure UTC   : {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}", CYAN))
    print(colorize(f"🕒 Heure Paris : {now_paris.strftime('%Y-%m-%d %H:%M:%S %Z')}", CYAN))

    # Sauvegarde JSON résumé
    summary = {
        "run_id": run_id,
        "completed": sorted(completed_ids),
        "skipped_count": skipped_count,
        "replayed_count": replayed_count,
        "utc_time": now_utc.isoformat(),
        "paris_time": now_paris.isoformat()
    }
    summary_path = Path(RUNS_ROOT) / run_id / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(colorize(f"💾 Résumé sauvegardé : {summary_path}", CYAN))


    print(f"{CYAN}📊 Bilan : {skipped_count} skippé(s), {replayed_count} rejoué(s).{RESET}")
    return {"status": "success", "completed": sorted(completed_ids), "run_id": run_id}