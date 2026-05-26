"""Novita provider — email-only free tier."""

from src.providers.base import BaseProvider


class NovitaProvider(BaseProvider):
    name = "Novita"
    env_var = "NOVITA_API_KEY"
    tier = "email"
    signup_url = "https://novita.ai/"
    api_key_url = "https://novita.ai/"
    free_models = [
        "Various open models",
    ]
    credits = "$0.50 / 1 year"
    rate_limits = "Standard limits"
    gotchas = "Only $0.50 but lasts a year. Image/video generation focus."
