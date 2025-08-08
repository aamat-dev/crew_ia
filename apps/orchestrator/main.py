"""
apps/orchestrator/main.py — Lance l'orchestrateur sur un plan JSON.
Usage :
  python -m apps.orchestrator.main --task-file examples/task_rapport_80p.json
  python -m apps.orchestrator.main --task-file plan.json --run-id 2025-08-08T16-40Z_demo
Reprise :
  python -m apps.orchestrator.main --task-file plan.json --run-id 2025-08-08T16-40Z_demo --resume
Forcer la relance de nœuds déjà completed :
  python -m apps.orchestrator.main --task-file plan.json --override n2 --override n5
"""

from __future__ import annotations
import argparse
import json
import os
from datetime import datetime, timezone
from typing import List, Set

from core.config import get_var
from core.planning.task_graph import TaskGraph
from core.storage.file_adapter import FileStorage
from apps.orchestrator.executor import run_graph


def _default_run_id(hint: str | None = None) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    if hint:
        # slug très simple
        hint = "".join(c if c.isalnum() or c in "-_" else "_" for c in hint)[:40]
        return f"{ts}_{hint}"
    return ts


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Orchestrateur CrewIA — exécution d'un plan avec reprise après crash")
    p.add_argument("--task-file", required=True, help="Chemin vers un JSON contenant la clé 'plan'")
    p.add_argument("--run-id", default=None, help="Identifiant stable du run (requis pour --resume)")
    p.add_argument("--title", default=None, help="Indice lisible pour générer un run_id par défaut")
    p.add_argument("--resume", action="store_true", help="Reprendre un run existant (nécessite --run-id)")
    p.add_argument("--override", action="append", default=[], help="Node ID à relancer même s'il est 'completed' (répéter l'option)")
    p.add_argument("--dry-run", action="store_true", help="Affiche les décisions de skip/recalc sans exécuter les nœuds"
)
    return p.parse_args()


def main() -> None:
    args = parse_args()

    # Chargement du plan
    with open(args.task_file, "r", encoding="utf-8") as f:
        plan_dict = json.load(f)

    graph = TaskGraph.from_plan(plan_dict)

    if not graph.nodes:
        raise SystemExit("❌ Le plan est vide ou mal formé (clé 'plan' absente ou liste vide).")

    # Gestion du run_id
    run_id = args.run_id or _default_run_id(args.title or plan_dict.get("title") or "run")
    if args.resume and not args.run_id:
        raise SystemExit("❌ --resume nécessite de spécifier --run-id (pour reprendre exactement le même run).")

    # Dossiers .runs
    runs_root = get_var("RUNS_ROOT", ".runs")
    run_dir = os.path.join(runs_root, run_id)
    os.makedirs(run_dir, exist_ok=True)

    # Sauvegarde du plan pour traçabilité
    plan_out = os.path.join(run_dir, "plan.json")
    with open(plan_out, "w", encoding="utf-8") as f:
        json.dump(plan_dict, f, ensure_ascii=False, indent=2)

    # Storage pour artifacts
    storage = FileStorage(base_dir=run_dir)

    # Overrides (liste -> set)
    override_completed: Set[str] = set(args.override or [])

    print(f"▶️  Run ID     : {run_id}")
    print(f"📁 Runs root  : {runs_root}")
    print(f"🗂  Run dir    : {run_dir}")
    if override_completed:
        print(f"♻️  Overrides  : {sorted(override_completed)}")
    if args.resume:
        print("🔁 Reprise activée (les nœuds déjà 'completed' seront SKIP, sauf override).")

    # Exécution
    import asyncio
    result = asyncio.run(
        run_graph(
            dag=graph,
            storage=storage,
            run_id=run_id,
            override_completed=override_completed,
            dry_run=args.dry_run
        )
    )

    status = result.get("status")
    if status == "success":
        completed = result.get("completed", [])
        print(f"✅ Succès — {len(completed)} nœud(s) complété(s).")
    else:
        print(f"❌ Échec — details: {result}")


if __name__ == "__main__":
    main()
