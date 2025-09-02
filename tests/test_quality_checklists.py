import json
import math
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

SCHEMA_PATH = Path("quality/schemas/checklist-1.0.schema.json")
CHECKLISTS_DIR = Path("quality/checklists/1.0.0")

@pytest.fixture(scope="module")
def schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _load_checklist(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_checklists_exist():
    assert CHECKLISTS_DIR.exists(), "Checklists directory missing"
    files = list(CHECKLISTS_DIR.glob("qa.*.v1.json"))
    assert {"qa.write.v1.json","qa.research.v1.json","qa.build.v1.json","qa.review.v1.json"}.issubset(
        {p.name for p in files}
    )

def test_checklists_schema(schema):
    validator = Draft202012Validator(schema)
    for p in CHECKLISTS_DIR.glob("qa.*.v1.json"):
        data = _load_checklist(p)
        errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
        assert not errors, f"Schema errors in {p.name}: " + "; ".join(e.message for e in errors)

def test_weights_sum_to_one():
    for p in CHECKLISTS_DIR.glob("qa.*.v1.json"):
        data = _load_checklist(p)
        total = sum(c["weight"] for c in data["criteria"])
        assert math.isclose(total, 1.0, rel_tol=1e-9, abs_tol=1e-9), f"Weights must sum to 1.0 in {p.name}"

def test_criterion_ids_unique():
    for p in CHECKLISTS_DIR.glob("qa.*.v1.json"):
        data = _load_checklist(p)
        ids = [c["id"] for c in data["criteria"]]
        assert len(ids) == len(set(ids)), f"Duplicate criterion id in {p.name}"
