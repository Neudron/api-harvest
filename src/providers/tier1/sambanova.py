"""SambaNova Cloud provider — email-only free tier."""

from src.providers.base import BaseProvider


class SambanovaProvider(BaseProvider):
    name = "SambaNova Cloud"
    env_var = "SAMBANOVA_API_KEY"
    tier = "email"
    signup_url = "https://cloud.sambanova.ai/"
    api_key_url = "https://cloud.sambanova.ai/apis"
    free_models = [
        "Llama 3.3 70B",
        "Llama 4 Maverick 17B",
        "DeepSeek V3.1",
        "Gemma 3 12B",
        "GPT-OSS 120B",
    ]
    credits = "$5 / 3 months (+$5 extra if signed up for newsletter)"
    rate_limits = "Standard developer tier limits"
    gotchas = "Extra $5 if you subscribe to newsletter. Up to 25 API keys."
