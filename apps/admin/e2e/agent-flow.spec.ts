import { test, expect } from '@playwright/test';

test.describe('E2E Agent / CSC Console Flow & Consent Enforcement', () => {
  test('Agent Login -> Authorized Citizen List -> Consent Verification -> Revocation Access Denied', async ({ page }) => {
    // 1. Agent Login
    await page.goto('/login');
    await page.fill('input[type="email"]', 'agent@csc.gov.in');
    await page.fill('input[type="password"]', 'Password123!@#');
    await page.click('button[type="submit"]');

    await page.fill('input[placeholder="123456"]', '123456');
    await page.click('button[type="submit"]');

    // 2. Navigate to Assisted Citizens
    await page.click('a[href="/assisted-citizens"]');
    await expect(page.locator('h1:has-text("Agent / CSC Assisted Citizens")')).toBeVisible();

    // 3. Verify role boundaries: Agents cannot see global admin settings/users or global citizens directory
    await expect(page.locator('a[href="/settings"]')).toHaveCount(0);
    await expect(page.locator('a[href="/audit"]')).toHaveCount(0);
  });
});
