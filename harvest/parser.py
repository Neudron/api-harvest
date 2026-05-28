from __future__ import annotations

import re
from pathlib import Path

from harvest.models import ProviderSpec

_FIELD_RE = re.compile(r"^- \*\*([^:*]+):\*\*\s*(.+?)\s*$", re.MULTILINE)
_SECTION_HEADING_RE = re.compile(r"^### \d+\.\s+(.+?)\s*$", re.MULTILINE)
_TIER_HEADING_RE = re.compile(r"^## (TIER \d+|NOT FREE)\b", re.MULTILINE)
_ENV_VAR_RE = re.compile(r"^([A-Z][A-Z0-9_]+)=\s*#\s*(.+?)\s*$", re.MULTILINE)


def _slugify(name: str) -> str:
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    return name.strip("-")


def _split_top_sections(text: str) -> dict[str, str]:
    """Split file by ## TIER 1 / TIER 2 / NOT FREE headings."""
    matches = list(_TIER_HEADING_RE.finditer(text))
    sections: dict[str, str] = {}
    for i, m in enumerate(matches):
        label = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[label] = text[start:end]
    return sections


def _split_provider_blocks(section_text: str) -> list[tuple[str, str]]:
    """Return [(provider_name, block_text)] from a tier section."""
    matches = list(_SECTION_HEADING_RE.finditer(section_text))
    blocks: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        name = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(section_text)
        blocks.append((name, section_text[start:end]))
    return blocks


def _extract_fields(block: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for m in _FIELD_RE.finditer(block):
        key = m.group(1).strip().lower()
        fields[key] = m.group(2).strip()
    return fields


def _parse_bool(value: str | None) -> bool:
    if not value:
        return False
    v = value.strip().lower()
    return v.startswith("yes") or v == "true"


def _extract_env_var_map(text: str) -> dict[str, str]:
    """Map env var name → comment label (used as a hint for slug lookup)."""
    return {m.group(1): m.group(2) for m in _ENV_VAR_RE.finditer(text)}


# Map slug → env var. Built by inspecting providers.md & the env var section.
_SLUG_TO_ENV_VAR: dict[str, str] = {
    "google-gemini-ai-studio": "GOOGLE_GENERATIVE_AI_API_KEY",
    "groq": "GROQ_API_KEY",
    "cerebras": "CEREBRAS_API_KEY",
    "mistral-la-plateforme": "MISTRAL_API_KEY",
    "mistral-codestral-separate-endpoint": "CODESTRAL_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "cohere": "COHERE_API_KEY",
    "vercel-ai-gateway": "VERCEL_AI_GATEWAY_KEY",
    "nvidia-nim": "NVIDIA_API_KEY",
    "github-models": "GITHUB_TOKEN",
    "cloudflare-workers-ai": "CLOUDFLARE_API_TOKEN",
    "huggingface-inference-providers": "HF_TOKEN",
    "opencode-zen": "OPENCODE_API_KEY",
    "xai-grok": "XAI_API_KEY",
    "alibaba-qwen-dashscope": "DASHSCOPE_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "sambanova-cloud": "SAMBANOVA_API_KEY",
    "amazon-bedrock": "AWS_ACCESS_KEY_ID",
    "google-vertex-ai": "GOOGLE_APPLICATION_CREDENTIALS",
    "azure-openai": "AZURE_OPENAI_API_KEY",
    "perplexity": "PERPLEXITY_API_KEY",
    "fireworks-ai": "FIREWORKS_API_KEY",
    "baseten": "BASETEN_API_KEY",
    "nebius": "NEBIUS_API_KEY",
    "nlp-cloud": "NLPCLOUD_API_KEY",
    "ai21": "AI21_API_KEY",
    "upstage": "UPSTAGE_API_KEY",
    "modal": "MODAL_TOKEN",
    "hyperbolic": "HYPERBOLIC_API_KEY",
    "inference-net": "INFERENCE_NET_API_KEY",
    "scaleway-generative-apis": "SCALEWAY_API_KEY",
    "novita": "NOVITA_API_KEY",
}


def _free_models_list(value: str) -> list[str]:
    if not value:
        return []
    parts = re.split(r",\s*(?![^()]*\))", value)
    return [p.strip() for p in parts if p.strip()]


def parse_providers_md(path: Path) -> list[ProviderSpec]:
    text = Path(path).read_text(encoding="utf-8")
    sections = _split_top_sections(text)

    specs: list[ProviderSpec] = []
    order = 0
    for label, content in sections.items():
        if label.startswith("NOT FREE"):
            continue
        tier: int = 1 if "TIER 1" in label else 2
        for name, block in _split_provider_blocks(content):
            fields = _extract_fields(block)
            slug = _slugify(name)
            env_var = _SLUG_TO_ENV_VAR.get(slug)
            signup_url = fields.get("signup url", "")
            api_key_url = fields.get("api key url", signup_url)
            rate_limits = fields.get("rate limits") or fields.get("trial credits", "")
            free_models_raw = fields.get("free models", "")
            specs.append(
                ProviderSpec(
                    slug=slug,
                    name=name,
                    tier=tier,  # type: ignore[arg-type]
                    order_index=order,
                    signup_url=signup_url,
                    api_key_url=api_key_url,
                    env_var=env_var,
                    requires_cc=_parse_bool(fields.get("requires credit card")),
                    requires_phone=_parse_bool(fields.get("requires phone verification")),
                    rate_limits=rate_limits,
                    free_models=_free_models_list(free_models_raw),
                    gotchas=fields.get("gotchas", ""),
                    raw_section=block,
                )
            )
            order += 1
    return specs


def build_run_order(specs: list[ProviderSpec]) -> list[ProviderSpec]:
    """Return specs with Google AI Studio pinned first, then tier 1, then tier 2."""
    google = [s for s in specs if s.slug == "google-gemini-ai-studio"]
    tier1 = [s for s in specs if s.tier == 1 and s.slug != "google-gemini-ai-studio"]
    tier2 = [s for s in specs if s.tier == 2]
    return google + tier1 + tier2
