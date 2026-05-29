"""Inference.net provider — email-only free tier."""

from src.providers.base import BaseProvider


class InferenceNetProvider(BaseProvider):
    name = "Inference.net"
    env_var = "INFERENCE_NET_API_KEY"
    tier = "email"
    signup_url = "https://inference.net"
    api_key_url = "https://inference.net"
    free_models = [
        "Various open models",
    ]
    credits = "$1 trial (+$25 extra if you respond to their email survey)"
    rate_limits = "Standard limits"
    gotchas = "Respond to their email survey for $25 bonus credits."
