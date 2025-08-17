from __future__ import annotations

import inspect
from typing import Sequence, Callable, Optional, Any, Dict


class CompositeAdapter:
    """
    Diffuse chaque appel vers plusieurs adaptateurs (sync/async).
    - Permet de normaliser les IDs (ex.: 'n1' logique -> UUID DB) *uniquement* pour
      les adaptateurs qui en ont besoin (expects_uuid_ids=True).
    """

    def __init__(self, adapters: Sequence[object]):
        self.adapters = list(adapters)
        self._resolve_run_uuid: Optional[Callable[[str], Any]] = None
        self._resolve_node_uuid: Optional[Callable[[str], Any]] = None

    def set_resolvers(
        self,
        *,
        run_resolver: Optional[Callable[[str], Any]] = None,
        node_resolver: Optional[Callable[[str], Any]] = None
    ):
        self._resolve_run_uuid = run_resolver
        self._resolve_node_uuid = node_resolver

    def _normalize_ids(self, kwargs: Dict) -> Dict:
        out = dict(kwargs)
        if "run_id" in out and isinstance(out["run_id"], str) and self._resolve_run_uuid:
            maybe = self._resolve_run_uuid(out["run_id"])
            if inspect.iscoroutinefunction(self._resolve_run_uuid):
                # support async resolver
                pass  # handled in _call
            elif maybe:
                out["run_id"] = maybe

        if "node_id" in out and isinstance(out["node_id"], str) and self._resolve_node_uuid:
            maybe = self._resolve_node_uuid(out["node_id"])
            if inspect.iscoroutinefunction(self._resolve_node_uuid):
                # support async resolver
                pass
            elif maybe:
                out["node_id"] = maybe
        return out

    async def _normalize_ids_async(self, kwargs: Dict) -> Dict:
        out = dict(kwargs)
        if "run_id" in out and isinstance(out["run_id"], str) and self._resolve_run_uuid:
            if inspect.iscoroutinefunction(self._resolve_run_uuid):
                maybe = await self._resolve_run_uuid(out["run_id"])
            else:
                maybe = self._resolve_run_uuid(out["run_id"])
            if maybe:
                out["run_id"] = maybe

        if "node_id" in out and isinstance(out["node_id"], str) and self._resolve_node_uuid:
            if inspect.iscoroutinefunction(self._resolve_node_uuid):
                maybe = await self._resolve_node_uuid(out["node_id"])
            else:
                maybe = self._resolve_node_uuid(out["node_id"])
            if maybe:
                out["node_id"] = maybe

        return out

    async def _call(self, name: str, *args, **kwargs):
        result = None
        needs_norm = name in {"save_artifact", "save_event"}
        for a in self.adapters:
            if not hasattr(a, name):
                continue

            fn = getattr(a, name)
            # On ne normalise que pour les adaptateurs qui le demandent
            if needs_norm and getattr(a, "expects_uuid_ids", False):
                # async resolvers support
                call_kwargs = await self._normalize_ids_async(kwargs)
            else:
                call_kwargs = kwargs

            if inspect.iscoroutinefunction(fn):
                result = await fn(*args, **call_kwargs)
            else:
                result = fn(*args, **call_kwargs)
        return result

    # façade
    async def save_run(self, *args, **kwargs): return await self._call("save_run", *args, **kwargs)
    async def save_node(self, *args, **kwargs): return await self._call("save_node", *args, **kwargs)
    async def save_artifact(self, *args, **kwargs): return await self._call("save_artifact", *args, **kwargs)
    async def save_event(self, *args, **kwargs): return await self._call("save_event", *args, **kwargs)

    async def get_run(self, *args, **kwargs):
        # premier qui répond
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
