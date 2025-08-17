# core/storage/composite_adapter.py
from __future__ import annotations
import inspect
from typing import Sequence

class CompositeAdapter:
    """Diffuse chaque appel vers plusieurs adaptateurs (sync/async)."""

    def __init__(self, adapters: Sequence[object]):
        self.adapters = list(adapters)
        # évite les AttributeError si set_resolvers n'a pas encore été appelé
        self._resolve_run_uuid = None
        self._resolve_node_uuid = None

    def set_resolvers(self, *, run_resolver=None, node_resolver=None):
        self._resolve_run_uuid = run_resolver
        self._resolve_node_uuid = node_resolver

    def _normalize_ids(self, kwargs: dict) -> dict:
        out = dict(kwargs)
        if "run_id" in out and isinstance(out["run_id"], str) and self._resolve_run_uuid:
            maybe = self._resolve_run_uuid(out["run_id"])
            if maybe:
                out["run_id"] = maybe
        if "node_id" in out and isinstance(out["node_id"], str) and self._resolve_node_uuid:
            maybe = self._resolve_node_uuid(out["node_id"])
            if maybe:
                out["node_id"] = maybe
        return out

    async def _call(self, name: str, *args, **kwargs):
        result = None
        # on normalise pour les écritures qui utilisent des IDs
        needs_norm = name in {"save_artifact", "save_event"}  # {"save_node"} si un jour tu passes des IDs bruts
        call_kwargs = self._normalize_ids(kwargs) if needs_norm else kwargs

        for a in self.adapters:
            if not hasattr(a, name):
                continue
            fn = getattr(a, name)
            if inspect.iscoroutinefunction(fn):
                # ⚠️ utiliser call_kwargs (et pas kwargs)
                result = await fn(*args, **call_kwargs)
            else:
                result = fn(*args, **call_kwargs)
        return result

    async def save_run(self, *args, **kwargs): return await self._call("save_run", *args, **kwargs)
    async def save_node(self, *args, **kwargs): return await self._call("save_node", *args, **kwargs)
    async def save_artifact(self, *args, **kwargs): return await self._call("save_artifact", *args, **kwargs)
    async def save_event(self, *args, **kwargs): return await self._call("save_event", *args, **kwargs)

    async def get_run(self, *args, **kwargs):
        for a in self.adapters:
            if hasattr(a, "get_run"):
                fn = getattr(a, "get_run")
                res = await fn(*args, **kwargs) if inspect.iscoroutinefunction(fn) else fn(*args, **kwargs)
                if res:
                    return res
        return None

    async def list_runs(self, *args, **kwargs):
        for a in self.adapters:
            if hasattr(a, "list_runs"):
                fn = getattr(a, "list_runs")
                return await fn(*args, **kwargs) if inspect.iscoroutinefunction(fn) else fn(*args, **kwargs)
        return []
