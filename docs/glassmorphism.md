# Surcouche verre (« glassmorphism »)

La classe utilitaire `.glass` permet d'appliquer un effet de verre translucide
réutilisable dans le cockpit.

## Utilisation

```html
<div class="glass glass-card">…</div>
```

### Variantes
- `glass-muted` : surfaces secondaires (barres latérales, en-têtes).
- `glass-card` : cartes et panneaux flottants.
- `glass-danger` : messages d’alerte, fond teinté rouge.

Les variantes peuvent être combinées avec la classe principale :
`<div class="glass glass-muted">`.

## Bonnes pratiques
- ✅ Limiter l'effet aux éléments autonomes (cartes, barres, panneaux).
- ✅ Vérifier un contraste AA minimum pour le texte ou les icônes.
- ✅ Prévoir un fond solide de repli si `backdrop-filter` n’est pas pris en
  charge.
- ✅ Respecter les préférences utilisateur (`prefers-reduced-transparency` ou
  `prefers-reduced-motion`).
- ❌ Éviter d’appliquer le blur sur de grands conteneurs défilants : cela coûte
  cher en performances.
- ❌ Ne pas superposer plusieurs couches de blur.

## Exemples

| Avant | Après |
|-------|------|
| ![header brut](../docs/feedback-panel.png) | `class="glass glass-muted"` |

## Conseils d’usage
- Préférer l’utiliser sur le `Header`, la `Sidebar` ou des cartes KPI.
- Pour les vues longues ou les sections scrollables, privilégier un fond uni.

