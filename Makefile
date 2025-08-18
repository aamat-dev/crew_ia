.PHONY: db-up db-down db-logs db-init db-revision db-upgrade db-reset init-env install venv fmt lint test test-recovery run env-check

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

test-agents:
	pytest -k "runner or supervisor or executor_llm_artifact or normalize_super_plan" -v

run-ollama:
	LLM_DEFAULT_PROVIDER=ollama LLM_DEFAULT_MODEL=llama3.1:8b make run

run-openai:
	LLM_DEFAULT_PROVIDER=openai LLM_DEFAULT_MODEL=gpt-4o-mini make run

.PHONY: tail
tail:
	@latest_run="$$(ls -dt .runs/* 2>/dev/null | head -1)"; \
	if [ -z "$$latest_run" ]; then echo "No runs yet."; exit 0; fi; \
	echo "Tailing $$latest_run/orchestrator.log ..."; \
	tail -f "$$latest_run/orchestrator.log"

db-up:
	 docker compose up -d postgres pgadmin
	 @echo "PgAdmin: http://localhost:5050 (login: $$PGADMIN_DEFAULT_EMAIL)"

db-down:
	 docker compose down

db-logs:
	 docker compose logs -f postgres

db-init:
	 @if [ ! -d "alembic" ]; then alembic init alembic; fi
	 @echo "Alembic initialisé (si nécessaire). Pense à configurer alembic.ini/env.py."

db-revision:
        ALEMBIC_DATABASE_URL=$$ALEMBIC_DATABASE_URL alembic revision --autogenerate -m "$$msg"

db-upgrade:
	 ALEMBIC_DATABASE_URL=$$ALEMBIC_DATABASE_URL alembic upgrade head

db-reset:
	 docker compose down -v
	 docker compose up -d postgres pgadmin
	 sleep 3
	 ALEMBIC_DATABASE_URL=$$ALEMBIC_DATABASE_URL alembic upgrade head

# === API FastAPI (lecture seule) ===
API_MODULE=api.fastapi_app.app:app
API_HOST?=0.0.0.0
API_PORT?=8080

.PHONY: api-run api-run-prod api-test api-lint api-curl-examples

api-run:
        uvicorn api.fastapi_app.app:app --reload --env-file .env

api-run-prod:
	uvicorn api.fastapi_app.app:app --host 0.0.0.0 --port 8000 --workers 2

api-test:
	PYTHONWARNINGS=ignore pytest -q api/tests -k test_tasks_e2e

api-lint:
	ruff check .
	black --check .
	# pyright (si présent) : pyright

api-curl-examples:
	@echo "Health (public)"
	@curl -i http://localhost:8000/health
	@echo "\\nRuns (auth)"
	@API_KEY=$$(grep ^API_KEY .env | cut -d= -f2); \\
	curl -i -H "X-API-Key: $$API_KEY" "http://localhost:8000/runs?limit=5&order_by=-started_at"