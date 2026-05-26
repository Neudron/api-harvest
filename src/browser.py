"""Async Playwright browser manager for AI API key harvesting."""

from playwright.async_api import async_playwright


class BrowserManager:
    """Context manager for launching and reusing a single Chromium browser.

    Usage:
        async with BrowserManager() as page:
            for provider in providers:
                await provider.run(page, config)
    """

    def __init__(self):
        """Initialize the BrowserManager."""
        self.browser = None
        self.page = None
        self.playwright_instance = None

    async def __aenter__(self):
        """Launch the browser and create a page.

        Returns:
            The Playwright page object for all providers to reuse.
        """
        # Start Playwright
        self.playwright_instance = await async_playwright().start()

        # Launch Chromium in non-headless mode (user can see and interact)
        self.browser = await self.playwright_instance.chromium.launch(headless=False)

        # Create a single page to reuse across all providers
        self.page = await self.browser.new_page()

        return self.page

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up: close the page and browser.

        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)
        """
        # Close the page
        if self.page:
            await self.page.close()

        # Close the browser
        if self.browser:
            await self.browser.close()

        # Stop Playwright
        if self.playwright_instance:
            await self.playwright_instance.stop()

        # Don't suppress exceptions
        return False
