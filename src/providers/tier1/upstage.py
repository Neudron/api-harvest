"""Upstage provider — email-only free tier."""

from src.providers.base import BaseProvider


class UpstageProvider(BaseProvider):
    name = "Upstage"
    env_var = "UPSTAGE_API_KEY"
    tier = "email"
    signup_url = "https://console.upstage.ai/"
    api_key_url = "https://console.upstage.ai/"
    free_models = [
        "Solar Pro",
        "Solar Mini",
    ]
    credits = "$10 / 3 months"
    rate_limits = "Standard limits"
    gotchas = "Only Solar models. Korean-focused provider."
