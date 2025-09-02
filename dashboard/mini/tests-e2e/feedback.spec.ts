import { test, expect } from '@playwright/test';

const PREVIEW_URL = process.env.PREVIEW_URL;

test('feedback panel & actions', async ({ page }) => {
  test.skip(!PREVIEW_URL, 'PREVIEW_URL non défini');

  const apiBase = 'https://mock.api';
  const apiKey = 'test-key';
  let feedbacks = [
    {
      id: 'f1',
      run_id: 'run-1',
      node_id: 'node-1',
      source: 'auto',
      reviewer: 'auto',
      score: 55,
      comment: 'auto bad',
      created_at: new Date().toISOString(),
    },
  ];
  let patchCalled = false;

  await page.route(`${apiBase}/**`, async (route) => {
    const req = route.request();
    const url = req.url();
    if (url.endsWith('/runs/run-1')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'run-1',
          status: 'running',
          dag: {
            nodes: [
              { id: 'node-1', status: 'running', role: 'agent', feedbacks },
            ],
            edges: [],
          },
        }),
      });
    } else if (url.includes('/runs/run-1/nodes')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'X-Total-Count': '1' },
        body: JSON.stringify({
          items: [
            {
              id: 'node-1',
              status: 'running',
              role: 'agent',
              feedbacks,
            },
          ],
        }),
      });
    } else if (url.includes('/feedbacks') && req.method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'X-Total-Count': String(feedbacks.length) },
        body: JSON.stringify({ items: feedbacks }),
      });
    } else if (url.includes('/feedbacks') && req.method() === 'POST') {
      const body = JSON.parse(req.postData() || '{}');
      const fb = {
        id: `f${feedbacks.length + 1}`,
        created_at: new Date().toISOString(),
        ...body,
      };
      feedbacks.push(fb);
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify(fb),
      });
    } else if (url.includes('/nodes/node-1') && req.method() === 'PATCH') {
      patchCalled = true;
      await route.fulfill({ status: 200, body: '{}' });
    } else {
      await route.fulfill({ status: 200, body: '{}' });
    }
  });

  await page.goto(PREVIEW_URL!);
  await page.getByTestId('apiUrlInput').fill(apiBase);
  await page.getByRole('button', { name: 'Enregistrer' }).last().click();
  await page.getByLabel('api-key').fill(apiKey);
  await page.getByRole('button', { name: 'Enregistrer' }).first().click();

  await page.goto(`${PREVIEW_URL}/runs/run-1`);
  await page.getByRole('tab', { name: 'Nodes' }).click();
  await page.getByTestId('node-row-node-1').click();
  const panel = page.getByTestId('feedback-panel');
  await expect(panel).toBeVisible();
  await expect(panel.getByText('auto bad')).toBeVisible();

  // Ajouter feedback humain
  await panel.getByPlaceholder('score').fill('80');
  await panel.getByPlaceholder('commentaire').fill('good');
  await panel.getByRole('button', { name: 'Envoyer' }).click();
  await expect(panel.getByText('good')).toBeVisible();

  // Badge critique
  const badge = page.getByTestId('node-row-node-1').getByTestId('feedback-badge');
  await expect(badge).toBeVisible();
  await expect(badge).toHaveCSS('background-color', 'rgb(255, 0, 0)');

  // Re-run guidé
  page.on('dialog', (d) => d.accept());
  await panel.getByRole('button', { name: 'Re-run guidé' }).click();
  await expect.poll(() => patchCalled).toBeTruthy();
});
