# Cockpit

## AppShell

Le layout global fournit une sidebar de navigation et un header avec recherche, notifications, palette de commandes (Cmd/Ctrl+K) et bascule de thème. Il est intégré dans `src/app/layout.tsx` via le composant `AppShell`.

## Design System

Tokens et thèmes sont centralisés dans `src/app/globals.css` via `@theme inline` (Tailwind v4).

- Couleurs clés: `background`, `foreground`, `primary`, `secondary`, `success`, `warning`, `destructive` et leurs `*-foreground`.
- Surfaces: `card`, `muted`, alias `accent`, `popover`, `input`, `border` pour compat shadcn/ui.
- Focus: `--focus-ring` (couleur), `--focus-width`, `--outline-offset` et utilitaire `.focus-ring`.
- Rayons: `--radius-sm|md|lg|2xl`. Ombres: `--shadow-sm|md|lg`.
- Thèmes: clair par défaut, sombre via `[data-theme="dark"]` ou préférence système.

Utilisation (exemples):

- Fond/texte: `bg-background text-foreground`, `bg-primary text-primary-foreground`.
- États: `bg-success text-success-foreground`, `bg-warning text-warning-foreground`, `bg-destructive`…
- Ring d’accessibilité: `focus:outline-none focus-visible:ring-2 focus-visible:ring-focus` ou `.focus-ring`.
- Surfaces glass réutilisables: `glass`, `glass-muted`, `glass-danger` (opacité, flou, bordure subtile intégrés).

Composants DS minimalistes: `src/components/ds` (`Button`, `Input`, `Toast`, etc.). Ils utilisent les classes ci-dessus pour rester alignés avec les tokens.

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
## Graphiques (mocks)

Le panneau `ChartsPanel` affiche 3 graphiques basés sur des mocks Next.js:

- Throughput (runs/heure): `GET /api/agents`
- Latence moyenne (p50/p95): `GET /api/runs`
- Répartition des feedbacks (critique/major/minor): `GET /api/feedbacks`

Intégration:

- Importer `ChartsPanel` et l’insérer dans une page (ex: Dashboard) — déjà fait dans `src/app/dashboard/page.tsx`.
- États pris en charge: chargement (skeleton), aucune donnée (no‑data), erreurs (toast via `ToastProvider`).
- A11y: chaque graphique est un `role="img"` avec `aria-label` descriptif + texte alternatif sr‑only.
