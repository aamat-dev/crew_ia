#!/usr/bin/env bash
set -euo pipefail

# ========= Helpers =========
BLUE='\033[1;34m'; GREEN='\033[1;32m'; YELLOW='\033[1;33m'; RED='\033[1;31m'; NC='\033[0m'
log()  { echo -e "${BLUE}[$(date +%H:%M:%S)]$NC $*"; }
ok()   { echo -e "${GREEN}✔$NC $*"; }
warn() { echo -e "${YELLOW}⚠$NC $*"; }
die()  { echo -e "${RED}✖$NC $*"; exit 1; }

require() {
  command -v "$1" >/dev/null 2>&1 || die "Commande requise manquante: $1"
}

# ========= Prérequis =========
require jq
require curl
require uvicorn
require grep
require sed
require awk

# Racine projet = dossier contenant ce script / remonte d'1 niveau si besoin
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR%/scripts}"
cd "$ROOT_DIR"

test -f ".env" || die ".env introuvable à la racine du projet."

# Charge .env (sans exporter tout le shell)
API_KEY="$(grep -E '^API_KEY=' .env | cut -d= -f2- | tr -d '"')" || true
DB_URL="$(grep -E '^ALEMBIC_DATABASE_URL=' .env | cut -d= -f2- | tr -d '"')" || true
ASYNC_DB_URL="$(grep -E '^DATABASE_URL=' .env | cut -d= -f2- | tr -d '"')" || true
API_HOST="127.0.0.1"
API_PORT="8000"
BASE_URL="http://${API_HOST}:${API_PORT}"

test -n "${API_KEY:-}" || die "API_KEY manquante dans .env"
test -n "${DB_URL:-}" || warn "ALEMBIC_DATABASE_URL manquant dans .env (ok si DB déjà migrée)."
test -n "${ASYNC_DB_URL:-}" || warn "DATABASE_URL manquant dans .env (l'API pourrait échouer à se connecter)."

# ========= Étape 1 : DB up & migrations =========
if command -v docker >/dev/null 2>&1 && test -f docker-compose.yml; then
  log "Démarrage Postgres (docker compose) si nécessaire…"
  docker compose up -d postgres >/dev/null 2>&1 || true
  sleep 2
else
  warn "docker compose absent ou pas de docker-compose.yml — je suppose une DB Postgres déjà joignable."
fi

if command -v alembic >/dev/null 2>&1 && test -n "${DB_URL:-}"; then
  log "Mise à niveau du schéma (alembic upgrade head)…"
  ALEMBIC_DATABASE_URL="$DB_URL" alembic upgrade head
else
  warn "alembic non trouvé ou ALEMBIC_DATABASE_URL manquant — je saute les migrations."
fi

# ========= Étape 2 : Lancement API (uvicorn) =========
log "Lancement de l’API (uvicorn) en arrière-plan…"
UVICORN_CMD=(uvicorn api.fastapi_app.app:app --env-file .env --host "$API_HOST" --port "$API_PORT")
# --reload engendre des process enfants : on évite en CI
"${UVICORN_CMD[@]}" >/tmp/crew_api.log 2>&1 &
API_PID=$!

cleanup() {
  log "Arrêt API (pid=$API_PID)…"
  kill "$API_PID" >/dev/null 2>&1 || true
  wait "$API_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# ========= Étape 3 : Healthcheck =========
log "Attente de l’API /health (timeout 30s)…"
for i in {1..60}; do
  if curl -sf "${BASE_URL}/health" >/dev/null 2>&1; then
    ok "API joignable."
    break
  fi
  sleep 0.5
  if ! kill -0 "$API_PID" >/dev/null 2>&1; then
    echo "---- LOGS UVICORN ----"
    tail -n +1 /tmp/crew_api.log || true
    die "Le process API est tombé pendant le démarrage."
  fi
  if [ "$i" -eq 60 ]; then
    echo "---- LOGS UVICORN ----"
    tail -n +1 /tmp/crew_api.log || true
    die "Timeout en attendant /health"
  fi
done

# ========= Étape 4 : POST /tasks (202) =========
log "POST /tasks → 202 attendu…"
TASK_PAYLOAD='{
  "title": "Validation e2e – Adhoc run",
  "task_spec": {"type": "demo", "sections": ["intro"]},
  "options": {"resume": false, "override": [], "dry_run": false}
}'
# Un seul POST : on capture body + code HTTP dans la même requête
RESP_AND_CODE="$(curl -sS -X POST "${BASE_URL}/tasks" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d "${TASK_PAYLOAD}" \
  -w "\n%{http_code}")" || {
  echo "---- LOGS UVICORN ----"; tail -n +1 /tmp/crew_api.log || true; die "Échec POST /tasks"
}
RESP="$(echo "${RESP_AND_CODE}" | sed '$d')"
STATUS_CODE="$(echo "${RESP_AND_CODE}" | tail -n1)"
test "$STATUS_CODE" = "202" || { echo "$RESP"; die "Code HTTP inattendu sur /tasks: ${STATUS_CODE} (attendu 202)"; }

