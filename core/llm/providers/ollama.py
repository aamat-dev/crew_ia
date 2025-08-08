"""
Provider Ollama — appel à un modèle local (port 11434).
But : fournir une fonction simple `ollama_chat()` qui envoie un prompt système + utilisateur,
      et récupère la réponse textuelle. On reste minimaliste, mais robuste.
"""

import os
import httpx
from typing import List, Dict

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

async def ollama_chat(system_prompt: str, user_prompt: str, temperature: float = 0.2, max_tokens: int = 800) -> str:
    """
    Envoie un prompt 'chat' à Ollama et retourne la sortie texte.
    - system_prompt : consignes globales (rôle, format JSON strict, etc.)
    - user_prompt   : contenu spécifique à la tâche
    """
    # Format "chat" d'Ollama : messages avec rôle system / user
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "options": {
            "temperature": temperature
        },
        "stream": False  # on veut une réponse complète
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
        r.raise_for_status()
        data = r.json()
        # La réponse utile se trouve dans data["message"]["content"]
        return data.get("message", {}).get("content", "")
