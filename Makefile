.PHONY: init-env install venv fmt lint test test-recovery run env-check

# 1) Créer .env à partir de .env.example si absent (idempotent)
init-env:
	@if [ -f .env ]; then \
		echo "✔ .env déjà présent — rien à faire"; \
	else \
		if [ -f .env.example ]; then \
			cp .env.example .env; \
			echo "✅ Créé .env à partir de .env.example (pense à compléter les variables)"; \
		else \
			echo "❌ .env.example introuvable — crée-le d'abord"; \
			exit 1; \
		fi \
	fi

# 2) Installer le projet en mode editable (+ deps) dans le venv local
install: init-env
	@python3 -m venv .venv
	@. .venv/bin/activate && pip install -U pip
	@. .venv/bin/activate && pip install -e .
	@echo "✅ Installation terminée"

# (optionnel) forcer juste la (ré)création du venv et l'install
venv:
	@python3 -m venv .venv
	@. .venv/bin/activate && pip install -U pip
	@. .venv/bin/activate && pip install -e .

fmt:
	@echo "Skip (formatter non configuré)"

lint:
	@echo "Skip (linter non configuré)"

test:
	@. .venv/bin/activate && pytest -q

test-recovery:
	@. .venv/bin/activate && pytest -q -k "recovery or status_store"

run:
	@. .venv/bin/activate && python -m apps.orchestrator.main --task-file examples/task_rapport_80p.json

# 3) Vérifier rapidement que les variables d'env sont chargées
env-check:
	@. .venv/bin/activate && python - << 'PY'
		from core.config import get_var
		print("LLM_MODEL         =", get_var("LLM_MODEL"))
		print("USE_OLLAMA        =", get_var("USE_OLLAMA"))
		print("OLLAMA_MODEL      =", get_var("OLLAMA_MODEL"))
		print("DB_URL            =", get_var("DB_URL"))
	PY
