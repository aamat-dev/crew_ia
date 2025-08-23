# Fil G – Mini Dashboard (read only)

## Variables d'environnement (.env)

Copiez le fichier `.env.example` en `.env` pour configurer l'application en développement.

- `VITE_API_BASE_URL` : URL de base de l'API FastAPI (ex : http://localhost:8000)
- `VITE_API_TIMEOUT_MS` : timeout des requêtes HTTP côté front (en millisecondes)
- `VITE_DEMO_API_KEY` : **optionnel**, clé API de démonstration pour usage local uniquement. Ne jamais commiter une vraie clé.

## API Key (sécurité)

Par défaut, aucune clé API n'est persistée. La clé saisie via l'UI n'est conservée qu'en mémoire.

En production, fournissez la clé à l'exécution via le champ prévu dans l'interface plutôt que dans le build.

L'option « clé .env (démo) » permet d'utiliser automatiquement la clé définie dans le fichier `.env` pour des tests locaux.
