# UI Anthracite Claymorphic — Cockpit

Objectif: thème sombre anthracite, accents colorés, relief claymorphic. Refactor progressif sans suppression de composants.

## Palette & Tokens

- Fond global: `#1C1E26` (HSL ~ `231 16% 13%`)
- Surfaces: `#2A2D36` (HSL ~ `223 13% 19%`)
- Texte primaire: `#F1F5F9` (slate-100)
- Texte secondaire: `#94A3B8` (slate-400)
- Bordures: `#334155`–`#475569` (slate-700/600)
- Accents:
  - indigo: `#6366F1` (500), `#818CF8` (400)
  - cyan: `#06B6D4` (500), `#22D3EE` (400)
  - emerald: `#10B981` (500), `#34D399` (400)
  - amber: `#F59E0B` (500), `#FBBF24` (400)
  - rose: `#F43F5E` (500), `#FB7185` (400)

Exposition via CSS variables (globals.css): `--bg`, `--fg`, `--card`, `--border`, `--indigo-500`, etc. Utilisées par Tailwind v4 via `@theme inline` et en utilitaires.

## Utilitaires Claymorphic

- `.clay-card`: carte claymorphique
  - dark: `bg-[#2A2D36] border-slate-700 rounded-2xl shadow-[inset_0_2px_6px_rgba(255,255,255,0.04),0_8px_24px_rgba(0,0,0,0.4)]`
- `.clay-shadow-out`: `0 8px 24px rgba(0,0,0,0.4)`
- `.clay-shadow-in`: `inset 0 2px 6px rgba(255,255,255,0.04)`

Focus: `focus-visible:ring-2 ring-offset-2 ring-[hsl(var(--ring))]` (indigo)

## Composants clés

- Sidebar (AppShell):
  - largeur `w-56`, `bg-[#1C1E26]` + `border-slate-800`
  - items: `flex items-center gap-3 p-3 rounded-2xl bg-[#2A2D36] border border-slate-700 hover:bg-slate-700/40`
  - pastille icône: `h-9 w-9 rounded-xl text-white bg-gradient-to-br from-<accent-500> to-<accent-400>`
  - actif: `ring-1 ring-<accent> shadow-[0_0_12px_rgba(99,102,241,0.35)]`
  - a11y: `nav[aria-label]`, `aria-current="page"`

- Header:
  - titre: `text-3xl font-extrabold text-slate-100`
  - recherche: `bg-[#2A2D36] border-slate-700 shadow-[inset_0_2px_6px_rgba(255,255,255,0.04)]`
  - actions: boutons ghost sombres `hover:bg-indigo-600/15` + focus visible

- KpiCard (API):
  - props: `label, value, delta, accent ('indigo'|'cyan'|'emerald'|'amber'|'rose'), icon`
  - compat: `title` supporté (alias de label)
  - style: bandeau 1px gradient top, médaillon gradient, valeur `text-3xl` claire
  - motion: apparition 150ms

- Graphiques (Recharts):
  - grilles `strokeOpacity=0.15`, axes/ticks `#94A3B8`
  - tooltips sombres `rgba(28,30,38,0.95)` bord `rgba(148,163,184,0.25)` radius 12
  - AreaChart débit: stroke `currentColor`, remplissage gradient indigo
  - BarChart feedbacks: barres `cyan-400` radius `[8,8,0,0]`

- Timeline:
  - cartes: `.clay-card`
  - badges: completed/running/queued/failed avec fonds 15% + `border-<accent>/30`, `text-<accent>-300` (running pulse)

- Rail droit:
  - progress track `bg-slate-800`, barres accent (indigo/cyan/emerald)
  - annonces: cartes anthracite avec bordure accent + emoji

## Exemples

Pastille icône dégradée: `className="grid h-9 w-9 place-content-center rounded-xl text-white bg-gradient-to-br from-indigo-500 to-indigo-400"`

Carte claymorphic: `<div className="clay-card p-4">...</div>`

KPI:
```
<KpiCard label="Agents actifs" value={9} delta={1} accent="cyan" icon={Users} />
```

## Accessibilité

- Contraste AA: texte principal sur `#1C1E26` ≥ 4.5:1, secondaire ≈ #94A3B8 validé visuellement
- Navigation clavier complète (Tab/Shift+Tab), `aria-current="page"`
- Focus visible sur tous les contrôles

## Notes de migration

- `KpiCard` ajoute `label` et `accent`; `title` reste supporté (alias). Mise à jour recommandée des pages pour fournir `accent` et `icon`.

