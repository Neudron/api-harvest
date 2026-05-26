"""Cohere provider — email-only free tier."""

from src.providers.base import BaseProvider


class CohereProvider(BaseProvider):
    name = "Cohere"
    env_var = "COHERE_API_KEY"
    tier = "email"
    signup_url = "https://dashboard.cohere.com/welcome/register"
    api_key_url = "https://dashboard.cohere.com"
    free_models = [
        "Command A",
        "Command R+",
        "Command R",
        "Aya Expanse 32B",
        "Rerank",
        "Embed",
    ]
    credits = "Permanent free tier (Trial key)"
    rate_limits = "20 RPM, 1,000 requests/month (all models combined)"
    gotchas = "Only 1,000 API calls/month TOTAL. Trial keys not for production/commercial use."
