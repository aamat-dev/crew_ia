import { test, expect } from '@playwright/test';

const PREVIEW_URL = process.env.PREVIEW_URL;

test('affiche les erreurs d\'API', async ({ page }) => {
  test.skip(!PREVIEW_URL, 'PREVIEW_URL non défini');

  const apiBase = 'https://mock.api';
  const apiKey = 'test-key';

  await page.route(`${apiBase}/**`, async (route) => {
    const req = route.request();
    const url = new URL(req.url());
    const path = url.pathname;

    if (req.method() === 'POST' && path === '/tasks') {
      return route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ id: 't1', title: 'demo', status: 'draft' }),
      });
    }

    if (req.method() === 'POST' && path === '/tasks/t1/plan') {
      return route.fulfill({
        status: 409,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Plan déjà généré' }),
      });
    }

    if (req.method() === 'GET' && path === '/plans/p1') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'p1',
          status: 'draft',
          graph: { nodes: [{ id: 'n1' }], edges: [] },
        }),
      });
    }

    if (req.method() === 'POST' && path === '/plans/p1/assignments') {
      return route.fulfill({
        status: 422,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'node inconnu' }),
      });
    }

    return route.fulfill({ status: 200, body: '{}' });
  });

  await page.goto(PREVIEW_URL!);
  await page.getByTestId('apiUrlInput').fill(apiBase);
  await page.getByRole('button', { name: 'Enregistrer' }).last().click();
  await page.getByLabel('api-key').fill(apiKey);
  await page.getByRole('button', { name: 'Enregistrer' }).first().click();

  await page.goto(`${PREVIEW_URL}/tasks`);
  await page.getByText('Nouvelle tâche').click();
  await page.getByPlaceholder('Titre').fill('demo');
  await page.getByText('Créer').click();

  await page.goto(`${PREVIEW_URL}/tasks/t1`);
  page.on('dialog', (d) => {
    expect(d.message()).toContain('409');
    d.accept();
  });
  await page.getByText('Générer le plan').click();

  await page.goto(`${PREVIEW_URL}/plans/p1`);
  await page.getByTestId('plan-node-n1').click();
  await page.getByLabel('role').fill('r1');
  await page.getByLabel('agent').fill('a1');
  await page.getByLabel('backend').fill('b1');
  await page.getByLabel('model').fill('m1');
  await page.getByRole('button', { name: 'Save Assignments' }).click();
  await expect(page.getByRole('alert')).toHaveText('node inconnu');
});

