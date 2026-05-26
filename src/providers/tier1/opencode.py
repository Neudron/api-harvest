"""OpenCode Zen provider — email-only free tier."""

from src.providers.base import BaseProvider


class OpenCodeProvider(BaseProvider):
    name = "OpenCode Zen"
    env_var = "OPENCODE_API_KEY"
    tier = "email"
    signup_url = "https://opencode.ai/docs/zen/"
    api_key_url = "https://opencode.ai"
    free_models = [
        "Big Pickle Stealth",
        "MiniMax M2.5 Free",
        "Arcee Large Preview Free",
    ]
    credits = "Permanent free tier"
    rate_limits = "Not documented"
    gotchas = "Very limited model selection. Data may be used for model improvement."
