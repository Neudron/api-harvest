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

# Tighter regexes. Where the provider uses a known fixed prefix we anchor on it;
# where it doesn't, we still require length-appropriate text and rely on the
# per-provider "capture inside the modal" flow (handlers/base.py) to scope the match.
KEY_PATTERNS: dict[str, re.Pattern] = {
    "google-gemini-ai-studio": re.compile(r"AIza[0-9A-Za-z_-]{35,}"),
    "groq": re.compile(r"gsk_[A-Za-z0-9]{40,}"),
    "cerebras": re.compile(r"csk-[A-Za-z0-9-]{30,}"),
    # Mistral keys are 32 chars hex-ish. No fixed prefix → keep strict shape.
    "mistral-la-plateforme": re.compile(r"\b[A-Za-z0-9]{32}\b"),
    "mistral-codestral-separate-endpoint": re.compile(r"\b[A-Za-z0-9]{32}\b"),
    "openrouter": re.compile(r"sk-or-v\d-[A-Za-z0-9]{30,}"),
    # Cohere trial keys are mixed-case 40 chars exactly. Use \b anchors.
    "cohere": re.compile(r"\b[A-Za-z0-9]{40}\b"),
    # Vercel AI Gateway tokens start with vck_ on dashboard preview
    "vercel-ai-gateway": re.compile(r"vck_[A-Za-z0-9_-]{30,}"),
    "nvidia-nim": re.compile(r"nvapi-[A-Za-z0-9_-]{30,}"),
    "github-models": re.compile(r"(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})"),
    # Cloudflare tokens are 40-char alphanumeric+hyphen
    "cloudflare-workers-ai": re.compile(r"\b[A-Za-z0-9_-]{40}\b"),
    "huggingface-inference-providers": re.compile(r"hf_[A-Za-z0-9]{30,}"),
    "opencode-zen": re.compile(r"\b(?:sk-|oc_)[A-Za-z0-9_-]{30,}\b"),
    "xai-grok": re.compile(r"xai-[A-Za-z0-9]{30,}"),
    "alibaba-qwen-dashscope": re.compile(r"sk-[A-Za-z0-9]{30,}"),
    "anthropic": re.compile(r"sk-ant-[A-Za-z0-9_-]{30,}"),
    "sambanova-cloud": re.compile(r"\b[A-Za-z0-9-]{36,}\b"),
    "perplexity": re.compile(r"pplx-[A-Za-z0-9]{30,}"),
    # Fireworks keys are fw_ prefixed; fall back to length-bounded match
    "fireworks-ai": re.compile(r"(?:fw_[A-Za-z0-9]{30,}|\b[A-Za-z0-9]{48,}\b)"),
    # Baseten API keys start with various prefixes; capture inside modal
    "baseten": re.compile(r"\b[A-Za-z0-9._-]{30,}\b"),
    "nebius": re.compile(r"\beyJ[A-Za-z0-9._-]{50,}\b"),  # JWT-shape
    "nlp-cloud": re.compile(r"\b[a-f0-9]{40}\b"),  # 40-char lowercase hex
    "ai21": re.compile(r"\b[A-Za-z0-9_-]{40,}\b"),
    "upstage": re.compile(r"\bup_[A-Za-z0-9]{30,}\b"),
    "modal": re.compile(r"ak-[A-Za-z0-9-]{20,}"),
    "hyperbolic": re.compile(r"eyJ[A-Za-z0-9._-]{50,}"),  # JWT
    "inference-net": re.compile(r"\binference_[A-Za-z0-9_-]{20,}\b|\b[A-Za-z0-9]{40,}\b"),
    "scaleway-generative-apis": re.compile(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"
    ),
    "novita": re.compile(r"sk_[A-Za-z0-9_-]{30,}"),
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
