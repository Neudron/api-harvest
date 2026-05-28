from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from harvest.handlers.base import Handler

# Registry populated by importing the handler modules below.
HANDLER_REGISTRY: dict[str, type[Handler]] = {}


def register(slug: str):
    def deco(cls):
        HANDLER_REGISTRY[slug] = cls
        return cls

    return deco


# Import side-effects: each module decorates its class with @register(slug).
from harvest.handlers import (  # noqa: E402,F401
    ai21,
    alibaba_qwen,
    anthropic,
    aws_bedrock,
    azure_openai,
    baseten,
    cerebras,
    cloudflare,
    codestral,
    cohere,
    fireworks,
    gcp_vertex,
    github_models,
    google_aistudio,
    groq,
    huggingface,
    hyperbolic,
    inference_net,
    mistral,
    modal,
    nebius,
    nlpcloud,
    novita,
    nvidia,
    opencode_zen,
    openrouter,
    perplexity,
    sambanova,
    scaleway,
    upstage,
    vercel,
    xai,
)
