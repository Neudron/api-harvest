from __future__ import annotations

import re

SSO_BUTTON_CANDIDATES: list[str] = [
    "Continue with Google",
    "Sign in with Google",
    "Sign up with Google",
    "Log in with Google",
    "Connect with Google",
    "Continue using Google",
    "Google",
]

CREATE_KEY_CANDIDATES: list[str] = [
    "Create API Key",
    "Create API key",
    "Create key",
    "Create new key",
    "+ Create API Key",
    "Generate key",
    "Generate API Key",
    "New key",
    "New API Key",
    "Add key",
]

CONSENT_BUTTON_CANDIDATES: list[str] = [
    "Accept",
    "I agree",
    "Agree",
    "Accept all",
    "Allow",
    "Continue",
    "Get started",
    "I accept",
]

CAPTCHA_IFRAME_SELECTORS: list[str] = [
    'iframe[src*="hcaptcha"]',
    'iframe[src*="recaptcha"]',
    'iframe[src*="turnstile"]',
    'iframe[src*="cloudflare"][src*="challenge"]',
]

KEY_PATTERNS: dict[str, re.Pattern] = {
    "google-gemini-ai-studio": re.compile(r"AIza[0-9A-Za-z_-]{35,}"),
    "groq": re.compile(r"gsk_[A-Za-z0-9]{40,}"),
    "cerebras": re.compile(r"csk-[A-Za-z0-9-]{20,}"),
    "mistral-la-plateforme": re.compile(r"[A-Za-z0-9]{32,}"),
    "mistral-codestral-separate-endpoint": re.compile(r"[A-Za-z0-9]{32,}"),
    "openrouter": re.compile(r"sk-or-[A-Za-z0-9_-]{20,}"),
    "cohere": re.compile(r"[A-Za-z0-9]{40,}"),
    "vercel-ai-gateway": re.compile(r"[A-Za-z0-9_-]{20,}"),
    "nvidia-nim": re.compile(r"nvapi-[A-Za-z0-9_-]{20,}"),
    "github-models": re.compile(r"(ghp_|github_pat_)[A-Za-z0-9_]{30,}"),
    "cloudflare-workers-ai": re.compile(r"[A-Za-z0-9_-]{30,}"),
    "huggingface-inference-providers": re.compile(r"hf_[A-Za-z0-9]{30,}"),
    "opencode-zen": re.compile(r"[A-Za-z0-9_-]{20,}"),
    "xai-grok": re.compile(r"xai-[A-Za-z0-9]{30,}"),
    "alibaba-qwen-dashscope": re.compile(r"sk-[A-Za-z0-9]{20,}"),
    "anthropic": re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    "sambanova-cloud": re.compile(r"[A-Za-z0-9_-]{20,}"),
    "perplexity": re.compile(r"pplx-[A-Za-z0-9]{20,}"),
    "fireworks-ai": re.compile(r"[A-Za-z0-9]{20,}"),
    "baseten": re.compile(r"[A-Za-z0-9]{20,}"),
    "nebius": re.compile(r"[A-Za-z0-9_.-]{20,}"),
    "nlp-cloud": re.compile(r"[A-Za-z0-9]{20,}"),
    "ai21": re.compile(r"[A-Za-z0-9_-]{20,}"),
    "upstage": re.compile(r"[A-Za-z0-9]{20,}"),
    "modal": re.compile(r"[A-Za-z0-9_-]{20,}"),
    "hyperbolic": re.compile(r"[A-Za-z0-9._-]{20,}"),
    "inference-net": re.compile(r"[A-Za-z0-9_-]{20,}"),
    "scaleway-generative-apis": re.compile(r"[A-Za-z0-9_-]{20,}"),
    "novita": re.compile(r"sk_[A-Za-z0-9_-]{20,}"),
}


KEY_CONTAINER_SELECTORS: list[str] = [
    "input[readonly]",
    'input[type="text"][readonly]',
    "code",
    "pre",
    '[data-testid*="api-key" i]',
    '[data-testid*="key" i]',
    '[class*="api-key" i]',
    '[class*="apikey" i]',
    'div[role="dialog"] code',
    'div[role="dialog"] input',
]
