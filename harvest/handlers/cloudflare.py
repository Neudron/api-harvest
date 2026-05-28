from __future__ import annotations

from datetime import UTC, datetime

from harvest.handlers import register
from harvest.handlers.base import Handler, HandlerError
from harvest.models import HarvestResult
from harvest.selectors import KEY_PATTERNS


@register("cloudflare-workers-ai")
class CloudflareHandler(Handler):
    """Cloudflare requires creating a scoped token via the API tokens page."""

    key_pattern = KEY_PATTERNS["cloudflare-workers-ai"]

    async def run(self, page) -> HarvestResult:
        try:
            await self.step("opening Cloudflare API tokens")
            await page.goto(
                "https://dash.cloudflare.com/profile/api-tokens",
                wait_until="domcontentloaded",
            )

            if "login" in page.url or "sign" in page.url:
                choice = await self.interactive.pause_for_manual_takeover(
                    self.spec.name,
                    "Sign in / sign up to Cloudflare in the browser. Press r when on the API Tokens page.",
                )
                if choice != "resume":
                    return self._skipped("Cloudflare login required")

            await self.safe_click_candidates(
                page, ["Create Token", "Create Custom Token"], goal="click 'Create Token'"
            )

            await self.interactive.pause_for_manual_takeover(
                self.spec.name,
                "In Cloudflare's Token creation UI, pick 'Workers AI' template and confirm. Press r when the token value is shown.",
            )

            # Try to find the generated token on screen
            for sel in (
                "input[readonly]",
                "code",
                "[data-testid*='token' i]",
            ):
                try:
                    loc = page.locator(sel).first
                    await loc.wait_for(state="visible", timeout=3_000)
                    try:
                        val = await loc.input_value(timeout=1_000)
                    except Exception:
                        val = await loc.text_content(timeout=1_000) or ""
                    if val and len(val.strip()) >= 30:
                        return HarvestResult(
                            provider_slug=self.spec.slug,
                            provider_name=self.spec.name,
                            tier=self.spec.tier,
                            status="done",
                            api_key=val.strip(),
                            env_var=self.spec.env_var,
                            created_at=datetime.now(UTC).isoformat(),
                            dashboard_url=self.spec.api_key_url,
                            rate_limits=self.spec.rate_limits,
                        )
                except Exception:
                    continue

            raise HandlerError(goal="capture Cloudflare token")
        except HandlerError as e:
            return HarvestResult(
                provider_slug=self.spec.slug,
                provider_name=self.spec.name,
                tier=self.spec.tier,
                status="failed",
                env_var=self.spec.env_var,
                dashboard_url=self.spec.api_key_url,
                rate_limits=self.spec.rate_limits,
                error=e.goal,
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
