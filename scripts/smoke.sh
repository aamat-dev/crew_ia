#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# Config & arguments
# -----------------------------
API_BASE="${API_BASE:-http://localhost:8080}"
API_KEY="${API_KEY:-}"
RUN_ID="${RUN_ID:-}"
NODE_ID="${NODE_ID:-}"

usage() {
  cat <<USAGE
Usage: API_BASE=http://localhost:8080 API_KEY=<key> ./smoke.sh
Options:
  -b <base_url>   (ex: http://localhost:8080)    [par défaut: \$API_BASE]
  -k <api_key>    (ou export API_KEY)            [obligatoire]
  -r <run_uuid>   (sinon auto-détection)
  -n <node_uuid>  (sinon auto-détection)
Exemples:
  API_KEY=changeme ./smoke.sh
  ./smoke.sh -b http://127.0.0.1:8080 -k changeme
USAGE
}

while getopts ":b:k:r:n:h" opt; do
  case $opt in
    b) API_BASE="$OPTARG" ;;
    k) API_KEY="$OPTARG" ;;
    r) RUN_ID="$OPTARG" ;;
    n) NODE_ID="$OPTARG" ;;
    h) usage; exit 0 ;;
    \?) echo "Option invalide: -$OPTARG" >&2; usage; exit 2 ;;
    :) echo "Option -$OPTARG requiert une valeur." >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$API_KEY" ]]; then
  echo "❌ API_KEY manquante. Passe -k <key> ou export API_KEY=..." >&2
  exit 2
fi

# Détecte jq ou Python pour parser le JSON
JSON_TOOL=""
if command -v jq >/dev/null 2>&1; then
  JSON_TOOL="jq"
elif command -v python3 >/dev/null 2>&1; then
  JSON_TOOL="python"
else
  echo "❌ Ni jq ni python3 trouvés pour parser le JSON. Installe l'un des deux (ex: sudo apt install jq)." >&2
  exit 2
fi

# Helpers
OK()   { echo "✅ $*"; }
FAIL() { echo "❌ $*"; }

req() {
  # $1 = method, $2 = path (ex: /health), $3 = out var for body (name), $4 = expected http code (default 200)
  local method="$1"; shift
  local path="$1"; shift
  local __outvar_body="$1"; shift
  local expect="${1:-200}"

  local url="${API_BASE}${path}"
  local tmp_body; tmp_body="$(mktemp)"
  local code
  code="$(curl -sS -o "$tmp_body" -w '%{http_code}' -H "X-API-Key: ${API_KEY}" "$url")" || true
  if [[ "$code" != "$expect" ]]; then
    FAIL "${method} ${path} → HTTP ${code}"
    echo "--- Réponse ---"
    cat "$tmp_body" || true
    echo "---------------"
    rm -f "$tmp_body"
    return 1
  fi
  printf -v "$__outvar_body" '%s' "$(cat "$tmp_body")"
  rm -f "$tmp_body"
  return 0
}

json_get() {
  # $1 = json string, $2 = jq-like path (e.g. '.items[0].id')
  local json="$1"; shift
  local path="$1"; shift

  if [[ "$JSON_TOOL" == "jq" ]]; then
    echo "$json" | jq -r "$path"
  else
    # python3
    python3 - "$path" <<'PY' "$json"
import json, sys
path = sys.argv[1]
data = json.loads(sys.stdin.read())
# Support minimal: .items[0].id / .id
def get(d, p):
    if not p or p == '.':
        return d
    parts = p.lstrip('.').split('.')
    cur = d
    for part in parts:
        if '[' in part and ']' in part:
            name, idx = part[:-1].split('[')
            if name:
                cur = cur.get(name)
            cur = cur[int(idx)]
        else:
            if isinstance(cur, dict):
                cur = cur.get(part)
            else:
                cur = getattr(cur, part, None)
    return cur
val = get(data, path)
if val is None:
    print("")
else:
    if isinstance(val, (dict, list)):
        print(json.dumps(val))
    else:
        print(val)
PY
  fi
}

# -----------------------------
# Tests
# -----------------------------
overall=0
failures=0

echo "🔎 Base: $API_BASE"

# 1) Health
body=""
if req GET "/health" body 200; then
  OK "GET /health"
else
  FAIL "GET /health"
  failures=$((failures+1))
fi

# 2) Runs list
if req GET "/runs?limit=5&offset=0&order_by=-started_at" body 200; then
  OK "GET /runs"
  if [[ -z "$RUN_ID" ]]; then
    rid="$(json_get "$body" '.items[0].id')"
    if [[ -n "$rid" && "$rid" != "null" ]]; then
      RUN_ID="$rid"
      echo "   ↳ RUN_ID=$RUN_ID"
    else
      echo "   ↳ Aucun run trouvé (liste vide)."
    fi
  fi
else
  FAIL "GET /runs"
  failures=$((failures+1))
fi

# 3) Run detail + summary (si RUN_ID)
if [[ -n "$RUN_ID" ]]; then
  if req GET "/runs/${RUN_ID}" body 200; then
    OK "GET /runs/{run_id}"
  else
    FAIL "GET /runs/{run_id}"
    failures=$((failures+1))
  fi

  if req GET "/runs/${RUN_ID}/summary" body 200; then
    OK "GET /runs/{run_id}/summary"
  else
    FAIL "GET /runs/{run_id}/summary"
    failures=$((failures+1))
  fi

  # 4) Nodes (et extraction d'un NODE_ID)
  if req GET "/runs/${RUN_ID}/nodes?order_by=-created_at" body 200; then
    OK "GET /runs/{run_id}/nodes"
    if [[ -z "$NODE_ID" ]]; then
      nid="$(json_get "$body" '.items[0].id')"
      if [[ -n "$nid" && "$nid" != "null" ]]; then
        NODE_ID="$nid"
        echo "   ↳ NODE_ID=$NODE_ID"
      else
        echo "   ↳ Aucun node trouvé (liste vide)."
      fi
    fi
  else
    FAIL "GET /runs/{run_id}/nodes"
    failures=$((failures+1))
  fi

  # 5) Events
  if req GET "/events?run_id=${RUN_ID}&order_by=-timestamp" body 200; then
    OK "GET /events"
  else
    FAIL "GET /events"

    failures=$((failures+1))
  fi
else
  echo "ℹ️  RUN_ID introuvable → tests run detail/nodes/events sautés."
fi

# 6) Artifacts (si NODE_ID)
if [[ -n "$NODE_ID" ]]; then
  if req GET "/nodes/${NODE_ID}/artifacts?order_by=-created_at" body 200; then
    OK "GET /nodes/{node_id}/artifacts"
  else
    FAIL "GET /nodes/{node_id}/artifacts"
    failures=$((failures+1))
  fi
else
  echo "ℹ️  NODE_ID introuvable → test artifacts sauté."
fi

# Résumé
if [[ "$failures" -eq 0 ]]; then
  echo "🎉 Smoke-tests OK"
  exit 0
else
  echo "⚠️  Smoke-tests terminés avec $failures échec(s)"
  exit 1
fi
