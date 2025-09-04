# Fil 8 – API Agents

Ce module ajoute les fonctionnalités suivantes :

- **Listing des agents** avec en-tête `Link` (RFC5988) et champs `_links` dans la
  réponse JSON.
- **Matrice des modèles** : `GET /agents/models-matrix` (lecture seule) avec
  filtres `role` et `domain`.
- **RBAC minimal** activable via `FEATURE_RBAC=true` et l'en-tête `X-Role`.
- **Client orchestrateur** pour recruter dynamiquement un agent manquant.

## Endpoints principaux

```bash
# Liste des agents
curl -i "${api_base}/agents?limit=1&offset=0"

# Création (requiert rôle editor|admin si RBAC)
curl -s -X POST "${api_base}/agents" \
  -H "Content-Type: application/json" \
  -H "X-Role: editor" \
  -d '{"name":"a1","role":"manager","domain":"frontend"}'

# Matrice des modèles
curl -s "${api_base}/agents/models-matrix?role=manager&domain=frontend"
```

## RBAC

| Rôle    | Accès           |
|---------|-----------------|
| viewer  | lecture seule   |
| editor  | lecture/écriture|
| admin   | lecture/écriture|

## Sidecar de recrutement

Lorsqu'un agent est recruté dynamiquement, le sidecar retourné est écrit sous
`runs/${run_id}/sidecars/${request_id}.llm.json`.

## Développement local

```bash
make migrate-fil8
make seed-agents
make test-fil8
```

## Dépannage

- **403 interdit** : vérifier `FEATURE_RBAC` et l'en-tête `X-Role`.
- **Pas de sidecar** : vérifier les permissions d'écriture dans `RUNS_ROOT`.

