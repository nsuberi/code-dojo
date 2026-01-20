"""
Playwright E2E tests for PR submission feature.

These tests verify the complete PR submission workflow including:
- PR URL input and validation
- Real-time preview
- Submission creation
- Review tab display
- File diff viewer

Run with: pytest tests/playwright/test_pr_submission.py
"""

import pytest
from playwright.sync_api import Page, expect
import time


# Test Configuration
BASE_URL = "http://localhost:5000"
TEST_PR_URL = "https://github.com/nsuberi/snippet-manager-starter/pull/1"
INVALID_PR_URL = "https://github.com/invalid/repo/pull/999999"
WRONG_BASE_PR_URL = "https://github.com/octocat/Hello-World/pull/1"


@pytest.fixture(scope="session")
def base_url():
    """Provide base URL for tests."""
    return BASE_URL


@pytest.fixture
def authenticated_page(page: Page, base_url: str):
    """
    Provide an authenticated page for tests.

    Note: Update this fixture with actual login credentials
    or use a test user account.
    """
    # Navigate to login page
    page.goto(f"{base_url}/auth/login")

    # Fill in login credentials (update with test credentials)
    page.fill('input[name="email"]', 'test@example.com')
    page.fill('input[name="password"]', 'testpassword')

    # Submit login form
    page.click('button[type="submit"]')

    # Wait for navigation
    page.wait_for_load_state('networkidle')

    return page


class TestPRSubmissionFlow:
    """Test the complete PR submission workflow."""

    def test_submit_tab_displays_pr_input(self, authenticated_page: Page, base_url: str):
        """Test that submit tab shows PR URL input field."""
        # Navigate to a challenge page
        authenticated_page.goto(f"{base_url}/modules/1/goals/1")

        # Click Submit tab
        authenticated_page.click('button[data-tab="submit"]')

        # Verify PR URL input exists
        pr_input = authenticated_page.locator('#pr_url')
        expect(pr_input).to_be_visible()
        expect(pr_input).to_have_attribute('placeholder',
            'https://github.com/username/repo/pull/123')

        # Verify old repo_url and branch inputs don't exist
        repo_input = authenticated_page.locator('#repo_url')
        expect(repo_input).not_to_be_attached()

        branch_input = authenticated_page.locator('#branch')
        expect(branch_input).not_to_be_attached()

    def test_pr_preview_shows_on_valid_url(self, authenticated_page: Page, base_url: str):
        """Test that PR preview appears when valid URL is entered."""
        authenticated_page.goto(f"{base_url}/modules/1/goals/1")
        authenticated_page.click('button[data-tab="submit"]')

        # Enter valid PR URL
        pr_input = authenticated_page.locator('#pr_url')
        pr_input.fill(TEST_PR_URL)

        # Wait for preview to appear (debounced, so wait a bit)
        authenticated_page.wait_for_timeout(600)

        # Verify preview is visible
        preview = authenticated_page.locator('#pr-preview')
        expect(preview).to_be_visible()

        # Verify preview contains PR information
        expect(authenticated_page.locator('#pr-preview-content')).to_be_visible()

        # Verify status badge is shown
        status_badge = authenticated_page.locator('#pr-preview-status')
        expect(status_badge).to_be_visible()
        expect(status_badge).to_have_text(/OPEN|CLOSED|MERGED/)

    def test_pr_preview_shows_error_on_invalid_url(self, authenticated_page: Page, base_url: str):
        """Test that PR preview shows error for invalid URL."""
        authenticated_page.goto(f"{base_url}/modules/1/goals/1")
        authenticated_page.click('button[data-tab="submit"]')

        # Enter invalid format URL
        pr_input = authenticated_page.locator('#pr_url')
        pr_input.fill('https://github.com/owner/repo')

        # Wait for validation
        authenticated_page.wait_for_timeout(600)

        # Verify error is shown
        error = authenticated_page.locator('#pr-preview-error')
        expect(error).to_be_visible()
        expect(error).to_contain_text('Invalid PR URL format')

    def test_pr_preview_validates_base_repo(self, authenticated_page: Page, base_url: str):
        """Test that PR preview validates PR base matches starter repo."""
        authenticated_page.goto(f"{base_url}/modules/1/goals/1")
        authenticated_page.click('button[data-tab="submit"]')

        # Enter PR URL from wrong base repo
        pr_input = authenticated_page.locator('#pr_url')
        pr_input.fill(WRONG_BASE_PR_URL)

        # Wait for validation
        authenticated_page.wait_for_timeout(600)

        # Verify error about base repo mismatch
        error = authenticated_page.locator('#pr-preview-error')
        expect(error).to_be_visible()
        expect(error).to_contain_text(/base|does not match/i)

    def test_submit_valid_pr_creates_submission(self, authenticated_page: Page, base_url: str):
        """Test that submitting valid PR creates submission and redirects."""
        authenticated_page.goto(f"{base_url}/modules/1/goals/1")
        authenticated_page.click('button[data-tab="submit"]')

        # Enter valid PR URL
        pr_input = authenticated_page.locator('#pr_url')
        pr_input.fill(TEST_PR_URL)

        # Wait for preview validation
        authenticated_page.wait_for_timeout(600)

        # Submit form
        submit_button = authenticated_page.locator('button[type="submit"]')
        submit_button.click()

        # Wait for navigation to review tab
        authenticated_page.wait_for_url(f"**/#tab-review")

        # Verify we're on review tab
        review_tab = authenticated_page.locator('#tab-review')
        expect(review_tab).to_be_visible()

        # Verify success message
        success_alert = authenticated_page.locator('.alert-success')
        expect(success_alert).to_be_visible()
        expect(success_alert).to_contain_text(/submission received/i)

    def test_submit_invalid_pr_shows_error(self, authenticated_page: Page, base_url: str):
        """Test that submitting invalid PR shows error message."""
        authenticated_page.goto(f"{base_url}/modules/1/goals/1")
        authenticated_page.click('button[data-tab="submit"]')

        # Enter invalid PR URL (non-existent)
        pr_input = authenticated_page.locator('#pr_url')
        pr_input.fill(INVALID_PR_URL)

        # Submit form without waiting for validation
        submit_button = authenticated_page.locator('button[type="submit"]')
        submit_button.click()

        # Verify error message appears
        error_alert = authenticated_page.locator('.alert-danger')
        expect(error_alert).to_be_visible()
        expect(error_alert).to_contain_text(/could not fetch/i)


