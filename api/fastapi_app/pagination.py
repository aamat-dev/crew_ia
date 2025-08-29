from __future__ import annotations
from fastapi import Request, Response


def set_pagination_headers(response: Response, request: Request, total: int, limit: int, offset: int) -> None:
    """Ajoute les en-têtes RFC5988 Link et X-Total-Count."""
    links: list[str] = []
    if offset > 0:
        prev_offset = max(offset - limit, 0)
        prev_url = str(request.url.include_query_params(offset=prev_offset, limit=limit))
        links.append(f"<{prev_url}>; rel=\"prev\"")
    if offset + limit < total:
        next_url = str(request.url.include_query_params(offset=offset + limit, limit=limit))
        links.append(f"<{next_url}>; rel=\"next\"")
    if links:
        response.headers["Link"] = ", ".join(links)
    response.headers["X-Total-Count"] = str(total)
