.DEFAULT_GOAL := help
# ===== Makefile — Crew IA Orchestrator =====
SHELL := /bin/bash

# ---- Vars ----------------------------------------------------
PYTHON              ?= python3
PIP                 ?= pip
VENV_DIR            ?= .venv
ACTIVATE            := . $(VENV_DIR)/bin/activate
REQ_FILE            ?= requirements.txt
ENV_FILE            ?= .env

RUNS_ROOT           ?= .runs
DEFAULT_TASK_JSON   ?= examples/task_rapport_80p.json
RUN_ARGS            ?=

# Superviseur (CLI)
SUP_TITLE           ?= "Rapport 80p"
SUP_DESC            ?= "Décomposer la production d'un rapport de 80 pages."
SUP_ACCEPTANCE      ?= --acceptance "structure claire" --acceptance "pas de cycles"

# API
API_MODULE          ?= api.fastapi_app.app:app
API_HOST            ?= 127.0.0.1
API_PORT            ?= 8000

# ---- Help (target par défaut) --------------------------------
.PHONY: help
help:
	@echo "Targets utiles :"
	@echo "  init-env            -> crée .env depuis .env.example si absent"
	@echo "  install             -> crée venv + installe deps"
	@echo "  venv                -> (re)crée le venv"
	@echo "  clean-venv          -> supprime le venv"
	@echo "  deps-update        -> met à jour les dépendances"
	@echo "  test                -> pytest (rapide)"
	@echo "  test-extra          -> pytest tests_extra (si présents)"
	@echo "  test-all            -> pytest tests + tests_extra (si présents)"
	@echo "  test-recovery       -> pytest -k 'recovery or status_store' (si présent)"
	@echo "  run                 -> exécute avec un plan JSON (DEFAULT_TASK_JSON)"
	@echo "  run-supervisor      -> génère le plan via superviseur et exécute"
	@echo "  run-ollama          -> idem run-supervisor avec provider=ollama"
	@echo "  run-openai          -> idem run-supervisor avec provider=openai"
	@echo "  tail                -> tail du dernier .runs/*/orchestrator.log"
	@echo "  env-check           -> imprime quelques variables utiles"
	@echo "  api-run             -> lance FastAPI en dev (reload)"
	@echo "  api-run-prod        -> lance FastAPI en prod"
	@echo "  api-migrate         -> applique les migrations Alembic"
	@echo "  api-test            -> teste l’API (si tests présents)"
	@echo "  db-up / db-down     -> docker compose (postgres/pgadmin) si docker-compose.yml existe"
	@echo "  db-logs / db-reset  -> idem"
	@echo "  validate            -> valide les sidecars .llm.json"
	@echo "  validate-strict     -> validation stricte des sidecars"
	@echo "  ui-run-e2e          -> build + preview + tests e2e UI"
.PHONY: init-env
init-env:
	@if [ -f $(ENV_FILE) ]; then \
		echo "✔ $(ENV_FILE) déjà présent — rien à faire"; \
	else \
		if [ -f $(ENV_FILE).example ]; then \
			cp $(ENV_FILE).example $(ENV_FILE); \
			echo "✅ Créé $(ENV_FILE) à partir de $(ENV_FILE).example"; \
		else \
			echo "❌ $(ENV_FILE).example introuvable — crée-le d'abord"; \
			exit 1; \
		fi \
	fi

.PHONY: venv
venv:
	@$(PYTHON) -m venv $(VENV_DIR)
	@$(ACTIVATE) && $(PIP) install -U pip
	@if [ -f $(REQ_FILE) ]; then \
		$(ACTIVATE) && $(PIP) install -r $(REQ_FILE); \
	fi
	@echo "✅ Venv prêt"

.PHONY: install
install: init-env venv
	@echo "✅ Installation terminée"

.PHONY: clean-venv
clean-venv:
	@rm -rf $(VENV_DIR)
	@echo "🧹 Venv supprimé"
.PHONY: deps-update
deps-update: ensure-venv
	@$(ACTIVATE) && $(PIP) install -r $(REQ_FILE)
	@echo "✅ Dépendances mises à jour"

# ---- Qualité -------------------------------------------------
.PHONY: fmt
fmt:
	@echo "⏭️  Skip (formatter non configuré)"

.PHONY: lint
lint:
	@echo "⏭️  Skip (linter non configuré)"

