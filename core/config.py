"""
Charge la configuration du projet depuis .env
- Utilise python-dotenv pour charger les variables d'environnement
- Compare avec .env.example pour détecter les variables manquantes
- Fournit la résolution LLM stricte (provider/modèle par rôle) + compat legacy
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv


# ===============================
# 1) Charger .env
# ===============================
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
EXAMPLE_PATH = Path(__file__).resolve().parent.parent / ".env.example"

if ENV_PATH.exists():
    SKIP_DOTENV = os.getenv("CONFIG_SKIP_DOTENV", "").strip() in {"1", "true", "yes", "on"}
    if ENV_PATH.exists() and not SKIP_DOTENV:
    # Ne surcharge pas les variables déjà présentes (override=False par défaut)
        load_dotenv(dotenv_path=ENV_PATH)
else:
    print(f"⚠️ Fichier .env introuvable à {ENV_PATH} — certaines variables risquent de manquer.")

# ===============================
# 2) Vérifier par rapport à .env.example
# ===============================
if EXAMPLE_PATH.exists() and not SKIP_DOTENV:
    with open(EXAMPLE_PATH, "r", encoding="utf-8") as f:
        example_vars = {
            line.split("=", 1)[0].strip()
            for line in f
            if line.strip() and not line.strip().startswith("#") and "=" in line
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
def get_var(key: str, default: Any | None = None) -> Any | None:
    """Récupère une variable d'env avec valeur par défaut (chaîne vide => default)."""
    v = os.getenv(key)
    if v is None:
        return default
    v = v.strip()
    return v if v != "" else default


def _env_int(name: str, default: int) -> int:
    try:
        raw = os.getenv(name, "")
        return int(raw.strip()) if raw.strip() else default
    except Exception:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        raw = os.getenv(name, "")
        return float(raw.strip()) if raw.strip() else default
    except Exception:
        return default


def _role_key(role: str, suffix: str) -> str:
    # e.g. role="executor", suffix="TIMEOUT_S" => "EXECUTOR_TIMEOUT_S"
    return f"{role.upper()}_{suffix}"


# ===============================
# 4) Exemples d'utilisation (exécuter ce fichier seul)
# ===============================
if __name__ == "__main__":
    print("Modèle LLM (legacy):", get_var("LLM_MODEL"))
    print("Base URL Ollama :", get_var("OLLAMA_BASE_URL"))


# ===============================
# 5) Config LLM (providers + modèles + fallback) — compatible legacy
# ===============================

# Nouveau schéma (globaux)
LLM_DEFAULT_PROVIDER = get_var("LLM_DEFAULT_PROVIDER")  # "ollama" | "openai" | "anthropic" | ...
LLM_DEFAULT_MODEL = get_var("LLM_DEFAULT_MODEL")
LLM_FALLBACK_ORDER = [
    p.strip() for p in get_var("LLM_FALLBACK_ORDER", "ollama,openai").split(",") if p.strip()
]
LLM_TIMEOUT_S = int(get_var("LLM_TIMEOUT_S", 60))
LLM_TEMPERATURE = float(get_var("LLM_TEMPERATURE", 0.2))
LLM_MAX_TOKENS = int(get_var("LLM_MAX_TOKENS", 1500))

# Overrides par agent (nouveau schéma)
SUPERVISOR_PROVIDER = get_var("SUPERVISOR_PROVIDER")
SUPERVISOR_MODEL = get_var("SUPERVISOR_MODEL")
MANAGER_PROVIDER = get_var("MANAGER_PROVIDER")
MANAGER_MODEL = get_var("MANAGER_MODEL")
EXECUTOR_PROVIDER = get_var("EXECUTOR_PROVIDER")
EXECUTOR_MODEL = get_var("EXECUTOR_MODEL")
RECRUITER_PROVIDER = get_var("RECRUITER_PROVIDER")
RECRUITER_MODEL = get_var("RECRUITER_MODEL")


# ---- Compatibilité legacy ----
# USE_OLLAMA=1 => provider=ollama, modèle=OLLAMA_MODEL ou LLM_MODEL
# USE_OLLAMA=0 => provider=openai, modèle=LLM_MODEL
def _legacy_provider_model() -> Tuple[str, str]:
    use_ollama = str(get_var("USE_OLLAMA", "1")).strip()
    if use_ollama == "1":
        provider = "ollama"
        model = get_var("OLLAMA_MODEL") or get_var("LLM_MODEL") or "llama3.1:8b"
    else:
        provider = "openai"
        model = get_var("LLM_MODEL") or "gpt-4o-mini"
    return provider, model


