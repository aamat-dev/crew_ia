# Fil G – Mini Dashboard (read‑only)

## Introduction
Mini interface web permettant de visualiser l'exécution des runs orchestrés.
Le tableau de bord est **en lecture seule** et vise principalement les
équipes de développement, d'exploitation et de test souhaitant consulter
l'état des runs.

## Comment tester la preview
URL publique : https://preview.example.com

1. Ouvrir la preview dans le navigateur.
2. Renseigner `API Base URL` dans le panneau de configuration (ex : `https://api.<domaine>/`).
3. Saisir l'API Key dans le champ dédié puis cliquer sur `Enregistrer`.
4. Vérifier que la bannière ⚠ disparaît.
5. Ouvrir "Runs" et consulter la liste (pagination, etc.).

### Rappels
- Les requêtes incluent l'en-tête `X-API-Key`.
- La pagination est bornée (limite maximale 50) et les en-têtes `Link` sont disponibles.

### Troubleshooting
En cas d'erreurs CORS, 401 ou 403 : vérifier la variable `ALLOWED_ORIGINS` du backend et la validité de la clé API.

## Installation locale
Node.js 20 LTS ou supérieur est requis.

1. **Installer les dépendances** :
   ```bash
   make dash-mini-install
   ```
2. **Configurer l'API** : créer un fichier `.env.local` dans `dashboard/mini`
   contenant les variables suivantes :
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   VITE_API_TIMEOUT_MS=15000
   # optionnel
   VITE_API_KEY=<cle>
   ```
3. **Démarrer l'API FastAPI** (répertoire racine du projet) :
   ```bash
   uvicorn api.fastapi_app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   Si l'API tourne en local loopback, l'option `--host 0.0.0.0` permet l'accès
   depuis un autre appareil du réseau.
4. **Lancer le dashboard** :
   ```bash
   make dash-mini-run
   ```
   Pour générer une version de production et la prévisualiser :
   ```bash
   make dash-mini-build
   ```

## Utilisation
- **Runs** : liste paginée des runs avec statut et dates.
- **Run Detail** : détail d'un run avec plusieurs onglets :
  - **Résumé** : synthèse du run.
  - **DAG** : visualisation du graphe des nœuds.
  - **Nodes** : tableau des nœuds ; sélectionner un nœud charge ses artifacts.
  - **Events** : chronologie filtrable par type, niveau et nœud.
  - **Artifacts** : fichiers générés par le nœud sélectionné.

## Captures d’écran
![Runs](docs/img/runs.png)

![Run Detail](docs/img/run-detail.png)

## CI/CD
Une GitHub Action exécute lint, typage, tests et build. Pour lancer ces
vérifications en local :
```bash
make dash-mini-ci-local
```

## Limites connues
- Fonctionnement uniquement en lecture ; aucune création/édition de runs.
- Nécessite une API accessible protégée par clé.
- Dépend de la disponibilité de l'orchestrateur.

## Améliorations futures
- Pagination avancée.
- Recherche en temps réel.
- Mode sombre.
- Édition des runs.
