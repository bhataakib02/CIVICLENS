import { test, expect } from '@playwright/test';

test.describe('E2E Admin Operations Flow', () => {
  test('Staff Login -> Dashboard -> Application Review -> Document Verification', async ({ page }) => {
    // 1. Staff Login
    await page.goto('/login');
    await page.fill('input[type="email"]', 'admin@gov.in');
    await page.fill('input[type="password"]', 'Password123!@#');
    await page.click('button[type="submit"]');

    // 2. MFA
    await expect(page.locator('text=Multi-Factor Authentication Required')).toBeVisible();
    await page.fill('input[placeholder="123456"]', '123456');
    await page.click('button[type="submit"]');

    // 3. Dashboard
    await expect(page.locator('h1:has-text("Operational Dashboard")')).toBeVisible();
    await expect(page.locator('text=Pending Application Review')).toBeVisible();

    // 4. Open submitted applications
    await page.click('a[href="/applications"]');
    await expect(page.locator('h1:has-text("Application Queue")')).toBeVisible();

    // 5. Open application detail if available
    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.isVisible()) {
      await firstRow.click();
      await expect(page.locator('h1:has-text("Case File Detail")')).toBeVisible();
      await expect(page.locator('text=Authoritative Eligibility Snapshot')).toBeVisible();
      await expect(page.locator('text=Document Readiness Checklist')).toBeVisible();
    }
  });
});
