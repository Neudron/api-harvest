"""Fireworks AI provider — email-only free tier."""

from src.providers.base import BaseProvider


class FireworksProvider(BaseProvider):
    name = "Fireworks AI"
    env_var = "FIREWORKS_API_KEY"
    tier = "email"
    signup_url = "https://fireworks.ai/"
    api_key_url = "https://fireworks.ai/api-keys"
    free_models = [
        "Various open models: Llama, Qwen, Mixtral",
    ]
    credits = "$1 trial credit"
    rate_limits = "Standard limits"
    gotchas = "Only $1 in credits — very limited."
