"""
executor.py — Exécute un DAG avec gestion de reprise + checksum des inputs.
- Skip seulement si: status == completed ET input_checksum identique (sauf override).
- --dry-run: affiche [SKIP]/[RECALC] pour tous les nœuds et n'exécute rien.
"""
from __future__ import annotations

import json
import traceback
import logging
from typing import Optional, Set, Callable, Awaitable, Dict, Any
from datetime import datetime, timezone
from pathlib import Path

from core.config import get_var
from core.planning.task_graph import TaskGraph, PlanNode
from core.storage.db_models import NodeStatus  # peut rester importé si réutilisé ailleurs
from core.storage.composite_adapter import CompositeAdapter
from core.agents.executor_llm import run_executor_llm

log = logging.getLogger("crew.executor")

RESET = "\033[0m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"


def colorize(msg: str, color: str) -> str:
    return f"{color}{msg}{RESET}"


def _node_input_checksum(node) -> str:
    """
    Calcule un checksum stable en acceptant:
      - PlanNode (avec .title/.key/.params/.deps)
      - dict (keys semblables)
      - str (titre brut)
    NE FAIT AUCUNE ASSUMPTION sur la présence de .deps / .title etc.
    """
    import hashlib, json

    def _get(obj, attr, default=None):
        # attr depuis objet (getattr) ou dict (get), sinon default
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)

    # Champs "soft"
    title = _get(node, "title")
    if callable(title):
        title = None
    key = _get(node, "key")
    params = _get(node, "params", {}) or {}

    # deps peut ne pas exister (str), ne pas être list, etc.
    raw_deps = _get(node, "deps", []) or []
    if not isinstance(raw_deps, (list, tuple)):
        raw_deps = [raw_deps]
    # Normaliser les deps pour le hash (identifiants lisibles)
    norm_deps = []
    for d in raw_deps:
        if isinstance(d, str):
            norm_deps.append(d)
        elif isinstance(d, dict):
            norm_deps.append(d.get("key") or d.get("title") or "")
        else:
            # objet PlanNode-like
            nk = getattr(d, "key", None)
            nt = getattr(d, "title", None)
            if callable(nt):
                nt = None
            norm_deps.append(nk or nt or "")

    # Si node est str, on la prend comme titre
    if title is None and isinstance(node, str):
        title = node

    # Construire un payload stable pour hashing
    payload = {
        "title": title or "",
        "key": key or "",
        "params": params,
        "deps": norm_deps,
    }

    h = hashlib.sha256()
    h.update(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    return h.hexdigest()


def _get_attr(node, name, default=""):
    """
    Accès tolérant aux attributs d'un nœud (PlanNode | dict | str).
    - Si dict: lit node[name]
    - Si objet: getattr(node, name)
    - Si valeur est callable (ex: str.title), on renvoie default
    """
    if isinstance(node, dict):
        val = node.get(name, default)
    else:
        val = getattr(node, name, default)
    return default if callable(val) else val


def _node_id_str(node, checksum: str) -> str:
    """
    Retourne un identifiant *texte* pour le nœud.
    - Si le nœud a un .id (UUID/str), on l'utilise.
    - Sinon on dérive un id déterministe à partir du checksum (stable).
    """
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
    """
    Normalise la liste des deps en une liste d'identifiants texte.
    Accepte deps en str/dict/objets PlanNode.
    """
    raw = _get_attr(node, "deps", []) or []
    if not isinstance(raw, (list, tuple)):
        raw = [raw]
    out: list[str] = []
    for d in raw:
        d_cs = _node_input_checksum(d)
        out.append(_node_id_str(d, d_cs))
    return out


async def _execute_node(node: PlanNode, storage: CompositeAdapter) -> Dict[str, Any]:
    # Pour l’instant, exécuteur LLM unique
    return await run_executor_llm(node=node, storage=storage)


async def run_graph(
    dag: TaskGraph,
    storage: CompositeAdapter,
    run_id: str,
    override_completed: Set[str] | None = None,
    dry_run: bool = False,
    on_node_start: Optional[Callable[..., Awaitable[None]]] = None,
    on_node_end: Optional[Callable[..., Awaitable[None]]] = None,
):
    RUNS_ROOT = get_var("RUNS_ROOT", ".runs")
    Path(RUNS_ROOT).mkdir(parents=True, exist_ok=True)

    completed_ids: Set[str] = set()
    skipped_count = 0
    replayed_count = 0

    # exécution topologique simple (le DAG produit déjà un ordre valable)
    for node in dag.nodes:
        # Préparation (tolérante aux str/dict)
        log.debug(
            "Preparing node: key=%s title=%s deps=%s",
            _get_attr(node, "key"),
            _get_attr(node, "title"),
            _get_attr(node, "deps", []),
        )
        _cs = _node_input_checksum(node)
        if hasattr(node, "checksum"):
            node.checksum = _cs

        node_id_txt = _node_id_str(node, _cs)
        node_dir = Path(RUNS_ROOT) / run_id / "nodes" / node_id_txt
        node_dir.mkdir(parents=True, exist_ok=True)
        status_file = node_dir / "status.json"

        previous: Dict[str, Any] = {}
        if status_file.exists():
            try:
                previous = json.loads(status_file.read_text(encoding="utf-8"))
            except Exception:
                previous = {}

        prev_status = previous.get("status")
        prev_checksum = previous.get("checksum")

        # Dépendances: si une dep a échoué, on s'arrête
        dep_ids = _norm_dep_ids(node)
        if any(dep not in completed_ids for dep in dep_ids):
            print(colorize(f"[BLOCK]  {node_id_txt} — dépendances incomplètes", YELLOW))
            continue

        must_recompute = True
        if prev_status == "completed" and prev_checksum == _cs and node_id_txt not in (override_completed or set()):
            must_recompute = False

        label = "exécution" if must_recompute else "skip (cache)"
        print(f"[RUN]    {node_id_txt} — {label}")

        if not must_recompute and dry_run:
            skipped_count += 1
            continue
        if not must_recompute:
            skipped_count += 1
            completed_ids.add(node_id_txt)
            continue

        # start hook (tolérant: tente (node, node_id_txt), sinon (node))
        if on_node_start:
            try:
                try:
                    await on_node_start(node, node_id_txt)  # nouvelle signature
                except TypeError:
                    await on_node_start(node)  # rétro-compat
            except Exception as e:
                print(colorize(f"[HOOK-ERR] on_node_start: {e}", RED))

        # Exécution du nœud
        status = "failed"
        try:
            _ = await _execute_node(node, storage)
            status = "completed"
            replayed_count += 1
            completed_ids.add(node_id_txt)
        except Exception as e:
            traceback.print_exc()
            print(colorize(f"[ERR]    {node_id_txt} — {e}", RED))
            status = "failed"

        # Persiste statut file-based (toujours)
        out = {
            "status": status,
            "checksum": _cs,
            "ended_at": datetime.now(timezone.utc).isoformat(),
        }
        status_file.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

        # end hook (tolérant: tente (node, node_id_txt, status), sinon (node, status))
        if on_node_end:
            try:
                try:
                    await on_node_end(node, node_id_txt, status)  # nouvelle signature
                except TypeError:
                    await on_node_end(node, status)  # rétro-compat
            except Exception as e:
                print(colorize(f"[HOOK-ERR] on_node_end: {e}", RED))

    # résumé
    now_utc = datetime.now(timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Europe/Paris")
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
        "paris_time": now_paris.isoformat(),
    }
    summary_path = Path(RUNS_ROOT) / run_id / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(colorize(f"💾 Résumé sauvegardé : {summary_path}", CYAN))

    print(f"{CYAN}📊 Bilan : {skipped_count} skippé(s), {replayed_count} rejoué(s).{RESET}")
    return {"status": "success", "completed": sorted(completed_ids), "run_id": run_id}
