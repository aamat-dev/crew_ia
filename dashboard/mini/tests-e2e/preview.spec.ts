import { test, expect } from '@playwright/test';

const PREVIEW_URL = process.env.PREVIEW_URL;

// Teste la preview déployée sans dépendre d'une API réelle
// en interceptant les requêtes réseau et en renvoyant des réponses mockées.
test('preview UI fonctionne avec API mockée', async ({ page }) => {
  test.skip(!PREVIEW_URL, 'PREVIEW_URL non défini');

  const apiBase = 'https://mock.api';
  const apiKey = 'test-key';

  // Interception de toutes les requêtes vers l'API mockée
  await page.route(`${apiBase}/**`, async (route) => {
    const req = route.request();
    if (req.url().includes('/runs')) {
      // Vérifie que l'en-tête X-API-Key est bien envoyé
      expect(req.headers()['x-api-key']).toBe(apiKey);

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: {
          Link: '<https://mock.api/runs?limit=20&offset=20>; rel="next", <https://mock.api/runs?limit=20&offset=0>; rel="prev"',
          'X-Total-Count': '40',
        },
        body: JSON.stringify({
          items: [{ id: 'run-1', status: 'completed' }],
          meta: { page: 1, page_size: 20, total: 40 },
        }),
      });
    } else {
      await route.fulfill({ status: 200, body: '{}' });
    }
  });

  // Ouvre la preview et vérifie la bannière initiale
  await page.goto(PREVIEW_URL!);
  await expect(page.getByRole('alert')).toHaveText(/API Key requise/);

  // Configure l'URL de l'API
  await page.getByTestId('apiUrlInput').fill(apiBase);
  await page.getByRole('button', { name: 'Enregistrer' }).last().click();

  // Saisit la clé API et sauvegarde
  await page.getByLabel('api-key').fill(apiKey);
  await page.getByRole('button', { name: 'Enregistrer' }).first().click();

  // La bannière doit disparaître
  await expect(page.getByRole('alert')).toHaveCount(0);

  // Navigue vers Runs et attend l'affichage d'au moins un item
  await page.goto(`${PREVIEW_URL}/runs`);
  await expect(page.getByRole('row', { name: /run-1/ })).toBeVisible();
});
