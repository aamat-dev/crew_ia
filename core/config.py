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
