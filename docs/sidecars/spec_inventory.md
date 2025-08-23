# Inventaire des sidecars LLM

Un script ponctuel a parcouru le dossier `.runs/` et analysé **2 fichiers** `*.llm.json`.
Les champs ci‑dessous ont été observés.

## Fréquences observées

- `provider`, `model`, `model_used`, `usage`, `prompts.user` : 2/2 fichiers (~100 %).
- `usage.prompt_tokens`, `usage.total_tokens` : 2/2 fichiers (~100 %).
- `latency_ms`, `usage.completion_tokens`, `prompts.system`, `prompts.final` : 1/2 fichiers (~50 %).

## Spécification proposée

| champ | O/Opt | type | format/enum/regex | description | source/observabilité |
|---|---|---|---|---|---|
| `version` | O | str | ex. `"1.0"` | Version du schéma | sidecar FS |
| `provider` | O | str | `openai` \| `anthropic` \| `ollama` \| `azure_openai` \| `other` | Fournisseur du modèle | sidecar FS |
| `model` | O | str | — | Nom du modèle demandé | sidecar FS |
| `model_used` | O | str | — | Modèle réellement exécuté | sidecar FS |
| `latency_ms` | O | int | ≥0 | Latence totale en millisecondes | sidecar FS / métriques |
| `usage` | O | obj | — | Métadonnées de consommation | sidecar FS |
| `usage.prompt_tokens` | O | int | ≥0 | Tokens du prompt | sidecar FS / métriques |
| `usage.completion_tokens` | O | int | ≥0 | Tokens de la complétion | sidecar FS / métriques |
| `usage.total_tokens` | Opt | int | ≥0 | Total des tokens | sidecar FS / métriques |
| `cost` | O | obj | — | Métadonnées de coût | sidecar FS / métriques |
| `cost.estimated` | O | number | ≥0 | Coût estimé de l’appel | sidecar FS / métriques |
| `prompts` | O | obj | — | Prompts capturés (tronqués à 800 car.) | sidecar FS |
| `prompts.system` | O | str | ≤800 car. | Prompt système envoyé | sidecar FS |
| `prompts.user` | O | str \| array<obj> | ≤800 car. \| {role, content} | Prompt utilisateur | sidecar FS |
| `prompts.final` | Opt | str | ≤800 car. | Prompt final concaténé | sidecar FS |
| `prompts.messages` | Opt | array<obj> | {role, content} | Alias évolutif de `prompts.user` | sidecar FS |
| `timestamps` | O | obj | — | Début et fin de l’appel | sidecar FS / instrumentation |
| `timestamps.started_at` | O | str | date-time | Début de l’appel | sidecar FS / instrumentation |
| `timestamps.ended_at` | O | str | date-time | Fin de l’appel | sidecar FS / instrumentation |
| `run_id` | O | str | UUID v4 | Identifiant d’exécution | orchestrateur |
| `node_id` | O | str | UUID v4 | Identifiant du nœud | orchestrateur |
| `request_id` | Opt | str | — | Identifiant du provider | sidecar FS |
| `retry.index` | Opt | int | ≥0 | Position dans la boucle de retry | orchestrateur |
| `inputs` | Opt | obj | — | Entrées non textuelles | sidecar FS |
| `tooling` | Opt | array<obj> | {name, version?} | Outils auxiliaires | sidecar FS |
| `warnings` | Opt | array<str> | — | Avertissements du provider | sidecar FS |
| `errors` | Opt | array<obj> | {code, message, retriable?} | Erreurs rencontrées | sidecar FS |
| `metadata` | Opt | obj | — | Métadonnées additionnelles | sidecar FS |
| `raw` | Opt | obj | — | Données brutes (déprécié) | sidecar FS |

## Compat ascendante

- `model` ou `model_used` doivent être présents (au moins un) ; s’ils coexistent, les valeurs doivent être identiques.
- `prompts.user` peut être une chaîne ou un tableau d’objets `{role, content}` pour accompagner la migration vers les messages multi‑rôles.
- `raw` est toléré pour compatibilité mais sera rejeté en mode `--strict`.

## Formats & regex

- **UUID v4** : `^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$` (insensible à la casse).
- **date-time** : timestamps au format RFC3339.
- **provider** : `openai`, `anthropic`, `ollama`, `azure_openai`, `other`.
- **Prompts** : stockage limité à 800 caractères par champ `prompts.*`.

## Proposition v1.0

### Champs obligatoires
- `version` : repère la version du schéma et permet l’évolution.
- `provider` : identifie la source LLM.
- `model` et/ou `model_used` : garantissent la reproductibilité.
- `latency_ms` : mesure pour l’observabilité des performances.
- `usage.prompt_tokens` & `usage.completion_tokens` : base des métriques de consommation.
- `cost.estimated` : suivi budgétaire de chaque appel.
- `prompts.system` & `prompts.user` : audit des prompts émis.
- `timestamps.started_at` & `timestamps.ended_at` : traçage temporel précis.
- `run_id` & `node_id` : corrélation des exécutions et des nœuds.

### Champs optionnels
- `usage.total_tokens` : somme pratique des tokens.
- `request_id`, `retry.index` : diagnostics et corrélation fournisseur.
- `inputs`, `tooling` : suivi des entrées et outils adjacents.
- `warnings`, `errors` : analyse des comportements anormaux.
- `metadata` : propagation de traces (ex. `trace_id`).
- `raw` : conservation temporaire de la réponse brute.
- `prompts.final`, `prompts.messages` : variantes de prompts selon les besoins.
