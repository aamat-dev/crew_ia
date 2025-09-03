import { test, expect } from '@playwright/test';

test('bascule du thème et persistance', async ({ page }) => {
  await page.goto('/');
  const toggle = page.getByTestId('theme-toggle');
  await toggle.click();
  await expect(page.locator('html')).toHaveClass(/dark/);
  await page.reload();
  await expect(page.locator('html')).toHaveClass(/dark/);
});
