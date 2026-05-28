"""Asserts every KEY_PATTERNS entry matches a realistic sample and rejects
common false-positive strings (search results, request IDs, etc.).

When a new provider is added or a real key is observed, append to KEY_SAMPLES
and FALSE_POSITIVES below.
"""

from __future__ import annotations

import pytest

from harvest.selectors import KEY_PATTERNS

# Each provider → list of (sample, should_match) tuples.
KEY_SAMPLES: dict[str, list[tuple[str, bool]]] = {
    "google-gemini-ai-studio": [
        ("AIzaSyB7Wq4_xfFakeKeyForTestingOnlyABCDEFG", True),
        ("AIza", False),  # too short
        ("SomeUnrelatedTextHere", False),
    ],
    "groq": [
        ("gsk_" + "a" * 50, True),
        ("gsk_short", False),
        ("random_id_1234", False),
    ],
    "cerebras": [
        ("csk-" + "a" * 35, True),
        ("csk-short", False),
    ],
    "mistral-la-plateforme": [
        ("a1b2c3d4e5f6g7h8i9j0klmnopqrstuv", True),  # exactly 32
        ("short", False),
    ],
    "openrouter": [
        ("sk-or-v1-" + "a" * 40, True),
        ("sk-or-something", False),  # missing v\d-
    ],
    "anthropic": [
        ("sk-ant-" + "a" * 40, True),
        ("sk-something", False),
    ],
    "xai-grok": [
        ("xai-" + "B" * 40, True),
        ("xai-short", False),
    ],
    "perplexity": [
        ("pplx-" + "x" * 40, True),
        ("pplx-x", False),
    ],
    "huggingface-inference-providers": [
        ("hf_" + "Z" * 40, True),
        ("hf_x", False),
    ],
    "nvidia-nim": [
        ("nvapi-" + "x" * 40, True),
        ("nvapi-short", False),
    ],
    "github-models": [
        ("ghp_" + "a" * 40, True),
        ("github_pat_" + "a" * 60, True),
        ("ghp_short", False),
    ],
    "alibaba-qwen-dashscope": [
        ("sk-" + "a" * 40, True),
        ("not-a-key", False),
    ],
    "scaleway-generative-apis": [
        ("12345678-1234-1234-1234-1234567890ab", True),
        ("not-a-uuid", False),
    ],
    "novita": [
        ("sk_" + "a" * 40, True),
        ("sk_short", False),
    ],
    "modal": [
        ("ak-" + "X" * 30, True),
        ("modal-key-abcdef", False),
    ],
    "upstage": [
        ("up_" + "a" * 35, True),
        ("upstage-id-xx", False),
    ],
    "nlp-cloud": [
        ("0123456789abcdef0123456789abcdef01234567", True),  # 40 hex
        ("ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ", False),  # uppercase, not hex
    ],
    "vercel-ai-gateway": [
        ("vck_" + "a" * 40, True),
        ("randomstuff", False),
    ],
    "cohere": [
        ("aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890ABCD", True),  # 40 chars
    ],
    "cloudflare-workers-ai": [
        ("a" * 40, True),  # CF tokens are 40-char
        ("short", False),
    ],
}


@pytest.mark.parametrize("slug", sorted(KEY_PATTERNS.keys()))
def test_every_provider_has_a_pattern(slug: str) -> None:
    assert KEY_PATTERNS[slug] is not None
    assert KEY_PATTERNS[slug].pattern, f"empty pattern for {slug}"


@pytest.mark.parametrize(
    "slug,sample,expected",
    [(slug, s, exp) for slug, samples in KEY_SAMPLES.items() for s, exp in samples],
)
def test_pattern_matches_sample(slug: str, sample: str, expected: bool) -> None:
    pat = KEY_PATTERNS[slug]
    matched = bool(pat.search(sample))
    assert matched is expected, (
        f"{slug}: pattern={pat.pattern!r} sample={sample!r} "
        f"expected_match={expected} got={matched}"
    )


def test_no_pattern_matches_common_false_positives() -> None:
    """Patterns shouldn't match obvious garbage like generic UUIDs without prefixes,
    request IDs, version strings."""
    benign = [
        "ver=12345",
        "click here to continue",
        "https://example.com/path",
        "x",
    ]
    # Don't assert across ALL patterns (some are intentionally permissive once
    # we're inside a modal); just check the prefixed ones.
    for slug in ("groq", "anthropic", "xai-grok", "huggingface-inference-providers",
                 "openrouter", "perplexity", "nvidia-nim", "novita"):
        pat = KEY_PATTERNS[slug]
        for s in benign:
            assert not pat.search(s), f"{slug} matched benign string {s!r}"
