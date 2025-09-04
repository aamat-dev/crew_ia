#!/usr/bin/env python3
"""Petit utilitaire pour suivre les events d'un run en temps réel."""

import argparse
import json
import time
from typing import Any

import httpx


def format_event(evt: dict[str, Any]) -> str:
    ts = evt.get("timestamp")
    level = evt.get("level")
    msg = evt.get("message", "")
    try:
        payload = json.loads(msg)
    except Exception:
        payload = {}
    if level == "NODE_COMPLETED":
        return (
            f"{ts} NODE_COMPLETED node={payload.get('node_key')} "
            f"provider={payload.get('provider')} "
            f"model={payload.get('model')} latency_ms={payload.get('latency_ms')}"
        )
    return f"{ts} {level} {payload or msg}"


def tail_events(run_id: str, url: str, interval: float = 1.0) -> None:
    offset = 0
    while True:
        try:
            resp = httpx.get(url, params={"run_id": run_id, "offset": offset, "limit": 100})
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            print(f"Erreur requête: {exc}")
            time.sleep(interval)
            continue
        items = data.get("items", [])
        for evt in items:
            print(format_event(evt), flush=True)
        offset += len(items)
        time.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True, dest="run_id")
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000/events",
        help="URL de base vers /events",
    )
    parser.add_argument("--interval", type=float, default=1.0, help="Pause entre deux requêtes")
    args = parser.parse_args()
    tail_events(args.run_id, args.url, args.interval)


if __name__ == "__main__":
    main()

