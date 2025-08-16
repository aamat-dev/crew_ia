# core/llm/providers/ollama.py
"""
Provider Ollama conforme à l'interface LLMProvider.
Utilise l'endpoint /api/chat d'Ollama (messages system/user).
- Le modèle, le timeout, la température viennent de LLMRequest.
- Aucune dépendance à des variables d'environnement ici.
- Exceptions normalisées pour permettre le fallback.
"""

import os
import httpx
from core.llm.providers.base import (
    LLMProvider, LLMRequest, LLMResponse,
    ProviderUnavailable, ProviderTimeout
)

# On lit juste la base URL ici (stable, pas critique) ; le reste vient de la requête
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")


class OllamaProvider(LLMProvider):
    async def generate(self, req: LLMRequest) -> LLMResponse:
        """
        Appelle Ollama /api/chat avec messages [system, user].
        Retourne LLMResponse(text=...), ou lève ProviderTimeout/ProviderUnavailable.
        """
        url = f"{OLLAMA_BASE_URL}/api/chat"

        # messages chat : system + user
        messages = []
        if req.system:
            messages.append({"role": "system", "content": req.system})
        messages.append({"role": "user", "content": req.prompt})

        payload = {
            "model": req.model,
            "messages": messages,
            "options": {
                "temperature": req.temperature,
                # Ollama ne prend pas max_tokens directement en chat;
                # si besoin finement → basculer sur /api/generate (num_predict)
            },
            "stream": False,
        }

        # httpx gère nativement le timeout total via paramètre timeout=...
        try:
            async with httpx.AsyncClient(timeout=req.timeout_s) as client:
                resp = await client.post(url, json=payload)
        except httpx.ConnectTimeout:
            raise ProviderTimeout("Ollama timeout (connect)")
        except httpx.ReadTimeout:
            raise ProviderTimeout("Ollama timeout (read)")
        except httpx.TimeoutException as e:
            # couvre tout autre timeout agrégé
            raise ProviderTimeout(f"Ollama timeout: {e}")
        except httpx.ConnectError as e:
            # Daemon non lancé, port fermé, etc.
            raise ProviderUnavailable(f"Ollama indisponible: {e}")
        except httpx.HTTPError as e:
            # Autres erreurs transport
            raise ProviderUnavailable(f"Ollama erreur HTTP: {e}")

        # Statuts HTTP non-200
        if resp.status_code == 404:
            raise ProviderUnavailable(
                f"Modèle '{req.model}' introuvable côté Ollama (404). "
                f"Assure-toi d'avoir fait: `ollama pull {req.model}`."
            )
        if resp.status_code != 200:
            raise ProviderUnavailable(f"Ollama status {resp.status_code}: {resp.text[:200]}")

        # Corps de réponse
        try:
            data = resp.json()
        except ValueError:
            raise ProviderUnavailable("Réponse Ollama invalide (JSON)")

        # Format attendu pour /api/chat : {"message": {"content": "..."}}
        text = ""
        if isinstance(data, dict):
            msg = data.get("message") or {}
            text = msg.get("content") or ""

        if not text:
            # tolérant : certaines versions peuvent renvoyer un autre champ
            text = data.get("response", "") if isinstance(data, dict) else ""

        return LLMResponse(text=text or "", raw=data)
