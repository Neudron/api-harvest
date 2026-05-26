"""Groq provider — email-only free tier."""

from src.providers.base import BaseProvider


class GroqProvider(BaseProvider):
    name = "Groq"
    env_var = "GROQ_API_KEY"
    tier = "email"
    signup_url = "https://console.groq.com"
    api_key_url = "https://console.groq.com/keys"
    free_models = [
        "Llama 3.1 8B (14,400 RPD)",
        "Llama 3.3 70B (1,000 RPD)",
        "Llama 4 Scout (1,000 RPD)",
        "Qwen3 32B (1,000 RPD)",
    ]
    credits = "Permanent free tier"
    rate_limits = "30 RPM, 6K-70K tok/min, 1,000-14,400 RPD"
    gotchas = "Rate limits vary per model. No batch API on free tier."
