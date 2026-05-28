from __future__ import annotations

from harvest.handlers import register
from harvest.handlers.base import Handler
from harvest.models import HarvestResult


@register("azure-openai")
class AzureOpenAiHandler(Handler):
    """Azure OpenAI requires manual access approval (1+ business days). Auto-skip."""

    async def run(self, page) -> HarvestResult:
        await self.step("auto-skip (manual approval required)")
        return HarvestResult(
            provider_slug=self.spec.slug,
            provider_name=self.spec.name,
            tier=self.spec.tier,
            status="skipped",
            env_var=self.spec.env_var,
            dashboard_url=self.spec.api_key_url,
            rate_limits=self.spec.rate_limits,
            user_skipped=True,
            notes="Azure OpenAI requires manual access approval, 1+ business days",
        )
