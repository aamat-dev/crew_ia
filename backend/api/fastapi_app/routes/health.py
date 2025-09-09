from fastapi import APIRouter, Depends, Request
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import get_session

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
        return {"status": "ok", "db": "ok"}
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
        return {"status": "degraded", "db": str(e)}
