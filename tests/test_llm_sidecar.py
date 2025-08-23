import json
from pathlib import Path

from apps.orchestrator.api_runner import _read_llm_sidecar_fs, _normalize_llm_sidecar


def _write_sidecar(base: Path, run_id: str, node_key: str, data: dict) -> None:
    folder = base / run_id / "nodes" / node_key
    folder.mkdir(parents=True)
    (folder / f"artifact_{node_key}.llm.json").write_text(
        json.dumps(data), encoding="utf-8"
    )


def test_read_llm_sidecar_fs_with_runs_root(tmp_path: Path) -> None:
    _write_sidecar(tmp_path, "run1", "n1", {"provider": "p"})
    out = _read_llm_sidecar_fs("run1", "n1", runs_root=str(tmp_path))
    assert out["provider"] == "p"


def test_read_llm_sidecar_fs_with_env(tmp_path: Path, monkeypatch) -> None:
    _write_sidecar(tmp_path, "run2", "n2", {"model_used": "m"})
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    out = _read_llm_sidecar_fs("run2", "n2")
    assert out["model"] == "m"


def test_read_llm_sidecar_fs_missing(tmp_path: Path) -> None:
    out = _read_llm_sidecar_fs("missing", "none", runs_root=str(tmp_path))
    assert out == {}


def test_normalize_llm_sidecar_idempotent() -> None:
    src = {"model": "a", "usage": {"prompt_tokens": 1}}
    first = _normalize_llm_sidecar(src)
    second = _normalize_llm_sidecar(first)
    assert first == second
    assert first["model"] == first["model_used"] == "a"
    assert src == {"model": "a", "usage": {"prompt_tokens": 1}}
