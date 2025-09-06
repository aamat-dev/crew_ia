# Utilisation du module QA

## Configuration LLM (OpenAI)
Variables d'environnement attendues :
- `OPENAI_API_KEY` (**obligatoire**)
- `OPENAI_BASE_URL` (optionnel)

Exemple :
```bash
export OPENAI_API_KEY=sk-...
# export OPENAI_BASE_URL=https://api.openai.com/v1   # par défaut
```

## Exécution d'une revue automatique
Après l'exécution d'un nœud, appeler le hook :
```python
from orchestrator.hooks.qa_reviewer import post_node_hook
await post_node_hook(node, run, artifact_text)
```
Le hook interroge un LLM, envoie un feedback `auto` et écrit un fichier `*.qa.json` dans les sidecars.

## Création manuelle d'un feedback
```bash
curl -X POST http://localhost:8000/feedbacks \
  -H 'Content-Type: application/json' \
  -d '{
        "run_id": "<RUN_ID>",
        "node_id": "<NODE_ID>",
        "source": "manual",
        "reviewer": "user@example.com",
        "score": 95,
        "comment": "RAS",
        "evaluation": {"overall_score":95,"decision":"accept"}
      }'
```

## Rapport QA agrégé
```bash
curl http://localhost:8000/runs/<RUN_ID>/qa-report
```
Retourne les statistiques globales, par type de nœud et la liste des feedbacks.

## Migration de base de données
Appliquer les migrations (dont l'ajout du champ `evaluation`) :
```bash
ALEMBIC_DATABASE_URL=<url_postgres_sync_psycopg> \
  alembic -c backend/migrations/alembic.ini upgrade head
```
