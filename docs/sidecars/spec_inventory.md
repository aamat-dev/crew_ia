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
| `provider` | O | str | `openai` \| `ollama` … | Fournisseur du modèle | sidecar FS (`.runs/<run>/nodes/<node>/artifact_*.llm.json`) |
| `model` | O | str | — | Nom du modèle demandé | sidecar FS |
| `model_used` | O | str | — | Modèle réellement exécuté | sidecar FS |
| `latency_ms` | Opt | int | ≥0 | Latence totale en millisecondes | sidecar FS / métriques |
| `usage` | O | obj | — | Métadonnées de consommation | sidecar FS |
| `usage.prompt_tokens` | Opt | int | ≥0 | Tokens du prompt | sidecar FS / métriques |
| `usage.completion_tokens` | Opt | int | ≥0 | Tokens de la complétion | sidecar FS / métriques |
| `usage.total_tokens` | Opt | int | ≥0 | Total des tokens | sidecar FS / métriques |
| `prompts` | Opt | obj | — | Prompts capturés (tronqués à 800 car.) | sidecar FS |
| `prompts.system` | Opt | str | ≤800 car. | Prompt système envoyé | sidecar FS |
| `prompts.user` | O | str | ≤800 car. | Prompt utilisateur | sidecar FS |
| `prompts.final` | Opt | str | ≤800 car. | Prompt final concaténé | sidecar FS |

## Proposition v1.0

### Champs obligatoires
- `provider` : identifie la source LLM.
- `model` & `model_used` : garantissent la reproductibilité.
- `usage` : suivi de la consommation.
- `prompts.user` : audit du prompt émis.

### Champs optionnels
- `latency_ms` : utile pour la performance mais non bloquant.
- `usage.prompt_tokens`, `usage.completion_tokens`, `usage.total_tokens` : dépend de la granularité offerte par le provider.
- `prompts.system`, `prompts.final` : présents seulement si nécessaire pour l'observabilité.
- `prompts` : peut être omis si le stockage des prompts est désactivé.
