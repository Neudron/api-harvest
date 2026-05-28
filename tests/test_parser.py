from __future__ import annotations

from pathlib import Path

import pytest

from harvest.parser import build_run_order, parse_providers_md

ROOT = Path(__file__).resolve().parent.parent
PROVIDERS_MD = ROOT / "providers.md"


def test_parse_returns_32_providers() -> None:
    specs = parse_providers_md(PROVIDERS_MD)
    assert len(specs) == 32, f"expected 32 providers, got {len(specs)}"


def test_tier_split() -> None:
    specs = parse_providers_md(PROVIDERS_MD)
    tier1 = [s for s in specs if s.tier == 1]
    tier2 = [s for s in specs if s.tier == 2]
    assert len(tier1) == 13, f"expected 13 tier-1, got {len(tier1)}"
    assert len(tier2) == 19, f"expected 19 tier-2, got {len(tier2)}"


def test_no_not_free_in_specs() -> None:
    specs = parse_providers_md(PROVIDERS_MD)
    slugs = {s.slug for s in specs}
    for not_free in ("openai", "together-ai", "deepinfra", "venice-ai", "github-copilot"):
        assert not_free not in slugs, f"NOT FREE provider {not_free} leaked through"


def test_google_first_in_run_order() -> None:
    specs = build_run_order(parse_providers_md(PROVIDERS_MD))
    assert specs[0].slug == "google-gemini-ai-studio"


def test_phone_required_set() -> None:
    specs = parse_providers_md(PROVIDERS_MD)
    phone = {s.slug for s in specs if s.requires_phone}
    expected = {
        "mistral-la-plateforme",
        "mistral-codestral-separate-endpoint",
        "nvidia-nim",
        "nlp-cloud",
    }
    assert phone == expected, f"phone required mismatch: {phone}"


def test_cc_required_set() -> None:
    specs = parse_providers_md(PROVIDERS_MD)
    cc = {s.slug for s in specs if s.requires_cc}
    expected = {"amazon-bedrock", "google-vertex-ai", "azure-openai"}
    assert cc == expected, f"cc required mismatch: {cc}"


def test_signup_urls_present() -> None:
    specs = parse_providers_md(PROVIDERS_MD)
    for s in specs:
        assert s.signup_url.startswith("http"), f"{s.slug} missing signup_url"


def test_env_vars_mapped_for_tier1() -> None:
    specs = parse_providers_md(PROVIDERS_MD)
    for s in specs:
        if s.tier == 1:
            assert s.env_var, f"{s.slug} (tier 1) has no env var"


@pytest.mark.parametrize(
    "slug,expected_env",
    [
        ("google-gemini-ai-studio", "GOOGLE_GENERATIVE_AI_API_KEY"),
        ("groq", "GROQ_API_KEY"),
        ("cerebras", "CEREBRAS_API_KEY"),
        ("xai-grok", "XAI_API_KEY"),
        ("anthropic", "ANTHROPIC_API_KEY"),
    ],
)
def test_specific_env_var_mappings(slug: str, expected_env: str) -> None:
    specs = parse_providers_md(PROVIDERS_MD)
    by_slug = {s.slug: s for s in specs}
    assert by_slug[slug].env_var == expected_env
