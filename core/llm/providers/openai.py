# core/llm/providers/openai.py
import os
import asyncio
from typing import Optional

from core.llm.providers.base import (
    LLMProvider, LLMRequest, LLMResponse,
    ProviderUnavailable, ProviderTimeout
)

# Paramétrables via .env
_OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "2"))            # + la 1ère tentative
_OPENAI_BACKOFF_BASE_MS = int(os.getenv("OPENAI_BACKOFF_BASE_MS", "200"))  # 200ms, 400ms, 800ms…
_OPENAI_BACKOFF_FACTOR = float(os.getenv("OPENAI_BACKOFF_FACTOR", "2.0"))

class OpenAIProvider(LLMProvider):
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ProviderUnavailable("OPENAI_API_KEY non défini")
        import openai  # lib officielle >= 1.x
        self._client = openai.OpenAI(
            api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL") or None
        )

    async def _chat_once(self, req: LLMRequest) -> LLMResponse:
        """
        Une tentative (sans retry). Laisse remonter les exceptions.
        """
        def _call():
            resp = self._client.chat.completions.create(
                model=req.model,
                messages=[
                    {"role": "system", "content": req.system or ""},
                    {"role": "user", "content": req.prompt or ""},
                ],
                temperature=req.temperature,
                max_tokens=req.max_tokens or None,
            )
            text = resp.choices[0].message.content if getattr(resp, "choices", None) else ""
            raw = {
                "id": getattr(resp, "id", None),
                "usage": getattr(resp, "usage", None)  # <-- important pour tokens
            }
            return LLMResponse(text=text, raw=raw)

        try:
            return await asyncio.to_thread(_call)
        except Exception:
            raise  # classification faite au niveau supérieur

    def _classify(self, err: Exception) -> str:
        """
        'timeout' | 'rate_limit' | 'server' | 'client' | 'unknown'
        """
        code = getattr(err, "status_code", None) or getattr(getattr(err, "response", None), "status_code", None)
        name = type(err).__name__.lower()
        msg = str(err).lower()

        if "timeout" in name or "timed out" in msg:
            return "timeout"
        if code == 429 or ("rate" in msg and "limit" in msg):
            return "rate_limit"
        if code and int(code) >= 500:
            return "server"
        if code and 400 <= int(code) < 500:
            return "client"
        return "unknown"

    async def generate(self, req: LLMRequest) -> LLMResponse:
        """
        Retry court avec backoff pour 429/5xx/timeout, puis reclassement:
        - timeout => ProviderTimeout
        - autres (429/5xx/4xx/unknown) => ProviderUnavailable (déclenche le fallback)
        """
        attempts = _OPENAI_MAX_RETRIES + 1
        last_err: Optional[Exception] = None

        for i in range(attempts):
            try:
                return await self._chat_once(req)
            except Exception as e:
                last_err = e
                kind = self._classify(e)
                if i == attempts - 1:
                    break
                delay = (_OPENAI_BACKOFF_BASE_MS * (_OPENAI_BACKOFF_FACTOR ** i)) / 1000.0
                await asyncio.sleep(delay)
                continue

        kind = self._classify(last_err) if last_err else "unknown"
        if kind == "timeout":
            raise ProviderTimeout(f"OpenAI timeout après {attempts} tentative(s): {last_err}")
        raise ProviderUnavailable(f"OpenAI indisponible ({kind}) après {attempts} tentative(s): {last_err}")
