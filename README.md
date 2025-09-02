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

### Feedbacks

Créer un feedback manuel :

```
curl -X POST "http://localhost:8000/feedbacks" \
 -H 'Content-Type: application/json' \
 -H 'X-API-Key: test-key' -H 'X-Request-ID: demo-1' -H 'X-Role: editor' \
 -d '{
   "run_id": "11111111-1111-1111-1111-111111111111",
   "node_id": "22222222-2222-2222-2222-222222222222",
   "source": "human",
   "score": 35,
   "comment": "Format JSON invalide"
 }'
```

Un feedback automatique est généré après chaque nœud. Si le score est
inférieur au seuil configuré (`FEEDBACK_CRITICAL_THRESHOLD`, 60 par
défaut) :

1. Le nœud est marqué en pause et un événement `feedback.critical` est
émis.
2. Depuis l'interface, un re-run guidé peut être déclenché après avoir
corrigé le prompt ou relancé le nœud.
![Feedback Panel](docs/feedback-panel.png)

Workflow complet :

1. Saisir un feedback humain dans le panneau Feedback (score, commentaire).
2. Le tableau affiche immédiatement les feedbacks auto et humains.
3. En cas de score critique, utiliser « Re-run guidé » pour relancer le nœud.

### Scénario E2E feedback auto + re-run

1. Lancer l'API (`make api-run`).
2. Exécuter un DAG : un feedback auto est créé et visible dans le
   panneau Feedback du dashboard.
3. En cas de score critique, utiliser le bouton « Re-run guidé » pour
   relancer le nœud après correction.

### Tests E2E UI (Playwright)

1. Lancer le front en mode dev ou preview :
   ```bash
   (cd dashboard/mini && npm i && npm run dev)
   # repérez l'URL, par ex. http://localhost:5173
   ```
2. Exécuter les tests :
   ```bash
   PREVIEW_URL=http://localhost:5173 make ui-feedbacks-e2e
   ```
   Le test est ignoré si `PREVIEW_URL` n'est pas défini.

## Scénario E2E (API + UI)

### Prérequis

- Python 3.11+
- Node 18+
- `make`, `npm`

Variables d'environnement minimales :

```
API_KEY=test-key
DATABASE_URL=sqlite+aiosqlite:///./app.db
API_URL=http://localhost:8000
```

### Étapes (local)

1. Appliquer les migrations :

   ```bash
   make api-migrate
   ```

2. Démarrer l'API (terminal séparé) :

   ```bash
   make api-run
   ```

3. Déclencher le flux de démonstration (création → plan → assignation → start) :

   ```bash
   make task-plan-start
   ```

### Étapes (prévisualisation UI)

Lance les tests E2E Playwright sur la version buildée du dashboard :

```bash
make ui-run-e2e
```

### Exemples cURL

```bash
# 1) Créer une tâche brouillon
curl -X POST -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"title":"Demo"}' $API_URL/tasks

# 2) Générer un plan
curl -X POST -H "X-API-Key: $API_KEY" \
  $API_URL/tasks/<TASK_ID>/plan

# 3) Assigner des nœuds
curl -X POST -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"items":[{"node_id":"n1","role":"writer","agent_id":"a1","llm_backend":"openai","llm_model":"gpt-4o-mini"}]}' \
  $API_URL/plans/<PLAN_ID>/assignments

# 4) Démarrer (dry run)
curl -X POST -H "X-API-Key: $API_KEY" \
  "$API_URL/tasks/<TASK_ID>/start?dry_run=true"
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
- `FEEDBACK_CRITICAL_THRESHOLD` — seuil (0-100) déclenchant un badge critique (défaut 60).
- `FEEDBACK_REVIEW_TIMEOUT_MS` — délai d'attente de l'auto‑review en ms (défaut 3500).

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

## Fil F — Validation sidecars

### Objectifs
- Qualité des sidecars, observabilité, analytics, coûts.
- Rétro‑compatibilité assurée par [`_normalize_llm_sidecar`](apps/orchestrator/api_runner.py).

### Fichiers
- Schéma : [`schemas/llm_sidecar.schema.json`](schemas/llm_sidecar.schema.json)
- Exemples : [`schemas/examples/llm_sidecar.valid.json`](schemas/examples/llm_sidecar.valid.json), [`schemas/examples/llm_sidecar.invalid.json`](schemas/examples/llm_sidecar.invalid.json)
- CLI : [`tools/validate_sidecars.py`](tools/validate_sidecars.py)

### Commandes
```bash
make validate
make validate-strict
python tools/validate_sidecars.py --since <run_id|timestamp>
```

### CI
- Job `validate` en amont, qui bloque en cas d'échec.

### Stratégie d’évolution
- version : "1.0" (actuelle) ; ajouts non‑breaking → "1.1".
- Ne jamais supprimer un champ sans migration.
- Champs dépréciés tolérés en mode normal, bloqués en `--strict`.
- `latency_ms` = latence mur‑à‑mur (demande→réponse).

### Exemple
Exemple de sidecar valide :

```json
{
  "version": "1.0",
  "provider": "openai",
  "model": "gpt-4o",
  "latency_ms": 1200,
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  },
  "cost": { "estimated": 0.12 },
  "prompts": { "system": "Vous êtes un assistant IA.", "user": "Bonjour" },
  "timestamps": {
    "started_at": "2024-05-21T10:00:00Z",
    "ended_at": "2024-05-21T10:00:01Z"
  },
  "run_id": "123e4567-e89b-42d3-a456-426614174000",
  "node_id": "123e4567-e89b-42d3-a456-426614174001"
}
```

## Cockpit front-end

Un tableau de bord Next.js est disponible dans `apps/cockpit`.
Pour le démarrer en développement :

```bash
cd apps/cockpit
npm run dev
```

Cela démarre un serveur local accessible sur http://localhost:3000.
