"""HuggingFace provider — email-only free tier."""

from src.providers.base import BaseProvider


class HuggingFaceProvider(BaseProvider):
    name = "HuggingFace"
    env_var = "HF_TOKEN"
    tier = "email"
    signup_url = "https://huggingface.co/join"
    api_key_url = "https://huggingface.co/settings/tokens"
    free_models = [
        "Various open models under 10GB via Inference API",
    ]
    credits = "$0.10/month in credits"
    rate_limits = "$0.10/month credit cap"
    gotchas = "Very modest credits. Models must be under 10GB for serverless inference."
