# Crew Orchestrator — API + Cockpit

Petit orchestrateur d’agents avec API FastAPI, stockage Postgres/FS et cockpit Next.js. Objectif: onboarding rapide, runs observables et mini‑dashboard prêt pour la démo.

Architecture (vue simplifiée)

```
 [Cockpit Next.js]  ───────── HTTP ─────────▶  [FastAPI]
     (frontend)                            (backend/api)
                                               │
                                       ┌───────┴────────┐
                                       │ Storage (DB/FS)│
                                       │  Postgres + FS │
                                       └───────┬────────┘
                                               │
                                    [Orchestrator Runtime]
                                           (backend/orchestrator)
```

## Quickstart (≤ 5 minutes)

1) Dépendances
- Python 3.11+, Node 18+, `make`, Postgres local (ou Docker Compose fourni).

2) Environnement
- Copier l’exemple et ajuster les variables minimales:
  ```bash
  make init-env
  # éditez .env si besoin
  ```

  Variables essentielles:
  - API_KEY: clé API (ex: test-key)
  - DATABASE_URL: `postgresql+asyncpg://crew:crew@localhost:5432/crew`
  - ALEMBIC_DATABASE_URL: `postgresql+psycopg://crew:crew@localhost:5432/crew`
  - ALLOWED_ORIGINS: `http://localhost:3000,http://localhost:5173`
  - NEXT_PUBLIC_API_URL: `http://127.0.0.1:8000` (cockpit)
  - NEXT_PUBLIC_API_KEY: `test-key` (doit = API_KEY)

3) Installation + migrations
```bash
make install
make api-migrate
```

4) Démarrer l’API et le Cockpit
```bash
# Terminal A — API (FastAPI + reload)
make api

# Terminal B — Cockpit (Next.js, dossier frontend/cockpit)
make cockpit-install
make cockpit
```

5) Démonstration rapide
```bash
# Déclencher un run ad-hoc (demo)
curl -X POST -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"title":"Demo","task_spec":{"type":"demo"}}' \
  $NEXT_PUBLIC_API_URL/tasks

# Suivre le run
curl -H "X-API-Key: $API_KEY" "$NEXT_PUBLIC_API_URL/runs"
```

6) Voir dans le cockpit
- Ouvrez le cockpit sur http://localhost:3000 (ou port affiché) et naviguez vers la page Runs; vous devez voir le run Demo et ses événements.

Notes
- Après un `git pull`, lancez `make deps-update`.
- Pour peupler des modèles/agents de démonstration: `make seed`.

Pour lister les événements d'un run spécifique :

```
curl -H "X-API-Key: test-key" "http://127.0.0.1:8000/events?run_id=<RUN_ID>"
```

## Variables `.env` (essentielles)

