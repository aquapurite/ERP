import { test, expect, Page } from '@playwright/test';

// Helper to login
async function login(page: Page) {
  await page.goto('/login');
  await page.getByLabel(/email/i).fill('admin@consumer.com');
  await page.getByLabel(/password/i).fill('Admin@123');
  await page.getByRole('button', { name: /sign in/i }).click();
  await page.waitForURL(/dashboard/, { timeout: 30000 });
}

test.describe('Vendor Invoices - 3-Way Match Fix', () => {
  test.setTimeout(60000); // Increase timeout for all tests

  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should navigate to vendor invoices page', async ({ page }) => {
    await page.goto('/dashboard/procurement/vendor-invoices');
    await page.waitForLoadState('networkidle');

    // Check page loaded - use specific heading selector
    await expect(page.getByRole('heading', { name: 'Vendor Invoices' })).toBeVisible({ timeout: 10000 });
  });

  test('should show Upload Invoice button and dialog with form fields', async ({ page }) => {
    await page.goto('/dashboard/procurement/vendor-invoices');
    await page.waitForLoadState('networkidle');

    // Click Upload Invoice button
    const uploadBtn = page.getByRole('button', { name: /upload invoice/i });
    await expect(uploadBtn).toBeVisible({ timeout: 10000 });
    await uploadBtn.click();

    // Dialog should open
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText('Upload Vendor Invoice')).toBeVisible();

    // Check form fields are visible (vendor, invoice number, date, PO link)
    await expect(page.getByText('Vendor *')).toBeVisible();
    await expect(page.getByText(/Invoice Number/)).toBeVisible();
    await expect(page.getByText(/Invoice Date/)).toBeVisible();
    await expect(page.getByText(/Link to PO/)).toBeVisible();

    // Check action buttons exist
    await expect(page.getByRole('button', { name: /cancel/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /upload.*process/i })).toBeVisible();
  });

  test('should require vendor selection', async ({ page }) => {
    await page.goto('/dashboard/procurement/vendor-invoices');
    await page.waitForLoadState('networkidle');

    // Open dialog
    await page.getByRole('button', { name: /upload invoice/i }).click();
    await expect(page.getByRole('dialog')).toBeVisible();

    // Try to submit without vendor - should show error
    await page.getByRole('button', { name: /upload.*process/i }).click();

    // Should show error toast
    await expect(page.locator('text=Please select a vendor')).toBeVisible({ timeout: 5000 });
  });

  test('should load vendors dropdown', async ({ page }) => {
    await page.goto('/dashboard/procurement/vendor-invoices');
    await page.waitForLoadState('networkidle');

    // Open dialog
    const uploadBtn = page.getByRole('button', { name: /upload invoice/i });
    await expect(uploadBtn).toBeVisible({ timeout: 15000 });
    await uploadBtn.click();
    await expect(page.getByRole('dialog')).toBeVisible({ timeout: 10000 });

    // Click vendor dropdown - there's a label "Select Vendor *" for the trigger
    const vendorDropdown = page.locator('button').filter({ hasText: /select vendor/i }).first();
    await expect(vendorDropdown).toBeVisible({ timeout: 10000 });
    await vendorDropdown.click();

    // Wait for vendors to load - use longer timeout
    await page.waitForTimeout(3000);

    // Should show vendor options (checking dropdown opened) - could be listbox or popover
    const dropdownContent = page.locator('[role="listbox"], [data-radix-popper-content-wrapper]');
    await expect(dropdownContent.first()).toBeVisible({ timeout: 10000 });
  });

  test('should navigate to 3-way match page', async ({ page }) => {
    await page.goto('/dashboard/procurement/three-way-match');
    await page.waitForLoadState('networkidle');

    // Check page loaded
    await expect(page.locator('text=3-Way Match')).toBeVisible({ timeout: 10000 });
  });

  test('should navigate to GRN page', async ({ page }) => {
    await page.goto('/dashboard/procurement/grn');
    await page.waitForLoadState('networkidle');

    // Check page loaded - use heading or any text containing "GRN" or "Goods Receipt"
    await expect(page.getByText(/Goods Receipt|GRN/i).first()).toBeVisible({ timeout: 15000 });

    // Check Create GRN button exists
    await expect(page.getByRole('button', { name: /create grn/i })).toBeVisible({ timeout: 10000 });
  });

  test('should show stats cards on vendor invoices page', async ({ page }) => {
    await page.goto('/dashboard/procurement/vendor-invoices');
    await page.waitForLoadState('networkidle');

    // Check stats cards exist
    await expect(page.locator('text=Total Invoices')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Pending Review')).toBeVisible();
    await expect(page.locator('text=Matched')).toBeVisible();
    await expect(page.locator('text=Mismatch')).toBeVisible();
  });
});
