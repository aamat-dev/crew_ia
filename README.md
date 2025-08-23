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

> **Note :** Après un `git pull`, lancez `make deps-update` pour installer les nouvelles dépendances.

Pour lister les événements d'un run spécifique :

```
curl -H "X-API-Key: test-key" "http://localhost:8000/events?run_id=<RUN_ID>"
```

The server always returns timestamps in UTC. Clients may supply `X-Timezone`
header to ask for conversion to a specific zone.

## Hiérarchie

### Variables `.env`

Les variables essentielles sont définies dans `.env` (voir [`.env.example`](.env.example) pour la liste complète). Les principales :


- `API_KEY` — clé requise sur toutes les requêtes API.
- `DATABASE_URL` — URL de connexion asynchrone à la base.
- `CORS_ORIGINS` — origines autorisées pour CORS.
- `LLM_DEFAULT_PROVIDER` et `LLM_DEFAULT_MODEL` — fournisseur et modèle par défaut des agents.

### Presets dev / prod


Dans `.env.example` se trouvent deux profils commentés :

```
# --- DEV : Ollama only ---
# LLM_DEFAULT_PROVIDER=ollama
# LLM_DEFAULT_MODEL=llama3.1:8b
...
# --- PROD : OpenAI only ---
# LLM_DEFAULT_PROVIDER=openai
# LLM_DEFAULT_MODEL=gpt-4o-mini
...
```

Décommentez le bloc correspondant à votre contexte pour obtenir une configuration de base.

### Comment lancer


- API : `make api-run` (dev) ou `make api-run-prod` (prod).
- CLI : `python -m apps.orchestrator.main --use-supervisor --title "Rapport 80p"` pour générer un plan via le superviseur (cf. [`apps/orchestrator/main.py`](apps/orchestrator/main.py)).

### Commandes de test

- **API** : déclencher un run ad‑hoc via `POST /tasks` :

  ```
  curl -X POST -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
       -d '{"title":"Demo","task_spec":{"type":"demo"}}' \
       http://localhost:8000/tasks
  ```

- **CLI** : lancer l'orchestrateur en générant le plan :

  ```
  python -m apps.orchestrator.main --use-supervisor --title "Rapport 80p"
  ```

### Schéma textuel du flux

```
Supervisor → Manager → Exécutants → sidecars
```

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

## Observabilité

### Metrics Prometheus

- Activer avec la variable `METRICS_ENABLED=1` (ex : `make api-run-metrics`).
- Les métriques sont exposées sur `/metrics`.
- Exemple minimal de configuration pour Prometheus :

```yaml
scrape_configs:
  - job_name: 'crew_ia_api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: /metrics
```

### Sentry

- Variables requises : `SENTRY_DSN`, `SENTRY_ENV`, `RELEASE`.
- Test rapide : appeler une route qui lève une exception, l'événement apparaît dans Sentry (mock possible côté tests).
