# Repository Guidelines

## Préférences personnelles — Alexandre
- Langue par défaut : français (France). Toujours répondre en français.
- Pédagogie : pas à pas, vulgariser si nécessaire (novice sur Codex/CLI).
- Style : professionnel, concis, humain et direct (sans fioritures).
- Sécurité : ne jamais afficher de secrets ; utiliser `.env` ; demander avant tout accès réseau hors `localhost`.
- Contrôle : proposer les modifications avec diff clair ; exécuter les tests avant de proposer un commit.
- En cas d’hésitation : énoncer un plan puis exécuter étape par étape.

## Project Structure & Module Organization
- `backend/api/fastapi_app`: FastAPI app (routes, services, models, schemas). Examples: `routes/agents.py`, `services/recruit_service.py`.
- `backend/orchestrator`: Orchestrator runtime, hooks, and client.
- `backend/core`: Agent registry, recruiter, shared config.
- `backend/tests`: Pytest suites (API, integration). 
- `dashboard/mini`, `frontend/cockpit`: UI packages (Vite/Next.js).
- `scripts`, `seeds`, `examples`, `.runs`: Utilities, seed data, sample tasks, run artifacts.

## Build, Test, and Development Commands
- `make install` — Create venv and install dependencies (.env auto-init if missing).
- `make api-migrate` — Apply Alembic migrations to the configured DB.
- `make api-run` — Start FastAPI in dev with reload (Uvicorn).
- `make test` — Run all tests quickly with pytest.
- `make db-up | db-down` — Start/stop Postgres via docker compose (if available).
- Orchestrator: `make run` (from JSON plan) or `make run-supervisor` (LLM-generated plan).

## Coding Style & Naming Conventions
- Python 3.10+, Pydantic v2, SQLModel/SQLAlchemy 2.
- Indentation: 4 spaces. Names: `snake_case` (vars/functions), `PascalCase` (classes), `UPPER_SNAKE` (constants), module files lowercase.
- Type hints required for new code. Keep functions short and explicit.
- Pre-commit runs basic hygiene hooks; no enforced formatter—mirror existing style in `backend/api`.

## Testing Guidelines
- Framework: pytest (+ pytest-asyncio). Place tests under `backend/tests`, name files `test_*.py`.
- Run: `make test` or selective: `pytest -q backend/tests -k "agents or recruit"`.
- Use provided fixtures (e.g., `client`) for API tests. Add assertions for persistence and conflicts when touching DB.

## Commit & Pull Request Guidelines
- Conventional Commits: `type(scope): summary` (e.g., `fix(api,agents): persist recruited agent with commit/refresh`).
- PRs must include: clear description, linked issue, test coverage for changes, and any schema notes. Ensure CI passes.

## Security & Configuration Tips
- Copy env: `make init-env`; review `.env.example`. Start DB with `make db-up`, then `make api-migrate` before running `make api-run`.
- Do not commit secrets. Prefer environment variables. API uses key + role headers by default.

## Agent-Specific Notes
- DB models in `backend/api/fastapi_app/models/agent.py`. Recruiting via `POST /agents/recruit` persists the agent; verify with `GET /agents`.