RUN_ID="$(echo "$RESP" | jq -r '.run_id')"
LOCATION="$(echo "$RESP" | jq -r '.location')"
test -n "${RUN_ID}" && test "${RUN_ID}" != "null" || die "run_id absent dans la réponse"
test -n "${LOCATION}" && test "${LOCATION}" != "null" || die "location absente dans la réponse"
ok "Run accepté: ${RUN_ID} (Location: ${LOCATION})"

# ========= Étape 5 : Polling GET /runs/{id} =========
log "Polling du run jusqu’à 'completed' (timeout 90s)…"
DEADLINE=$((SECONDS + 90))
RUN_STATUS=""
while [ $SECONDS -lt $DEADLINE ]; do
  RUN_JSON="$(curl -sS -H "X-API-Key: ${API_KEY}" "${BASE_URL}/runs/${RUN_ID}")" || true
  RUN_STATUS="$(echo "$RUN_JSON" | jq -r '.status // empty')"
  if [ "$RUN_STATUS" = "completed" ]; then
    ok "Run complété."
    break
  elif [ "$RUN_STATUS" = "failed" ]; then
    echo "$RUN_JSON"
    echo "---- LOGS UVICORN ----"; tail -n +1 /tmp/crew_api.log || true
    die "Le run est passé à l'état 'failed'."
  fi
  sleep 0.5
done
test "$RUN_STATUS" = "completed" || { echo "Dernier état: ${RUN_STATUS}"; die "Timeout polling /runs/{id}"; }

# ========= Étape 6 : Vérifs nodes, artifacts, events =========
log "Vérification des nodes du run…"
NODES_JSON="$(curl -sS -H "X-API-Key: ${API_KEY}" "${BASE_URL}/runs/${RUN_ID}/nodes")"
NODES_TOTAL="$(echo "$NODES_JSON" | jq -r '.total // 0')"
test "$NODES_TOTAL" -ge 1 || { echo "$NODES_JSON"; die "Aucun node trouvé pour le run"; }
ok "Nodes OK (total: ${NODES_TOTAL})"

FIRST_NODE_ID="$(echo "$NODES_JSON" | jq -r '.items[0].id')"
log "Vérification des artifacts du node ${FIRST_NODE_ID}…"
ARTS_JSON="$(curl -sS -H "X-API-Key: ${API_KEY}" "${BASE_URL}/nodes/${FIRST_NODE_ID}/artifacts")"
ARTS_TOTAL="$(echo "$ARTS_JSON" | jq -r '.total // 0')"
test "$ARTS_TOTAL" -ge 1 || { echo "$ARTS_JSON"; die "Aucun artifact pour le premier node"; }
ok "Artifacts OK (total: ${ARTS_TOTAL})"

log "Vérification des events du run…"
EVT_JSON="$(curl -sS -H "X-API-Key: ${API_KEY}" "${BASE_URL}/runs/${RUN_ID}/events")"
LEVELS="$(echo "$EVT_JSON" | jq -r '.items[].level')"
echo "$LEVELS" | grep -q 'RUN_STARTED'   || { echo "$EVT_JSON"; die "RUN_STARTED absent des events"; }
echo "$LEVELS" | grep -q 'RUN_COMPLETED' || { echo "$EVT_JSON"; die "RUN_COMPLETED absent des events"; }
ok "Events OK (RUN_STARTED & RUN_COMPLETED présents)."

# ========= Étape 7 : (Optionnel) lancer les tests pytest spécifiques =========
if [ "${RUN_PYTEST:-1}" = "1" ]; then
  if command -v pytest >/dev/null 2>&1; then
    log "Exécution des tests API (pytest)…"
    # Priorité à vos nouveaux tests API; ajuster le chemin si besoin
    PYTHONWARNINGS=ignore pytest -q api/tests -k test_tasks_e2e || {
      echo "---- LOGS UVICORN ----"; tail -n +1 /tmp/crew_api.log || true; die "Tests pytest échoués"
    }
    ok "Tests pytest OK."
  else
    warn "pytest non installé – étape sautée."
  fi
else
  warn "RUN_PYTEST=0, tests pytest désactivés."
fi

ok "Validation e2e terminée avec succès ✅"
