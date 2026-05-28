from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class BrowserHandle:
    playwright: Any
    browser: Any | None  # may be None for persistent_context mode
    context: Any
    is_cdp: bool


async def open_browser(
    *,
    cdp_port: int | None = None,
    profile_dir: Path | None = None,
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
        context = contexts[0] if contexts else await browser.new_context()
        return BrowserHandle(playwright=pw, browser=browser, context=context, is_cdp=True)

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


async def close_browser(handle: BrowserHandle) -> None:
    try:
        if handle.is_cdp and handle.browser is not None:
            # CDP: don't close the user's Chrome; just disconnect
            await handle.browser.close()
        else:
            await handle.context.close()
    finally:
        await handle.playwright.stop()
