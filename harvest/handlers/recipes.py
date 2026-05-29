from __future__ import annotations

from datetime import UTC, datetime

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
        await self._handle_email_verification_if_present(page)

        if self.consent_required:
            await self._dismiss_consent(page)

    _EMAIL_VERIFY_HINTS = (
        "verify your email",
        "check your inbox",
        "we sent you a verification",
        "confirm your email",
        "email confirmation required",
    )

    async def _handle_email_verification_if_present(self, page) -> None:
        """If the post-SSO page says 'verify your email', pause for the user
        to click the link in their inbox. We don't read email; user just
        clicks through and presses r to continue."""
        try:
            body_text = (await page.locator("body").inner_text(timeout=2_000)).lower()
        except Exception:
            return
        if not any(h in body_text for h in self._EMAIL_VERIFY_HINTS):
            return
        await self.log("email verification screen detected")
        choice = await self.interactive.pause_for_manual_takeover(
            self.spec.name,
            "Click the verification link in your email, then come back here.",
        )
        if choice != "resume":
            raise HandlerError(goal="email verification (user did not confirm)")

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

    _SMS_INPUT_SELECTORS = (
        'input[name*="code" i]',
        'input[autocomplete="one-time-code"]',
        'input[type="tel"][maxlength="6"]',
        'input[placeholder*="code" i]',
        'input[aria-label*="code" i]',
    )

    async def _handle_sms_if_present(self, page) -> None:
        """Wait for an SMS input element to be visible, THEN prompt the user.
        If no input appears within the window, the provider probably did not
        ask for SMS this signup (e.g., the account already has a verified
        phone) and we skip the prompt entirely."""
        await self.step("waiting for SMS input to appear (up to 60s)")
        sms_input = None
        for sel in self._SMS_INPUT_SELECTORS:
            try:
                loc = page.locator(sel).first
                await loc.wait_for(state="visible", timeout=60_000)
                sms_input = loc
                break
            except Exception:
                continue
        if sms_input is None:
            await self.log("no SMS input detected; phone step skipped")
            return

        code = await self.interactive.ask_sms_code(self.spec.name)
        if not code:
            await self.log("empty SMS code entered; phone step skipped")
            return
        try:
            await sms_input.fill(code, timeout=3_000)
        except Exception as e:
            await self.log(f"could not fill SMS code: {e}")
            return
        for label in ("Verify", "Submit", "Confirm", "Continue"):
            try:
                await page.locator(f"role=button[name=/{label}/i]").first.click(timeout=2_000)
                return
            except Exception:
                continue

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
                await self._handle_sms_if_present(page)

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
                created_at=datetime.now(UTC).isoformat(),
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
    """AWS, GCP, and Azure need a credit card and a multi-step IAM flow.
    We pause for the user, guide them, then capture whatever credentials they
    paste back into the CLI."""

    cc_pause_reason: str = "This provider requires a credit card during signup."
    manual_capture_message: str = (
        "Once you have created the API credential in the console, paste the key value here."
    )

    async def run(self, page) -> HarvestResult:
        # CC pause is handled upfront by the orchestrator (spec.requires_cc=True).
        # If we got here the user already accepted; no need to prompt again.
        await self.step("opening credentials console")
        try:
            await page.goto(self.spec.api_key_url, wait_until="domcontentloaded")
        except Exception:
            pass

        # Hand off to the user to navigate to the create-credential page.
        await self.interactive.pause_for_manual_takeover(
            self.spec.name, self.manual_capture_message
        )

        # Prompt for the captured key value via the public InteractiveManager API.
        key = (await self.interactive.prompt_value(
            f"Paste {self.spec.name} key (blank to skip)"
        )).strip()

        if not key:
            return self._skipped("no key entered")

        return HarvestResult(
            provider_slug=self.spec.slug,
            provider_name=self.spec.name,
            tier=self.spec.tier,
            status="done",
            api_key=key,
            env_var=self.spec.env_var,
            created_at=datetime.now(UTC).isoformat(),
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
