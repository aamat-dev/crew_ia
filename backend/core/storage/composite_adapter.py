from __future__ import annotations

import inspect
import logging
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

        async def get_node_id_by_logical(self, run_id: str, logical_id: str) -> str | None:
            for ad in self.adapters:
                meth = getattr(ad, "get_node_id_by_logical", None)
                if meth:
                    nid = await meth(run_id, logical_id)
                    if nid:
                        return nid
            return None

        async def list_artifacts_for_node(self, node_id: str) -> list[dict]:
            for ad in self.adapters:
                meth = getattr(ad, "list_artifacts_for_node", None)
                if meth:
                    try:
                        return await meth(node_id)
                    except Exception:
                        pass
            return []

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
        needs_norm = name in {"save_artifact", "save_event", "save_feedback"}
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

            # Filtre les kwargs pour les fonctions qui n'acceptent pas **kwargs
            try:
                sig = inspect.signature(fn)
                accepts_varkw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
                if not accepts_varkw:
                    call_kwargs = {k: v for k, v in call_kwargs.items() if k in sig.parameters}
            except Exception:
                pass

            if inspect.iscoroutinefunction(fn):
                result = await fn(*args, **call_kwargs)
            else:
                result = fn(*args, **call_kwargs)
        return result

    # façade
    async def save_run(self, *args, **kwargs):
        return await self._call("save_run", *args, **kwargs)

    async def save_node(self, *args, **kwargs):
        return await self._call("save_node", *args, **kwargs)

    async def save_artifact(self, *args, **kwargs):
        return await self._call("save_artifact", *args, **kwargs)

    async def save_event(self, *args, **kwargs):
        return await self._call("save_event", *args, **kwargs)

    async def save_feedback(self, *args, **kwargs):
        return await self._call("save_feedback", *args, **kwargs)

    async def get_run(self, *args, **kwargs):
        # premier qui répond (tolérant aux erreurs backend)
        log = logging.getLogger(__name__)
        for a in self.adapters:
            if not hasattr(a, "get_run"):
                continue
            fn = getattr(a, "get_run")
            try:
                res = await fn(*args, **kwargs) if inspect.iscoroutinefunction(fn) else fn(*args, **kwargs)
            except Exception as e:
                # Ex : Postgres occupé pendant qu'on peut lire depuis FileAdapter
                log.warning(
                    "composite.get_run backend_error adapter=%s err=%r",
                    type(a).__name__, e
                )
                continue
            if res:
                return res
        return None

    async def list_runs(self, *args, **kwargs):
        for a in self.adapters:
            if hasattr(a, "list_runs"):
                fn = getattr(a, "list_runs")
                return await fn(*args, **kwargs) if inspect.iscoroutinefunction(fn) else fn(*args, **kwargs)
        return []

    async def get_node_id_by_logical(self, run_id: str, logical_id: str) -> str | None:
        for ad in self.adapters:
            if hasattr(ad, "get_node_id_by_logical"):
                nid = await ad.get_node_id_by_logical(run_id, logical_id)
                if nid:
                    return nid
        return None

    async def list_artifacts_for_node(self, node_id: str) -> list[dict]:
        # Parcourt les adaptateurs et renvoie le premier résultat NON VIDE.
        # Permet de chaîner file -> pg sans bloquer si le premier ne sait pas répondre.
        for ad in self.adapters:
            if hasattr(ad, "list_artifacts_for_node"):
                try:
                    res = await ad.list_artifacts_for_node(node_id)
                    if res:
                        return res
                except Exception:
                    # Tolérant aux erreurs backend individuelles
                    continue
        return []

    # ---------- Finalisation atomique de run ----------
    async def finalize_run_status(
        self,
        *,
        run_id,
        title,
        status,
        started_at,
        ended_at,
        meta=None,
        request_id: str | None = None,
    ):
        """
        Finalise un run de manière atomique (run + event) si l'adaptateur le supporte.
        Fallback: save_run puis save_event.
        """
        result = None
        # 1) Tente finalize_run_status pour tous les adaptateurs qui le supportent
        for ad in self.adapters:
            fn = getattr(ad, "finalize_run_status", None)
            if not fn:
                continue
            if inspect.iscoroutinefunction(fn):
                result = await fn(
                    run_id=run_id,
                    title=title,
                    status=status,
                    started_at=started_at,
                    ended_at=ended_at,
                    meta=meta,
                    request_id=request_id,
                )
            else:
                result = fn(
                    run_id=run_id,
                    title=title,
                    status=status,
                    started_at=started_at,
                    ended_at=ended_at,
                    meta=meta,
                    request_id=request_id,
                )

        # 2) Fallback pour les autres adaptateurs: save_run + save_event
        #    On diffuse à tous les adaptateurs qui ont save_run/save_event
        import json as _json
        import uuid as _uuid
        level = "RUN_COMPLETED" if str(getattr(status, "value", status)).endswith("completed") else "RUN_FAILED"
        for ad in self.adapters:
            if hasattr(ad, "finalize_run_status"):
                continue
            rid = run_id
            try:
                if getattr(ad, "expects_uuid_ids", False):
                    rid = rid if isinstance(rid, _uuid.UUID) else _uuid.UUID(str(rid))
            except Exception:
                pass
            if hasattr(ad, "save_run"):
                fn_sr = getattr(ad, "save_run")
                payload = {
                    "id": rid,
                    "title": title,
                    "status": status,
                    "started_at": started_at,
                    "ended_at": ended_at,
                    "meta": meta or {},
                }
                if inspect.iscoroutinefunction(fn_sr):
                    result = await fn_sr(**payload)
                else:
                    result = fn_sr(**payload)
            if hasattr(ad, "save_event"):
                fn_se = getattr(ad, "save_event")
                ev = {
                    "run_id": rid,
                    "level": level,
                    "message": _json.dumps({"request_id": request_id} if request_id else {}),
                    "request_id": request_id,
                }
                if inspect.iscoroutinefunction(fn_se):
                    await fn_se(**ev)
                else:
                    fn_se(**ev)
        return result

    # ---------- Finalisation atomique de nœud ----------
    async def finalize_node_status(
        self,
        *,
        run_id,
        node_key: str,
        title: str | None,
        status,
        updated_at,
        checksum: str | None = None,
        node_id: str | None = None,
        event_message: str | None = None,
        request_id: str | None = None,
    ):
        """Finalise un nœud (node + event) si supporté, sinon fallback save_node + save_event.
        - status: string ou Enum
        - event_message: JSON string (optionnel)
        """
        import json as _json
        import uuid as _uuid
        # 1) Tente la méthode native
        for ad in self.adapters:
            fn = getattr(ad, "finalize_node_status", None)
            if not fn:
                continue
            call = fn
            if inspect.iscoroutinefunction(call):
                await call(
                    run_id=run_id,
                    node_key=node_key,
                    title=title,
                    status=status,
                    updated_at=updated_at,
                    checksum=checksum,
                    node_id=node_id,
                    event_message=event_message,
                    request_id=request_id,
                )
            else:
                call(
                    run_id=run_id,
                    node_key=node_key,
                    title=title,
                    status=status,
                    updated_at=updated_at,
                    checksum=checksum,
                    node_id=node_id,
                    event_message=event_message,
                    request_id=request_id,
                )

        # 2) Fallback
        # Normalise run/node ids pour adaptateurs expects_uuid_ids
        level = None
        st = str(getattr(status, "value", status))
        if st.endswith("completed"):
            level = "NODE_COMPLETED"
        elif st.endswith("failed"):
            level = "NODE_FAILED"

        for ad in self.adapters:
            if hasattr(ad, "finalize_node_status"):
                continue
            rid = run_id
            nid = node_id
            try:
                if getattr(ad, "expects_uuid_ids", False):
                    rid = rid if isinstance(rid, _uuid.UUID) else _uuid.UUID(str(rid))
                    if nid is not None:
                        nid = nid if isinstance(nid, _uuid.UUID) else _uuid.UUID(str(nid))
            except Exception:
                pass

            # ---- save_node (fallback) ----
            if hasattr(ad, "save_node"):
                fn_sn = getattr(ad, "save_node")
                payload = {
                    "id": nid,
                    "run_id": rid,
                    "key": node_key,
                    "title": title,
                    "status": status,
                    "updated_at": updated_at,
                    "checksum": checksum,
                }
                try:
                    params = inspect.signature(fn_sn).parameters
                except Exception:
                    params = {}
                # Si la fonction accepte un argument nommé 'node', on passe en kwargs (adapter type Postgres)
                if "node" in params:
                    if inspect.iscoroutinefunction(fn_sn):
                        await fn_sn(node=None, **payload)
                    else:
                        fn_sn(node=None, **payload)
                else:
                    # Sinon, on tente un appel positionnel avec un objet Node minimal (adapter DummyStorage des tests)
                    try:
                        from core.storage.db_models import Node as DBNode  # import local pour éviter dépendances globales
                        node_obj = DBNode(**payload)
                        if inspect.iscoroutinefunction(fn_sn):
                            await fn_sn(node_obj)
                        else:
                            fn_sn(node_obj)
                    except Exception:
                        # En dernier recours, tente un appel par kwargs sans 'node'
                        safe_payload = {k: v for k, v in payload.items() if k in getattr(params, 'keys', lambda: [])()}
                        if inspect.iscoroutinefunction(fn_sn):
                            await fn_sn(**safe_payload)
                        else:
                            fn_sn(**safe_payload)

            # ---- save_event (fallback) ----
            if level and hasattr(ad, "save_event"):
                fn_se = getattr(ad, "save_event")
                ev = {
                    "run_id": rid,
                    "node_id": nid,
                    "level": level,
                    "message": event_message or _json.dumps({}),
                    # request_id est optionnel suivant les adaptateurs (ne pas forcer)
                    "request_id": request_id,
                }
                try:
                    params = inspect.signature(fn_se).parameters
                except Exception:
                    params = {}
                # Filtre les clés aux paramètres acceptés par la fonction
                filtered = {k: v for k, v in ev.items() if k in params}
                if inspect.iscoroutinefunction(fn_se):
                    await fn_se(**filtered)
                else:
                    fn_se(**filtered)
