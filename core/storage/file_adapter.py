"""
file_adapter.py — Stockage simple basé sur le système de fichiers.
- FileStorage : écrit les artifacts Markdown dans ./.runs/
- FileStatusStore : checkpoints persistants par nœud dans ./.runs/{run_id}/{node_id}.status.json
  avec écriture atomique (os.replace) pour tolérance aux crashs.
"""

from __future__ import annotations
import os
import json
import tempfile
import aiofiles
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional

# ---------------------------
# 1) Storage des ARTIFACTS
# ---------------------------

class FileStorage:
    def __init__(self, base_dir: str = "./.runs"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)  # crée le dossier s'il n'existe pas

    async def save_artifact(self, node_id: str, content: str):
        """
        Écrit l'artifact d'un nœud dans un fichier Markdown.
        Nom de fichier = artifact_<node_id>.md
        """
        path = os.path.join(self.base_dir, f"artifact_{node_id}.md")
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(content)


# ---------------------------
# 2) Storage des CHECKPOINTS
# ---------------------------

ISO = "%Y-%m-%dT%H:%M:%S.%fZ"

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime(ISO)

def _atomic_write_json(path: str, data: dict) -> None:
    """
    Écriture atomique : on écrit dans un fichier temporaire puis os.replace.
    Évite les .json corrompus en cas de coupure.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=os.path.dirname(path), encoding="utf-8") as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = tmp.name
    os.replace(tmp_path, path)

@dataclass
class NodeStatus:
    run_id: str
    node_id: str
    status: str           # "pending" | "in_progress" | "completed" | "failed"
    attempts: int = 0
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    input_checksum: Optional[str] = None
    error: Optional[str] = None

    @classmethod
    def new_pending(cls, run_id: str, node_id: str, input_checksum: Optional[str] = None) -> "NodeStatus":
        return cls(run_id=run_id, node_id=node_id, status="pending", attempts=0, input_checksum=input_checksum)

class FileStatusStore:
    """
    Checkpoints par nœud :
      .runs/{run_id}/{node_id}.status.json

    Règles d'idempotence (implémentées côté exécuteur) :
      - "completed" => SKIP (ne jamais relancer sauf override explicite)
      - "in_progress" laissé par un crash => rejouable
      - "failed" => rejouable si retries restants
    """
    def __init__(self, runs_root: str = ".runs"):
        self.runs_root = runs_root

    def run_dir(self, run_id: str) -> str:
        return os.path.join(self.runs_root, run_id)

    def status_path(self, run_id: str, node_id: str) -> str:
        return os.path.join(self.run_dir(run_id), f"{node_id}.status.json")

    def read(self, run_id: str, node_id: str) -> Optional[NodeStatus]:
        path = self.status_path(run_id, node_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return NodeStatus(**data)

    def write(self, st: NodeStatus) -> None:
        _atomic_write_json(self.status_path(st.run_id, st.node_id), asdict(st))

    def mark_in_progress(self, run_id: str, node_id: str, input_checksum: str | None = None) -> NodeStatus:
        st = self.read(run_id, node_id) or NodeStatus.new_pending(run_id, node_id)
        st.status = "in_progress"
        st.attempts += 1
        st.started_at = _utcnow_iso()
        st.error = None
        if input_checksum is not None:
            st.input_checksum = input_checksum  # ⬅️ on enregistre l'empreinte
        self.write(st)
        return st

    def mark_completed(self, run_id: str, node_id: str) -> NodeStatus:
        st = self.read(run_id, node_id) or NodeStatus.new_pending(run_id, node_id)
        st.status = "completed"
        st.ended_at = _utcnow_iso()
        self.write(st)
        return st

    def mark_failed(self, run_id: str, node_id: str, error_msg: str) -> NodeStatus:
        st = self.read(run_id, node_id) or NodeStatus.new_pending(run_id, node_id)
        st.status = "failed"
        st.ended_at = _utcnow_iso()
        st.error = error_msg
        self.write(st)
        return st
