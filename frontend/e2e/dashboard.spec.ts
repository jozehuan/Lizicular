import { test, expect } from '@playwright/test';

test.describe('Dashboard & Workspaces', () => {
  test.beforeEach(async ({ page }) => {
    const uniqueId = Date.now().toString();
    const email = `workspace_${uniqueId}@example.com`;
    const password = 'Password123!';
    const name = 'Workspace Tester';

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Register
    const signUpTab = page.getByRole('tab', { name: /Registrarse|Sign Up/i });
    await signUpTab.click();
    const signupPanel = page.getByRole('tabpanel', { name: /Registrarse|Sign Up/i });
    await signupPanel.getByPlaceholder(/Juan Pérez|John Doe/i).fill(name);
    await signupPanel.getByPlaceholder(/tu@ejemplo.com|you@example.com/i).fill(email);
    await signupPanel.getByPlaceholder(/Crea una contraseña|Create a password/i).fill(password);
    await signupPanel.getByRole('button', { name: /Crear cuenta|Create account/i }).click();
    
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.locator('header')).toBeVisible();
  });

  test('should create a new workspace', async ({ page }) => {
    const spaceName = 'E2E Test Space';
    const spaceDesc = 'Created via Playwright';

    await page.getByRole('button', { name: /Nuevo espacio|New space/i }).click();
    await expect(page.locator('#space-name')).toBeVisible();
    
    await page.fill('#space-name', spaceName);
    await page.fill('#space-description', spaceDesc);

    await page.locator('button[type="submit"]').click();

    // Verify name appears (it's a link)
    const spaceLink = page.getByRole('link', { name: spaceName });
    await expect(spaceLink).toBeVisible();

    // To see description, we must expand the accordion. 
    // The trigger is the parent button. We can find it by finding the row that contains the text.
    // However, clicking the link navigates. We need to click the trigger area OUTSIDE the link.
    // The hexagon icon is a good safe target inside the trigger.
    const spaceRow = page.locator('div.group', { hasText: spaceName });
    const trigger = spaceRow.locator('button[aria-expanded]'); 
    // Or simpler: click the SVG icon which is part of the trigger but not the link
    await spaceRow.locator('svg').first().click();

    await expect(page.getByText(spaceDesc)).toBeVisible();
  });

  test('should navigate to workspace details', async ({ page }) => {
    const spaceName = 'Navigation Space';
    
    await page.getByRole('button', { name: /Nuevo espacio|New space/i }).click();
    await page.fill('#space-name', spaceName);
    await page.locator('button[type="submit"]').click();

    const spaceLink = page.getByRole('link', { name: spaceName });
    await expect(spaceLink).toBeVisible();
    
    // Force click if necessary, or just click. 
    // Sometimes animations intervene, so we wait.
    await spaceLink.click();

    await expect(page).toHaveURL(/\/space\/.+/);
    // CardTitle renders as a div usually in recent shadcn versions or h3. 
    // Let's use a text locator restricted to main to be safe.
    await expect(page.locator('main').getByText(spaceName, { exact: true })).toBeVisible();
  });
});
