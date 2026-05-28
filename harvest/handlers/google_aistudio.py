from __future__ import annotations

import re
from datetime import datetime

from harvest.handlers import register
from harvest.handlers.base import Handler, HandlerError, RequiresManualLogin
from harvest.models import HarvestResult


@register("google-gemini-ai-studio")
class GoogleAiStudioHandler(Handler):
    """Runs FIRST. No AI rescue (we haven't bootstrapped Gemini yet)."""

    key_pattern = re.compile(r"AIza[0-9A-Za-z_-]{35,}")

    async def run(self, page) -> HarvestResult:
        try:
            await self.step("opening AI Studio")
            await page.goto("https://aistudio.google.com/apikey", wait_until="domcontentloaded")
            await self.check_google_signin_redirect(page)

            # Accept terms checkbox if shown
            for label in ("I accept", "I agree", "Accept"):
                try:
                    await page.locator(f"role=checkbox[name=/{label}/i]").first.check(timeout=1_500)
                    break
                except Exception:
                    continue

            # Click "Create API key" / "Get API key"
            await self.step("clicking Create API key")
            for label in (
                "Create API key",
                "Get API key",
                "Create API Key",
                "Create new key",
                "+ Create API key",
            ):
                try:
                    btn = page.locator(f"role=button[name=/{label}/i]").first
                    await btn.wait_for(state="visible", timeout=3_000)
                    await btn.click(timeout=3_000)
                    break
                except Exception:
                    continue

            # In some flows a project-picker modal shows next
            for label in ("Create API key in new project", "Create in new project", "Create"):
                try:
                    btn = page.locator(f"role=button[name=/{label}/i]").first
                    await btn.wait_for(state="visible", timeout=3_000)
                    await btn.click(timeout=3_000)
                    break
                except Exception:
                    continue

            # Capture the key
            await self.step("waiting for generated key")
            key = ""
            for sel in (
                'input[readonly][value^="AIza"]',
                "code:has-text('AIza')",
                "pre:has-text('AIza')",
                "[data-testid*='api-key' i]",
            ):
                try:
                    loc = page.locator(sel).first
                    await loc.wait_for(state="visible", timeout=10_000)
                    try:
                        val = await loc.input_value(timeout=1_000)
                    except Exception:
                        val = await loc.text_content(timeout=1_000) or ""
                    if val:
                        m = self.key_pattern.search(val)
                        if m:
                            key = m.group(0)
                            break
                except Exception:
                    continue

            if not key:
                # Fall back to scanning the page text
                html = await page.content()
                m = self.key_pattern.search(html)
                if m:
                    key = m.group(0)

            if not key:
                shot = await self.screenshot(page, "ai-studio-no-key")
                _, html_path = await self.capture_dom(page)
                raise HandlerError(
                    goal="capture Gemini API key",
                    screenshot_path=str(shot),
                    html_path=str(html_path),
                )

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
                self.spec.name, f"Sign in to Google manually. {e}"
            )
            if choice == "resume":
                return await self.run(page)
            return HarvestResult(
                provider_slug=self.spec.slug,
                provider_name=self.spec.name,
                tier=self.spec.tier,
                status="skipped",
                env_var=self.spec.env_var,
                dashboard_url=self.spec.api_key_url,
                rate_limits=self.spec.rate_limits,
                user_skipped=True,
                notes="Google login required",
            )
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
