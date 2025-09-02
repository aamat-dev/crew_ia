# Qualité et évaluation automatique

Ce module fournit un dispositif standardisé d'évaluation des livrables produit par les nœuds de l'orchestrateur.

## Checklists

Les checklists sont versionnées dans `quality/checklists/<version>/`. Un alias `latest` pointe vers la version courante.
Chaque fichier `qa.<type>.v1.json` suit le schéma commun et définit les critères, poids et seuils de rejet.
Le schéma interne est défini dans `quality/schemas/checklist-1.0.schema.json` (Draft 2020-12).
Règles :
- La somme des `weight` = 1.0 (hors critères marqués `na` → renormalisation).
- `reject_threshold` ∈ [0;100].
- `allow_na`: si vrai, un critère peut être noté `na=true` et exclu du calcul.

## Prompts reviewer

Les prompts utilisés par l'agent de revue sont versionnés dans `quality/prompts/<version>/`.
- `reviewer.system.txt` : rôle et règles générales.
- `reviewer.user.md` : gabarit incluant la checklist, les métadonnées du nœud et le livrable.

## Contrat de sortie

L'évaluateur retourne un JSON strict : score global, décision (accept / revise / reject), détails par critère et méta-données.
Format attendu :
```json
{
  "spec_version": "1.0.0",
  "checklist_id": "qa.<type>.v1",
  "checklist_version": "1.0.0",
  "node": { "id": "UUID", "type": "write|research|build|review", "run_id": "UUID" },
  "overall_score": 0,
  "decision": "accept|revise|reject",
  "per_criterion": [
    { "id": "clarity", "score": 0, "comment": "raison courte", "na": false }
  ],
  "summary_comment": "≈80 mots max",
  "failed_criteria": ["format","constraints"],
  "meta": { "content_sha256": "..." }
}
```
Règles de décision :
- `reject` si `overall_score` < `reject_threshold` de la checklist
- `accept` si `overall_score` ≥ 85
- sinon `revise`
Scoring : moyenne pondérée des critères, avec renormalisation si `na=true` sur certains critères.

## Sidecars
Chaque évaluation écrit un sidecar `*.qa.json` à côté de `*.llm.json` :
```
runs/{run_id}/nodes/{node_id}/{ts}.qa.json
```
Le contenu reprend le contrat de sortie ci-dessus et inclut si possible un hash du livrable (`meta.content_sha256`).

## Intégration Orchestrateur
- Hook post-nœud : invoque le reviewer (LLM) avec la checklist correspondant à `node_type`.
- Persiste un feedback auto (`source=auto`, `evaluation`=JSON complet) via l’API `POST /feedbacks` (Fil J).
- Non bloquant : en cas de timeout/erreur, log + possibilité de relancer l’évaluation.

## Rapport agrégé
`GET /runs/{id}/qa-report` retourne :
```json
{
  "run_id": "UUID",
  "global": { "mean": 0, "median": 0, "p95": 0, "accept_rate": 0, "reject_rate": 0 },
  "by_node_type": { "write": { "mean": 0, "count": 0, "accept_rate": 0, "reject_rate": 0 } },
  "nodes": [
    { "node_id": "UUID", "type": "write", "score": 0, "decision": "revise",
      "failed_criteria": ["coherence"], "feedback_id": "UUID", "created_at": "..." }
  ]
}
```
RBAC : viewer → lecture ; editor/admin → peut relancer une évaluation.
