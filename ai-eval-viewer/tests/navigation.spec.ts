import { test, expect } from '@playwright/test';

// Selector for all possible thread detail terminal states
const THREAD_DETAIL_READY = '[data-testid="span-tree-loaded"], [data-testid="span-tree-empty"], [data-testid="thread-not-found"]';

test.describe('AI Eval Viewer Navigation', () => {
  test('should load the dashboard with feature cards', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('[data-testid="dashboard-loaded"]', { timeout: 30000 });

    // Check page title content
    await expect(page.locator('h1')).toContainText('AI Eval Trace Viewer');

    // Check feature cards are present
    await expect(page.locator('.feature-card')).toHaveCount(3);

    // Check feature names - use first() to handle multiple matches
    await expect(page.locator('.feature-card-title').filter({ hasText: 'Digi-Trainer' })).toBeVisible();
    await expect(page.locator('.feature-card-title').filter({ hasText: 'Coding Planner' })).toBeVisible();
    await expect(page.locator('.feature-card-title').filter({ hasText: 'Code Review' })).toBeVisible();
  });

  test('should navigate to feature thread list on click', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('[data-testid="dashboard-loaded"]', { timeout: 30000 });

    // Wait for feature cards to load
    await expect(page.locator('.feature-card')).toHaveCount(3);

    // Click on Digi-Trainer feature card
    await page.locator('.feature-card-title').filter({ hasText: 'Digi-Trainer' }).click();

    // Should navigate to thread list
    await expect(page).toHaveURL(/\/feature\/digi-trainer/);

    // Should show feature name in header
    await expect(page.locator('.sidebar-header')).toContainText('Digi-Trainer');
  });

  test('should navigate using keyboard shortcuts', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('[data-testid="dashboard-loaded"]', { timeout: 30000 });

    // Wait for page to load
    await expect(page.locator('.feature-card')).toHaveCount(3);

    // Press j to move down
    await page.keyboard.press('j');

    // Press Enter to select
    await page.keyboard.press('Enter');

    // Should navigate to second feature (Coding Planner)
    await expect(page).toHaveURL(/\/feature\/coding-planner/);
  });

  test('should navigate directly with number keys', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('[data-testid="dashboard-loaded"]', { timeout: 30000 });

    // Wait for page to load
    await expect(page.locator('.feature-card')).toHaveCount(3);

    // Press 3 to jump to third feature (Code Review)
    await page.keyboard.press('3');

    // Should navigate to Code Review
    await expect(page).toHaveURL(/\/feature\/code-review/);
  });

  test('should open command palette with Cmd+K', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('[data-testid="dashboard-loaded"]', { timeout: 30000 });

    // Wait for page to fully load
    await expect(page.locator('.feature-card')).toHaveCount(3);

    // Open command palette - try Control+k as fallback since Meta may not work in headless
    await page.keyboard.press('Control+k');

    // Command palette should be visible
    await expect(page.locator('.command-palette')).toBeVisible({ timeout: 5000 });

    // Should have search input focused
    await expect(page.locator('.command-palette-input')).toBeFocused();
  });

  test('should show help overlay with ? key', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('[data-testid="dashboard-loaded"]', { timeout: 30000 });

    // Wait for page to fully load
    await expect(page.locator('.feature-card')).toHaveCount(3);

    // Open help overlay - type the ? character directly
    await page.keyboard.type('?');

    // Help overlay should be visible
    await expect(page.locator('.modal-title')).toContainText('Keyboard Shortcuts', { timeout: 5000 });

    // Close with Escape
    await page.keyboard.press('Escape');

    // Help should be closed
    await expect(page.locator('.modal-title')).not.toBeVisible();
  });

  test('should navigate back to dashboard from thread list', async ({ page }) => {
    await page.goto('/feature/digi-trainer');

    // Wait for threads to load (either loaded or no-threads)
    await page.waitForSelector('[data-testid="threads-loaded"], [data-testid="no-threads"]', { timeout: 30000 });

    // Wait for sidebar to be visible
    await expect(page.locator('.sidebar')).toBeVisible();

    // Press g to go back to dashboard
    await page.keyboard.press('g');

    // Should be back on dashboard
    await expect(page).toHaveURL('/');
  });

  test('should load thread list from LangSmith', async ({ page }) => {
    await page.goto('/feature/digi-trainer');

    // Wait for threads to load (either loaded or no-threads)
    await page.waitForSelector('[data-testid="threads-loaded"], [data-testid="no-threads"]', { timeout: 30000 });

    // Check the sidebar is visible
    await expect(page.locator('.sidebar')).toBeVisible();
  });
});