def _effective_defaults() -> Tuple[str, str]:
    """
    Règle de résolution stricte des défauts :
    1) Si LLM_DEFAULT_PROVIDER/MODEL sont renseignés -> on les utilise tels quels (PRIORITÉ).
    2) Sinon on retombe sur l'ancien schéma (USE_OLLAMA + LLM_MODEL/OLLAMA_MODEL).
    """
    provider = LLM_DEFAULT_PROVIDER
    model = LLM_DEFAULT_MODEL
    if not provider or not str(provider).strip() or not model or not str(model).strip():
        legacy_p, legacy_m = _legacy_provider_model()
        provider = (str(provider).strip() if provider else legacy_p).lower()
        model = str(model).strip() if model else legacy_m
    else:
        provider = str(provider).strip().lower()
        model = str(model).strip()
    return provider, model


def resolve_llm(agent_role: str) -> Tuple[str, str, Dict[str, Any]]:
    """
    Retourne (provider, model, params) pour un agent donné.
    - Priorité aux overrides par agent (nouveau schéma)
    - Sinon défauts (nouveau schéma explicite) ou legacy si non renseignés
    ⚠️ Ne fait AUCUN check de disponibilité live (le fallback runtime est géré par le runner).
    """
    role = (agent_role or "").strip().upper()
    default_provider, default_model = _effective_defaults()

    if role == "SUPERVISOR":
        provider = (SUPERVISOR_PROVIDER or default_provider).strip().lower()
        model = (SUPERVISOR_MODEL or default_model).strip()
    elif role == "MANAGER":
        provider = (MANAGER_PROVIDER or default_provider).strip().lower()
        model = (MANAGER_MODEL or default_model).strip()
    elif role == "EXECUTOR":
        provider = (EXECUTOR_PROVIDER or default_provider).strip().lower()
        model = (EXECUTOR_MODEL or default_model).strip()
    elif role == "RECRUITER":
        provider = (RECRUITER_PROVIDER or default_provider).strip().lower()
        model = (RECRUITER_MODEL or default_model).strip()
    else:
        provider, model = default_provider, default_model

    # PARAMS PAR DÉFAUT (globaux)
    default_timeout = _env_int("LLM_TIMEOUT_S", 60)
    default_temp = _env_float("LLM_TEMPERATURE", 0.2)
    default_tokens = _env_int("LLM_MAX_TOKENS", 1500)

    # OVERRIDES PAR RÔLE (si présents)
    timeout = _env_int(_role_key(role, "TIMEOUT_S"), default_timeout)
    temperature = _env_float(_role_key(role, "TEMPERATURE"), default_temp)
    max_tokens = _env_int(_role_key(role, "MAX_TOKENS"), default_tokens)

    # Ordre de fallback (existant)
    fallback_raw = os.getenv("LLM_FALLBACK_ORDER", "ollama,openai")
    fallback_order = [x.strip() for x in fallback_raw.split(",") if x.strip()]

    params: Dict[str, Any] = {
        "timeout_s": timeout,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "fallback_order": fallback_order,
    }
    return provider, model, params


def resolve_llm_with_overrides(role: str, overrides: Dict[str, Any] | None = None) -> Tuple[str, str, Dict[str, Any]]:
    """
    Étend resolve_llm(role) avec des overrides éventuels (provenant d'une tâche/DB).
    Overrides possibles (clés exemples):
      - provider, model
      - temperature, max_tokens, timeout_s
      - fallback_order (liste ou "a,b,c")
    """
    base_provider, base_model, base_params = resolve_llm(role)
    overrides = overrides or {}

    provider = (overrides.get("provider", base_provider) or base_provider).strip().lower()
    model = (overrides.get("model", base_model) or base_model).strip()

    def _coalesce_num(key: str, base: Any) -> Any:
        return overrides.get(key, base)

    params: Dict[str, Any] = {
        "timeout_s": _coalesce_num("timeout_s", base_params["timeout_s"]),
        "temperature": _coalesce_num("temperature", base_params["temperature"]),
        "max_tokens": _coalesce_num("max_tokens", base_params["max_tokens"]),
        "fallback_order": base_params["fallback_order"],
    }

    fo = overrides.get("fallback_order")
    if isinstance(fo, str):
        params["fallback_order"] = [x.strip() for x in fo.split(",") if x.strip()]
    elif isinstance(fo, (list, tuple)) and fo:
        params["fallback_order"] = list(fo)

    return provider, model, params


# Petits helpers debug si besoin
if __name__ == "__main__":
    print("LLM (defaults) ->", _effective_defaults())
    print("LLM (executor) ->", resolve_llm("executor"))
    print("LLM (supervisor) ->", resolve_llm("supervisor"))
    print("LLM (manager) ->", resolve_llm("manager"))
    print("LLM (recruiter) ->", resolve_llm("recruiter"))