# ---- Tests ---------------------------------------------------
.PHONY: ensure-venv
ensure-venv:
	@if [ ! -d $(VENV_DIR) ]; then $(MAKE) install; fi

.PHONY: test
test: ensure-venv
	@$(ACTIVATE) && pytest -q

.PHONY: test-extra
test-extra:
	pytest tests_extra -v

.PHONY: test-all
test-all: ensure-venv
	@$(ACTIVATE) && pytest -q && pytest tests_extra -v

.PHONY: test-recovery
test-recovery: ensure-venv
	@$(ACTIVATE) && pytest -q -k "recovery or status_store"

# ---- Exécution ------------------------------------------------
# Mode plan JSON explicite
.PHONY: run
run: ensure-venv
	@if [ ! -f "$(DEFAULT_TASK_JSON)" ]; then \
		echo "❌ Plan JSON manquant: $(DEFAULT_TASK_JSON)"; exit 1; \
	fi
	@$(ACTIVATE) && $(PYTHON) -m apps.orchestrator.main --task-file "$(DEFAULT_TASK_JSON)" $(RUN_ARGS)

# Mode superviseur (génère un plan via LLM)
.PHONY: run-supervisor
run-supervisor: ensure-venv
	@$(ACTIVATE) && $(PYTHON) -m apps.orchestrator.main \
		--use-supervisor \
		--title $(SUP_TITLE) \
		--description $(SUP_DESC) \
		$(SUP_ACCEPTANCE) \
		$(RUN_ARGS)

# Profils rapides
.PHONY: run-ollama
run-ollama: ensure-venv
	@LLM_DEFAULT_PROVIDER=ollama LLM_DEFAULT_MODEL=llama3.1:8b \
	$(ACTIVATE) && $(PYTHON) -m apps.orchestrator.main \
		--use-supervisor \
		--title $(SUP_TITLE) \
		--description $(SUP_DESC) \
		$(SUP_ACCEPTANCE) \
		$(RUN_ARGS)

.PHONY: run-openai
run-openai: ensure-venv
	@LLM_DEFAULT_PROVIDER=openai LLM_DEFAULT_MODEL=gpt-4o-mini \
	$(ACTIVATE) && $(PYTHON) -m apps.orchestrator.main \
		--use-supervisor \
		--title $(SUP_TITLE) \
		--description $(SUP_DESC) \
		$(SUP_ACCEPTANCE) \
		$(RUN_ARGS)

.PHONY: tail
tail:
	@latest_run="$$(ls -dt $(RUNS_ROOT)/* 2>/dev/null | head -1)"; \
	if [ -z "$$latest_run" ]; then echo "No runs yet."; exit 0; fi; \
	if [ ! -f "$$latest_run/orchestrator.log" ]; then echo "No orchestrator.log in $$latest_run"; exit 0; fi; \
	echo "Tailing $$latest_run/orchestrator.log"; \
	tail -f "$$latest_run/orchestrator.log"

.PHONY: tail-events
tail-events: ensure-venv
	@if [ -z "$(RUN_ID)" ]; then echo "RUN_ID requis"; exit 1; fi
	@$(ACTIVATE) && $(PYTHON) tools/tail_events.py --run-id $(RUN_ID) --url http://$(API_HOST):$(API_PORT)/events

.PHONY: env-check
env-check: ensure-venv
	@$(ACTIVATE) && $(PYTHON) - << 'PY'
		from core.config import get_var
		print("LLM_DEFAULT_PROVIDER =", get_var("LLM_DEFAULT_PROVIDER"))
		print("LLM_DEFAULT_MODEL    =", get_var("LLM_DEFAULT_MODEL"))
		print("OLLAMA_MODEL         =", get_var("OLLAMA_MODEL"))
		print("OPENAI_FALLBACK_MODEL=", get_var("OPENAI_FALLBACK_MODEL"))
		print("RUNS_ROOT            =", get_var("RUNS_ROOT"))
	PY

# ---- API (FastAPI) -------------------------------------------
.PHONY: api-run
api-run: ensure-venv
		@$(ACTIVATE) && uvicorn $(API_MODULE) --reload --host $(API_HOST) --port $(API_PORT) --env-file $(ENV_FILE)

.PHONY: api-run-metrics
api-run-metrics: ensure-venv
	@export METRICS_ENABLED=1; \
	$(ACTIVATE) && uvicorn $(API_MODULE) --reload --port $(API_PORT)

