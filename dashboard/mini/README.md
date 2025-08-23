# Fil G – Mini Dashboard (read‑only)

## Démarrage rapide

Node.js 20 LTS minimum est recommandé.

```bash
make dash-mini-install
make dash-mini-run
make dash-mini-build
```

## Filtres & pagination

L'API `/runs` accepte les paramètres suivants :

- `page` — numéro de page (>=1)
- `page_size` — taille de page (`10`, `20` ou `50`)
- `status` — liste de statuts séparés par des virgules (`queued`, `running`, `succeeded`, `failed`, `canceled`, `partial`)
- `date_from`, `date_to` — bornes de date (`YYYY-MM-DD`)
- `title` — filtre texte sur le titre

Chaque modification de filtre remet la page à `1`.
