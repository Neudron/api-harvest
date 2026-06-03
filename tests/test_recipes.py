"""Handler recipe smoke tests driven by FakePage (offline, no browser).

Covers GoogleSsoCreateKeyRecipe.run() down its main branches: a captured key
('done'), a missing key / unclickable create button ('failed'), CAPTCHA and
Google sign-in detection routed to interactive takeover.
"""

from __future__ import annotations

import re

import pytest

from harvest.events import EventBus
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.models import ProviderSpec
from tests.fakes import FakePage


def _spec(slug: str = "groq", *, requires_phone: bool = False, requires_cc: bool = False) -> ProviderSpec:
    return ProviderSpec(
        slug=slug,
        name=slug.title(),
        tier=1,
        order_index=1,
        signup_url="https://provider.example/signup",
        api_key_url="https://provider.example/keys",
        env_var=f"{slug.upper()}_API_KEY",
        requires_cc=requires_cc,
        requires_phone=requires_phone,
        rate_limits="generous",
        free_models=["m1"],
        gotchas="",
        raw_section="",
    )


class _FakeInteractive:
    """Records takeover prompts and returns a scripted choice."""

    def __init__(self, choice: str = "skip"):
        self.choice = choice
        self.takeover_calls: list[str] = []

    async def pause_for_manual_takeover(self, provider_name: str, message: str) -> str:
        self.takeover_calls.append(message)
        return self.choice

    async def ask_sms_code(self, provider_name: str, phone_hint=None) -> str:
        return ""


def _make_recipe(spec, page, interactive=None):
    bus = EventBus()  # no subscribers → emit() is a no-op
    recipe = GoogleSsoCreateKeyRecipe(
        spec=spec,
        ai=None,
        interactive=interactive or _FakeInteractive(),
        bus=bus,
    )
    # Anchor a key pattern so capture is deterministic.
    recipe.key_pattern = re.compile(r"gsk_[A-Za-z0-9]{20,}")
    return recipe


@pytest.mark.asyncio
async def test_run_done_on_captured_key() -> None:
    key = "gsk_" + "a" * 30
    page = FakePage(key_value=key)
    recipe = _make_recipe(_spec(), page)

    result = await recipe.run(page)

    assert result.status == "done"
    assert result.api_key == key
    assert result.env_var == "GROQ_API_KEY"
    assert result.created_at is not None
    # It navigated to signup and then the keys page.
    assert page.goto_urls[0] == "https://provider.example/signup"
    assert "https://provider.example/keys" in page.goto_urls


@pytest.mark.asyncio
async def test_run_failed_when_no_key_captured() -> None:
    # evaluate() returns "" → no key → HandlerError → status failed.
    page = FakePage(key_value="")
    recipe = _make_recipe(_spec(), page)

    result = await recipe.run(page)

    assert result.status == "failed"
    assert result.api_key is None
    assert "capture generated API key" in (result.error or "")


@pytest.mark.asyncio
async def test_run_failed_when_create_button_unclickable() -> None:
    # fail_clicks makes every click/wait_for raise; with ai=None there's no
    # rescue, so safe_click_candidates raises HandlerError → status failed.
    page = FakePage(key_value="gsk_" + "b" * 30, fail_clicks=True)
    recipe = _make_recipe(_spec(), page)

    result = await recipe.run(page)

    assert result.status == "failed"


@pytest.mark.asyncio
async def test_captcha_routes_to_takeover_and_skips_when_declined() -> None:
    page = FakePage(captcha=True, key_value="gsk_" + "c" * 30)
    interactive = _FakeInteractive(choice="skip")
    recipe = _make_recipe(_spec(), page, interactive)

    result = await recipe.run(page)

    assert result.status == "skipped"
    assert result.user_skipped is True
    assert interactive.takeover_calls, "should have prompted for CAPTCHA takeover"
    assert "captcha" in (result.notes or "").lower()


@pytest.mark.asyncio
async def test_google_signin_routes_to_manual_login_skip() -> None:
    # wait_for_url lands on a Google sign-in challenge URL →
    # check_google_signin_redirect raises RequiresManualLogin.
    page = FakePage(
        signin_url="https://accounts.google.com/v3/signin/challenge/pwd",
        key_value="gsk_" + "d" * 30,
    )
    interactive = _FakeInteractive(choice="skip")
    recipe = _make_recipe(_spec(), page, interactive)

    result = await recipe.run(page)

    assert result.status == "skipped"
    assert interactive.takeover_calls, "should have prompted for manual login"
