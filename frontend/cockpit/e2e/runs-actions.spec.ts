import { test, expect } from '@playwright/test';

test('actions Pause puis Resume affichent des toasts', async ({ page }) => {
  await page.goto('/runs');
  await page.getByRole('button', { name: 'Pause' }).click();
  await expect(page.getByText('Run paused')).toBeVisible();
  await page.getByRole('button', { name: 'Resume' }).click();
  await expect(page.getByText('Run resumed')).toBeVisible();
});
