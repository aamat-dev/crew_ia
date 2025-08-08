"""
executor_llm.py — Exécutant "LLM" (placeholder)
- Produit un artifact .md structuré (front-matter + sections).
- Retourne True si tout va bien, False sinon.
"""

from __future__ import annotations
from textwrap import dedent

async def run_executor_llm(node, storage) -> bool:
    """
    Génère un artifact .md pour le nœud.
    Ici on produit un contenu standardisé. Tu pourras remplacer le corps par un appel LLM/Ollama.
    """
    title = getattr(node, "title", node.id)
    acceptance = getattr(node, "acceptance", "")
    node_type = getattr(node, "type", "task")
    description = getattr(node, "description", "")

    content = dedent(f"""\
    ---
    node_id: {node.id}
    title: {title}
    type: {node_type}
    acceptance: "{acceptance.replace('"','\\\"')}"
    ---

    # {title}

    > Type: {node_type} | Acceptation: {acceptance}

    ## Description
    {description or "—"}

    ## Démarche proposée
    1. Comprendre précisément le besoin
    2. Rechercher / analyser / décider (selon le type)
    3. Produire un livrable aligné avec l'acceptance

    ## Livrable attendu
    - {acceptance or "Livrable à préciser."}
    """)

    await storage.save_artifact(node_id=node.id, content=content)
    return True
