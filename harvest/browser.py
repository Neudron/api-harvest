from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class BrowserHandle:
    playwright: Any
    browser: Any | None  # None when launched as a persistent_context
    context: Any
    is_cdp: bool
    owned_pages: list[Any] = field(default_factory=list)  # pages we created (CDP only)
    context_count_at_attach: int = 0  # how many contexts existed when we attached


async def open_browser(
    *,
    cdp_port: int | None = None,
    profile_dir: Path | None = None,
    cdp_context_index: int = 0,
) -> BrowserHandle:
    """Open a Playwright context either by attaching to a running Chrome (CDP)
    or by launching a persistent Chromium profile."""
    if (cdp_port is None) == (profile_dir is None):
        raise ValueError("Exactly one of cdp_port or profile_dir must be provided")

    from playwright.async_api import async_playwright

    pw = await async_playwright().start()

    if cdp_port is not None:
        browser = await pw.chromium.connect_over_cdp(f"http://127.0.0.1:{cdp_port}")
        contexts = browser.contexts
        if not contexts:
            context = await browser.new_context()
        elif cdp_context_index < len(contexts):
            context = contexts[cdp_context_index]
        else:
            context = contexts[0]
        return BrowserHandle(
            playwright=pw,
            browser=browser,
            context=context,
            is_cdp=True,
            context_count_at_attach=len(contexts),
        )

    assert profile_dir is not None
    profile_dir.mkdir(parents=True, exist_ok=True)
    context = await pw.chromium.launch_persistent_context(
        user_data_dir=str(profile_dir),
        headless=False,
        channel="chrome",
        viewport={"width": 1400, "height": 900},
        args=["--disable-blink-features=AutomationControlled"],
    )
    return BrowserHandle(playwright=pw, browser=None, context=context, is_cdp=False)


async def new_page(handle: BrowserHandle):
    """Open a new page and track it so close_browser only closes pages we created."""
    page = await handle.context.new_page()
    if handle.is_cdp:
        handle.owned_pages.append(page)
    return page


async def close_browser(handle: BrowserHandle) -> None:
    try:
        if handle.is_cdp and handle.browser is not None:
            # CDP attach: close only pages we created, never touch the browser
            # or the user's pre-existing context — stopping Playwright tears down
            # the websocket cleanly without telling Chrome to exit.
            for page in handle.owned_pages:
                try:
                    if not page.is_closed():
                        await page.close()
                except Exception:
                    pass
        else:
            await handle.context.close()
    finally:
        try:
            await handle.playwright.stop()
        except Exception:
            pass
