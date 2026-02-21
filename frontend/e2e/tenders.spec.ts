import { test, expect } from '@playwright/test';

test.describe('Tender Management', () => {
  test.beforeEach(async ({ page }) => {
    const uniqueId = Date.now().toString();
    const email = `tender_${uniqueId}@example.com`;
    const password = 'Password123!';
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const signUpTab = page.getByRole('tab', { name: /Registrarse|Sign Up/i });
    await signUpTab.click();
    const signupPanel = page.getByRole('tabpanel', { name: /Registrarse|Sign Up/i });
    await signupPanel.getByPlaceholder(/Juan Pérez|John Doe/i).fill('Tender User');
    await signupPanel.getByPlaceholder(/tu@ejemplo.com|you@example.com/i).fill(email);
    await signupPanel.getByPlaceholder(/Crea una contraseña|Create a password/i).fill(password);
    await signupPanel.getByRole('button', { name: /Crear cuenta|Create account/i }).click();
    
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.locator('header')).toBeVisible();
    
    // Create workspace for tenders
    await page.getByRole('button', { name: /Nuevo espacio|New space/i }).click();
    await page.fill('#space-name', 'Tender Workspace');
    await page.locator('button[type="submit"]').click();
    
    // Enter workspace via link
    await page.getByRole('link', { name: 'Tender Workspace' }).click();
    await expect(page).toHaveURL(/\/space\/.+/);
  });

  test('should create a new tender with a document', async ({ page }) => {
    const tenderName = 'E2E Tender';

    await page.getByRole('button', { name: /Nueva licitación|New tender/i }).click();
    await page.fill('#tender-name', tenderName);

    await page.setInputFiles('input[type="file"]', {
      name: 'test-document.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('%PDF-1.4\n%...')
    });

    await page.getByRole('button', { name: /Crear licitación|Create tender/i }).click();

    await expect(page.locator(`a:has-text("${tenderName}")`)).toBeVisible();
  });
});
