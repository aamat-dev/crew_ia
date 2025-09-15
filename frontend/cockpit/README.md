# Cockpit

## AppShell

Le layout global fournit une sidebar de navigation et un header avec recherche, notifications, palette de commandes (Cmd/Ctrl+K) et bascule de thème. Il est intégré dans `src/app/layout.tsx` via le composant `AppShell`.

## Design System

Les tokens (couleurs, typographies, radius, ombres, animations) sont définis dans `src/app/globals.css` via des variables CSS. Les composants de base du DS (`Button`, `Input`) sont disponibles dans `src/components/ds` et le composant KPI dans `src/components/kpi`.

## Thème

Le mode clair/sombre respecte `prefers-color-scheme` et peut être changé depuis le header.

## Données (API Backend)

Le cockpit consomme l'API FastAPI réelle via `NEXT_PUBLIC_API_URL` et gère les états `loading`/`error`/`empty` grâce à TanStack Query.

- Pages branchées :
  - `/dashboard` : extrait (5 derniers runs) avec CTA.
  - `/runs` : `GET ${API_URL}/runs?limit=20`.
  - `/tasks` : `GET ${API_URL}/tasks?limit=20`, création et démarrage d’une tâche.

Variables d’environnement côté client :

```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
# Doit correspondre à API_KEY côté backend pour autoriser les requêtes
NEXT_PUBLIC_API_KEY=test-key
```

Sans `NEXT_PUBLIC_API_KEY`, les endpoints protégés renverront 401 et l’UI affichera un état d’erreur.

## Tests d'accessibilité

Lancer `npm test` pour exécuter les tests `jest-axe` sur l'AppShell et le Dashboard et vérifier qu'aucune violation n'est détectée.

## Documentation

La documentation complète est disponible dans [cockpit-docs](../cockpit-docs).
