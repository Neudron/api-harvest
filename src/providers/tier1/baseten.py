"""Baseten provider — email-only free tier."""

from src.providers.base import BaseProvider


class BasetenProvider(BaseProvider):
    name = "Baseten"
    env_var = "BASETEN_API_KEY"
    tier = "email"
    signup_url = "https://app.baseten.co/"
    api_key_url = "https://app.baseten.co/"
    free_models = [
        "Any supported model — pay by compute time",
    ]
    credits = "$30 trial credits"
    rate_limits = "Pay by compute time, not tokens"
    gotchas = "Model library at baseten.co/library. Good for custom deployments."
