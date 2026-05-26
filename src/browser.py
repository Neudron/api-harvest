"""Async Playwright browser manager for AI API key harvesting."""

from playwright.async_api import async_playwright

_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)


class BrowserManager:
    """Context manager for launching and reusing a single Chromium browser.

    Usage:
        async with BrowserManager() as page:
            for provider in providers:
                await provider.run(page, config)
    """

    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.playwright_instance = None

    async def __aenter__(self):
        """Launch browser with a realistic context and return a single shared page."""
        self.playwright_instance = await async_playwright().start()
        self.browser = await self.playwright_instance.chromium.launch(headless=False)

        # Use a browser context so user-agent + viewport apply and Google doesn't
        # immediately flag the session as automated.
        self.context = await self.browser.new_context(
            user_agent=_USER_AGENT,
            viewport={"width": 1280, "height": 800},
        )
        self.page = await self.context.new_page()
        return self.page

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close page, context, browser, and Playwright cleanly."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright_instance:
            await self.playwright_instance.stop()
        return False
