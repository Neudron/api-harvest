"""Alibaba/Qwen (DashScope) provider — email-only free tier."""

from src.providers.base import BaseProvider


class AlibabaProvider(BaseProvider):
    name = "Alibaba/Qwen (DashScope)"
    env_var = "DASHSCOPE_API_KEY"
    tier = "email"
    signup_url = "https://www.alibabacloud.com/en/product/model-studio"
    api_key_url = "https://dashscope.console.aliyun.com/apiKey"
    free_models = [
        "qwen-max",
        "qwen-plus",
        "qwen-turbo",
        "qwen-vl",
        "qwen3-coder",
        "qwen3-next",
    ]
    credits = "~1M tokens per model (input+output), 90 days after activation"
    rate_limits = "Rate limits apply on free tier"
    gotchas = "Free tokens expire 90 days after activation. Alibaba Cloud account required."
