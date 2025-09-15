from fastapi import APIRouter, Depends, Request
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import get_session
from core.services.orchestrator_service import get_health as get_orchestrator_health
import time
import datetime as dt

router = APIRouter(prefix="", tags=["health"])

@router.get("/health")
async def healthcheck(request: Request, session: AsyncSession = Depends(get_session)):
    try:
        await session.execute(text("SELECT 1"))
        rid = getattr(request.state, "request_id", None)
        lg = logging.getLogger("api.access")
        try:
            # Assure un handler pour caplog au besoin
            import sys
            if not lg.handlers:
                lg.addHandler(logging.StreamHandler(sys.stderr))
            lg.propagate = True
        except Exception:
            pass
        lg.info("HEALTH ok", extra={"request_id": rid})
        # Uptime API
        started_mono = getattr(request.app.state, "started_monotonic", None)
        uptime_s = int(time.monotonic() - started_mono) if started_mono else None
        orch = get_orchestrator_health(request.app.state)
        return {
            "status": "ok",
            "service": "api",
            "version": getattr(request.app, "version", None),
            "db_ok": True,
            "uptime_s": uptime_s,
            "orchestrator": orch,
        }
    except Exception as e:
        rid = getattr(request.state, "request_id", None)
        lg = logging.getLogger("api.access")
        try:
            import sys
            if not lg.handlers:
                lg.addHandler(logging.StreamHandler(sys.stderr))
            lg.propagate = True
        except Exception:
            pass
        lg.info("HEALTH degraded", extra={"request_id": rid})
        started_mono = getattr(request.app.state, "started_monotonic", None)
        uptime_s = int(time.monotonic() - started_mono) if started_mono else None
        orch = get_orchestrator_health(request.app.state)
        return {
            "status": "degraded",
            "service": "api",
            "version": getattr(request.app, "version", None),
            "db_ok": False,
            "error": str(e),
            "uptime_s": uptime_s,
            "orchestrator": orch,
        }