test.describe('Annotation Panel', () => {
  test('should open annotation panel with a key', async ({ page }) => {
    await page.goto('/feature/digi-trainer');
    await page.waitForSelector('[data-testid="threads-loaded"], [data-testid="no-threads"]', { timeout: 30000 });

    const threadList = page.locator('.list-item');
    const threadCount = await threadList.count();

    if (threadCount === 0) {
      test.skip(true, 'No threads available');
      return;
    }

    // Focus and open first thread
    await threadList.first().focus();
    await page.keyboard.press('Enter');

    // Wait for thread detail to load
    await page.waitForSelector(THREAD_DETAIL_READY, { timeout: 30000 });

    // Skip if thread not found or no spans
    if (await page.locator('[data-testid="thread-not-found"]').isVisible()) {
      test.skip(true, 'Thread not found');
      return;
    }
    if (!(await page.locator('[data-testid="span-tree-loaded"]').isVisible())) {
      test.skip(true, 'No spans in thread');
      return;
    }
    await expect(page.locator('.tree-node').first()).toBeVisible();

    // Press a to open annotation panel
    await page.keyboard.press('a');

    // Annotation panel should be visible
    await expect(page.locator('.panel.open')).toBeVisible();

    // Should have notes section
    await expect(page.getByText('Notes')).toBeVisible();

    // Should have tags section
    await expect(page.getByRole('heading', { name: 'Tags' })).toBeVisible();

    // Should have datasets section
    await expect(page.getByText('Datasets')).toBeVisible();
  });

  test('should add a note to a span', async ({ page }) => {
    await page.goto('/feature/digi-trainer');
    await page.waitForSelector('[data-testid="threads-loaded"], [data-testid="no-threads"]', { timeout: 30000 });

    const threadList = page.locator('.list-item');
    const threadCount = await threadList.count();

    if (threadCount === 0) {
      test.skip(true, 'No threads available');
      return;
    }

    // Focus and open first thread
    await threadList.first().focus();
    await page.keyboard.press('Enter');

    // Wait for thread detail to load
    await page.waitForSelector(THREAD_DETAIL_READY, { timeout: 30000 });

    // Skip if thread not found or no spans
    if (await page.locator('[data-testid="thread-not-found"]').isVisible()) {
      test.skip(true, 'Thread not found');
      return;
    }
    if (!(await page.locator('[data-testid="span-tree-loaded"]').isVisible())) {
      test.skip(true, 'No spans in thread');
      return;
    }
    await expect(page.locator('.tree-node').first()).toBeVisible();

    // Press n to open annotation panel for span
    await page.keyboard.press('n');

    // Type a note
    await page.locator('textarea').fill('This is a test note');

    // Save with button click
    await page.getByRole('button', { name: 'Save Note' }).click();

    // Note should appear in the list
    await expect(page.getByText('This is a test note')).toBeVisible();
  });
});

test.describe('Thread Detail View', () => {
  test('should display span tree when viewing a thread', async ({ page }) => {
    // Navigate to a feature
    await page.goto('/feature/digi-trainer');
    await page.waitForSelector('[data-testid="threads-loaded"], [data-testid="no-threads"]', { timeout: 30000 });

    const threadList = page.locator('.list-item');
    const threadCount = await threadList.count();

    if (threadCount === 0) {
      test.skip(true, 'No threads available');
      return;
    }

    // Click first thread
    await threadList.first().click();

    // Wait for thread detail to load
    await page.waitForSelector(THREAD_DETAIL_READY, { timeout: 30000 });

    // Skip if thread not found or no spans
    if (await page.locator('[data-testid="thread-not-found"]').isVisible()) {
      test.skip(true, 'Thread not found');
      return;
    }
    if (!(await page.locator('[data-testid="span-tree-loaded"]').isVisible())) {
      test.skip(true, 'No spans in thread');
      return;
    }
    await expect(page.locator('.tree-node').first()).toBeVisible();
  });

  test('should navigate span tree with keyboard', async ({ page }) => {
    await page.goto('/feature/digi-trainer');
    await page.waitForSelector('[data-testid="threads-loaded"], [data-testid="no-threads"]', { timeout: 30000 });

    const threadList = page.locator('.list-item');
    const threadCount = await threadList.count();

    if (threadCount === 0) {
      test.skip(true, 'No threads available');
      return;
    }

    // Focus and open first thread
    await threadList.first().focus();
    await page.keyboard.press('Enter');

    // Wait for thread detail to load
    await page.waitForSelector(THREAD_DETAIL_READY, { timeout: 30000 });

    // Skip if thread not found or no spans
    if (await page.locator('[data-testid="thread-not-found"]').isVisible()) {
      test.skip(true, 'Thread not found');
      return;
    }
    if (!(await page.locator('[data-testid="span-tree-loaded"]').isVisible())) {
      test.skip(true, 'No spans in thread');
      return;
    }
    await expect(page.locator('.tree-node').first()).toBeVisible();

    // Navigate with j/k
    await page.keyboard.press('j');
    await page.keyboard.press('k');

    // Expand/collapse with l/h
    await page.keyboard.press('l');
    await page.keyboard.press('h');
  });
});
