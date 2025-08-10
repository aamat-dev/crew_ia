"""
Charge la configuration du projet depuis .env
- Utilise python-dotenv pour charger les variables d'environnement
- Compare avec .env.example pour détecter les variables manquantes
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ===============================
# 1) Charger .env
# ===============================
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
EXAMPLE_PATH = Path(__file__).resolve().parent.parent / ".env.example"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    print(f"⚠️ Fichier .env introuvable à {ENV_PATH} — certaines variables risquent de manquer.")

# ===============================
# 2) Vérifier par rapport à .env.example
# ===============================
if EXAMPLE_PATH.exists():
    with open(EXAMPLE_PATH, "r") as f:
        example_vars = {
            line.split("=")[0].strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        }
    missing_vars = [var for var in example_vars if var not in os.environ]
    if missing_vars:
        print(f"⚠️ Variables manquantes dans .env : {', '.join(missing_vars)}")
        print("💡 Pense à copier .env.example vers .env et à remplir tes clés.")
else:
    print(f"⚠️ Fichier .env.example introuvable à {EXAMPLE_PATH}")

# ===============================
# 3) Accès simplifié aux variables
# ===============================
def get_var(key: str, default=None):
    """Récupère une variable d'env avec valeur par défaut."""
    return os.getenv(key, default)

# ===============================
# 4) Exemples d'utilisation
# ===============================
if __name__ == "__main__":
    print("Modèle LLM :", get_var("LLM_MODEL"))
    print("Base URL Ollama :", get_var("OLLAMA_BASE_URL"))

# ===============================
# 5) Config LLM (providers + modèles + fallback) — compatible legacy
# ===============================

# Nouveau schéma (optionnel)
LLM_DEFAULT_PROVIDER = get_var("LLM_DEFAULT_PROVIDER")  # "ollama" | "openai" | None
LLM_DEFAULT_MODEL = get_var("LLM_DEFAULT_MODEL")
LLM_FALLBACK_ORDER = [
    p.strip() for p in get_var("LLM_FALLBACK_ORDER", "ollama,openai").split(",") if p.strip()
]
LLM_TIMEOUT_S = int(get_var("LLM_TIMEOUT_S", 60))
LLM_TEMPERATURE = float(get_var("LLM_TEMPERATURE", 0.2))
LLM_MAX_TOKENS = int(get_var("LLM_MAX_TOKENS", 1500))

# Overrides par agent (optionnels, nouveau schéma)
SUPERVISOR_PROVIDER = get_var("SUPERVISOR_PROVIDER")
SUPERVISOR_MODEL = get_var("SUPERVISOR_MODEL")
EXECUTOR_PROVIDER = get_var("EXECUTOR_PROVIDER")
EXECUTOR_MODEL = get_var("EXECUTOR_MODEL")

# ---- Compatibilité legacy (ton schéma actuel) ----
# USE_OLLAMA=1 => provider=ollama, modèle=OLLAMA_MODEL ou LLM_MODEL
# USE_OLLAMA=0 => provider=openai, modèle=LLM_MODEL
def _legacy_provider_model():
    use_ollama = get_var("USE_OLLAMA", "1").strip()
    if use_ollama == "1":
        provider = "ollama"
        model = get_var("OLLAMA_MODEL") or get_var("LLM_MODEL") or "llama3.1:8b"
    else:
        provider = "openai"
        model = get_var("LLM_MODEL") or "gpt-4o-mini"
    return provider, model

def _effective_defaults():
    """
    Règle de résolution :
    1) Si LLM_DEFAULT_PROVIDER/MODEL renseignés -> on les utilise
    2) Sinon on retombe sur l'ancien schéma (USE_OLLAMA + LLM_MODEL/OLLAMA_MODEL)
    """
    provider = LLM_DEFAULT_PROVIDER
    model = LLM_DEFAULT_MODEL
    if not provider or not model:
        legacy_p, legacy_m = _legacy_provider_model()
        provider = provider or legacy_p
        model = model or legacy_m
    return provider, model

def resolve_llm(agent_role: str):
    """
    Retourne (provider, model, params) pour un agent donné.
    - Priorité aux overrides par agent (nouveau schéma)
    - Sinon défauts (nouveau schéma) ou legacy si non renseignés
    """
    role = (agent_role or "").strip().upper()

    default_provider, default_model = _effective_defaults()

    if role == "SUPERVISOR":
        provider = SUPERVISOR_PROVIDER or default_provider
        model = SUPERVISOR_MODEL or default_model
    elif role == "EXECUTOR":
        provider = EXECUTOR_PROVIDER or default_provider
        model = EXECUTOR_MODEL or default_model
    else:
        provider, model = default_provider, default_model

    params = {
        "timeout_s": LLM_TIMEOUT_S,
        "temperature": LLM_TEMPERATURE,
        "max_tokens": LLM_MAX_TOKENS,
        "fallback_order": LLM_FALLBACK_ORDER,
    }
    return provider, model, params

if __name__ == "__main__":
    print("LLM (defaults) ->", _effective_defaults())
    print("LLM (executor) ->", resolve_llm("executor"))
    print("LLM (supervisor) ->", resolve_llm("supervisor"))