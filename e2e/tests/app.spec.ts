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

  test('should show correct CWMP Preview title based on viewMode', async ({ page }) => {
    await page.goto('/');

    // Wait for the tree to load and click the first available node
    const treeNode = page.locator('.node-name-box').first();
    await expect(treeNode).toBeVisible({ timeout: 10000 });
    await treeNode.click();

    // Verify View mode displays GetParameterValues
    const viewTitle = page.locator('h3', { hasText: 'Generated CWMP GetParameterValues' });
    await expect(viewTitle).toBeVisible();

    // Switch to Edit mode
    const editBtn = page.locator('button', { hasText: 'Edit Mode' });
    await editBtn.click();

    // Verify Edit mode displays SetParameterValues
    const editTitle = page.locator('h3', { hasText: 'Generated CWMP SetParameterValues' });
    await expect(editTitle).toBeVisible();
  });

});
