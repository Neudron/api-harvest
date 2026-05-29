"""Nebius provider — email-only free tier."""

from src.providers.base import BaseProvider


class NebiusProvider(BaseProvider):
    name = "Nebius"
    env_var = "NEBIUS_API_KEY"
    tier = "email"
    signup_url = "https://tokenfactory.nebius.com/"
    api_key_url = "https://tokenfactory.nebius.com/"
    free_models = [
        "Various open models",
    ]
    credits = "$1 trial credit"
    rate_limits = "Competitive inference pricing"
    gotchas = "Only $1. Good for EU-based users."
