import { test, expect } from '@playwright/test';

test('naviguer via la palette de commandes', async ({ page }) => {
  await page.goto('/');
  const modifier = process.platform === 'darwin' ? 'Meta' : 'Control';
  await page.keyboard.press(`${modifier}+K`);
  await page.getByRole('textbox').fill('Runs');
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/runs/);
});
