from __future__ import annotations

from datetime import datetime

from harvest.handlers import register
from harvest.handlers.base import Handler, HandlerError, RequiresManualLogin
from harvest.models import HarvestResult
from harvest.selectors import KEY_PATTERNS


@register("github-models")
class GithubModelsHandler(Handler):
    """GitHub Models uses a PAT with `models:read` scope. Bespoke flow."""

    key_pattern = KEY_PATTERNS["github-models"]

    async def run(self, page) -> HarvestResult:
        try:
            await self.step("opening github PAT page")
            await page.goto(
                "https://github.com/settings/tokens?type=beta",
                wait_until="domcontentloaded",
            )

            # If redirected to login, ask user to handle it
            if "/login" in page.url:
                choice = await self.interactive.pause_for_manual_takeover(
                    self.spec.name, "Sign in to GitHub in the browser, then press r."
                )
                if choice != "resume":
                    return self._skipped("user did not sign in")
                await page.goto(
                    "https://github.com/settings/tokens?type=beta",
                    wait_until="domcontentloaded",
                )

            # Click "Generate new token"
            await self.safe_click_candidates(
                page,
                ["Generate new token", "Generate a personal access token"],
                goal="click 'Generate new token'",
            )

            # Fill token name
            try:
                await page.locator("input[name='user_programmatic_access[name]']").fill(
                    f"api-harvest-models-{datetime.utcnow().strftime('%Y%m%d')}",
                    timeout=3_000,
                )
            except Exception:
                pass

            # Enable Models scope (fine-grained token)
            try:
                await page.get_by_label("Models", exact=False).first.check(timeout=3_000)
            except Exception:
                await self.log("models scope checkbox not found; user may need to enable manually")

            await self.interactive.pause_for_manual_takeover(
                self.spec.name,
                "Review the GitHub token form, choose 'Models' scope if needed, then click 'Generate token'. Press r when done.",
            )

            # Capture token from confirmation page
            for sel in (
                "input[readonly][value^='ghp_']",
                "input[readonly][value^='github_pat_']",
                "code:has-text('ghp_')",
                "code:has-text('github_pat_')",
            ):
                try:
                    loc = page.locator(sel).first
                    await loc.wait_for(state="visible", timeout=5_000)
                    try:
                        val = await loc.input_value(timeout=1_000)
                    except Exception:
                        val = await loc.text_content(timeout=1_000) or ""
                    m = self.key_pattern.search(val)
                    if m:
                        return HarvestResult(
                            provider_slug=self.spec.slug,
                            provider_name=self.spec.name,
                            tier=self.spec.tier,
                            status="done",
                            api_key=m.group(0),
                            env_var=self.spec.env_var,
                            created_at=datetime.utcnow().isoformat(),
                            dashboard_url=self.spec.api_key_url,
                            rate_limits=self.spec.rate_limits,
                        )
                except Exception:
                    continue

            raise HandlerError(goal="capture GitHub PAT")
        except RequiresManualLogin as e:
            return self._skipped(f"GitHub login required: {e}")
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
