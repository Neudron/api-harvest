"""Hyperbolic provider — email-only free tier."""

from src.providers.base import BaseProvider


class HyperbolicProvider(BaseProvider):
    name = "Hyperbolic"
    env_var = "HYPERBOLIC_API_KEY"
    tier = "email"
    signup_url = "https://app.hyperbolic.ai/"
    api_key_url = "https://app.hyperbolic.ai/"
    free_models = [
        "DeepSeek V3 0324",
        "DeepSeek R1 0528",
        "Llama 3.3 70B Instruct",
        "Qwen3 Coder 480B",
    ]
    credits = "$1 trial credit"
    rate_limits = "Standard limits"
    gotchas = "Only $1. Claims to be the cheapest GPU marketplace."
