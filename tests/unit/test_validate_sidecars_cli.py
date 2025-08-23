import json
import subprocess
import sys
from pathlib import Path


def _write_sidecar(base: Path, run_id: str, node: str, data: dict) -> Path:
    folder = base / run_id / "nodes" / node
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"artifact_{node}.llm.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_validate_sidecars_cli(tmp_path: Path) -> None:
    run1 = "11111111-1111-4111-8111-111111111111"
    run2 = "22222222-2222-4222-8222-222222222222"
    node = "33333333-3333-4333-8333-333333333333"

    base_sidecar = {
        "version": "1",
        "provider": "openai",
        "model": "m1",
        "latency_ms": 1,
        "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        "cost": {"estimated": 0.0},
        "prompts": {"system": "s", "user": "u"},
        "timestamps": {
            "started_at": "2025-01-01T00:00:00Z",
            "ended_at": "2025-01-01T00:01:00Z",
        },
        "run_id": run1,
        "node_id": node,
    }

    # fichiers de base
    _write_sidecar(tmp_path, run1, "valid", base_sidecar)
    raw_sc = dict(base_sidecar)
    raw_sc["raw"] = {}
    _write_sidecar(tmp_path, run1, "raw", raw_sc)
    old_sc = dict(base_sidecar)
    old_sc["timestamps"] = {
        "started_at": "2023-01-01T00:00:00Z",
        "ended_at": "2023-01-01T00:01:00Z",
    }
    _write_sidecar(tmp_path, run1, "old", old_sc)
    _write_sidecar(tmp_path, run1, "new", base_sidecar)
    run2_sc = dict(base_sidecar)
    run2_sc["run_id"] = run2
    _write_sidecar(tmp_path, run2, "other", run2_sc)

    env = {"RUNS_ROOT": str(tmp_path)}

    # exécution normale
    res = subprocess.run(
        [sys.executable, "tools/validate_sidecars.py"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0

    # ajoute sidecar avec model != model_used
    mm_sc = dict(base_sidecar)
    mm_sc["model_used"] = "m2"
    mismatch_path = _write_sidecar(tmp_path, run1, "mismatch", mm_sc)

    # strict => erreurs raw et model mismatch
    res = subprocess.run(
        [sys.executable, "tools/validate_sidecars.py", "--strict"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    assert "champ déprécié 'raw' présent" in res.stdout
    assert "'model' et 'model_used' diffèrent" in res.stdout

    mismatch_path.unlink()  # nettoyer pour les tests suivants

    # since timestamp => ignore le fichier 'old'
    res = subprocess.run(
        [
            sys.executable,
            "tools/validate_sidecars.py",
            "--since",
            "2024-01-01T00:00:00Z",
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "OK: 4" in res.stdout
    assert "old" not in res.stdout

    # since run_id => ignore le second run
    res = subprocess.run(
        [sys.executable, "tools/validate_sidecars.py", "--since", run1],
        env=env,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert run2 not in res.stdout
