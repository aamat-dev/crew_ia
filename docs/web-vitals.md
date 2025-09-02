# Suivi des Web Vitals

Ce module met en place une collecte des métriques Core Web Vitals en production.

## Pipeline
1. **Collecte** : `reportWebVitals` dans l'application Next.js envoie LCP, FID/INP, CLS, FCP et TTFB via `POST /api/vitals`.
2. **API** : l'endpoint valide les données (Zod) et les stocke en mémoire sur une fenêtre glissante de 24 h.
3. **Agrégations** : les métriques sont agrégées par nom et par page, avec calcul des moyennes et percentiles (p50/p75/p95).
4. **Dashboard** : `/performance` affiche les KPI, les graphiques temporels et une table par page.

## Limites
- Stockage en mémoire : les données disparaissent au redémarrage du serveur.
- Pas de sampling : toutes les valeurs sont collectées ; ajouter un échantillonnage si nécessaire.
- Aucune PII n'est transmise, uniquement les métriques techniques et l'agent utilisateur.

## Confidentialité
Les requêtes ne contiennent aucune information personnelle. Seuls `path`, `userAgent` et les mesures de performance sont envoyés.

## Tests
- Lancer l'application `npm run dev` (ou `npm start` en production).
- Simuler l'envoi de métriques via la console :
  ```js
  window.reportWebVitals({
    name: 'LCP',
    id: 'test',
    value: 3000,
    delta: 3000,
    label: 'web-vital'
  });
  ```
- Consulter `/performance` pour voir les agrégations et alertes.
