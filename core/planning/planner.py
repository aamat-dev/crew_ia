async def build_plan(task_input: dict) -> dict:
    # Plan minimal (2 nœuds parallèles + 1 nœud qui dépend des 2)
    return {
        "decompose": True,
        "plan": [
            {"id": "n1", "title": "Analyse secteur A", "description": task_input.get("description",""), "type": "analysis", "deps": [], "acceptance": "Texte A"},
            {"id": "n2", "title": "Analyse secteur B", "description": task_input.get("description",""), "type": "analysis", "deps": [], "acceptance": "Texte B"},
            {"id": "n3", "title": "Synthèse", "description": "Fusion A+B", "type": "write", "deps": ["n1","n2"], "acceptance": "Synthèse prête"}
        ],
        "risks": [], "assumptions": [], "notes": []
    }
