# core/storage/file_adapter.py
from __future__ import annotations
import os
import json
import tempfile
import asyncio        # <-- NEW
# import aiofiles     # <-- plus nécessaire pour les artifacts atomiques (tu peux supprimer l'import)
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional

# ---------------------------
# Helpers atomiques génériques
# ---------------------------

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def _sanitize_id(s: str) -> str:
    # nom de fichier "safe"
    return "".join(c if (c.isalnum() or c in "-_") else "_" for c in (s or "")) or "node"

def _atomic_write_text(path: str, text: str, encoding: str = "utf-8") -> None:
    """
    Écriture atomique d'un fichier texte:
      - écrit dans un fichier temporaire dans le même dossier
      - flush + fsync
      - os.replace(temp, path)
    """
    _ensure_dir(os.path.dirname(path))
    with tempfile.NamedTemporaryFile("w", delete=False, dir=os.path.dirname(path), encoding=encoding) as tmp:
        tmp.write(text)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = tmp.name
    os.replace(tmp_path, path)

# ---------------------------
# 1) Storage des ARTIFACTS
# ---------------------------

class FileStorage:
    def __init__(self, base_dir: str = "./.runs"):
        self.base_dir = base_dir
        _ensure_dir(self.base_dir)

    def _artifact_path(self, node_id: str, ext: str = ".md") -> str:
        if not ext.startswith("."):
            ext = "." + ext
        safe_id = _sanitize_id(node_id)
        filename = f"artifact_{safe_id}{ext}"
        return os.path.join(self.base_dir, filename)

    async def save_artifact(self, node_id: str, content: str, ext: str = ".md") -> str:
        """
        Écrit l'artifact d'un nœud de façon ATOMIQUE.
        Nom = artifact_<node_id><ext>. Retourne le chemin écrit.
        """
        path = self._artifact_path(node_id=node_id, ext=ext)
        # déporte l'I/O bloquante dans un thread pour ne pas bloquer l'event loop
        await asyncio.to_thread(_atomic_write_text, path, content, "utf-8")
        return path

    async def save_sidecar(self, node_id: str, content: str, ext: str = ".llm.json") -> str:
        return await self.save_artifact(node_id=node_id, content=content, ext=ext)

# ---------------------------
# 2) Storage des CHECKPOINTS
# ---------------------------

ISO = "%Y-%m-%dT%H:%M:%S.%fZ"

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime(ISO)

def _atomic_write_json(path: str, data: dict) -> None:
    _ensure_dir(os.path.dirname(path))
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
            st.input_checksum = input_checksum
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
