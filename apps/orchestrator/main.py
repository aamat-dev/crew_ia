# apps/orchestrator/main.py
from __future__ import annotations

"""
Lance l'orchestrateur sur un plan JSON ou généré par le superviseur.
Usage :
  python -m apps.orchestrator.main --task-file examples/task_rapport_80p.json
  python -m apps.orchestrator.main --use-supervisor --title "Rapport 80p"
Reprise :
  python -m apps.orchestrator.main --task-file plan.json --run-id 2025-08-08T16-40Z_demo --resume
Override :
  python -m apps.orchestrator.main --task-file plan.json --override n2 --override n5
"""

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from typing import Set

from core.config import get_var
from core.planning.task_graph import TaskGraph
from core.storage.file_adapter import FileStorage
from apps.orchestrator.executor import run_graph
from core.agents import supervisor
from core.telemetry.logging_setup import setup_logging


def _normalize_supervisor_plan(super_plan: dict, title: str) -> dict:
    """
    Transforme la sortie du superviseur en plan JSON compatible TaskGraph:
    - Crée des nœuds n1..nK linéaires (chaînés) à partir de super_plan["subtasks"] ou super_plan["plan"].
    """
    items = []
    if isinstance(super_plan.get("subtasks"), list) and super_plan["subtasks"]:
        for i, st in enumerate(super_plan["subtasks"], start=1):
            node_id = f"n{i}"
            node_title = st.get("title") or f"Tâche {i}"
            deps = [f"n{i-1}"] if i > 1 else []
            items.append({"id": node_id, "title": node_title, "deps": deps})
    elif isinstance(super_plan.get("plan"), list) and super_plan["plan"]:
        for i, t in enumerate(super_plan["plan"], start=1):
            node_id = f"n{i}"
            node_title = str(t)
            deps = [f"n{i-1}"] if i > 1 else []
            items.append({"id": node_id, "title": node_title, "deps": deps})
    else:
        items = [{"id": "n1", "title": "Tâche 1", "deps": []}]
    return {"title": title, "plan": items}


def _default_run_id(hint: str | None = None) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    if hint:
        hint = "".join(c if c.isalnum() or c in "-_" else "_" for c in hint)[:40]
        return f"{ts}_{hint}"
    return ts


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Orchestrateur CrewIA — exécution d'un plan avec reprise après crash")
    # plan fichier
    p.add_argument("--task-file", required=False, help="Chemin vers un JSON contenant la clé 'plan'")
    p.add_argument("--run-id", default=None, help="Identifiant stable du run (requis pour --resume)")
    p.add_argument("--run-title-hint", default=None, help="Indice lisible pour générer un run_id par défaut (si plan fichier)")

    p.add_argument("--resume", action="store_true", help="Reprendre un run existant (nécessite --run-id)")
    p.add_argument("--override", action="append", default=[], help="Node ID à relancer même s'il est 'completed'")
    p.add_argument("--dry-run", action="store_true", help="Affiche les décisions de skip/recalc sans exécuter")

    # génération via superviseur
    p.add_argument("--use-supervisor", action="store_true", help="Génère le plan via le superviseur LLM")
    p.add_argument("--title", default="Rapport 80p", help="Titre racine pour le superviseur")
    p.add_argument("--description", default="Décomposer la production d'un rapport de 80 pages.", help="Description")
    p.add_argument("--acceptance", default="Un plan séquencé avec sous-tâches claires.", help="Critères d'acceptance")

    # overrides LLM globaux (injection au niveau des nœuds)
    p.add_argument("--executor-provider", default=None)
    p.add_argument("--executor-model", default=None)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    runs_root = get_var("RUNS_ROOT", ".runs")

    # ---------- Construire plan_dict + run_id + run_dir ----------
    if args.use_supervisor:
        run_id = args.run_id or _default_run_id(args.title)
        run_dir = os.path.join(runs_root, run_id)
        os.makedirs(run_dir, exist_ok=True)

        # Init logging de RUN (accessible partout après)
        logger = setup_logging(run_dir, logger_name="crew")

        storage = FileStorage(base_dir=run_dir)

        # 1) appelle le superviseur
        import asyncio
        task = {"title": args.title, "description": args.description, "acceptance": args.acceptance}
        super_plan = asyncio.run(supervisor.run(task, storage))

        # 2) normalise en plan TaskGraph
        plan_dict = _normalize_supervisor_plan(super_plan, title=args.title)

        # 3) éventuels overrides injectés sur chaque nœud
        if args.executor_provider or args.executor_model:
            for p in plan_dict.get("plan", []):
                llm = p.setdefault("llm", {})
                if args.executor_provider:
                    llm["provider"] = args.executor_provider
                if args.executor_model:
                    llm["model"] = args.executor_model

        # 4) traçabilité du plan
        plan_out = os.path.join(run_dir, "plan.json")
        with open(plan_out, "w", encoding="utf-8") as f:
            json.dump(plan_dict, f, ensure_ascii=False, indent=2)

    else:
        if not args.task_file:
            raise SystemExit("❌ --task-file est requis si --use-supervisor n'est pas passé.")
        with open(args.task_file, "r", encoding="utf-8") as f:
            plan_dict = json.load(f)

        run_id = args.run_id or _default_run_id(args.run_title_hint or plan_dict.get("title") or "run")
        if args.resume and not args.run_id:
            raise SystemExit("❌ --resume nécessite de spécifier --run-id.")
        run_dir = os.path.join(runs_root, run_id)
        os.makedirs(run_dir, exist_ok=True)

        # Init logging de RUN
        logger = setup_logging(run_dir, logger_name="crew")

        # Sauvegarde copie du plan source dans le run
        plan_out = os.path.join(run_dir, "plan.json")
        with open(plan_out, "w", encoding="utf-8") as f:
            json.dump(plan_dict, f, ensure_ascii=False, indent=2)

        storage = FileStorage(base_dir=run_dir)

    # ---------- Suite commune : build DAG + exécution ----------
    graph = TaskGraph.from_plan(plan_dict)
    if not graph.nodes:
        raise SystemExit("❌ Le plan est vide ou mal formé (clé 'plan' absente ou liste vide).")

    override_completed: Set[str] = set(args.override or [])

    print(f"▶️  Run ID     : {run_id}")
    print(f"📁 Runs root  : {runs_root}")
    print(f"🗂  Run dir    : {run_dir}")
    if override_completed:
        print(f"♻️  Overrides  : {sorted(override_completed)}")
    if args.resume:
        print("🔁 Reprise activée (les nœuds déjà 'completed' seront SKIP, sauf override).")

    # Logs run
    logger.info("Plan nodes: %d", len(graph.nodes))
    if override_completed:
        logger.info("Overrides: %s", sorted(override_completed))
    logger.debug(
        "Env LLM_DEFAULT_PROVIDER=%s LLM_DEFAULT_MODEL=%s",
        get_var("LLM_DEFAULT_PROVIDER"), get_var("LLM_DEFAULT_MODEL")
    )

    # Exécution
    import asyncio
    result = asyncio.run(
        run_graph(
            dag=graph,
            storage=storage,
            run_id=run_id,
            override_completed=override_completed,
            dry_run=args.dry_run,
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
