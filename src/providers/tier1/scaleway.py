"""Scaleway Generative APIs provider — email-only free tier."""

from src.providers.base import BaseProvider


class ScalewayProvider(BaseProvider):
    name = "Scaleway Generative APIs"
    env_var = "SCALEWAY_API_KEY"
    tier = "email"
    signup_url = "https://console.scaleway.com/generative-api/models"
    api_key_url = "https://console.scaleway.com/"
    free_models = [
        "Llama 3.3 70B",
        "Gemma 3 27B",
        "Qwen3 variants (235B, Coder, 3.6 35B)",
        "Mistral Small 3.2",
        "GPT-OSS 120B",
        "DeepSeek R1",
        "Kimi K2.5/K2.6",
    ]
    credits = "1,000,000 free tokens (no expiration)"
    rate_limits = "Standard limits"
    gotchas = "EU-based provider (Paris). Good model selection."
