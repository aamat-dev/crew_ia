# Déploiement Vercel (preview)

Ce dépôt déclenche un déploiement automatique du mini dashboard sur Vercel à chaque push sur `main` et pour chaque pull request vers `main` ou `preview`. La construction de l'application est réalisée côté Vercel.

## Secrets requis

Configurez les secrets GitHub suivants dans les **Repository secrets** pour que le workflow `deploy-preview.yml` fonctionne :

- `VERCEL_TOKEN` – jeton d'accès personnel généré depuis votre compte Vercel.
- `VERCEL_ORG_ID` – identifiant de l’organisation Vercel.
- `VERCEL_PROJECT_ID` – identifiant du projet Vercel associé au dashboard.

Lors de l’exécution du workflow, l’URL de prévisualisation est exposée en sortie du job (`preview-url`) et un commentaire est publié sur la pull request avec cette URL.
