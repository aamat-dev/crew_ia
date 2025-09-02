## Checklist
```json
{{CHECKLIST_JSON}}
```

## Métadonnées du nœud
```json
{{NODE_META}}
```

## Livrable

{{LIVRABLE}}

## Rappel contrat de sortie (JSON strict)
Tu dois renvoyer un unique objet JSON avec les champs :
- spec_version, checklist_id, checklist_version
- node{id,type,run_id}, overall_score, decision
- per_criterion[] chaque item : id, score ∈ {0,50,100}, comment, na (bool)
- summary_comment (≈80 mots), failed_criteria[], meta{content_sha256?}

Décision : reject si score global < seuil ; accept si ≥ 85 ; sinon revise.
Scoring : moyenne pondérée des critères, renormalisée si certains sont na=true.
Sortie : JSON uniquement, pas de prose.
