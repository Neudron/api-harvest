"""Anthropic provider — email-only free tier."""

from src.providers.base import BaseProvider


class AnthropicProvider(BaseProvider):
    name = "Anthropic"
    env_var = "ANTHROPIC_API_KEY"
    tier = "email"
    signup_url = "https://console.anthropic.com/"
    api_key_url = "https://console.anthropic.com/"
    free_models = [
        "Claude 4 Sonnet",
        "Claude 4 Opus",
        "Claude Haiku 4.5",
        "Claude 3.5 Sonnet",
    ]
    credits = "~$5 one-time credits (no expiration)"
    rate_limits = "Standard API rate limits"
    gotchas = "Some users don't receive credits automatically — may need to contact support."
