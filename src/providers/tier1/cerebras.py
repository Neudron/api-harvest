"""Cerebras provider — email-only free tier."""

from src.providers.base import BaseProvider


class CerebrasProvider(BaseProvider):
    name = "Cerebras"
    env_var = "CEREBRAS_API_KEY"
    tier = "email"
    signup_url = "https://cloud.cerebras.ai"
    api_key_url = "https://cloud.cerebras.ai"
    free_models = [
        "GPT-OSS 120B",
        "Llama 3.1 8B",
        "DeepSeek R1",
        "Qwen3",
        "GLM 4.7",
    ]
    credits = "Permanent free tier"
    rate_limits = "30 RPM, 60K tok/min, 14,400 RPD, 1M tok/day"
    gotchas = "Context capped at 8,192 tokens on free tier. Some models being deprecated May 27, 2026."