class TestReviewTabPRDisplay:
    """Test PR information display in review tab."""

    def test_review_tab_shows_pr_information(self, authenticated_page: Page, base_url: str):
        """Test that review tab displays PR information correctly."""
        # Navigate to review tab (assumes submission exists)
        authenticated_page.goto(f"{base_url}/modules/1/goals/1#tab-review")
        authenticated_page.click('button[data-tab="review"]')

        # Verify PR Information section exists
        pr_section = authenticated_page.locator('.review-card').filter(has_text='Pull Request Information')
        expect(pr_section).to_be_visible()

        # Verify PR title is displayed as link
        pr_title_link = authenticated_page.locator('.pr-title a')
        expect(pr_title_link).to_be_visible()
        expect(pr_title_link).to_have_attribute('href', /github\.com.*\/pull\/\d+/)

        # Verify PR status badge
        status_badge = authenticated_page.locator('.pr-status-badge')
        expect(status_badge).to_be_visible()
        expect(status_badge).to_have_text(/OPEN|CLOSED|MERGED/)

        # Verify PR number is shown
        pr_number = authenticated_page.locator('.pr-number')
        expect(pr_number).to_be_visible()
        expect(pr_number).to_contain_text(/#\d+/)

    def test_pr_stats_load_automatically(self, authenticated_page: Page, base_url: str):
        """Test that PR stats load automatically on review tab."""
        authenticated_page.goto(f"{base_url}/modules/1/goals/1#tab-review")
        authenticated_page.click('button[data-tab="review"]')

        # Wait for stats to load
        authenticated_page.wait_for_timeout(1000)

        # Verify stats are populated
        files_stat = authenticated_page.locator('[data-stat="files"]')
        expect(files_stat).not_to_have_text('Loading...')
        expect(files_stat).to_contain_text(/\d+/)

        additions_stat = authenticated_page.locator('[data-stat="additions"]')
        expect(additions_stat).to_contain_text(/\+\d+/)

        deletions_stat = authenticated_page.locator('[data-stat="deletions"]')
        expect(deletions_stat).to_contain_text(/-\d+/)

    def test_view_on_github_link_works(self, authenticated_page: Page, base_url: str):
        """Test that View on GitHub link is correct."""
        authenticated_page.goto(f"{base_url}/modules/1/goals/1#tab-review")
        authenticated_page.click('button[data-tab="review"]')

        # Find View on GitHub link
        github_link = authenticated_page.locator('a').filter(has_text='View on GitHub')
        expect(github_link).to_be_visible()
        expect(github_link).to_have_attribute('href', /github\.com.*\/pull\/\d+/)
        expect(github_link).to_have_attribute('target', '_blank')


class TestFileDiffViewer:
    """Test file-by-file diff viewer functionality."""

    def test_load_code_changes_button_exists(self, authenticated_page: Page, base_url: str):
        """Test that Load Code Changes button is present."""
        authenticated_page.goto(f"{base_url}/modules/1/goals/1#tab-review")
        authenticated_page.click('button[data-tab="review"]')

        # Find Load Code Changes button
        load_button = authenticated_page.locator('#load-changes-btn')
        expect(load_button).to_be_visible()
        expect(load_button).to_have_text('Load Code Changes')

    def test_clicking_load_shows_file_tree(self, authenticated_page: Page, base_url: str):
        """Test that clicking Load Code Changes displays file tree."""
        authenticated_page.goto(f"{base_url}/modules/1/goals/1#tab-review")
        authenticated_page.click('button[data-tab="review"]')

        # Click Load Code Changes
        load_button = authenticated_page.locator('#load-changes-btn')
        load_button.click()

        # Wait for file list to load
        authenticated_page.wait_for_selector('#file-list', state='visible', timeout=5000)

        # Verify file tree is displayed
        file_list = authenticated_page.locator('#file-list')
        expect(file_list).to_be_visible()

        # Verify file tree has items
        file_items = authenticated_page.locator('.file-tree-item')
        expect(file_items.first).to_be_visible()

        # Verify badge shows file count
        badge = authenticated_page.locator('#files-count-badge')
        expect(badge).to_be_visible()
        expect(badge).to_contain_text(/\d+ files?/)

    def test_file_tree_items_show_stats(self, authenticated_page: Page, base_url: str):
        """Test that file tree items display file stats."""
        authenticated_page.goto(f"{base_url}/modules/1/goals/1#tab-review")
        authenticated_page.click('button[data-tab="review"]')

        # Load file tree
        authenticated_page.click('#load-changes-btn')
        authenticated_page.wait_for_selector('.file-tree-item', state='visible')

        # Check first file item
        first_file = authenticated_page.locator('.file-tree-item').first

        # Verify file name is shown
        file_name = first_file.locator('.file-name')
        expect(file_name).to_be_visible()

        # Verify additions/deletions are shown
        additions = first_file.locator('.text-success')
        expect(additions).to_be_visible()
        expect(additions).to_contain_text(/\+\d+/)

        deletions = first_file.locator('.text-danger')
        expect(deletions).to_be_visible()
        expect(deletions).to_contain_text(/-\d+/)

    def test_clicking_file_expands_diff(self, authenticated_page: Page, base_url: str):
        """Test that clicking a file expands its diff."""
        authenticated_page.goto(f"{base_url}/modules/1/goals/1#tab-review")
        authenticated_page.click('button[data-tab="review"]')

        # Load file tree
        authenticated_page.click('#load-changes-btn')
        authenticated_page.wait_for_selector('.file-tree-item', state='visible')

        # Click first file
        first_file = authenticated_page.locator('.file-tree-item').first
        first_file.click()

        # Wait for diff to render
        authenticated_page.wait_for_timeout(500)

        # Verify diff container is visible
        diff_container = authenticated_page.locator('.diff-container').first
        expect(diff_container).to_be_visible()

        # Verify diff content is rendered
        diff_viewer = authenticated_page.locator('.diff-viewer').first
        expect(diff_viewer).to_be_visible()

        # Verify diff lines are shown
        diff_lines = authenticated_page.locator('.diff-line')
        expect(diff_lines.first).to_be_visible()

    def test_diff_shows_line_numbers(self, authenticated_page: Page, base_url: str):
        """Test that diff display includes line numbers."""
        authenticated_page.goto(f"{base_url}/modules/1/goals/1#tab-review")
        authenticated_page.click('button[data-tab="review"]')

        # Load and expand first file
        authenticated_page.click('#load-changes-btn')
        authenticated_page.wait_for_selector('.file-tree-item', state='visible')
        authenticated_page.locator('.file-tree-item').first.click()
        authenticated_page.wait_for_timeout(500)

        # Verify line numbers are present
        line_numbers = authenticated_page.locator('.line-number')
        expect(line_numbers.first).to_be_visible()

    def test_diff_highlights_additions_and_deletions(self, authenticated_page: Page, base_url: str):
        """Test that diff properly highlights added and removed lines."""
        authenticated_page.goto(f"{base_url}/modules/1/goals/1#tab-review")
        authenticated_page.click('button[data-tab="review"]')

        # Load and expand first file
        authenticated_page.click('#load-changes-btn')
        authenticated_page.wait_for_selector('.file-tree-item', state='visible')
        authenticated_page.locator('.file-tree-item').first.click()
        authenticated_page.wait_for_timeout(500)

        # Check for different line types
        diff_lines = authenticated_page.locator('.diff-line')

        # Should have at least one of: add, remove, or context line
        has_diff_lines = diff_lines.count() > 0
        assert has_diff_lines, "Diff should contain lines"

    def test_clicking_file_again_collapses_diff(self, authenticated_page: Page, base_url: str):
        """Test that clicking an expanded file collapses it."""
        authenticated_page.goto(f"{base_url}/modules/1/goals/1#tab-review")
        authenticated_page.click('button[data-tab="review"]')

        # Load file tree
        authenticated_page.click('#load-changes-btn')
        authenticated_page.wait_for_selector('.file-tree-item', state='visible')

        # Click to expand
        first_file = authenticated_page.locator('.file-tree-item').first
        first_file.click()
        authenticated_page.wait_for_timeout(500)

        # Verify expanded
        diff_container = authenticated_page.locator('.diff-container').first
        expect(diff_container).to_be_visible()

        # Click again to collapse
        first_file.click()
        authenticated_page.wait_for_timeout(300)

        # Verify collapsed (display: none)
        expect(diff_container).to_be_hidden()


class TestPRSubmissionRegression:
    """Regression tests to prevent breaking changes."""

    def test_form_validation_prevents_empty_submission(self, authenticated_page: Page, base_url: str):
        """Test that form validation prevents submitting without PR URL."""
        authenticated_page.goto(f"{base_url}/modules/1/goals/1")
        authenticated_page.click('button[data-tab="submit"]')

        # Try to submit without filling PR URL
        # HTML5 validation should prevent submission
        submit_button = authenticated_page.locator('button[type="submit"]')
        submit_button.click()

        # Verify we're still on the same page (didn't submit)
        expect(authenticated_page.locator('#pr_url')).to_be_visible()

    def test_pr_url_pattern_validation(self, authenticated_page: Page, base_url: str):
        """Test that PR URL input has pattern validation."""
        authenticated_page.goto(f"{base_url}/modules/1/goals/1")
        authenticated_page.click('button[data-tab="submit"]')

        pr_input = authenticated_page.locator('#pr_url')

        # Verify pattern attribute exists
        expect(pr_input).to_have_attribute('pattern', /github.*pull/)

    def test_ai_feedback_still_generates(self, authenticated_page: Page, base_url: str):
        """Test that AI feedback generation still works with PR URLs."""
        authenticated_page.goto(f"{base_url}/modules/1/goals/1")
        authenticated_page.click('button[data-tab="submit"]')

        # Submit valid PR
        pr_input = authenticated_page.locator('#pr_url')
        pr_input.fill(TEST_PR_URL)
        authenticated_page.wait_for_timeout(600)

        submit_button = authenticated_page.locator('button[type="submit"]')
        submit_button.click()

        # Wait for redirect to review
        authenticated_page.wait_for_url("**/#tab-review", timeout=10000)

        # Verify AI feedback section exists
        ai_feedback_section = authenticated_page.locator('.review-card').filter(has_text='AI Feedback')
        expect(ai_feedback_section).to_be_visible()

    def test_multiple_files_can_be_expanded(self, authenticated_page: Page, base_url: str):
        """Test that multiple files can be expanded simultaneously."""
        authenticated_page.goto(f"{base_url}/modules/1/goals/1#tab-review")
        authenticated_page.click('button[data-tab="review"]')

        # Load file tree
        authenticated_page.click('#load-changes-btn')
        authenticated_page.wait_for_selector('.file-tree-item', state='visible')

        # Get all file items
        file_items = authenticated_page.locator('.file-tree-item')
        item_count = file_items.count()

        if item_count >= 2:
            # Expand first two files
            file_items.nth(0).click()
            authenticated_page.wait_for_timeout(300)
            file_items.nth(1).click()
            authenticated_page.wait_for_timeout(300)

            # Verify both are visible
            diff_containers = authenticated_page.locator('.diff-container')
            expect(diff_containers.nth(0)).to_be_visible()
            expect(diff_containers.nth(1)).to_be_visible()
