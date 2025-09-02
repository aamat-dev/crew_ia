# Budgets de performance

Ce dépôt applique des budgets de performance pour les principales pages du cockpit
(`/dashboard`, `/runs`, `/performance`). Les budgets sont définis dans
`perf-budgets.json` et vérifiés en CI via `scripts/lh-ci.mjs`.

## Metriques surveillées

- **LCP p75** ≤ 2,5 s
- **INP p75** ≤ 200 ms
- **CLS p75** ≤ 0,1
- **Temps d’interactivité (TTI)** ≤ 3 s
- Poids des ressources transférées :
  - JavaScript ≤ 180 KB
  - CSS ≤ 60 KB
  - Total ≤ 350 KB
- **Nombre de requêtes** ≤ 25

## Ajuster les budgets

1. Modifier les valeurs dans `perf-budgets.json`.
2. Lancer localement `node scripts/lh-ci.mjs` avec `PREVIEW_URL` pointant
   vers l’instance à tester.
3. Commiter le fichier mis à jour avec une description du changement.

## Workflow de mise à jour

- Les budgets doivent être stricts mais réalistes. Toute augmentation doit être
  justifiée dans le message de commit et la revue de code.
- En cas d’amélioration durable, réduire les limites plutôt que de les laisser
  dériver.

## Assouplissement temporaire (waiver)

Si une régression ponctuelle est inévitable :

1. Augmenter le budget concerné et préciser la durée de validité dans la PR.
2. Ouvrir un ticket pour le retour à la valeur initiale.
3. Réduire le budget dès que la régression est résolue.

Ces étapes garantissent que les budgets restent un garde‑fou efficace et que les
écarts sont documentés et suivis.
