# Fil G – Mini Dashboard (read-only)

## Introduction
Mini interface web permettant de visualiser l'exécution des runs orchestrés.
Le tableau de bord est **en lecture seule** et vise principalement les
équipes de développement, d'exploitation et de test souhaitant consulter
l'état des runs.

## Preview

### Vercel
Les déploiements sur la branche `main` sont publiés automatiquement sur Vercel.
L'URL de la preview est affichée dans les logs du job `vercel-deploy`.
Définir les variables d'environnement du projet :
- `VITE_API_BASE_URL`
- `VITE_API_KEY` (facultatif)

### Comment tester la preview
1. Ouvrir la preview dans le navigateur.
2. Saisir `API Base URL` dans le panneau de configuration.
3. Entrer l'`API Key` puis cliquer sur `Enregistrer`.
4. Vérifier que la bannière ⚠ disparaît.
5. Ouvrir **Runs** et vérifier la pagination (limite 50) et les en-têtes `Link`.

### Troubleshooting
- **CORS** : vérifier la variable `ALLOWED_ORIGINS` du backend.
- **401 / 403** : vérifier la validité de la clé API.
- **Pagination** : limite à 50 éléments avec en-têtes `Link` pour la navigation.

## 🔐 Secrets & variables requis

### Secrets GitHub du dépôt
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`
- `PREVIEW_URL` (optionnel, fallback pour les tests E2E)

### Variables d'environnement du projet Vercel
Ajouter dans **Project → Env Vars** :
- `VITE_API_BASE_URL`
- `VITE_API_KEY` (facultatif)

## Installation locale
… (le reste du fichier inchangé)

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

### Tests E2E

Pré-requis :

```bash
npx playwright install
```

Lancer localement :

```bash
PREVIEW_URL=http://localhost:5173 npm run e2e
```

Lancer sur une preview distante :

```bash
PREVIEW_URL=<url> npm run e2e
```

Les appels API sont mockés dans le test et seules les routes UI sont vérifiées.

## Limites connues
- Fonctionnement uniquement en lecture ; aucune création/édition de runs.
- Nécessite une API accessible protégée par clé.
- Dépend de la disponibilité de l'orchestrateur.

## Améliorations futures
- Pagination avancée.
- Recherche en temps réel.
- Mode sombre.
- Édition des runs.
