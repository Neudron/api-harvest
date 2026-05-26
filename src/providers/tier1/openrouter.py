"""OpenRouter provider — email-only free tier."""

from src.providers.base import BaseProvider


class OpenRouterProvider(BaseProvider):
    name = "OpenRouter"
    env_var = "OPENROUTER_API_KEY"
    tier = "email"
    signup_url = "https://openrouter.ai"
    api_key_url = "https://openrouter.ai/settings/keys"
    free_models = [
        "DeepSeek V4 Flash:free",
        "GPT-OSS 120B:free",
        "Llama 3.3 70B:free",
        "Qwen3 Coder:free",
        "Gemma 4 26B:free",
        "29+ more :free models",
    ]
    credits = "Permanent free tier (free models only)"
    rate_limits = "20 RPM, 50 RPD (unfunded); 1,000 RPD with $10 lifetime topup"
    gotchas = "Only ':free' suffix models are free. 50 RPD unfunded is very restrictive."
