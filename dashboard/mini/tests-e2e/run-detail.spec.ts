import { test, expect } from '@playwright/test';

const PREVIEW_URL = process.env.PREVIEW_URL;

test('actions sur un noeud', async ({ page }) => {
  test.skip(!PREVIEW_URL, 'PREVIEW_URL non défini');

  const apiBase = 'https://mock.api';
  const apiKey = 'test-key';
  let sidecarContent = '{"a":1}';

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
            nodes: [{ id: 'node-1', status: 'running', role: 'agent' }],
            edges: [],
          },
        }),
      });
    } else if (url.endsWith('/nodes/node-1/artifacts')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            { id: 'a1', node_id: 'node-1', name: 'log', kind: 'log', url: apiBase + '/log1' },
            {
              id: 'a2',
              node_id: 'node-1',
              name: 'sidecar',
              kind: 'llm_sidecar',
              url: apiBase + '/sc1',
            },
          ],
        }),
      });
    } else if (url.endsWith('/log1')) {
      await route.fulfill({ status: 200, body: 'log content' });
    } else if (url.endsWith('/sc1')) {
      await route.fulfill({ status: 200, body: sidecarContent });
    } else if (url.includes('/nodes/node-1') && req.method() === 'PATCH') {
      const body = JSON.parse(req.postData() || '{}');
      if (body.action === 'override') {
        sidecarContent = '{"override":true}';
      }
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
  await page.getByTestId('dag-node-node-1').click();
  await expect(page.getByTestId('node-sidepanel')).toBeVisible();
  await expect(page.getByText('log content')).toBeVisible();
  await expect(page.getByText('{"a":1}')).toBeVisible();

  page.on('dialog', (d) => d.accept());
  await page.getByRole('button', { name: 'Pause' }).click();
  await expect(page.getByText(/Request ID:/)).toBeVisible();

  page.on('dialog', (d) => d.accept());
  await page.getByRole('button', { name: 'Resume' }).click();

  page.on('dialog', (d) => d.accept());
  await page.getByPlaceholder('prompt').fill('new prompt');
  await page.getByPlaceholder('params JSON').fill('{"x":1}');
  await page.getByRole('button', { name: 'Envoyer' }).click();
  await expect(page.getByText('{"override":true}')).toBeVisible();

  page.on('dialog', (d) => d.accept());
  await page.getByRole('button', { name: 'Skip' }).click();
});
