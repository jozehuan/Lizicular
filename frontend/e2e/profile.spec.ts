import { test, expect } from '@playwright/test';

test.describe('Profile Management', () => {
  let email: string;

  test.beforeEach(async ({ page }) => {
    const uniqueId = Date.now().toString();
    email = `profile_${uniqueId}@example.com`;
    const password = 'Password123!';
    const name = 'Profile Tester';

    await page.goto('/');
    await page.waitForLoadState('networkidle');

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

  test('should allow changing the full name', async ({ page }) => {
    await page.locator('header button:has(.h-8.w-8)').click();
    
    // Wait for dropdown to appear
    const profileItem = page.getByRole('menuitem', { name: /Perfil|Profile/i });
    await expect(profileItem).toBeVisible();
    await profileItem.click();
    
    await expect(page).toHaveURL(/\/profile/);
    await page.waitForLoadState('networkidle'); // Ensure profile data is loaded

    const newName = 'Updated Name';
    await page.fill('#full_name', newName);
    await page.getByRole('button', { name: /Guardar cambios|Save changes/i }).click();

    await expect(page.getByText(/Perfil actualizado|Profile updated/i)).toBeVisible();
    await expect(page.locator('header')).toContainText(newName);
  });

  test('should allow changing the avatar', async ({ page }) => {
    await page.locator('header button:has(.h-8.w-8)').click();
    
    const profileItem = page.getByRole('menuitem', { name: /Perfil|Profile/i });
    await expect(profileItem).toBeVisible();
    await profileItem.click();
    
    await expect(page).toHaveURL(/\/profile/);
    await page.waitForLoadState('networkidle');

    const avatarButtons = page.locator('button:has(img[alt="Avatar Option"])');
    // Wait for buttons to be present
    await expect(avatarButtons.first()).toBeVisible();
    await expect(avatarButtons).toHaveCount(4); 
    
    await avatarButtons.nth(1).click();

    await expect(page.getByText(/Perfil actualizado|Profile updated/i)).toBeVisible();
  });
  
  test('should prevent changing email', async ({ page }) => {
      await page.locator('header button:has(.h-8.w-8)').click();
      
      const profileItem = page.getByRole('menuitem', { name: /Perfil|Profile/i });
      await expect(profileItem).toBeVisible();
      await profileItem.click();
      
      await expect(page).toHaveURL(/\/profile/);
      
      const emailDisplay = page.locator('main p').filter({ hasText: email });
      
      await expect(emailDisplay).toBeVisible();
      await expect(emailDisplay).toHaveClass(/cursor-not-allowed/);
  });
});
