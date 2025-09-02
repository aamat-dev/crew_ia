# Design Tokens

| Token | Rôle | Exemple d’usage |
| --- | --- | --- |
| `--bg` | Couleur de fond principale | `class="bg-background"` |
| `--fg` | Couleur de texte par défaut | `class="text-foreground"` |
| `--muted` | Fonds discrets et bordures | `class="bg-muted"` |
| `--muted-foreground` | Texte sur surfaces `muted` | `class="text-muted-foreground"` |
| `--primary` | Action principale | `class="bg-primary"` |
| `--primary-foreground` | Texte sur `primary` | `class="text-primary-foreground"` |
| `--secondary` | Action secondaire | `class="bg-secondary"` |
| `--secondary-foreground` | Texte sur `secondary` | `class="text-secondary-foreground"` |
| `--destructive` | États d’erreur | `class="bg-destructive"` |
| `--destructive-foreground` | Texte sur `destructive` | `class="text-destructive-foreground"` |
| `--ring` | Couleur d’anneau générique | `class="ring-ring"` |
| `--ring-foreground` | Contenu dans l’anneau | `class="text-ring-foreground"` |
| `--card` | Fond des cartes | `class="bg-card"` |
| `--card-foreground` | Texte sur cartes | `class="text-card-foreground"` |
| `--elev-0..3` | Opacité pour effets verre | `bg-[hsl(var(--bg)/var(--elev-2))]` |
| `--shadow-sm/md/lg` | Ombres de profondeur | `class="shadow-sm"` |
| `--radius-sm/md/lg/2xl` | Rayons de bordure | `class="rounded-lg"` |
| `--font-sans` | Police par défaut | `class="font-sans"` |
| `--font-mono` | Police monospace | `class="font-mono"` |
| `--scale-1..4` | Échelles de taille de texte | `class="text-[var(--scale-2)]"` |
| `--duration-fast/normal/slow` | Durées de transition | `class="duration-[var(--duration-fast)]"` |
| `--easing-standard/emph` | Courbes d’animation | `[transition-timing-function:var(--easing-standard)]` |
| `--focus-ring` | Couleur du focus visible | `class="focus-visible:ring-focus"` |
| `--focus-width` | Largeur du focus | gérée globalement |
| `--outline-offset` | Décalage du focus | géré globalement |

## Consignes d’accessibilité

- Viser un contraste minimum de **4.5:1** entre le texte et son fond.
- Assurer un focus toujours visible grâce à `--focus-ring`, `--focus-width` et `--outline-offset`.
- Respecter les préférences utilisateur : `prefers-reduced-motion` neutralise les animations.