Voir `.env.example` pour la liste complète. Essentielles côté dev:
- API_KEY: clé API
- DATABASE_URL / ALEMBIC_DATABASE_URL: URLs Postgres (async/sync)
- ALLOWED_ORIGINS: CORS (ex: http://localhost:3000,http://localhost:5173)
- NEXT_PUBLIC_API_URL / NEXT_PUBLIC_API_KEY: accès cockpit
- VITE_API_BASE_URL (si mini-dashboard Vite)
- LLM_DEFAULT_PROVIDER / LLM_DEFAULT_MODEL (optionnel)
- FEEDBACK_CRITICAL_THRESHOLD / FEEDBACK_REVIEW_TIMEOUT_MS (optionnel)

Sécurité (prod stricte / dev souple)
- REQUIRE_API_KEY=true — en prod, impose `X-API-Key` sur toutes les routes sensibles.
- ENV=dev + REQUIRE_API_KEY=false — en dev local, l’API peut laisser passer sans clé.
- FEATURE_RBAC=true — active `X-Role` minimal (viewer/editor/admin) sur routes critiques.
- Par défaut, les tests exigent la clé (REQUIRE_API_KEY=true) et surchargent l’auth via FastAPI overrides.

## Commandes Make principales

- `make install` — venv + deps
- `make api` — API en dev (reload)
- `make cockpit` — cockpit Next.js en dev
- `make test` — tests rapides
- `make api-migrate` — migrations Alembic (DB)
- `make seed` — seed agents (templates + matrice)
- `make format` / `make lint` — hooks de base (placeholders)

### Feedbacks

Créer un feedback manuel :

```
curl -X POST "http://127.0.0.1:8000/feedbacks" \
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

1. Lancer le cockpit Next.js en mode dev ou preview :
   ```bash
   (cd frontend/cockpit && npm install && npm run dev)
   # repérez l'URL, par ex. http://localhost:3000
   ```
2. Exécuter les tests :
   ```bash
   make ui-feedbacks-e2e
   ```

## Scénario E2E (API + UI)

### Prérequis

- Python 3.11+
- Node 18+
- `make`, `npm`

Variables d'environnement minimales :

```
API_KEY=test-key
DATABASE_URL=postgresql+asyncpg://crew:crew@localhost:5432/crew
ALEMBIC_DATABASE_URL=postgresql+psycopg://crew:crew@localhost:5432/crew
API_URL=http://127.0.0.1:8000
```

### Étapes (local)

1. Appliquer les migrations :

   ```bash
   ALEMBIC_DATABASE_URL=postgresql+psycopg://crew:crew@localhost:5432/crew \
     alembic -c backend/migrations/alembic.ini upgrade head
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
- `ALEMBIC_DATABASE_URL` — URL de connexion synchrone utilisée par Alembic.
- `API_URL` — URL de base de l'API.
- `ALLOWED_ORIGINS` — origines autorisées pour CORS (défaut `http://localhost:3000,http://localhost:5173`).
  - Inclut par défaut les ports dev de Next (`3000`) et Vite (`5173`).
  - Ne pas utiliser d'autres variables CORS : `ALLOWED_ORIGINS` est la source unique.

- Frontends (optionnel selon le client utilisé) :
  - `VITE_API_BASE_URL` — base API pour le mini-dashboard Vite.
  - `NEXT_PUBLIC_API_URL` — base API publique pour le cockpit Next.js.
  - `NEXT_PUBLIC_API_KEY` — clé API utilisée par le cockpit (doit correspondre à `API_KEY`).

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
- CLI : `python -m orchestrator.main --use-supervisor --title "Rapport 80p"` pour générer un plan via le superviseur (cf. [`apps/orchestrator/main.py`](apps/orchestrator/main.py)).

### Commandes de test

- **API** : déclencher un run ad‑hoc via `POST /tasks` :

  ```
  curl -X POST -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
       -d '{"title":"Demo","task_spec":{"type":"demo"}}' \
       http://127.0.0.1:8000/tasks
  ```

- **CLI** : lancer l'orchestrateur en générant le plan :

  ```
  python -m orchestrator.main --use-supervisor --title "Rapport 80p"
  ```

### Schéma textuel du flux

```
Supervisor → Manager → Exécutants → sidecars
```

## Authentication & CORS

All endpoints except `/health` require the `X-API-Key` header. Origins allowed
for CORS are configured via the `ALLOWED_ORIGINS` variable in `.env` (comma separated
list).

## Database migrations

Alembic est utilisé pour les migrations de schéma. Pour appliquer les
migrations localement :

```bash
ALEMBIC_DATABASE_URL=postgresql+psycopg://crew:crew@localhost:5432/crew \
  alembic -c backend/migrations/alembic.ini upgrade head
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
      - targets: ['127.0.0.1:8000']
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
- Schéma : [`backend/schemas/llm_sidecar.schema.json`](backend/schemas/llm_sidecar.schema.json)
- Exemples : [`backend/schemas/examples/llm_sidecar.valid.json`](backend/schemas/examples/llm_sidecar.valid.json), [`backend/schemas/examples/llm_sidecar.invalid.json`](backend/schemas/examples/llm_sidecar.invalid.json)
- CLI : [`backend/tools/validate_sidecars.py`](backend/tools/validate_sidecars.py)

### Commandes
```bash
make validate
make validate-strict
python backend/tools/validate_sidecars.py --since <run_id|timestamp>
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

Un tableau de bord Next.js est disponible dans `frontend/cockpit`.

Pour le démarrer en développement :

```bash
cd frontend/cockpit
npm run dev
```

Cela démarre un serveur local accessible sur http://localhost:3000.
## Arborescence

- `backend/api` — API FastAPI (app, routes, deps, clients, middlewares).
- `backend/core` — noyau (agents, LLM, planning, stockage, télémétrie, IO).
- `backend/orchestrator` — exécution du graphe et services d’orchestration.
- `backend/migrations` — Alembic (`alembic.ini`, `env.py`, `versions/`).
- `backend/tests` — tests API, unitaires, intégration, e2e.
- `frontend/cockpit` — cockpit Next.js (UI principale).
