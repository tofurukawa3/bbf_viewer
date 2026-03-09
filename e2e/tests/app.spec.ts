import { test, expect } from '@playwright/test';

test.describe('BBF Viewer Applicaton E2E tests', () => {

  test('should load the frontend and connect to backend', async ({ page }) => {
    // 1. Check if the frontend server is reachable
    await page.goto('/');

    // 2. Validate the title
    await expect(page).toHaveTitle(/BBF Viewer/);

    // 3. Check for specific UI elements
    const heading = page.getByRole('heading', { name: 'BBF DataModel Viewer' });
    await expect(heading).toBeVisible();

    // 4. Validate that data from the backend is loaded properly 
    const treeView = page.locator('.tree-container');
    await expect(treeView).toBeVisible({ timeout: 10000 });
  });

});
