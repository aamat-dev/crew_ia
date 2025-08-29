from __future__ import annotations
from typing import Mapping, Literal
from fastapi import HTTPException
from sqlalchemy import asc, desc

def apply_order(stmt, order_by: str | None, order_dir: Literal["asc", "desc"] | None, allowed: Mapping[str, object], default: str):
    field = order_by or default
    if field.startswith("-"):
        key = field[1:]
        direction = desc
    else:
        key = field
        dir_val = order_dir or "asc"
        direction = asc if dir_val == "asc" else desc
    if key not in allowed:
        allowed_cols = ", ".join(sorted(allowed.keys()))
        raise HTTPException(status_code=422, detail=f"order_by doit être parmi: {allowed_cols}")
    return stmt.order_by(direction(allowed[key]))
