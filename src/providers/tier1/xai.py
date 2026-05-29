"""xAI / Grok provider — email-only free tier."""

from src.providers.base import BaseProvider


class XAIProvider(BaseProvider):
    name = "xAI / Grok"
    env_var = "XAI_API_KEY"
    tier = "email"
    signup_url = "https://console.x.ai/"
    api_key_url = "https://console.x.ai/"
    free_models = [
        "Grok 3",
        "Grok 3 Mini",
        "Grok 2",
    ]
    credits = "$25/month recurring (resets each month)"
    rate_limits = "Varies by model"
    gotchas = "Best recurring credit deal. No CC needed — email signup only."
