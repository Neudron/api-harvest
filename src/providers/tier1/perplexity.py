"""Perplexity provider — email-only free tier."""

from src.providers.base import BaseProvider


class PerplexityProvider(BaseProvider):
    name = "Perplexity"
    env_var = "PERPLEXITY_API_KEY"
    tier = "email"
    signup_url = "https://www.perplexity.ai/settings/api"
    api_key_url = "https://www.perplexity.ai/settings/api"
    free_models = [
        "Sonar",
        "Sonar Pro",
        "Sonar Deep Research",
    ]
    credits = "$25-50 (inconsistent — some users get $0)"
    rate_limits = "Standard API limits"
    gotchas = "Credits are inconsistent — some accounts get $0. Free Perplexity accounts cannot access API without credits."
