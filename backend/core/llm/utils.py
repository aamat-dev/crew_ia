# core/llm/utils.py
def truncate(s: str | None, max_chars: int = 4000) -> str | None:
    if not isinstance(s, str):
        return s
    return s if len(s) <= max_chars else s[:max_chars] + f"... [truncated to {max_chars} chars]"
