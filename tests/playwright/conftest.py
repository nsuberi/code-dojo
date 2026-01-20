"""Pytest configuration for Playwright tests."""

import pytest
from playwright.sync_api import Browser, BrowserContext, Page


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """
    Configure browser context with common settings.

    This fixture can be used to set viewport size, locale, timezone, etc.
    """
    return {
        **browser_context_args,
        "viewport": {
            "width": 1920,
            "height": 1080,
        },
        "ignore_https_errors": True,  # For local testing
    }


@pytest.fixture(scope="function")
def context(browser: Browser, browser_context_args):
    """Create a new browser context for each test."""
    context = browser.new_context(**browser_context_args)
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext):
    """Create a new page for each test."""
    page = context.new_page()
    yield page
    page.close()
