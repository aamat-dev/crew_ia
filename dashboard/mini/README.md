# Fil G – Mini Dashboard (read‑only)

## Démarrage rapide

Node.js 20 LTS minimum est recommandé.

```bash
make dash-mini-install
make dash-mini-run
make dash-mini-build
```

Variables `.env.local` utiles :

```bash
VITE_API_BASE_URL=http://192.168.1.50:8000
VITE_API_TIMEOUT_MS=15000
# optionnel
VITE_API_KEY=<clé>
```

Rappel : si l’API tourne en local loopback, la lancer avec `--host 0.0.0.0` pour accès réseau.

## Filtres & pagination

L'API `/runs` accepte les paramètres suivants :

- `page` — numéro de page (>=1)
- `page_size` — taille de page (`10`, `20` ou `50`)
- `status` — liste de statuts séparés par des virgules (`queued`, `running`, `succeeded`, `failed`, `canceled`, `partial`)
- `date_from`, `date_to` — bornes de date (`YYYY-MM-DD`)
- `title` — filtre texte sur le titre

Chaque modification de filtre remet la page à `1`.
