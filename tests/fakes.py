"""Offline fakes for exercising handler recipes without a real browser.

`FakePage` implements just the slice of the Playwright Page/Locator surface that
`harvest/handlers` touches: ``goto``, ``locator`` (with ``.first``, ``click``,
``wait_for``, ``count``, ``inner_text``, ``fill``), ``wait_for_url``, ``url``,
``content``, ``screenshot``, and ``evaluate``. It's deliberately simple and
configurable so a single recipe run can be steered down the happy path or a
specific failure branch.
"""

from __future__ import annotations

from harvest.selectors import CAPTCHA_IFRAME_SELECTORS

_CAPTCHA_SELECTORS = set(CAPTCHA_IFRAME_SELECTORS)


class FakeLocator:
    def __init__(self, page: FakePage, selector: str):
        self._page = page
        self._selector = selector

    @property
    def first(self) -> FakeLocator:
        return self

    async def wait_for(self, state: str = "visible", timeout: int = 0) -> None:
        if self._selector in _CAPTCHA_SELECTORS:
            # CAPTCHA frames are only ever probed via count(); never waited on.
            raise TimeoutError("no captcha")
        if self._page.fail_clicks:
            raise TimeoutError(f"not visible: {self._selector}")

    async def click(self, timeout: int = 0) -> None:
        if self._page.fail_clicks:
            raise TimeoutError(f"not clickable: {self._selector}")
        self._page.clicks.append(self._selector)

    async def count(self) -> int:
        if self._selector in _CAPTCHA_SELECTORS:
            return 1 if self._page.captcha else 0
        return 0

    async def inner_text(self, timeout: int = 0) -> str:
        if self._selector == "body":
            return self._page.body_text
        return ""

    async def fill(self, value: str, timeout: int = 0) -> None:
        self._page.filled.append((self._selector, value))


class FakePage:
    def __init__(
        self,
        *,
        url: str = "https://provider.example/signup",
        captcha: bool = False,
        body_text: str = "Welcome to the dashboard",
        key_value: str = "",
        fail_clicks: bool = False,
        signin_url: str | None = None,
    ):
        self.url = url
        self.captcha = captcha
        self.body_text = body_text
        self.key_value = key_value
        self.fail_clicks = fail_clicks
        # If set, the next goto() lands here (used to simulate a Google sign-in
        # redirect that triggers RequiresManualLogin).
        self._signin_url = signin_url
        # Observability for assertions.
        self.clicks: list[str] = []
        self.filled: list[tuple[str, str]] = []
        self.goto_urls: list[str] = []

    async def goto(self, url: str, wait_until: str = "load", timeout: int = 0) -> None:
        self.goto_urls.append(url)
        self.url = url

    def locator(self, selector: str) -> FakeLocator:
        return FakeLocator(self, selector)

    async def wait_for_url(self, predicate, timeout: int = 0) -> None:
        if self._signin_url is not None:
            self.url = self._signin_url

    async def content(self) -> str:
        return "<html><body>fake</body></html>"

    async def screenshot(self, path: str | None = None, full_page: bool = False) -> bytes:
        return b"\x89PNG-fake"

    async def evaluate(self, script: str, arg=None) -> str:
        # The only evaluate() call is the post-click key observer.
        return self.key_value

    async def close(self) -> None:
        pass
