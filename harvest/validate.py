"""Live API-key validation.

After a key is harvested we know it *looks* right (it matched the per-provider
regex in ``selectors.py``), but not that it actually authenticates. This module
makes a single cheap, authenticated probe per provider — almost always
``GET {base}/v1/models`` with the key — and classifies the outcome.

It uses only the standard library (``urllib.request``) so it adds no runtime
dependency, and the network call goes through an injectable ``opener`` so the
whole thing is testable offline with zero network.
"""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

ValidationStatus = Literal["valid", "invalid", "unsupported", "error"]

# Auth styles:
#   bearer    -> Authorization: Bearer <key>
#   x_api_key -> x-api-key: <key>           (Anthropic; plus a version header)
#   query_key -> ?key=<key> appended to URL (Google Gemini)
AuthStyle = Literal["bearer", "x_api_key", "query_key"]


@dataclass(frozen=True)
class ValidationSpec:
    url: str
    auth: AuthStyle = "bearer"
    method: str = "GET"
    extra_headers: dict[str, str] = field(default_factory=dict)
    # HTTP codes that mean the key authenticated.
    success_codes: tuple[int, ...] = (200,)
    # HTTP codes that mean the key was rejected.
    invalid_codes: tuple[int, ...] = (401, 403)


@dataclass
class ValidationOutcome:
    status: ValidationStatus
    http_status: int | None = None
    latency_ms: int | None = None
    detail: str = ""


# Most providers are OpenAI-compatible: a GET on the models list returns 200 with
# a working key and 401/403 without. Providers with a bespoke auth scheme, a
# project/region-scoped base URL, or no account-agnostic probe are deliberately
# left out — they resolve to "unsupported" rather than a false "invalid".
VALIDATION_SPECS: dict[str, ValidationSpec] = {
    # --- OpenAI-compatible /models, bearer auth ---
    "groq": ValidationSpec("https://api.groq.com/openai/v1/models"),
    "cerebras": ValidationSpec("https://api.cerebras.ai/v1/models"),
    "mistral-la-plateforme": ValidationSpec("https://api.mistral.ai/v1/models"),
    "mistral-codestral-separate-endpoint": ValidationSpec("https://codestral.mistral.ai/v1/models"),
    "openrouter": ValidationSpec("https://openrouter.ai/api/v1/key"),
    "nvidia-nim": ValidationSpec("https://integrate.api.nvidia.com/v1/models"),
    "xai-grok": ValidationSpec("https://api.x.ai/v1/models"),
    "sambanova-cloud": ValidationSpec("https://api.sambanova.ai/v1/models"),
    "fireworks-ai": ValidationSpec("https://api.fireworks.ai/inference/v1/models"),
    "nebius": ValidationSpec("https://api.studio.nebius.com/v1/models"),
    "hyperbolic": ValidationSpec("https://api.hyperbolic.xyz/v1/models"),
    "inference-net": ValidationSpec("https://api.inference.net/v1/models"),
    "novita": ValidationSpec("https://api.novita.ai/v3/openai/models"),
    "alibaba-qwen-dashscope": ValidationSpec(
        "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/models"
    ),
    # --- bespoke but simple probes ---
    "google-gemini-ai-studio": ValidationSpec(
        "https://generativelanguage.googleapis.com/v1beta/models", auth="query_key"
    ),
    "anthropic": ValidationSpec(
        "https://api.anthropic.com/v1/models",
        auth="x_api_key",
        extra_headers={"anthropic-version": "2023-06-01"},
    ),
    "cohere": ValidationSpec("https://api.cohere.com/v1/models"),
    "github-models": ValidationSpec(
        "https://api.github.com/user",
        extra_headers={"Accept": "application/vnd.github+json"},
    ),
    "huggingface-inference-providers": ValidationSpec("https://huggingface.co/api/whoami-v2"),
    "cloudflare-workers-ai": ValidationSpec(
        "https://api.cloudflare.com/client/v4/user/tokens/verify"
    ),
}


def _build_request(spec: ValidationSpec, key: str) -> urllib.request.Request:
    url = spec.url
    headers: dict[str, str] = {"User-Agent": "api-harvest", **spec.extra_headers}
    if spec.auth == "bearer":
        headers["Authorization"] = f"Bearer {key}"
    elif spec.auth == "x_api_key":
        headers["x-api-key"] = key
    elif spec.auth == "query_key":
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}key={key}"
    return urllib.request.Request(url, method=spec.method, headers=headers)


def _classify(spec: ValidationSpec, code: int) -> ValidationOutcome:
    if code in spec.success_codes:
        return ValidationOutcome(status="valid", http_status=code, detail="authenticated")
    if code in spec.invalid_codes:
        return ValidationOutcome(status="invalid", http_status=code, detail=f"rejected (HTTP {code})")
    if code == 429:
        # Authenticated but rate-limited: the key works.
        return ValidationOutcome(status="valid", http_status=code, detail="rate limited (auth ok)")
    return ValidationOutcome(status="error", http_status=code, detail=f"unexpected HTTP {code}")


def validate_key(
    slug: str,
    key: str | None,
    *,
    opener: Callable = urllib.request.urlopen,
    timeout: float = 10.0,
) -> ValidationOutcome:
    """Probe one provider's key. Pure except for the injected ``opener``."""
    spec = VALIDATION_SPECS.get(slug)
    if spec is None:
        return ValidationOutcome(status="unsupported", detail="no validation endpoint for provider")
    if not key:
        return ValidationOutcome(status="error", detail="no key to validate")

    req = _build_request(spec, key)
    start = time.monotonic()
    try:
        resp = opener(req, timeout=timeout)
        code = getattr(resp, "status", None) or resp.getcode()
        outcome = _classify(spec, int(code))
    except urllib.error.HTTPError as e:
        outcome = _classify(spec, int(e.code))
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        outcome = ValidationOutcome(status="error", detail=f"{type(e).__name__}: {e}")
    outcome.latency_ms = int((time.monotonic() - start) * 1000)
    return outcome


async def validate_key_async(
    slug: str,
    key: str | None,
    *,
    opener: Callable = urllib.request.urlopen,
    timeout: float = 10.0,
) -> ValidationOutcome:
    """Async wrapper so the run pipeline can validate without blocking the loop."""
    import asyncio

    return await asyncio.to_thread(validate_key, slug, key, opener=opener, timeout=timeout)


def iso_now() -> str:
    return datetime.now(UTC).isoformat()
