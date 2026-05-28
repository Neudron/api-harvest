from __future__ import annotations

from datetime import datetime

from harvest.handlers.base import (
    CaptchaDetected,
    Handler,
    HandlerError,
    RequiresManualLogin,
)
from harvest.models import HarvestResult
from harvest.selectors import (
    CONSENT_BUTTON_CANDIDATES,
    CREATE_KEY_CANDIDATES,
    SSO_BUTTON_CANDIDATES,
)


class GoogleSsoCreateKeyRecipe(Handler):
    """Most common shape: signup page → 'Continue with Google' → keys page → 'Create key'."""

    sso_button_candidates: list[str] = SSO_BUTTON_CANDIDATES
    consent_button_candidates: list[str] = CONSENT_BUTTON_CANDIDATES
    create_button_candidates: list[str] = CREATE_KEY_CANDIDATES
    consent_required: bool = False
    landing_wait_url_substring: str | None = None  # e.g. "console.groq.com"

    async def _do_sso(self, page) -> None:
        await self.step("opening signup")
        await page.goto(self.spec.signup_url, wait_until="domcontentloaded")

        # Try to click Continue with Google. If it's not on the page, assume we're
        # already logged in (the persistent profile / CDP session).
        try:
            await self.safe_click_candidates(
                page, self.sso_button_candidates, goal="click 'Continue with Google'"
            )
            await self.step("waiting for Google SSO redirect")
            # Wait for either Google sign-in or a redirect back to the provider.
            try:
                await page.wait_for_url(
                    lambda url: "accounts.google.com" not in url
                    or "/oauth/" in url
                    or self.landing_wait_url_substring is not None
                    and self.landing_wait_url_substring in url,
                    timeout=30_000,
                )
            except Exception:
                pass
        except HandlerError:
            # Already signed in or no SSO button on this page
            await self.log("no Google SSO button found; assuming already signed in")

        await self.check_google_signin_redirect(page)
        await self.check_captcha(page)

        if self.consent_required:
            await self._dismiss_consent(page)

    async def _dismiss_consent(self, page) -> None:
        for label in self.consent_button_candidates:
            try:
                loc = page.locator(f"role=button[name=/{label}/i]").first
                await loc.wait_for(state="visible", timeout=1_500)
                await loc.click(timeout=2_000)
                await self.log(f"dismissed consent: {label}")
                return
            except Exception:
                continue

    async def _go_to_keys_page(self, page) -> None:
        if not self.spec.api_key_url or self.spec.api_key_url == self.spec.signup_url:
            return
        await self.step("navigating to keys page")
        await page.goto(self.spec.api_key_url, wait_until="domcontentloaded")

    async def _create_and_capture(self, page) -> str:
        await self.step("creating API key")

        async def click_create():
            await self.safe_click_candidates(
                page, self.create_button_candidates, goal="click 'Create key'"
            )
            # Some providers show a confirm dialog
            for label in ("Create", "Generate", "Confirm", "Yes"):
                try:
                    btn = page.locator(f"role=button[name=/^{label}$/i]").first
                    await btn.click(timeout=1_500)
                    break
                except Exception:
                    continue

        key = await self.capture_key_after_click(page, click_action=click_create, timeout_ms=15_000)
        return key

    async def run(self, page) -> HarvestResult:
        try:
            await self._do_sso(page)
            if self.spec.requires_phone:
                # Provider-side flow will surface an SMS input; the orchestrator's
                # interactive layer is consulted via self.interactive.
                code = await self.interactive.ask_sms_code(self.spec.name)
                # Best-effort: type into a visible code input
                for sel in (
                    'input[name*="code" i]',
                    'input[autocomplete="one-time-code"]',
                    'input[type="tel"][maxlength="6"]',
                    'input[placeholder*="code" i]',
                ):
                    try:
                        await page.locator(sel).first.fill(code, timeout=2_000)
                        for label in ("Verify", "Submit", "Confirm", "Continue"):
                            try:
                                await page.locator(f"role=button[name=/{label}/i]").first.click(timeout=2_000)
                                break
                            except Exception:
                                continue
                        break
                    except Exception:
                        continue

            await self._go_to_keys_page(page)
            key = await self._create_and_capture(page)

            if not key:
                raise HandlerError(goal="capture generated API key")

            return HarvestResult(
                provider_slug=self.spec.slug,
                provider_name=self.spec.name,
                tier=self.spec.tier,
                status="done",
                api_key=key,
                env_var=self.spec.env_var,
                created_at=datetime.utcnow().isoformat(),
                dashboard_url=self.spec.api_key_url,
                rate_limits=self.spec.rate_limits,
            )

        except RequiresManualLogin as e:
            choice = await self.interactive.pause_for_manual_takeover(
                self.spec.name, f"Sign in to Google manually in the browser. {e}"
            )
            if choice == "resume":
                # Re-run once after manual login
                return await self.run(page)
            return self._skipped("manual login required and user " + ("aborted" if choice == "abort" else "skipped"))
        except CaptchaDetected as e:
            choice = await self.interactive.pause_for_manual_takeover(
                self.spec.name, f"Solve the CAPTCHA in the browser. ({e})"
            )
            if choice == "resume":
                return await self.run(page)
            return self._skipped(f"captcha: {e}")
        except HandlerError as e:
            return HarvestResult(
                provider_slug=self.spec.slug,
                provider_name=self.spec.name,
                tier=self.spec.tier,
                status="failed",
                env_var=self.spec.env_var,
                dashboard_url=self.spec.api_key_url,
                rate_limits=self.spec.rate_limits,
                error=f"{e.goal}: {e.last_selector or ''}",
                screenshot_path=e.screenshot_path,
                html_path=e.html_path,
            )

    def _skipped(self, reason: str) -> HarvestResult:
        return HarvestResult(
            provider_slug=self.spec.slug,
            provider_name=self.spec.name,
            tier=self.spec.tier,
            status="skipped",
            env_var=self.spec.env_var,
            dashboard_url=self.spec.api_key_url,
            rate_limits=self.spec.rate_limits,
            user_skipped=True,
            notes=reason,
        )


