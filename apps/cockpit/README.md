# Cockpit

## AppShell

Le layout global fournit une sidebar de navigation et un header avec recherche, notifications, palette de commandes (Cmd/Ctrl+K) et bascule de thème. Il est intégré dans `src/app/layout.tsx` via le composant `AppShell`.

## Design System

Les tokens (couleurs, typographies, radius, ombres, animations) sont définis dans `src/app/globals.css` via des variables CSS. Les composants de base du DS (`Button`, `Input`, `KpiCard`) sont disponibles dans `src/components/ds`.

## Thème

Le mode clair/sombre respecte `prefers-color-scheme` et peut être changé depuis le header.

## Dashboard

La page `/dashboard` affiche des KPI animés et des graphes dynamiques construits avec Recharts. Les données sont récupérées via TanStack Query depuis des API mock (`/api/agents`, `/api/runs`, `/api/feedbacks`). Des Skeletons et toasts gèrent les états de chargement et d'erreur.

## Tests d'accessibilité

Lancer `npm test` pour exécuter les tests `jest-axe` sur l'AppShell et le Dashboard et vérifier qu'aucune violation n'est détectée.

## Documentation

La documentation complète est disponible dans [cockpit-docs](../cockpit-docs).
