# Oria — Thème "Claymorphic Anthracite"

Nouvelle fondation UI pour l'ensemble des pages cockpit. Objectifs : palette anthracite contrastée, pastilles dégradées, composants factorisés et accessibilité clavier.

## Palette & tokens

Les variables et utilitaires sont centralisés dans [`src/styles/theme.css`](src/styles/theme.css).

| Token | Valeur | Usage |
| --- | --- | --- |
| `--bg` | `#1C1E26` | Fond global |
| `--surface` | `#2A2D36` | Cartes et panneaux |
| `--border` | `#475569` | Trames et séparateurs |
| `--text` | `#F1F5F9` | Texte principal |
| `--text-secondary` | `#94A3B8` | Texte secondaire |
| Accents | `indigo=#6366F1`, `cyan=#22D3EE`, `emerald=#34D399`, `amber=#FBBF24`, `rose=#F87171` | Pastilles, highlights |

Focus clavier : `focus-visible:ring-2 ring-offset-2 ring-indigo-500/60` (via `baseFocusRing`).

## Utilitaires claymorphiques

- `surface` : fond anthracite + bord arrondi `rounded-2xl`.
- `shadow-card` : relief double (`inset` clair + ombre portée 0 8px 24px).
- `hover-glow-{accent}` : halo coloré léger.
- `accentGradient(accent)` (TypeScript) → classe Tailwind `bg-gradient-to-br from-[var(--accent-…)]`.

Ces utilitaires sont consommés dans les composants via `@/ui/theme`.

## Composants transverses (`src/ui`)

- **HeaderBar** : titre + breadcrumb, champ recherche claymorphique, actions (notifications, thème, profil). Persistance du thème via `onToggleTheme`.
- **SidebarItem** : bouton surface + pastille dégradée, accent configurable, état actif `ring-1`.
- **KpiCard** : bandeau supérieur dégradé, icône médaillon, badge delta sombre, animation cascade (Framer Motion).
- **MetricChartCard** : wrapper Recharts (axes sombres, tooltip anthracite, gradient auto).
- **TimelineItem** : statut + badge, actions `Relancer/Détails`, focus clavier.
- **NoticeCard** : messages success/warning/error avec point d'accent.
- **StatusBadge** : mapping `completed/running/queued/failed` → couleurs translucides.

## Features pages (`src/features`)

| Page | Points clés |
| --- | --- |
| `dashboard/DashboardPage` | Header + 4 KPIs, 2 graphiques (débit agents & feedbacks), progress bars dégradées, notices, timeline 6 runs, RunDrawer partagé. |
| `runs/RunsPage` | Barre filtres (status multi-select, dates, recherche), sélection multiple + actions groupées (pause/reprendre/annuler, gated par rôle), timeline virtualisée pour grandes listes, `RunDrawer`. |
| `agents/AgentsPage` | Filtres rôle/statut, graphique charge, grille `AgentCard` (emoji gradient, metrics). |
| `settings/SettingsPage` | Sections thème, clés API (afficher/regénérer), notifications (switch + slider). |

Les pages importent directement les composants `HeaderBar` dans le contenu afin de conserver un shell minimal côté layout.

## Shell & navigation

- `AppShell` : sidebar desktop (`surface` + `SidebarItem`), navigation mobile fixe (icônes), skip link accessible.
- Plus de `Header` global ; chaque feature gère son `HeaderBar`.

## Accessibilité

- Contrastes AA (`--text` sur `--bg` ≥ 4.5:1).
- `baseFocusRing` appliqué à tous les contrôles interactifs.
- Boutons `role="switch"` pour les toggles, `aria-current` sur navigation.
- `RunDrawer` gère `Escape` + overlay cliquable.

## Données factices

Fixtures locales (KPIs, runs, agents) typées TypeScript dans `src/features/**/types.ts`. Les états loading/empty sont simulés via `setTimeout` et skeletons.

## Tests & lint

Les composants historiques re-exportent les nouveaux (`components/kpi/KpiCard`, `components/ds/StatusBadge`, etc.) pour garantir rétro-compatibilité.
