import { test, expect } from '@playwright/test';

const PREVIEW_URL = process.env.PREVIEW_URL;

test('flux complet de création et exécution', async ({ page }) => {
  test.skip(!PREVIEW_URL, 'PREVIEW_URL non défini');

  const apiBase = 'https://mock.api';
  const apiKey = 'test-key';
  let sidecar = '{"a":1}';

  await page.route(`${apiBase}/**`, async (route) => {
    const req = route.request();
    const url = new URL(req.url());
    const path = url.pathname;

    if (req.method() === 'POST' && path === '/tasks') {
      expect(req.headers()['x-request-id']).toBeTruthy();
      return route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ id: 't1', title: 'demo', status: 'draft' }),
      });
    }

    if (req.method() === 'POST' && path === '/tasks/t1/plan') {
      return route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          plan_id: 'p1',
          status: 'ready',
          graph: { nodes: [{ id: 'n1' }, { id: 'n2' }], edges: [] },
        }),
      });
    }

    if (req.method() === 'GET' && path === '/plans/p1') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'p1',
          status: 'draft',
          graph: { nodes: [{ id: 'n1' }, { id: 'n2' }], edges: [] },
        }),
      });
    }

    if (req.method() === 'POST' && path === '/plans/p1/assignments') {
      expect(req.headers()['x-request-id']).toBeTruthy();
      return route.fulfill({ status: 200, body: '{}' });
    }

    if (req.method() === 'POST' && path === '/plans/p1/status') {
      return route.fulfill({ status: 200, body: '{}' });
    }

    if (req.method() === 'POST' && path === '/tasks/t1/start') {
      expect(url.searchParams.get('dry_run')).toBe('false');
      return route.fulfill({
        status: 202,
        contentType: 'application/json',
        body: JSON.stringify({ run_id: 'run-1', dry_run: false }),
      });
    }

    if (req.method() === 'GET' && path === '/runs/run-1') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'run-1',
          status: 'running',
          dag: {
            nodes: [{ id: 'n1', status: 'running', role: 'agent' }],
            edges: [],
          },
        }),
      });
    }

    if (req.method() === 'GET' && path === '/runs/run-1/summary') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'run-1', total_nodes: 1, succeeded: 0, failed: 0 }),
      });
    }

    if (req.method() === 'GET' && path === '/nodes/n1/artifacts') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            { id: 'a1', node_id: 'n1', name: 'log', kind: 'log', url: apiBase + '/log1' },
            { id: 'a2', node_id: 'n1', name: 'sidecar', kind: 'llm_sidecar', url: apiBase + '/sc1' },
          ],
        }),
      });
    }

    if (req.method() === 'GET' && path === '/log1') {
      return route.fulfill({ status: 200, body: 'log content' });
    }

    if (req.method() === 'GET' && path === '/sc1') {
      return route.fulfill({ status: 200, body: sidecar });
    }

    if (req.method() === 'PATCH' && path === '/nodes/n1') {
      const body = JSON.parse(req.postData() || '{}');
      if (body.action === 'override') {
        sidecar = '{"override":true}';
      }
      return route.fulfill({ status: 200, body: '{}' });
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
  await page.getByText('Générer le plan').click();

  await page.goto(`${PREVIEW_URL}/plans/p1`);

  await page.getByTestId('plan-node-n1').click();
  await page.getByLabel('role').fill('r1');
  await page.getByLabel('agent').fill('a1');
  await page.getByLabel('backend').fill('b1');
  await page.getByLabel('model').fill('m1');
  await page.getByRole('button', { name: 'Save Assignments' }).click();
  await expect(page.getByRole('status')).toHaveText('Assignation sauvegardée');

  await page.getByTestId('plan-node-n2').click();
  await page.getByLabel('role').fill('r2');
  await page.getByLabel('agent').fill('a2');
  await page.getByLabel('backend').fill('b2');
  await page.getByLabel('model').fill('m2');
  await page.getByRole('button', { name: 'Save Assignments' }).click();
  await expect(page.getByRole('status')).toHaveText('Assignation sauvegardée');

  await page.evaluate(async (base) => {
    await fetch(`${base}/tasks/t1/start?dry_run=false`, { method: 'POST' });
  }, apiBase);

  await page.goto(`${PREVIEW_URL}/runs/run-1`);
  await page.getByTestId('dag-node-n1').click();
  await expect(page.getByTestId('node-sidepanel')).toBeVisible();
  await expect(page.getByText('log content')).toBeVisible();
  await expect(page.getByText('{"a":1}')).toBeVisible();

  page.on('dialog', (d) => d.accept());
  await page.getByRole('button', { name: 'Pause' }).click();
  page.on('dialog', (d) => d.accept());
  await page.getByRole('button', { name: 'Resume' }).click();

  page.on('dialog', (d) => d.accept());
  await page.getByPlaceholder('prompt').fill('new prompt');
  await page.getByPlaceholder('params JSON').fill('{"x":1}');
  await page.getByRole('button', { name: 'Envoyer' }).click();
  await expect(page.getByText('{"override":true}')).toBeVisible();
});

