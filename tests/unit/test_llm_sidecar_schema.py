import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "llm_sidecar.schema.json"
EXAMPLES_DIR = ROOT / "schemas" / "examples"


@pytest.fixture(scope="module")
def validator():
    with SCHEMA_PATH.open("r", encoding="utf-8") as fh:
        schema = json.load(fh)
    return Draft202012Validator(schema, format_checker=FormatChecker())


@pytest.fixture()
def minimal_payload():
    return {
        "version": "1.0",
        "provider": "openai",
        "model": "gpt-4o",
        "latency_ms": 0,
        "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        "cost": {"estimated": 0},
        "prompts": {"system": "", "user": "hi"},
        "timestamps": {
            "started_at": "2024-05-21T10:00:00Z",
            "ended_at": "2024-05-21T10:00:01Z",
        },
        "run_id": "123e4567-e89b-42d3-a456-426614174000",
        "node_id": "123e4567-e89b-42d3-a456-426614174001",
    }


def test_examples_valid(validator):
    path = EXAMPLES_DIR / "llm_sidecar.valid.json"
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    validator.validate(data)


def test_examples_invalid(validator):
    path = EXAMPLES_DIR / "llm_sidecar.invalid.json"
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    errors = list(validator.iter_errors(data))
    assert errors
    messages = [e.message for e in errors]
    assert any("latency_ms" in msg for msg in messages)
    assert any(list(e.path) == ["run_id"] for e in errors)


def test_prompts_user_array_valid(validator, minimal_payload):
    payload = deepcopy(minimal_payload)
    payload["prompts"]["user"] = [{"role": "user", "content": "hi"}]
    validator.validate(payload)


def test_unknown_provider_invalid(validator, minimal_payload):
    payload = deepcopy(minimal_payload)
    payload["provider"] = "foo"
    errors = list(validator.iter_errors(payload))
    assert any(list(e.path) == ["provider"] for e in errors)


def test_malformed_timestamp_invalid(validator, minimal_payload):
    payload = deepcopy(minimal_payload)
    payload["timestamps"]["started_at"] = "not-a-timestamp"
    errors = list(validator.iter_errors(payload))
    assert any(list(e.path) == ["timestamps", "started_at"] for e in errors)
