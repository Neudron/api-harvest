"""Google Gemini provider — email-only free tier."""

from src.providers.base import BaseProvider


class GeminiProvider(BaseProvider):
    name = "Google Gemini"
    env_var = "GOOGLE_GENERATIVE_AI_API_KEY"
    tier = "email"
    signup_url = "https://aistudio.google.com"
    api_key_url = "https://aistudio.google.com/apikey"
    free_models = [
        "Gemini 2.5 Flash",
        "Gemini 2.5 Flash-Lite",
        "Gemini 3 Flash",
        "Gemma 3 (1B/4B/12B/27B)",
    ]
    credits = "Permanent free tier (rate-limited)"
    rate_limits = "5-15 RPM, 250K tok/min, 20-500 RPD (Flash); 30 RPM, 14,400 RPD (Gemma)"
    gotchas = "Rate limits periodically reduced. Not available in EU. Data used for training outside UK/CH/EEA/EU."
