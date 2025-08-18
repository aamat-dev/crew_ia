from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import get_session, require_api_key

router = APIRouter(prefix="", tags=["health"])

@router.get("/health")
async def healthcheck(session: AsyncSession = Depends(get_session), _=Depends(require_api_key)):
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception as e:
        return {"status": "degraded", "db": str(e)}