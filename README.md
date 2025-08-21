# Crew Orchestrator API

Minimal FastAPI application exposing read-only endpoints to inspect runs, nodes,
artifacts and events. A `/tasks` endpoint allows to trigger a small ad‑hoc run
used for testing.

## Quickstart

1. Create a `.env` file with at least:

```
API_KEY=test-key
DATABASE_URL=sqlite+aiosqlite:///./app.db
CORS_ORIGINS=
```

2. Start the API with Uvicorn (loads variables from `.env`):

```
make api-run
```

3. Query the API (replace the API key if you changed it):

```
curl -H "X-API-Key: test-key" http://localhost:8000/runs
```

Pour lister les événements d'un run spécifique :

```
curl -H "X-API-Key: test-key" "http://localhost:8000/events?run_id=<RUN_ID>"
```

The server always returns timestamps in UTC. Clients may supply `X-Timezone`
header to ask for conversion to a specific zone.

## Authentication & CORS

All endpoints except `/health` require the `X-API-Key` header. Origins allowed
for CORS are configured via the `CORS_ORIGINS` variable in `.env` (comma separated
list).

## Database migrations

Alembic is used for schema migrations. Set `ALEMBIC_DATABASE_URL` and run:

```
make db-revision msg="add table"
make db-upgrade
```

## Make targets

- `make api-run` – launch the API with hot reload and `.env` loading.
- `make api-test` – run API tests.
- `make db-revision msg="..."` – create a new Alembic revision.
- `make db-upgrade` – apply migrations to the database.
