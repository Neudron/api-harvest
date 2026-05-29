"""Cloudflare Workers AI provider — email-only free tier."""

from src.providers.base import BaseProvider


class CloudflareProvider(BaseProvider):
    name = "Cloudflare Workers AI"
    env_var = "CLOUDFLARE_API_TOKEN"
    tier = "email"
    signup_url = "https://dash.cloudflare.com/sign-up"
    api_key_url = "https://dash.cloudflare.com"
    free_models = [
        "Llama 3.3 70B (FP8)",
        "Llama 4 Scout",
        "Gemma 3 12B",
        "Qwen QwQ 32B",
        "GPT-OSS 120B",
        "Kimi K2.5/K2.6",
        "Mistral Small 3.1 24B",
        "DeepSeek R1 Distill Qwen 32B",
    ]
    credits = "Permanent free tier"
    rate_limits = "10,000 neurons/day"
    gotchas = "Neuron-based pricing — larger models consume more neurons. 10K/day may not go far."
    google_oauth = True