class EmailSignupRecipe(GoogleSsoCreateKeyRecipe):
    """Provider that prefers email signup but still has Google SSO; reuses parent flow.
    Useful for providers like Cloudflare/HF where the SSO button is partly hidden."""

    pass


class CloudConsoleRecipe(Handler):
    """AWS / GCP / Azure — these need a credit card and a complex IAM flow.
    We pause for the user, guide them, then capture whatever credentials they
    paste back into the CLI."""

    cc_pause_reason: str = "This provider requires a credit card during signup."
    manual_capture_message: str = (
        "Once you have created the API credential in the console, paste the key value here."
    )

    async def run(self, page) -> HarvestResult:
        # 1. CC pause
        choice = await self.interactive.pause_for_cc(self.spec.name, self.cc_pause_reason)
        if choice == "skip":
            return HarvestResult(
                provider_slug=self.spec.slug,
                provider_name=self.spec.name,
                tier=self.spec.tier,
                status="skipped",
                env_var=self.spec.env_var,
                dashboard_url=self.spec.api_key_url,
                rate_limits=self.spec.rate_limits,
                user_skipped=True,
                notes="CC required; user declined",
            )

        # 2. Open the credentials page
        await self.step("opening credentials console")
        try:
            await page.goto(self.spec.api_key_url, wait_until="domcontentloaded")
        except Exception:
            pass

        # 3. Hand off to the user to capture the key.
        await self.interactive.pause_for_manual_takeover(
            self.spec.name, self.manual_capture_message
        )

        # 4. Prompt for the captured key value
        from harvest.interactive import _async_prompt  # type: ignore

        await self.interactive._pause()  # type: ignore
        try:
            key = (await _async_prompt(f"Paste {self.spec.name} key (blank to skip)> ")).strip()
        finally:
            await self.interactive._resume()  # type: ignore

        if not key:
            return self._skipped("no key entered")

        return HarvestResult(
            provider_slug=self.spec.slug,
            provider_name=self.spec.name,
            tier=self.spec.tier,
            status="done",
            api_key=key,
            env_var=self.spec.env_var,
            created_at=datetime.utcnow().isoformat(),
            dashboard_url=self.spec.api_key_url,
            rate_limits=self.spec.rate_limits,
            notes="manually captured",
        )

    def _skipped(self, reason: str) -> HarvestResult:
        return HarvestResult(
            provider_slug=self.spec.slug,
            provider_name=self.spec.name,
            tier=self.spec.tier,
            status="skipped",
            env_var=self.spec.env_var,
            dashboard_url=self.spec.api_key_url,
            rate_limits=self.spec.rate_limits,
            user_skipped=True,
            notes=reason,
        )
