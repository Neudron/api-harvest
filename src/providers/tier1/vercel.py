"""Vercel AI Gateway provider — email-only free tier."""

from src.providers.base import BaseProvider


class VercelProvider(BaseProvider):
    name = "Vercel AI Gateway"
    env_var = "VERCEL_AI_GATEWAY_KEY"
    tier = "email"
    signup_url = "https://vercel.com/signup"
    api_key_url = "https://vercel.com/dashboard/~/ai-gateway"
    free_models = [
        "Multi-provider: OpenAI, Anthropic, Google, Meta via one key",
    ]
    credits = "$5/month recurring credits (resets monthly)"
    rate_limits = "$5/month credit cap"
    gotchas = "Some users report credits disappear after adding payment method. ZDR costs extra."
    google_oauth = True
