"""AI21 provider — email-only free tier."""

from src.providers.base import BaseProvider


class AI21Provider(BaseProvider):
    name = "AI21"
    env_var = "AI21_API_KEY"
    tier = "email"
    signup_url = "https://studio.ai21.com/"
    api_key_url = "https://studio.ai21.com/"
    free_models = [
        "Jamba 1.5 Large",
        "Jamba 1.5 Mini",
        "Jamba Instruct",
    ]
    credits = "$10 / 3 months"
    rate_limits = "Standard limits"
    gotchas = "Only Jamba family models. Niche provider."
