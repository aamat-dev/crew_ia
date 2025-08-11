# tests/test_normalize_super_plan.py
import importlib
import types

def get_normalize():
    # importer dynamiquement le module main pour récupérer la fonction
    mod = importlib.import_module("apps.orchestrator.main")
    assert hasattr(mod, "_normalize_supervisor_plan")
    return mod._normalize_supervisor_plan

def test_normalize_with_subtasks():
    normalize = get_normalize()
    super_plan = {
        "decompose": True,
        "subtasks": [
            {"title": "A", "description": "da"},
            {"title": "B", "description": "db"},
            {"title": "C", "description": "dc"},
        ]
    }
    plan = normalize(super_plan, title="T")
    assert plan["title"] == "T"
    assert [n["id"] for n in plan["plan"]] == ["n1","n2","n3"]
    assert plan["plan"][0]["deps"] == []
    assert plan["plan"][1]["deps"] == ["n1"]
    assert plan["plan"][2]["deps"] == ["n2"]

def test_normalize_with_plan_strings():
    normalize = get_normalize()
    super_plan = {
        "decompose": True,
        "plan": ["Etape 1", "Etape 2"]
    }
    plan = normalize(super_plan, title="T")
    assert [n["title"] for n in plan["plan"]] == ["Etape 1", "Etape 2"]

def test_normalize_empty_fallback():
    normalize = get_normalize()
    super_plan = {}
    plan = normalize(super_plan, title="T")
    assert len(plan["plan"]) == 1
    assert plan["plan"][0]["id"] == "n1"
