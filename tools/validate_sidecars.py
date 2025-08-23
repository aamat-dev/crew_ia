#!/usr/bin/env python3
"""CLI de validation des sidecars LLM."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from jsonschema import Draft202012Validator, FormatChecker

UUID4_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)


def parse_rfc3339(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def load_schema() -> Dict[str, Any]:
    schema_path = Path(__file__).resolve().parent.parent / "schemas/llm_sidecar.schema.json"
    with schema_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", help="run_id (UUID v4) ou timestamp RFC3339")
    parser.add_argument("--strict", action="store_true", help="mode strict")
    parser.add_argument("--all", action="store_true", help="valider tous les fichiers")
    args = parser.parse_args()

    since_kind: tuple[str, Any] | None = None
    if args.since:
        if UUID4_RE.match(args.since):
            since_kind = ("run_id", args.since)
        else:
            try:
                since_kind = ("timestamp", parse_rfc3339(args.since))
            except Exception as exc:  # noqa: BLE001
                parser.error("--since doit être un UUID v4 ou un timestamp RFC3339")

    schema = load_schema()
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    known_props = set(schema.get("properties", {}).keys())

    runs_root = Path(os.environ.get("RUNS_ROOT", ".runs"))
    files = sorted(runs_root.rglob("*.llm.json")) if runs_root.exists() else []

    ok = 0
    skipped = 0
    errors: Dict[Path, List[str]] = {}
    warnings: Dict[Path, List[str]] = {}

    for path in files:
        if since_kind and since_kind[0] == "run_id" and since_kind[1] not in str(path):
            continue
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as exc:  # noqa: BLE001
            errors[path] = [f"JSON invalide: {exc}"]
            continue
        if since_kind and since_kind[0] == "timestamp":
            started = data.get("timestamps", {}).get("started_at")
            if not started:
                continue
            try:
                started_dt = parse_rfc3339(started)
            except Exception:  # noqa: BLE001
                started_dt = None
            if started_dt is None or started_dt < since_kind[1]:
                continue
        if not args.all and "version" not in data:
            skipped += 1
            continue
        file_errors: List[str] = []
        file_warnings: List[str] = []
        for err in validator.iter_errors(data):
            file_errors.append(err.message)
        if args.strict:
            if "raw" in data:
                file_errors.append("champ déprécié 'raw' présent")
            if (
                "model" in data
                and "model_used" in data
                and data["model"] != data["model_used"]
            ):
                file_errors.append("'model' et 'model_used' diffèrent")
        unknown = set(data.keys()) - known_props
        unknown.discard("markdown")  # champs optionnel ignoré
        if unknown:
            file_warnings.append("Champs inconnus: " + ", ".join(sorted(unknown)))
        if file_errors:
            errors[path] = file_errors
        else:
            ok += 1
        if file_warnings:
            warnings[path] = file_warnings

    ko = len(errors)
    print(f"OK: {ok} KO: {ko} SKIP: {skipped}")
    for path in errors:
        print(path)
        for msg in errors[path]:
            print(f"  - {msg}")
        for w in warnings.get(path, []):
            print(f"  ! {w}")
    for path in warnings:
        if path in errors:
            continue
        print(path)
        for w in warnings[path]:
            print(f"  ! {w}")

    sys.exit(1 if ko else 0)


if __name__ == "__main__":
    main()
