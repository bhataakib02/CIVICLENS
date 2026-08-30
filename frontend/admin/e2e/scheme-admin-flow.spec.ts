import { test, expect } from '@playwright/test';

test.describe('E2E Scheme Admin & Four-Eyes Flow', () => {
  test('Scheme Creation -> Rule DSL -> Policy Simulation -> Four-Eyes Review -> Publish', async ({ page }) => {
    // 1. Author Login
    await page.goto('/login');
    await page.fill('input[type="email"]', 'scheme_author@gov.in');
    await page.fill('input[type="password"]', 'Password123!@#');
    await page.click('button[type="submit"]');

    await page.fill('input[placeholder="123456"]', '123456');
    await page.click('button[type="submit"]');

    // 2. Navigate to Schemes
    await page.click('a[href="/schemes"]');
    await expect(page.locator('h1:has-text("Scheme Administration Console")')).toBeVisible();

    // 3. Create Scheme
    await page.click('button:has-text("Create New Scheme")');
    await page.fill('input[placeholder*="Pradhan Mantri"]', 'PM Housing Support Scheme 2026');
    await page.fill('input[placeholder*="PM_KISAN"]', 'PM_HOUSING_2026');
    await page.click('button[type="submit"]');

    // 4. Validate & Add Rules in Rule DSL
    await expect(page.locator('text=Structured Eligibility Rule DSL Editor')).toBeVisible();
    await page.click('button:has-text("Validate DSL Grammar")');
    await expect(page.locator('text=Rule set is valid')).toBeVisible();

    // 5. Submit Version for Four-Eyes Review
    await page.click('button:has-text("Submit Version For Four-Eyes Review")');
    await expect(page.locator('text=Four-Eyes Rule Active')).toBeVisible();

    // 6. Test Author Self-Publish rejection (author cannot publish own version)
    await page.click('button:has-text("Approve & Publish Official Scheme Version")');
    await expect(page.locator('text=Publisher must differ from the version author')).toBeVisible();
  });
});
