# core/llm/providers/openai.py
import os
import asyncio
from openai import AsyncOpenAI
from core.llm.providers.base import (
    LLMProvider, LLMRequest, LLMResponse, ProviderUnavailable, ProviderTimeout
)

class OpenAIProvider(LLMProvider):
    async def generate(self, req: LLMRequest) -> LLMResponse:
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", None)
        if not api_key:
            raise ProviderUnavailable("OPENAI_API_KEY non défini")

        try:
            client = AsyncOpenAI(api_key=api_key, base_url=base_url or None)
            resp = await asyncio.wait_for(
                client.chat.completions.create(
                    model=req.model,
                    messages=[
                        {"role": "system", "content": req.system or ""},
                        {"role": "user", "content": req.prompt},
                    ],
                    temperature=req.temperature,
                    max_tokens=req.max_tokens,
                ),
                timeout=req.timeout_s
            )
            text = resp.choices[0].message.content or ""
            # .to_dict() n’existe pas toujours → on packe minimal
            return LLMResponse(text=text, raw={"id": getattr(resp, "id", None)})
        except asyncio.TimeoutError:
            raise ProviderTimeout("OpenAI timeout")
        except Exception as e:
            raise ProviderUnavailable(f"OpenAI error: {e}")