.PHONY: api-run-prod
api-run-prod: ensure-venv
        @$(ACTIVATE) && uvicorn $(API_MODULE) --host 0.0.0.0 --port $(API_PORT) --workers 2

.PHONY: api-migrate
api-migrate: ensure-venv
	@$(ACTIVATE) && alembic upgrade head

.PHONY: api-test
api-test: ensure-venv
	@if [ -d api/tests ]; then \
		PYTHONWARNINGS=ignore $(ACTIVATE) && pytest -q api/tests; \
	else \
		echo "⏭️  Pas de dossier api/tests — skip"; \
	fi

.PHONY: api-e2e
api-e2e: ensure-venv
	@$(ACTIVATE) && pytest -q api/tests

.PHONY: api-e2e-happy
api-e2e-happy: ensure-venv
	@$(ACTIVATE) && pytest -q api/tests/test_tasks_happy_e2e.py

.PHONY: api-e2e-meta
api-e2e-meta: ensure-venv
	@$(ACTIVATE) && pytest -q api/tests/test_tasks_meta_e2e.py

# ---- Scripts divers -----------------------------------------
.PHONY: task-plan-start
task-plan-start: ensure-venv
	@$(ACTIVATE) && $(PYTHON) scripts/task_plan_start.py

# ---- Validation ----------------------------------
.PHONY: validate validate-all validate-strict validate-non-uuid
validate: ensure-venv
	@$(ACTIVATE) && python tools/validate_sidecars.py

validate-all: ensure-venv
	@$(ACTIVATE) && python tools/validate_sidecars.py --all

validate-strict: ensure-venv
	@$(ACTIVATE) && python tools/validate_sidecars.py --strict

validate-non-uuid: ensure-venv
	@$(ACTIVATE) && python tools/validate_sidecars.py --non-uuid

# ---- Mini Dashboard ---------------------------
.PHONY: dash-mini-install dash-mini-run dash-mini-build dash-mini-test dash-mini-e2e dash-mini-e2e-ci dash-mini-ci-local ui-run-e2e
dash-mini-install:
	cd dashboard/mini && npm ci


dash-mini-run:
	cd dashboard/mini && npm run dev -- --host 0.0.0.0 --port 5173


dash-mini-build:
	cd dashboard/mini && npm run build && echo "🌐 Preview sur http://localhost:5173" && npm run preview


dash-mini-test:
	cd dashboard/mini && npm test -- --run


dash-mini-e2e:
	cd dashboard/mini && PREVIEW_URL=http://localhost:5173 npm run e2e


dash-mini-e2e-ci:
	cd dashboard/mini && npm run e2e:ci


dash-mini-ci-local:
	        cd dashboard/mini && npm run lint && npm run typecheck && npm test -- --run && npm run build


# ---- UI ------------------------------------------------------
.PHONY: ui-run-e2e
ui-run-e2e:
	cd dashboard/mini && npm run build
	cd dashboard/mini && (npm run preview & pid=$$!; \
		sleep 2; \
		PREVIEW_URL=http://localhost:5173 npm run e2e; \
		kill $$pid)

# ---- Docker compose (optionnel) -------------------------------
HAS_COMPOSE := $(shell test -f docker-compose.yml && echo yes || echo no)

.PHONY: db-up db-down db-logs db-reset
db-up:
	@if [ "$(HAS_COMPOSE)" != "yes" ]; then echo "⏭️  docker-compose.yml absent — skip"; exit 0; fi
	@docker compose up -d postgres pgadmin && echo "PgAdmin: http://localhost:5050"

db-down:
	@if [ "$(HAS_COMPOSE)" != "yes" ]; then echo "⏭️  docker-compose.yml absent — skip"; exit 0; fi
	@docker compose down

db-logs:
	@if [ "$(HAS_COMPOSE)" != "yes" ]; then echo "⏭️  docker-compose.yml absent — skip"; exit 0; fi
	@docker compose logs -f postgres

db-reset:
	@if [ "$(HAS_COMPOSE)" != "yes" ]; then echo "⏭️  docker-compose.yml absent — skip"; exit 0; fi
	@docker compose down -v
	@docker compose up -d postgres pgadmin
	@sleep 3
	@if [ -n "$$ALEMBIC_DATABASE_URL" ]; then \
		$(ACTIVATE) && alembic upgrade head; \
	else \
		echo "ℹ️  ALEMBIC_DATABASE_URL non défini — migration skip"; \
	fi
