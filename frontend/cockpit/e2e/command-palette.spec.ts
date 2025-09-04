import { test, expect } from '@playwright/test';

test('naviguer via la palette de commandes', async ({ page }) => {
  await page.goto('/');
  const modifier = process.platform === 'darwin' ? 'Meta' : 'Control';
  await page.keyboard.press(`${modifier}+K`);
  await expect(page.getByRole('textbox')).toBeFocused();
  await page.getByRole('textbox').fill('Runs');
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/runs/);
});

test('ouvrir la palette via le bouton', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Ouvrir la palette de commandes').click();
  await expect(page.getByRole('textbox')).toBeFocused();
});
