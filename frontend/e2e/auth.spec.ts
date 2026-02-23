import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  const uniqueId = Date.now().toString();
  const email = `testuser_${uniqueId}@example.com`;
  const password = 'Password123!';
  const name = 'Test User';

  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should allow a user to sign up', async ({ page }) => {
    // Switch to Sign Up tab
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

  test('should allow a user to log out', async ({ page }) => {
    // Create user
    const logoutId = Date.now().toString() + "_out";
    const logoutEmail = `logout_${logoutId}@example.com`;
    
    const signUpTab = page.getByRole('tab', { name: /Registrarse|Sign Up/i });
    await signUpTab.click();
    const signupPanel = page.getByRole('tabpanel', { name: /Registrarse|Sign Up/i });
    await signupPanel.getByPlaceholder(/Juan Pérez|John Doe/i).fill('Logout User');
    await signupPanel.getByPlaceholder(/tu@ejemplo.com|you@example.com/i).fill(logoutEmail);
    await signupPanel.getByPlaceholder(/Crea una contraseña|Create a password/i).fill(password);
    await signupPanel.getByRole('button', { name: /Crear cuenta|Create account/i }).click();
    
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.locator('header')).toBeVisible();

    // Perform Logout
    await page.locator('header button:has(.h-8.w-8)').click();
    await page.getByRole('menuitem', { name: /Cerrar sesión|Sign out/i }).click();
    
    // Should redirect to login page (or home with login form)
    // Allow matching /en, /es or root
    await expect(page).toHaveURL(/http:\/\/localhost:3000\/((en|es)\/?)?$/); 
    // Wait for something characteristic of the login page
    await expect(page.getByRole('tab', { name: /Login|Iniciar Sesión/i })).toBeVisible();
  });

  test('should allow a user to log in', async ({ page }) => {
    const loginId = Date.now().toString() + "_in";
    const loginEmail = `login_${loginId}@example.com`;
    
    // Register
    const signUpTab = page.getByRole('tab', { name: /Registrarse|Sign Up/i });
    await signUpTab.click();
    const signupPanel = page.getByRole('tabpanel', { name: /Registrarse|Sign Up/i });
    await signupPanel.getByPlaceholder(/Juan Pérez|John Doe/i).fill('Login User');
    await signupPanel.getByPlaceholder(/tu@ejemplo.com|you@example.com/i).fill(loginEmail);
    await signupPanel.getByPlaceholder(/Crea una contraseña|Create a password/i).fill(password);
    await signupPanel.getByRole('button', { name: /Crear cuenta|Create account/i }).click();
    
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.locator('header')).toBeVisible();
    
    // Logout
    await page.locator('header button:has(.h-8.w-8)').click();
    await page.getByRole('menuitem', { name: /Cerrar sesión|Sign out/i }).click();
    
    // Login
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const loginTab = page.getByRole('tab', { name: /Login|Iniciar Sesión/i });
    if (await loginTab.getAttribute('aria-selected') !== 'true') {
        await loginTab.click();
    }
    
    const loginPanel = page.getByRole('tabpanel', { name: /Login|Iniciar Sesión/i });
    await loginPanel.getByPlaceholder(/tu@ejemplo.com|you@example.com/i).fill(loginEmail);
    await loginPanel.getByPlaceholder(/Introduce tu contraseña|Enter your password/i).fill(password);
    
    await loginPanel.getByRole('button', { name: /Entrar|Sign in/i }).click();
    
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.locator('header')).toBeVisible();
  });
});
