from __future__ import annotations
from typing import Optional, Literal
from fastapi import Query, Request, Response
from pydantic import BaseModel

MAX_LIMIT = 200
DEFAULT_LIMIT = 50


def cap_limit(limit: int) -> int:
    """Tronque ``limit`` à ``MAX_LIMIT``."""
    return min(limit, MAX_LIMIT)


class PaginationParams(BaseModel):
    limit: int
    offset: int
    order_by: Optional[str] = None
    order_dir: Optional[Literal["asc", "desc"]] = None


def pagination_params(
    limit: int = Query(DEFAULT_LIMIT, ge=1),
    offset: int = Query(0, ge=0),
    order_by: Optional[str] = Query(None),
    order_dir: Optional[Literal["asc", "desc"]] = Query(None),
) -> PaginationParams:
    """Dépendance FastAPI pour lire les paramètres de pagination."""
    return PaginationParams(
        limit=cap_limit(limit), offset=offset, order_by=order_by, order_dir=order_dir
    )


def set_pagination_headers(
    response: Response, request: Request, total: int, limit: int, offset: int
) -> None:
    """Ajoute les en-têtes RFC5988 Link et X-Total-Count."""
    links: list[str] = []
    if offset > 0:
        prev_offset = max(offset - limit, 0)
        prev_url = str(
            request.url.include_query_params(offset=prev_offset, limit=limit)
        )
        links.append(f"<{prev_url}>; rel=\"prev\"")
    if offset + limit < total:
        next_url = str(
            request.url.include_query_params(offset=offset + limit, limit=limit)
        )
        links.append(f"<{next_url}>; rel=\"next\"")
    if links:
        response.headers["Link"] = ", ".join(links)
    response.headers["X-Total-Count"] = str(total)
